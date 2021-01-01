# (c) 2018-2020 The Tunfish Developers
import asyncio
import json
import os
import ssl
import sys
import time
from functools import partial

import six
from autobahn.asyncio.wamp import ApplicationRunner, ApplicationSession
from pyroute2 import IPDB, IPRoute


PATH = '/vagrant/etc/tunfish'
CERTPATH = '/vagrant/certs'


class Interface:

    def __init__(self):
        self.ifname = None
        self.ip = None

        from pyroute2 import WireGuard
        self.wg = WireGuard()

    def create(self, **kwargs):
        # Create WireGuard Interface
        self.ifname = kwargs.get('ifname')
        self.ip = kwargs.get('ip')

        with IPDB() as ip:
            dev = ip.create(kind='wireguard', ifname=self.ifname)
            dev.add_ip(self.ip)
            dev.up()
            dev.commit()

        self.wg.set(self.ifname, private_key=kwargs.get('privatekey'), listen_port=kwargs.get('listenport'))

    # noch nicht getestet
    def delete(self, **kwargs):
        self.ifname = kwargs.get('ifname')
        with IPDB() as ip:
            dev = ip.delete(ifname=self.ifname)
            dev.commit()

    def addpeer(self, **kwargs):
        # Create WireGuard object

        # build peer dict
        peer = {}
        for key in kwargs.keys():
            if key == 'publickey':
                peer = {**peer, **{'public_key': kwargs.get('publickey')}}
            if key == 'endpointaddr':
                peer = {**peer, **{'endpoint_addr': kwargs.get('endpointaddr')}}
            if key == 'endpointport':
                peer = {**peer, **{'endpoint_port': kwargs.get('endpointport')}}
            if key == 'keepalive':
                peer = {**peer, **{'persistent_keepalive': kwargs.get('keepalive')}}
            if key == 'allowedips':
                peer = {**peer, **{'allowed_ips': kwargs.get('allowedips')}}

        print(f"peer: {peer}")

        # add peer
        self.wg.set(self.ifname, peer=peer)

    def removepeer(self):
        pass


class TunfishClientSession(ApplicationSession):

    def __init__(self, *args, **kwargs):
        super(TunfishClientSession, self).__init__(*args, **kwargs)
        self.tfcfg = self.config.extra["tunfish_config"]

    async def onJoin(self, details):

        def got(started, msg, ff):
            print(f"result received")
            res = ff.result()
            duration = 1000. * (time.process_time() - started)
            print("{}: {} in {}".format(msg, res, duration))
            if msg == "REQUEST GATEWAY":
                # TODO: open interface

                interface = Interface()
                device = IPRoute()

                ip_and_mask = f"{self.tfcfg['ip']}/{self.tfcfg['mask']}"

                # new interface/wg control
                print(f"new control")
                interface.create(ifname=self.tfcfg['device_id'], ip=ip_and_mask, privatekey=self.tfcfg['wgprvkey'], listenport=42001)
                interface.addpeer(ifname=self.tfcfg['device_id'], publickey=res['wgpubkey'], endpointaddr=res['endpoint'], endpointport=res['listen_port'], keepalive=10, allowedips={'0.0.0.0/0'})

                # set rule
                # router.dev.rule('del', table=10, src='192.168.100.10/24')
                # router.dev.rule('add', table=10, src='172.16.100.15/16')
                # router.dev.rule('add', table=10, src='10.0.23.15/16')
                device.rule('add', table=10, src=ip_and_mask)
                # set route
                # router.dev.route('del', table=10, src='192.168.100.10/24', oif=idx)
                idx = device.link_lookup(ifname=self.tfcfg['device_id'])[0]
                device.route('add', table=10, src='10.0.42.15/16', gateway='10.0.23.15', oif=idx)

                # iptables
                import iptc
                chain = iptc.Chain(iptc.Table(iptc.Table.NAT), "POSTROUTING")
                rule = iptc.Rule()
                rule.out_interface = "tf-0815"
                target = iptc.Target(rule, "MASQUERADE")
                rule.target = target
                chain.insert_rule(rule)

        t1 = time.process_time()

        # task = self.call(u'com.portier.requestgateway', self.tfcfg, options=CallOptions(timeout=0))
        task = self.call(u'com.portier.request_gateway', self.tfcfg)
        task.add_done_callback(partial(got, t1, "REQUEST GATEWAY"))
        await asyncio.gather(task)

        t1 = time.process_time()
        task = self.call(u'com.portier.request_status')
        task.add_done_callback(partial(got, t1, "REQUEST STATUS"))
        await asyncio.gather(task)

        self.leave()

    def onDisconnect(self):
        # delete interface
        # reconnect
        asyncio.get_event_loop().stop()


class TunfishClient:

    def __init__(self):
        self.clientdata = None

    def start(self, conf):

        config_file = f"{PATH}/{conf}.json"

        with open(config_file, 'r') as f:
            self.clientdata = json.load(f)

        cf = f"{CERTPATH}/{self.clientdata['cf']}"
        kf = f"{CERTPATH}/{self.clientdata['kf']}"
        caf = f"{CERTPATH}/{self.clientdata['caf']}"

        client_ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        client_ctx.verify_mode = ssl.CERT_REQUIRED
        client_ctx.options |= ssl.OP_SINGLE_ECDH_USE
        client_ctx.options |= ssl.OP_NO_COMPRESSION
        client_ctx.load_cert_chain(certfile=cf, keyfile=kf)
        client_ctx.load_verify_locations(cafile=caf)
        client_ctx.set_ciphers('ECDH+AESGCM')

        # url = os.environ.get("AUTOBAHN_DEMO_ROUTER", u"wss://127.0.0.1:8080/ws")
        url = os.environ.get("AUTOBAHN_DEMO_ROUTER", u"wss://172.16.42.2:8080/ws")
        print(f"URL: {url}")
        if six.PY2 and type(url) == six.binary_type:
            url = url.decode('utf8')
        realm = u"tf_cb_router"
        runner = ApplicationRunner(url, realm, ssl=client_ctx, extra={'tunfish_config': self.clientdata})
        runner.run(TunfishClientSession)


def start():
    name = sys.argv[1]
    client = TunfishClient()
    client.start(name)

# (c) 2018-2020 The Tunfish Developers
import asyncio
import logging
import ssl
import time
from functools import partial

import six
from autobahn.asyncio import ApplicationSession
from autobahn.asyncio.wamp import ApplicationRunner

from tunfish.node.crypto import AsymmetricKey
from tunfish.node.model import WireGuardPeer
from tunfish.node.settings import TunfishClientSettings

logger = logging.getLogger(__name__)


class TunfishClientService:

    # TODO: Make autosign URL configurable.
    # autosign_url = "http://localhost:8000/pki/RootCA/autosign"

    def __init__(
        self, settings: TunfishClientSettings, start_interface_callback: callable
    ):
        self.settings: TunfishClientSettings = settings
        self.start_interface_callback = start_interface_callback
        self.autocrypt()

    def autocrypt(self):
        """
        Generate X.509 material and autosign it at CA.
        """

        # TODO: Check if certificate is about to expire.

        if not (
            self.settings.bus.private_key_path.exists()
            and self.settings.bus.certificate_path.exists()
        ):
            logger.info(f"Generating X.509 material")

            try:
                akey = AsymmetricKey()
                akey.make_rsa_key()
                akey.make_csr()

                # Submit CSR to CA for auto-signing.
                akey.submit_csr(self.settings.bus.autosign_url.geturi())

                # Save key material to disk.
                akey.save_key(self.settings.bus.private_key_path)
                akey.save_cert(self.settings.bus.certificate_path)

            except Exception as ex:
                logger.error(f"Generating X.509 material failed: {ex}")

    def start(self):

        url = self.settings.bus.broker_url.geturi()
        logger.info(f"Connecting to broker address {url}")
        if six.PY2 and type(url) == six.binary_type:
            url = url.decode("utf8")

        # FIXME: This is still hardcoded.
        realm = "tf_cb_router"

        extra = {
            "tunfish_settings": self.settings,
            "start_interface_callback": self.start_interface_callback,
        }
        runner = ApplicationRunner(url, realm, ssl=self.make_ssl_context(), extra=extra)
        runner.run(TunfishClientSession)

    def make_ssl_context(self):

        logger.info(f"Loading X.509 material")

        if not self.settings.bus.certificate_path.exists():
            logger.error(f"File not found: {self.settings.bus.certificate_path}")

        if not self.settings.bus.private_key_path.exists():
            logger.error(f"File not found: {self.settings.bus.private_key_path}")

        client_ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        client_ctx.verify_mode = ssl.CERT_REQUIRED
        client_ctx.options |= ssl.OP_SINGLE_ECDH_USE
        client_ctx.options |= ssl.OP_NO_COMPRESSION
        client_ctx.load_cert_chain(
            certfile=self.settings.bus.certificate_path,
            keyfile=self.settings.bus.private_key_path,
        )

        # TODO: Review - do we really need this?
        # client_ctx.load_verify_locations(cafile=caf)

        client_ctx.set_ciphers("ECDH+AESGCM")

        return client_ctx


class TunfishClientSession(ApplicationSession):
    def __init__(self, *args, **kwargs):
        super(TunfishClientSession, self).__init__(*args, **kwargs)
        self.settings: TunfishClientSettings = self.config.extra["tunfish_settings"]
        self.start_interface_callback = self.config.extra["start_interface_callback"]

    async def onJoin(self, details):

        logger.info("Joined messaging bus")

        def got(started, msg, ff):
            logger.info(f"Result received")
            res = ff.result()
            duration = 1000.0 * (time.process_time() - started)
            logger.info("{}: {} in {}".format(msg, res, duration))
            if msg == "REQUEST GATEWAY":

                peer_info = WireGuardPeer(
                    persistent_keepalive=10, allowed_ips={"0.0.0.0/0"}
                )

                if "wgpubkey" in res:
                    peer_info.public_key = res["wgpubkey"]
                if "endpoint" in res:
                    peer_info.endpoint_addr = res["endpoint"]
                if "listen_port" in res:
                    peer_info.endpoint_port = res["listen_port"]

                self.start_interface_callback(peer_info=peer_info)

        t1 = time.process_time()

        message = {
            "device_id": self.settings.device_id,
            "wgpubkey": self.settings.wireguard.public_key,
        }
        # task = self.call(u'com.portier.requestgateway', message, options=CallOptions(timeout=0))
        task = self.call("com.portier.request_gateway", message)
        task.add_done_callback(partial(got, t1, "REQUEST GATEWAY"))
        await asyncio.gather(task)

        t1 = time.process_time()
        task = self.call("com.portier.request_status")
        task.add_done_callback(partial(got, t1, "REQUEST STATUS"))
        await asyncio.gather(task)

        self.leave()

    def onDisconnect(self):
        # delete interface
        # reconnect
        asyncio.get_event_loop().stop()

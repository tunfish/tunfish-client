# (c) 2018-2020 The Tunfish Developers
import logging
from pathlib import Path

from pyroute2 import IPRoute

from tunfish.node.model import WireGuardInterface, WireGuardPeer
from tunfish.node.service import TunfishClientService
from tunfish.node.settings import TunfishClientSettings

logger = logging.getLogger(__name__)


class TunfishClient:
    def __init__(self, config_file: Path):
        self.settings: TunfishClientSettings = TunfishClientSettings()
        self.settings.load(config_file)

    def start_service(self):
        service = TunfishClientService(
            settings=self.settings, start_interface_callback=self.start_interface
        )
        service.start()

    def start_interface(self, peer_info: WireGuardPeer):

        ip_and_mask = self.settings.wireguard.address
        wg_interface = WireGuardInterface(
            ifname=self.settings.device_id, ip=ip_and_mask
        )

        # FIXME: This is still hardcoded.
        listenport = 41001

        # New interface/wg control.
        logger.info(f"new control")
        wg_interface.create(
            privatekey=self.settings.wireguard.private_key, listenport=listenport
        )
        wg_interface.add_peer(peer_info=peer_info)

        # TODO: Maybe refactor all of this into "WireGuardInterface"...
        device = IPRoute()

        # set rule
        # router.dev.rule('del', table=10, src='192.168.100.10/24')
        # router.dev.rule('add', table=10, src='172.16.100.15/16')
        # router.dev.rule('add', table=10, src='10.0.23.15/16')
        device.rule("add", table=10, src=ip_and_mask)
        # set route
        # router.dev.route('del', table=10, src='192.168.100.10/24', oif=idx)
        idx = device.link_lookup(ifname=self.settings.device_id)[0]
        # FIXME: This is still hardcoded.
        device.route(
            "add", table=10, src="10.0.42.15/16", gateway="10.0.23.15", oif=idx
        )

        # iptables
        import iptc

        chain = iptc.Chain(iptc.Table(iptc.Table.NAT), "POSTROUTING")
        rule = iptc.Rule()
        # FIXME: This is still hardcoded.
        rule.out_interface = "tf-0815"
        target = iptc.Target(rule, "MASQUERADE")
        rule.target = target
        chain.insert_rule(rule)

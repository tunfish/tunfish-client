# (c) 2018-2020 The Tunfish Developers
import dataclasses
import logging

from pyroute2 import IPDB

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class WireGuardPeer:

    public_key: str = None
    endpoint_addr: str = None
    endpoint_port: int = None
    persistent_keepalive: int = None
    allowed_ips: set = None

    def asdict(self, filter_unset=True):
        data = dataclasses.asdict(self)
        if filter_unset:
            data = {key: value for key, value in data.items() if value is not None}
        return data


@dataclasses.dataclass
class WireGuardInterface:

    ifname: str
    ip: str

    def __post_init__(self):
        from pyroute2 import WireGuard

        self.wg = WireGuard()

    def create(self, **kwargs):
        """
        Create WireGuard Interface
        """

        with IPDB() as ip:
            dev = ip.create(kind="wireguard", ifname=self.ifname)
            dev.add_ip(self.ip)
            dev.up()
            dev.commit()

        self.wg.set(
            self.ifname,
            private_key=kwargs.get("privatekey"),
            listen_port=kwargs.get("listenport"),
        )

    # noch nicht getestet
    def delete(self, **kwargs):
        self.ifname = kwargs.get("ifname")
        with IPDB() as ip:
            dev = ip.delete(ifname=self.ifname)
            dev.commit()

    def add_peer(self, peer_info: WireGuardPeer):

        # Build peer dictionary.
        peer = peer_info.asdict()
        logger.info(f"WireGuardInterface.add_peer: {peer}")

        # Add peer.
        self.wg.set(self.ifname, peer=peer)

    def remove_peer(self):
        pass

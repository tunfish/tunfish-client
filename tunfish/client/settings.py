# (c) 2018-2020 The Tunfish Developers
from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from pathlib import Path
from typing import Union

import json5


@dataclass
class BusSettings:

    broker_url: str = None
    private_key_path: Path = None
    certificate_path: Path = None


@dataclass
class WireGuardSettings:

    network_name: str = None
    private_key: str = None
    public_key: str = None
    client_ip: Union[IPv4Network, IPv6Network] = None
    vpn_ip: Union[IPv4Address, IPv6Address] = None


@dataclass
class TunfishClientSettings:

    path: Path = None
    device_id: str = None
    bus: BusSettings = field(default_factory=BusSettings)
    wireguard: WireGuardSettings = field(default_factory=WireGuardSettings)

    def load(self, filename: Path):

        filename = filename.resolve().absolute()
        configfile_name = filename.stem
        configfile_path = filename.parent

        settings = {}
        with open(filename, 'r') as f:
            settings = json5.load(f)
            self.path = filename

        version = int(settings.get("version", "1"))

        if version == 1:

            self.device_id = settings.get("device_id")

            self.bus.broker_url = settings.get("bus_broker_url")
            if "kf" in settings:
                self.bus.private_key_path = configfile_path / settings["kf"]
            if "cf" in settings:
                self.bus.certificate_path = configfile_path / settings["cf"]

            wireguard_settings = settings.get("wireguard", {})
            self.wireguard.network_name = wireguard_settings.get("network")
            if "ip" in wireguard_settings and "mask" in wireguard_settings:
                self.wireguard.client_ip = IPv4Network(f"{wireguard_settings['ip']}/{wireguard_settings['mask']}")
            if "vpn_ip" in wireguard_settings:
                self.wireguard.vpn_ip = IPv4Address(wireguard_settings["vpn_ip"])

        # Fill in the gaps.
        if not self.bus.private_key_path:
            self.bus.private_key_path = configfile_path / f"{configfile_name}-bus.key"
        if not self.bus.certificate_path:
            self.bus.certificate_path = configfile_path / f"{configfile_name}-bus.pem"

import ipaddress
from pathlib import Path

import uritools

from tunfish.client.settings import TunfishClientSettings


def test_0815():
    configfile = Path("./examples/tf-0815.json5")
    configpath = configfile.parent.absolute()
    settings = TunfishClientSettings()
    settings.load(configfile)

    assert settings.path == configfile.absolute()
    assert settings.device_id == "tf-0815"

    assert settings.bus.broker_url == uritools.urisplit("wss://172.16.42.2:8080/ws")
    assert settings.bus.private_key_path == configpath / "tf-0815.key"
    assert settings.bus.certificate_path == configpath / "tf-0815.pem"

    assert settings.wireguard.endpoint == uritools.urisplit("null://172.16.100.16:51820")
    assert settings.wireguard.private_key == "CyqisJ1eVXzjkMocWsRkAaXyXMBOxpDLFgTdDQTtXjM="
    assert settings.wireguard.public_key == "/46NfRLITFUDZAb1ZANxqrGb7hPsciTX0cFEXZBUKjk="
    assert settings.wireguard.address == ipaddress.IPv4Network("10.0.23.15/32")
    assert settings.wireguard.network_name == "swarmone"

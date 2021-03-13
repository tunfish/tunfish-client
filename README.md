# Tunfish Client

## About
Bootstrap and maintain connection to Tunfish network.
Please note this software is in its very early stages.

## Synopsis
```bash
tf-node --config examples/tf-0815.json5
```

## Example configuration
```json5
{

  // Configuration version
  "version": 1,

  // The device ID
  "device_id": "tf-0815",

  // How to connect and authenticate with WAMP message broker
  "bus": {
    "autosign": "http://localhost:8000/pki/autosign",
    "broker": "wss://172.16.42.2:8080/ws",
    "key": "tf-0815-bus.key",
    "cert": "tf-0815-bus.pem",
    // TODO: Is it really needed?
    //"cacert": "ca-bus.pem",
  },

  // WireGuard settings
  // https://wiki.archlinux.org/index.php/WireGuard#Client_config
  "wireguard": {
    "endpoint": "172.16.100.16:51820",
    "private_key": "CyqisJ1eVXzjkMocWsRkAaXyXMBOxpDLFgTdDQTtXjM=",
    "public_key": "/46NfRLITFUDZAb1ZANxqrGb7hPsciTX0cFEXZBUKjk=",
    "address": "10.0.23.15/32",
    "network": "swarmone",
  },

}
```

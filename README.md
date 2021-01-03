# Tunfish Client

## About
Bootstrap and maintain connection to Tunfish network.
Please note this software is in its very early stages.

## Synopsis
```bash
tf-client --config examples/tf-0815.json5
```

## Example configuration
```json5
{

  // The device ID
  "device_id": "tf-0815",

  // WireGuard private and public key.
  "wgprvkey": "CyqisJ1eVXzjkMocWsRkAaXyXMBOxpDLFgTdDQTtXjM=",
  "wgpubkey": "/46NfRLITFUDZAb1ZANxqrGb7hPsciTX0cFEXZBUKjk=",

  // Client network information.
  "ip": "10.0.23.15",
  "mask": "32",
  "type": "client",

}
```

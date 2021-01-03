from cryptography.x509 import CertificateSigningRequest

from tunfish.client.crypto import AsymmetricKey


def test_crypto():
    akey = AsymmetricKey()
    akey.make_rsa_key()
    akey.make_csr()

    assert isinstance(akey.csr, CertificateSigningRequest)

from pars_shared import crypto


def test_sign_verify_roundtrip():
    priv, pub = crypto.generate_keypair()
    message = b"grant payload"
    signature = crypto.sign(priv, message)
    assert crypto.verify(pub, message, signature) is True


def test_verify_rejects_tampered_message():
    priv, pub = crypto.generate_keypair()
    signature = crypto.sign(priv, b"grant payload")
    assert crypto.verify(pub, b"grant payloae", signature) is False


def test_verify_rejects_wrong_key():
    priv, _pub = crypto.generate_keypair()
    _other_priv, other_pub = crypto.generate_keypair()
    message = b"grant payload"
    signature = crypto.sign(priv, message)
    assert crypto.verify(other_pub, message, signature) is False


def test_verify_rejects_malformed_key():
    assert crypto.verify(b"not a real key", b"message", b"not a real sig") is False

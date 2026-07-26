from insightbridge.crypto import decrypt_json, encrypt_json


def test_encrypt_roundtrip_without_fernet_key(monkeypatch):
    monkeypatch.setattr("insightbridge.crypto.settings.encryption_key", None)
    data = {"url": "postgresql://u:p@localhost/db"}
    blob = encrypt_json(data)
    assert blob.startswith("plain:")
    assert decrypt_json(blob) == data

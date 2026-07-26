from insightbridge.auth_jwt import create_access_token, decode_access_token


def test_jwt_roundtrip():
    token = create_access_token(
        user_id="00000000-0000-4000-a000-000000000002",
        org_id="00000000-0000-4000-a000-000000000001",
        role="owner",
        email="demo@insightbridge.local",
    )
    payload = decode_access_token(token)
    assert payload["sub"] == "00000000-0000-4000-a000-000000000002"
    assert payload["org_id"] == "00000000-0000-4000-a000-000000000001"

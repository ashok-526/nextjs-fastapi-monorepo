import pytest


@pytest.mark.anyio
async def test_auth_signup_login(client):
    # Signup
    res = await client.post("/auth/signup", json={
        "email": "alice@example.com",
        "username": "alice",
        "password": "password123"
    })
    assert res.status_code in (200, 201)
    token = res.json()["access_token"]
    assert token

    # Login by email
    res = await client.post("/auth/login", json={
        "email_or_username": "alice@example.com",
        "password": "password123"
    })
    assert res.status_code == 200
    token2 = res.json()["access_token"]
    assert token2

    # Login by username
    res = await client.post("/auth/login", json={
        "email_or_username": "alice",
        "password": "password123"
    })
    assert res.status_code == 200


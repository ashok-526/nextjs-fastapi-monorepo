import pytest


async def _signup(client, email, username, password="password123"):
    r = await client.post("/auth/signup", json={"email": email, "username": username, "password": password})
    assert r.status_code in (200, 201)
    return r.json()["access_token"]


@pytest.mark.anyio
async def test_friend_request_feed(client):
    # Users A and B
    token_a = await _signup(client, "a@example.com", "usera")
    token_b = await _signup(client, "b@example.com", "userb")

    # A sends friend request to B
    r = await client.post("/social/friend-requests/userb", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200
    req_id = r.json()["id"]

    # B accepts
    r = await client.post(f"/social/friend-requests/{req_id}/accept", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 200

    # B creates a post
    r = await client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"body": "from B", "visibility": "public"},
    )
    assert r.status_code in (200, 201)

    # A fetches feed and should see B's post
    r = await client.get("/feed", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200
    items = r.json()["data"]
    assert any(p["body"] == "from B" for p in items)


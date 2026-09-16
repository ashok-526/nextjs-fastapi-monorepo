import pytest


async def _signup(client, email, username, password="password123"):
    r = await client.post("/auth/signup", json={"email": email, "username": username, "password": password})
    assert r.status_code in (200, 201)
    return r.json()["access_token"]


@pytest.mark.anyio
async def test_post_react_comment_flow(client):
    token = await _signup(client, "bob@example.com", "bob")

    # Create post
    r = await client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"body": "hello world", "visibility": "public"},
    )
    assert r.status_code in (200, 201)
    post = r.json()

    # Get post (first time - should return 200)
    r = await client.get(f"/posts/{post['id']}")
    assert r.status_code == 200
    etag = r.headers.get("etag")

    # Fetch again with ETag -> 304
    if etag:
        r = await client.get(f"/posts/{post['id']}", headers={"If-None-Match": etag})
        assert r.status_code == 304

    # React
    r = await client.post(
        f"/posts/{post['id']}/react",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "like"},
    )
    assert r.status_code == 200

    # Comment
    r = await client.post(
        f"/posts/{post['id']}/comments",
        headers={"Authorization": f"Bearer {token}"},
        json={"body": "nice"},
    )
    assert r.status_code in (200, 201)

    # List comments
    r = await client.get(f"/posts/{post['id']}/comments")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1


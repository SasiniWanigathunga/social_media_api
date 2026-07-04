import pytest
from httpx import AsyncClient
from social_media_api import security

pytestmark = pytest.mark.anyio

async def create_post(content: str, async_client: AsyncClient, logged_in_token: str):
    response = await async_client.post("/posts", json={"content": content}, headers={"Authorization": f"Bearer {logged_in_token}"})
    return response.json()

async def create_comment(comments: str, post_id: int, async_client: AsyncClient, logged_in_token: str):
    response = await async_client.post("/comments", json={"comments": comments, "post_id": post_id}, headers={"Authorization": f"Bearer {logged_in_token}"})
    return response.json()

@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post("Test post content", async_client, logged_in_token)

@pytest.fixture()
async def created_comment(async_client: AsyncClient, created_post: dict, logged_in_token: str):
    return await create_comment("Test comment content", created_post["id"], async_client, logged_in_token)

@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient, registered_user: dict, logged_in_token: str):
    content = "This is a test post"
    response = await async_client.post(
        "/posts", 
        json={"content": content},
        headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 201
    assert {"id": 1, "content": content, "user_id": registered_user["id"]}.items() <= response.json().items()

@pytest.mark.anyio
async def test_create_post_missing_data(async_client: AsyncClient, logged_in_token: str):
    response = await async_client.post("/posts", json={}, headers={"Authorization": f"Bearer {logged_in_token}"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/posts")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json() == [created_post]

@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict, registered_user: dict, logged_in_token: str):
    comments = "Test comment"
    response = await async_client.post("/comments", json={"comments": comments, "post_id": created_post["id"]}, headers={"Authorization": f"Bearer {logged_in_token}"})

    assert response.status_code == 201
    assert {"id": 1, "comments": comments, "post_id": created_post["id"], "user_id": registered_user["id"]}.items() <= response.json().items()

@pytest.mark.anyio
async def test_get_comments_for_post(async_client: AsyncClient, created_post: dict, created_comment: dict):
    response = await async_client.get(f"/posts/{created_post['id']}/comments")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json() == [created_comment]

@pytest.mark.anyio
async def test_get_comments_for_post_without_comments(async_client: AsyncClient, created_post: dict):
    response = await async_client.get(f"/posts/{created_post['id']}/comments")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.anyio
async def test_get_post_with_comments(async_client: AsyncClient, created_post: dict, created_comment: dict):
    response = await async_client.get(f"/posts/{created_post['id']}")
    assert response.status_code == 200
    assert response.json() == {
        "post": created_post,
        "comments": [created_comment]
    }

@pytest.mark.anyio
async def test_get_comments_for_nonexistent_post(async_client: AsyncClient, created_post: dict, created_comment: dict):
    response = await async_client.get("/posts/999/comments")
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}

@pytest.mark.anyio
async def test_create_post_expired_token(async_client: AsyncClient, registered_user: dict, mocker):
    mocker.patch("social_media_api.security.access_token_expire_miniutes", return_value=-1)
    token = security.create_access_token(registered_user["email"])
    response = await async_client.post(
        "/posts",
        json={"content": "This is a test post"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]
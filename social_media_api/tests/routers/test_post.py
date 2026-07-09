import pytest
from httpx import AsyncClient
from social_media_api import security

pytestmark = pytest.mark.anyio


async def create_post(content: str, async_client: AsyncClient, logged_in_token: str):
    response = await async_client.post(
        "/posts",
        json={"content": content},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_comment(
    comments: str, post_id: int, async_client: AsyncClient, logged_in_token: str
):
    response = await async_client.post(
        "/comments",
        json={"comments": comments, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def like_post(post_id: int, async_client: AsyncClient, logged_in_token: str):
    response = await async_client.post(
        "/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post("Test post content", async_client, logged_in_token)


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    return await create_comment(
        "Test comment content", created_post["id"], async_client, logged_in_token
    )


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str
):
    content = "This is a test post"
    response = await async_client.post(
        "/posts",
        json={"content": content},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201
    assert {
        "id": 1,
        "content": content,
        "user_id": confirmed_user["id"],
        "image_url": None,
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_missing_data(
    async_client: AsyncClient, logged_in_token: str
):
    response = await async_client.post(
        "/posts", json={}, headers={"Authorization": f"Bearer {logged_in_token}"}
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 201
    assert {
        "id": 1,
        "post_id": created_post["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/posts")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert created_post.items() <= response.json()[0].items()
    assert response.json() == [{**created_post, "likes": 0}]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        ("newest", [2, 1]),
        ("oldest", [1, 2]),
    ],
)
async def test_get_all_posts_sorted(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    await create_post("First post", async_client, logged_in_token)
    await create_post("Second post", async_client, logged_in_token)

    response = await async_client.get("/posts", params={"sorting": sorting})
    data = response.json()
    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_sorted_most_liked(
    async_client: AsyncClient, logged_in_token: str
):
    await create_post("First post", async_client, logged_in_token)
    await create_post("Second post", async_client, logged_in_token)
    await like_post(1, async_client, logged_in_token)

    response = await async_client.get("/posts", params={"sorting": "most_liked"})
    data = response.json()
    post_ids = [post["id"] for post in data]
    expected_order = [1, 2]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_get_all_posts_wrong_sorting(
    async_client: AsyncClient,
):
    response = await async_client.get("/posts", params={"sorting": "invalid_sorting"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    confirmed_user: dict,
    logged_in_token: str,
):
    comments = "Test comment"
    response = await async_client.post(
        "/comments",
        json={"comments": comments, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201
    assert {
        "id": 1,
        "comments": comments,
        "post_id": created_post["id"],
        "user_id": confirmed_user["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_for_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/posts/{created_post['id']}/comments")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_for_post_without_comments(
    async_client: AsyncClient, created_post: dict
):
    response = await async_client.get(f"/posts/{created_post['id']}/comments")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/posts/{created_post['id']}")
    assert response.status_code == 200
    assert response.json() == {
        "post": {**created_post, "likes": 0},
        "comments": [created_comment],
    }


@pytest.mark.anyio
async def test_get_comments_for_nonexistent_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get("/posts/999/comments")
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, confirmed_user: dict, mocker
):
    mocker.patch(
        "social_media_api.security.access_token_expire_minutes", return_value=-1
    )
    token = security.create_access_token(confirmed_user["email"])
    response = await async_client.post(
        "/posts",
        json={"content": "This is a test post"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]

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
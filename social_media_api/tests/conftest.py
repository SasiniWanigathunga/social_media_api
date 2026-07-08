import os
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient, Response, Request

os.environ["ENV_STATE"] = "test"
from social_media_api.database import database, user_table  # noqa: E402
from social_media_api.main import app # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)

@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    await database.connect()
    yield
    await database.disconnect()

@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=client.base_url
    ) as ac:
        yield ac

@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_data = {"email": "test@email.com", "password": "testpassword"}
    await async_client.post("/register", json=user_data)
    query = user_table.select().where(user_table.c.email == user_data["email"])
    user = await database.fetch_one(query)
    user_data["id"] = user["id"]
    return user_data

@pytest.fixture()
async def confirmed_user(registered_user: dict) -> dict:
    query = (
        user_table.update()
        .where(user_table.c.email == registered_user["email"])
        .values(confirmed=True)
    )
    await database.execute(query)
    return registered_user

@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict) -> str:
    response = await async_client.post(
        "/token",
        json=confirmed_user,
    )
    return response.json()["access_token"]

@pytest.fixture(autouse=True)
def mock_httpx_client(mocker):
    mocked_client = mocker.patch("social_media_api.tasks.httpx.AsyncClient")
    mocked_async_client = Mock()
    response = Response(status_code=200, content="",request=Request("POST", "//"))
    mocked_async_client.post = AsyncMock(return_value=response)
    mocked_client.return_value.__aenter__.return_value = mocked_async_client

    return mocked_async_client
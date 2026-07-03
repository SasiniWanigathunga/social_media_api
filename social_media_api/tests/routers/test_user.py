import pytest
from httpx import AsyncClient


async def register_user(async_client: AsyncClient, email: str, password: str):
    response = await async_client.post(
        "/register", json={"email": email, "password": password}
    )
    return response


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    response = await register_user(async_client, "test@example.com", "testpassword")
    assert response.status_code == 201
    assert "User registered successfully" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_existing_user(async_client: AsyncClient, registered_user: dict):
    response = await register_user(
        async_client, registered_user["email"], registered_user["password"]
    )
    assert response.status_code == 400
    assert "User already exists" in response.json()["detail"]

@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post(
        "/token",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.anyio
async def test_login_nonexistent_user(async_client: AsyncClient):
    response = await async_client.post(
        "/token",
        json={"email": "test1@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


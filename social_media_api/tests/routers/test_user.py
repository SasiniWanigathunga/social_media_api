import pytest
from httpx import AsyncClient
from fastapi import Request


async def register_user(async_client: AsyncClient, email: str, password: str):
    response = await async_client.post(
        "/register", json={"email": email, "password": password}
    )
    return response


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    response = await register_user(async_client, "test@example.com", "testpassword")
    assert response.status_code == 201
    assert "User created successfully" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_existing_user(async_client: AsyncClient, registered_user: dict):
    response = await register_user(
        async_client, registered_user["email"], registered_user["password"]
    )
    assert response.status_code == 400
    assert "User already exists" in response.json()["detail"]

@pytest.mark.anyio
async def test_confirm_user(async_client: AsyncClient, mocker):
    spy = mocker.spy(Request, "url_for")
    await register_user(async_client, "test@example.com", "testpassword")
    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)
    assert response.status_code == 200
    assert "User confirmed" in response.json()["detail"]
    
@pytest.mark.anyio
async def test_confirm_user_invalid_token(async_client: AsyncClient):
    response = await async_client.get("/confirm/invalidtoken")
    assert response.status_code == 401

@pytest.mark.anyio
async def test_confirm_user_expired_token(async_client: AsyncClient, mocker):
    mocker.patch("social_media_api.security.confirmation_token_expire_minutes", return_value=-1)
    spy = mocker.spy(Request, "url_for")
    await register_user(async_client, "test@example.com", "testpassword")
    confirmation_url = str(spy.spy_return)
    response = await async_client.get(confirmation_url)
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]

@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post(
        "/token",
        json={"email": confirmed_user["email"], "password": confirmed_user["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.anyio
async def test_login_user_not_confirmed(async_client: AsyncClient, registered_user: dict):
    response = await async_client.post(
        "/token",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 401
    assert "User account is not confirmed" in response.json()["detail"]

@pytest.mark.anyio
async def test_login_nonexistent_user(async_client: AsyncClient):
    response = await async_client.post(
        "/token",
        json={"email": "test1@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


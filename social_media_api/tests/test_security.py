import pytest

from social_media_api import security

pytestmark = pytest.mark.anyio


async def test_access_token_expire_minutes():
    assert security.access_token_expire_miniutes() == 30


async def test_create_access_token():
    token = security.create_access_token("1234")
    assert {"sub": "1234"}.items() <= security.jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()


async def test_get_hashed_password():
    password = "testpassword"
    assert security.verify_password(password, security.get_hashed_password(password))


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])
    assert user is not None
    assert user["email"] == registered_user["email"]


async def test_get_user_not_found():
    user = await security.get_user("test1@example.com")
    assert user is None

@pytest.mark.anyio
async def test_authenticate_user(registered_user: dict):
    user = await security.authenticate_user(
        registered_user["email"], registered_user["password"]
    )
    assert user is not None
    assert user.email == registered_user["email"]

@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test1.email.com", "wrongpassword")

@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(
            registered_user["email"], "wrongpassword"
        )
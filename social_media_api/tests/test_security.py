import pytest

from social_media_api import security

pytestmark = pytest.mark.anyio


@pytest.mark.anyio
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

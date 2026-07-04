import pytest

from social_media_api import security

pytestmark = pytest.mark.anyio


async def test_access_token_expire_minutes():
    assert security.access_token_expire_minutes() == 30

async def test_confirmation_token_expire_minutes():
    assert security.confirmation_token_expire_minutes() == 1440

async def test_create_access_token():
    token = security.create_access_token("1234")
    assert {"sub": "1234"}.items() <= security.jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()

async def test_create_confirmation_token():
    token = security.create_confirmation_token("1234")
    assert {"sub": "1234", "type": "confirmation"}.items() <= security.jwt.decode(
        token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM]
    ).items()

@pytest.mark.parametrize(
    "method,expected_type",
    [("create_access_token", "access"), ("create_confirmation_token", "confirmation")],
)
async def test_get_subject_for_security_token_valid(method: str, expected_type: str):
    email = "test@example.com"
    token = getattr(security, method)(email)
    subject = security.get_subject_for_security_token(token, expected_type)
    assert subject == email

@pytest.mark.parametrize(
    "expire_method,method,expected_type",
    [("access_token_expire_minutes", "create_access_token", "access"), ("confirmation_token_expire_minutes", "create_confirmation_token", "confirmation")]
)
async def test_get_subject_for_security_token_expired(mocker, method: str, expire_method: str, expected_type: str):
    mocker.patch(
        f"social_media_api.security.{expire_method}", return_value=-1
    )
    email = "test@example.com"
    token = getattr(security, method)(email)
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_security_token(token, expected_type)
    assert "Token has expired" == str(exc_info.value.detail)

@pytest.mark.parametrize(
    "expected_type",
    ["access", "confirmation"]
)
async def test_get_subject_for_security_token_invalid(expected_type: str):
    token = "invalidtoken"
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_security_token(token, expected_type)
    assert "Invalid token" == str(exc_info.value.detail)

@pytest.mark.parametrize(
    "method,expected_type",
    [("create_access_token", "access"), ("create_confirmation_token", "confirmation")]
)
async def test_get_subject_for_security_token_missing_sub(method: str, expected_type: str):
    email = "test@example.com"
    token = getattr(security, method)(email)
    payload = security.jwt.decode(token, key=security.SECRET_KEY, algorithms=[security.ALGORITHM])
    del payload["sub"]
    modified_token = security.jwt.encode(payload, key=security.SECRET_KEY, algorithm=security.ALGORITHM)
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_security_token(modified_token, expected_type)
    assert "Token is missing 'sub' claim" == str(exc_info.value.detail)

@pytest.mark.parametrize(
    "method,expected_wrong_type",
    [("create_access_token", "confirmation"), ("create_confirmation_token", "access")]
)
async def test_get_subject_for_security_token_wrong_type(method: str, expected_wrong_type: str):
    email = "test@example.com"
    token = getattr(security, method)(email)
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_security_token(token, expected_wrong_type)
    assert "Token has incorrect type. Expected '{}', got '{}'".format(expected_wrong_type, "access" if method == "create_access_token" else "confirmation") == str(exc_info.value.detail)

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
async def test_authenticate_user(confirmed_user: dict):
    user = await security.authenticate_user(
        confirmed_user["email"], confirmed_user["password"]
    )
    assert user is not None
    assert user.email == confirmed_user["email"]

@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test1.email.com", "wrongpassword")

@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user(registered_user["email"], "wrongpassword")

@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)
    assert user is not None
    assert user.email == registered_user["email"]

@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalidtoken")

@pytest.mark.anyio
async def test_get_current_user_invalid_token_type(registered_user: dict):
    token = security.create_confirmation_token(registered_user["email"])
    with pytest.raises(security.HTTPException):
        await security.get_current_user(token)

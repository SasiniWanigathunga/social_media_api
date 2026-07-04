import logging
import datetime
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status, Depends
from typing import Annotated, Literal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from social_media_api.database import user_table, database

logger = logging.getLogger(__name__)

SECRET_KEY="jni8943jnweintgnng94i59ug4n98ru4n9u4hv9uji9"
ALGORITHM="HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwt_context = CryptContext(schemes=["pbkdf2_sha256"])

def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

def access_token_expire_minutes() -> int:
    return 30

def confirmation_token_expire_minutes() -> int:
    return 1440

def create_access_token(email: str):
    logger.debug(f"Creating access token", extra={"email": email}) #noqa
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_confirmation_token(email: str):
    logger.debug(f"Creating confirmation token for email: {email}", extra={"email": email}) #noqa
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=confirmation_token_expire_minutes()
    )
    jwt_data = {"sub": email, "exp": expire, "type": "confirmation"}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_subject_for_security_token(token: str, expected_type: Literal["access", "confirmation"]) -> str:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired") from e
    except JWTError as e:
        raise create_credentials_exception("Invalid token") from e
    email: str = payload.get("sub")
    if email is None:
        raise create_credentials_exception("Token is missing 'sub' claim")
    token_type: str = payload.get("type")
    if token_type is None or token_type != expected_type:
        raise create_credentials_exception(f"Token has incorrect type. Expected '{expected_type}', got '{token_type}'")
    return email

def get_hashed_password(password: str) -> str:
    return pwt_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwt_context.verify(plain_password, hashed_password)

async def get_user(email: str):
    logger.debug(f"Fetching user from the database.", extra={"email": email}) #noqa
    query = user_table.select().where(user_table.c.email == email)
    user = await database.fetch_one(query)
    if user:
        return user
    
async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user:
        raise create_credentials_exception("Invalid email or password")
    if not verify_password(password, user["password"]):
        raise create_credentials_exception("Invalid email or password")
    if not user.confirmed:
        raise create_credentials_exception("User account is not confirmed.")
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    email = get_subject_for_security_token(token, expected_type="access")
    user = await get_user(email)
    if user is None:
        raise create_credentials_exception("Could not find user for the provided token")
    return user
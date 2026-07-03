import logging
import datetime
from jose import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from social_media_api.database import user_table, database

logger = logging.getLogger(__name__)

SECRET_KEY="jni8943jnweintgnng94i59ug4n98ru4n9u4hv9uji9"
ALGORITHM="HS256"

pwt_context = CryptContext(schemes=["pbkdf2_sha256"])

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
)

def access_token_expire_miniutes() -> int:
    return 30

def create_access_token(email: str):
    logger.debug(f"Creating access token for email: {email}")
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=access_token_expire_miniutes()
    )
    jwt_data = {"sub": email, "exp": expire}
    encoded_jwt = jwt.encode(jwt_data, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_hashed_password(password: str) -> str:
    return pwt_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwt_context.verify(plain_password, hashed_password)

async def get_user(email: str):
    logger.debug(f"Fetching user from the database.", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    user = await database.fetch_one(query)
    if user:
        return user
    
async def authenticate_user(email: str, password: str):
    user = await get_user(email)
    if not user:
        raise credentials_exception
    if not verify_password(password, user["password"]):
        raise credentials_exception
    return user
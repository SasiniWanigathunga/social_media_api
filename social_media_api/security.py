import logging

from passlib.context import CryptContext

from social_media_api.database import user_table, database

logger = logging.getLogger(__name__)

pwt_context = CryptContext(schemes=["pbkdf2_sha256"])

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
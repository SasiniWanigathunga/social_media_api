import logging

from fastapi import APIRouter, HTTPException, status, Request

from social_media_api.database import database, user_table
from social_media_api.models.user import UserInput
from social_media_api.security import get_user, get_hashed_password, authenticate_user, create_access_token, get_subject_for_security_token, create_confirmation_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_input: UserInput, request: Request):
    if await get_user(user_input.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )
    hashed_password = get_hashed_password(user_input.password)
    query = user_table.insert().values(
        email=user_input.email, password=hashed_password
    )
    logger.debug(query)
    await database.execute(query)
    return {
        "detail": "User created successfully. Please check your email to confirm your account.",
        "confirmation_email": request.url_for(
            "confirm_email", token=create_confirmation_token(user_input.email)
        )
    }


@router.post("/token")
async def login(user_input: UserInput):
    user = await authenticate_user(user_input.email, user_input.password)
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/confirm/{token}")
async def confirm_email(token: str):
    email = get_subject_for_security_token(token, expected_type="confirmation")
    query = user_table.update().where(user_table.c.email == email).values(confirmed=True)
    logger.debug(query)
    await database.execute(query)
    return {"detail": "User confirmed"}

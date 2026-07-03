from fastapi import APIRouter
import logging
from social_media_api.models.post import (
    UserPostInput,
    UserPostOutput,
    CommentInput,
    CommentOutput,
    UserPostwithComments,
)
from social_media_api.models.user import User
from social_media_api import security
from social_media_api.database import post_table, comment_table, database
from fastapi import HTTPException, Request

router = APIRouter()

logger = logging.getLogger(__name__)

async def find_post(post_id: int):
    logger.info(f"Searching for post with ID: {post_id}")
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(f"Executing query: {query}")
    return await database.fetch_one(query)


@router.post("/posts", response_model=UserPostOutput, status_code=201)
async def create_post(post: UserPostInput, request: Request):
    logger.info(f"Creating a new post") #noqa
    current_user: User = await security.get_current_user(await security.oauth2_scheme(request)) #noqa
    data = post.dict()
    query = post_table.insert().values(**data)
    logger.debug(f"Executing query: {query}")
    last_record_id = await database.execute(query)
    logger.info(f"Post created with ID: {last_record_id}")
    return {**data, "id": last_record_id}


@router.get("/posts", response_model=list[UserPostOutput])
async def get_posts():
    logger.info("Fetching all posts")
    query = post_table.select()
    logger.debug(f"Executing query: {query}")
    return await database.fetch_all(query)


@router.post("/comments", response_model=CommentOutput, status_code=201)
async def create_comment(comment: CommentInput, request: Request):
    logger.info(f"Creating a new comment for post ID: {comment.post_id}")
    current_user: User = await security.get_current_user(await security.oauth2_scheme(request)) #noqa
    data = comment.dict()
    post = await find_post(data["post_id"])
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    query = comment_table.insert().values(**data)
    logger.debug(f"Executing query: {query}")
    last_record_id = await database.execute(query)
    logger.info(f"Comment created with ID: {last_record_id}")
    return {**data, "id": last_record_id}


@router.get("/posts/{post_id}/comments", response_model=list[CommentOutput])
async def get_comments_for_post(post_id: int):
    logger.info(f"Fetching comments for post ID: {post_id}")
    post = await find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug(f"Executing query: {query}")
    return await database.fetch_all(query)


@router.get("/posts/{post_id}", response_model=UserPostwithComments)
async def get_post_with_comments(post_id: int):
    logger.info(f"Fetching post with ID: {post_id} and its comments")
    post = await find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comments = await get_comments_for_post(post_id)
    logger.info(f"Found {len(comments)} comments for post ID: {post_id}")
    return {"post": post, "comments": comments}

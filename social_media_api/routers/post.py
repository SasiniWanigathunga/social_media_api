import logging
from enum import Enum
from typing import Annotated

import sqlalchemy
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from social_media_api import security
from social_media_api.database import comment_table, database, like_table, post_table
from social_media_api.models.post import (
    CommentInput,
    CommentOutput,
    PostLikeInput,
    PostLikeOutput,
    UserPostInput,
    UserPostOutput,
    UserPostWithComments,
    UserPostWithLikes,
)
from social_media_api.models.user import User
from social_media_api.tasks import generate_and_add_to_post

router = APIRouter()

logger = logging.getLogger(__name__)

select_posts_and_likes = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(like_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(like_table))
    .group_by(post_table.c.id)
)


async def find_post(post_id: int):
    logger.info(f"Searching for post with ID: {post_id}")
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(f"Executing query: {query}")
    return await database.fetch_one(query)


@router.post("/posts", response_model=UserPostOutput, status_code=201)
async def create_post(
    post: UserPostInput,
    current_user: Annotated[User, Depends(security.get_current_user)],
    background_tasks: BackgroundTasks,
    request: Request,
    prompt: str = None,
):
    logger.info(f"Creating a new post")  # noqa
    data = {**post.model_dump(), "user_id": current_user.id}
    query = post_table.insert().values(**data)
    logger.debug(f"Executing query: {query}")
    last_record_id = await database.execute(query)

    if prompt:
        background_tasks.add_task(
            generate_and_add_to_post,
            email=current_user.email,
            post_id=last_record_id,
            post_url=request.url_for("get_post_with_comments", post_id=last_record_id),
            database=database,
            prompt=prompt,
        )

    logger.info(f"Post created with ID: {last_record_id}")
    return {**data, "id": last_record_id}


class PostSorting(str, Enum):
    newest = "newest"
    oldest = "oldest"
    most_liked = "most_liked"


@router.get("/posts", response_model=list[UserPostWithLikes])
async def get_posts(
    sorting: PostSorting = PostSorting.newest,
):  # http://localhost:8000/posts?sorting=newest
    logger.info("Fetching all posts")

    if sorting == PostSorting.newest:
        query = select_posts_and_likes.order_by(post_table.c.id.desc())
    elif sorting == PostSorting.oldest:
        query = select_posts_and_likes.order_by(post_table.c.id.asc())
    elif sorting == PostSorting.most_liked:
        query = select_posts_and_likes.order_by(sqlalchemy.desc("likes"))

    logger.debug(f"Executing query: {query}")
    return await database.fetch_all(query)


@router.post("/comments", response_model=CommentOutput, status_code=201)
async def create_comment(
    comment: CommentInput,
    current_user: Annotated[User, Depends(security.get_current_user)],
):
    logger.info(f"Creating a new comment for post ID: {comment.post_id}")
    data = {**comment.model_dump(), "user_id": current_user.id}
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


@router.get("/posts/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    logger.info(f"Fetching post with ID: {post_id} and its comments")
    query = select_posts_and_likes.where(post_table.c.id == post_id)
    logger.debug(f"Executing query: {query}")
    post = await database.fetch_one(query)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comments = await get_comments_for_post(post_id)
    logger.info(f"Found {len(comments)} comments for post ID: {post_id}")
    return {"post": post, "comments": comments}


@router.post("/like", response_model=PostLikeOutput, status_code=201)
async def like_post(
    like: PostLikeInput,
    current_user: Annotated[User, Depends(security.get_current_user)],
):
    logger.info(f"Creating a new like for post ID: {like.post_id}")
    data = {**like.model_dump(), "user_id": current_user.id}
    post = await find_post(data["post_id"])
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    query = like_table.insert().values(**data)
    logger.debug(f"Executing query: {query}")
    last_record_id = await database.execute(query)
    logger.info(f"Like created with ID: {last_record_id}")
    return {**data, "id": last_record_id}

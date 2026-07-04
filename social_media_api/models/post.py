from pydantic import BaseModel, ConfigDict


class UserPostInput(BaseModel):
    content: str

    model_config = ConfigDict(from_attributes=True)


class UserPostOutput(UserPostInput):
    id: int
    user_id: int


class UserPostWithLikes(UserPostOutput):
    likes: int


class CommentInput(BaseModel):
    comments: str
    post_id: int

    model_config = ConfigDict(from_attributes=True)


class CommentOutput(CommentInput):
    id: int
    user_id: int


class UserPostWithComments(BaseModel):
    post: UserPostWithLikes
    comments: list[CommentOutput]


class UserPostwithComments(BaseModel):
    post: UserPostOutput
    comments: list[CommentOutput]


class PostLikeInput(BaseModel):
    post_id: int


class PostLikeOutput(PostLikeInput):
    id: int
    user_id: int

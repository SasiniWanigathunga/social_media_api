from pydantic import BaseModel, ConfigDict


class UserPostInput(BaseModel):
    content: str

    model_config = ConfigDict(from_attributes=True)


class UserPostOutput(UserPostInput):
    id: int


class CommentInput(BaseModel):
    comments: str
    post_id: int

    model_config = ConfigDict(from_attributes=True)


class CommentOutput(CommentInput):
    id: int

class UserPostWithComments(BaseModel):
    post: UserPostOutput
    comments: list[CommentOutput]

class UserPostwithComments(BaseModel):
    post: UserPostOutput
    comments: list[CommentOutput]
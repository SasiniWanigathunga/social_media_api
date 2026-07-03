from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None
    email: str


class UserInput(User):
    password: str
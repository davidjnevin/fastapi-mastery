from pydantic import BaseModel


class User(BaseModel):
    id: int
    email: str


class UserIn(User):
    password: str

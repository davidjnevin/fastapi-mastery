from typing import Optional

import pytest
from databases.interfaces import Record

from social import security


def test_access_token_expire_minutes():
    assert security.access_token_expire_minutes() == 30


def test_confirmation_token_expire_minutes():
    assert security.confirmation_token_expire_minutes() == 1440


def test_create_access_token():
    token = security.create_access_token("123")
    assert isinstance(token, str)
    assert {"sub": "123", "type": "access"}.items() <= security.jwt.decode(
        token,
        security.JWT_SECRET,
        algorithms=[security.JWT_ALGORITHM],
    ).items()


def test_confirmation_access_token():
    token = security.create_confirmation_token("123")
    assert isinstance(token, str)
    assert {
        "sub": "123",
        "type": "confirmation",
    }.items() <= security.jwt.decode(
        token,
        security.JWT_SECRET,
        algorithms=[security.JWT_ALGORITHM],
    ).items()


@pytest.mark.slow(reason="Slow test")
def test_password_hashes():
    password = "secret"
    hashed_password = security.get_password_hash(password)
    assert security.verify_password(password, hashed_password)


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user: Optional[Record] = await security.get_user(registered_user["email"])
    if not user:
        pytest.fail("User not found")
    assert user.email == registered_user["email"]
    assert user.id == registered_user["id"]
    assert user.password != registered_user["password"]


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("non_existing_email")
    assert user is None


@pytest.mark.anyio
async def test_authenticate_user(registered_user: dict):
    user = await security.authenticate_user(
        registered_user["email"], registered_user["password"]
    )
    assert user.email == registered_user["email"]
    assert user.id == registered_user["id"]
    assert user.password != registered_user["password"]


@pytest.mark.anyio
async def test_authenticate_user_not_found():
    with pytest.raises(security.fastapi.HTTPException):
        await security.authenticate_user("non_existing_email", "password")


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(registered_user: dict):
    with pytest.raises(security.fastapi.HTTPException):
        await security.authenticate_user(
            registered_user["email"], registered_user["password"] + "wrong"
        )


@pytest.mark.anyio
async def test_get_current_user(registered_user: dict):
    token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)
    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.fastapi.HTTPException):
        await security.get_current_user("invalid token")


@pytest.mark.anyio
async def test_get_current_user_incorrect_token_type(registered_user: dict):
    token = security.create_confirmation_token(registered_user["email"])
    with pytest.raises(security.fastapi.HTTPException):
        await security.get_current_user(token)

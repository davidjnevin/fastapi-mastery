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
    assert {
        "sub": "123",
        "type": "access",
    }.items() <= security.jwt.decode(
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


def test_get_email_for_token_type_access():
    email = "test@davidnevin.net"
    token = security.create_access_token(email)
    token_email = security.get_email_for_token_type(token, "access")
    assert token_email == email


def test_get_email_for_token_type_confirmation():
    email = "test@davidnevin.net"
    token = security.create_confirmation_token(email)
    token_email = security.get_email_for_token_type(token, "confirmation")
    assert token_email == email


def test_get_email_for_expired_access_token():
    email = "test@davidnevin.net"
    access_token = security.create_access_token(email, expires_minutes=-1)
    with pytest.raises(security.fastapi.HTTPException) as exc_info:
        security.get_email_for_token_type(access_token, "access")
    assert exc_info.value.detail == "Token has expired"


def test_get_email_for_expired_confirmation_token():
    email = "test@davidnevin.net"
    confirmation_token = security.create_access_token(
        email, expires_minutes=-1
    )
    with pytest.raises(security.fastapi.HTTPException) as exc_info:
        security.get_email_for_token_type(confirmation_token, "access")
    assert exc_info.value.detail == "Token has expired"


def test_get_email_invalid_access_token():
    with pytest.raises(security.fastapi.HTTPException) as exc_info:
        security.get_email_for_token_type("invalid token", "access")
    assert exc_info.value.detail == "Invalid token"


def test_get_email_invalid_confirmation_token():
    with pytest.raises(security.fastapi.HTTPException) as exc_info:
        security.get_email_for_token_type("invalid token", "confirmation")
    assert exc_info.value.detail == "Invalid token"


def test_get_email_for_token_missing_sub_field():
    email = "test@davidnevin.net"
    token = security.create_access_token(email)
    payload = security.jwt.decode(
        token,
        key=security.JWT_SECRET,
        algorithms=[security.JWT_ALGORITHM],
    )
    del payload["sub"]
    token = security.jwt.encode(
        payload, security.JWT_SECRET, security.JWT_ALGORITHM
    )

    with pytest.raises(security.fastapi.HTTPException) as exc_info:
        security.get_email_for_token_type(token, "access")
    assert exc_info.value.detail == "Token is missing 'sub' field"


def test_get_email_for_token_wrong_type():
    email = "test@davidnevin.net"
    access_token = security.create_access_token(email)
    confirmation_token = security.create_confirmation_token(email)

    with pytest.raises(security.fastapi.HTTPException) as exc_info:
        security.get_email_for_token_type(access_token, "confirmation")
    assert (
        exc_info.value.detail
        == "Token is of invalid type, expected confirmation"
    )

    with pytest.raises(security.fastapi.HTTPException) as exc_info:
        security.get_email_for_token_type(confirmation_token, "access")
    assert exc_info.value.detail == "Token is of invalid type, expected access"


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
async def test_authenticate_user(confirmed_user: dict):
    user = await security.authenticate_user(
        confirmed_user["email"], confirmed_user["password"]
    )
    assert user.email == confirmed_user["email"]
    assert user.id == confirmed_user["id"]
    assert user.password != confirmed_user["password"]


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

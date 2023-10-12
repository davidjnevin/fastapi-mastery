from typing import Optional

import pytest
from databases.interfaces import Record

from social import security


@pytest.mark.skip(reason="Slow test")
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

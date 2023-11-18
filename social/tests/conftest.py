import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, Request, Response

from social.tests.helpers import create_post  # noqa: E402

os.environ["ENV_STATE"] = "test"
from social.database import database, user_table  # noqa: E402
from social.main import app  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    await database.connect()
    yield database
    await database.disconnect()


@pytest.fixture()
async def async_client(client) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=client.base_url) as ac:
        yield ac


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@davidnevin.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(
        user_table.c.email == user_details["email"]
    )
    user = await database.fetch_one(query)
    if user:
        user_details["id"] = user.id
    return user_details


@pytest.fixture()
async def confirmed_user(registered_user: dict) -> dict:
    query = (
        user_table.update()
        .where(user_table.c.email == registered_user["email"])
        .values(is_active=True)
    )
    await database.execute(query)
    return registered_user


@pytest.fixture()
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post("/token", json=confirmed_user)
    return response.json()["access_token"]


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post(
        "Test Post",
        async_client,
        logged_in_token,
    )


@pytest.fixture(autouse=True)
def mock_httpx_client(mocker):
    mocked_client = mocker.patch("social.tasks.httpx.AsyncClient")
    mocked_async_client = Mock()
    response = Response(
        status_code=200, content="", request=Request("POST", "//")
    )
    mocked_async_client.post = AsyncMock(return_value=response)
    mocked_client.return_value.__aenter__.return_value = (
        mocked_async_client  # using async context manager
    )

    return mocked_async_client

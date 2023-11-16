import pytest
from fastapi import BackgroundTasks
from httpx import AsyncClient


async def create_user(email: str, password: str, async_client: AsyncClient):
    return await async_client.post(
        "/register",
        json={"email": email, "password": password},
    )


@pytest.mark.anyio
async def test_register_user(async_client: AsyncClient):
    email = "bob@davidnevin.net"
    password = "password"

    response = await create_user(email, password, async_client)
    assert response.status_code == 201
    assert {
        "detail": "User created. Please confirm your email"
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_register_user_with_existing_email(
    async_client: AsyncClient, registered_user: dict
):
    response = await create_user(
        registered_user["email"], registered_user["password"], async_client
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.anyio
async def test_register_user_with_invalid_email(async_client: AsyncClient):
    response = await async_client.post(
        "/token", json={"email": "bob", "password": "password"}
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_user(async_client: AsyncClient, confirmed_user: dict):
    response = await async_client.post(
        "/token",
        json={
            "email": confirmed_user["email"],
            "password": confirmed_user["password"],
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_unconfirmed_user(
    async_client: AsyncClient, registered_user: dict
):
    response = await async_client.post(
        "/token",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 401
    assert "User has not confirmed email" in response.json()["detail"]


@pytest.mark.anyio
async def test_activate_user(async_client: AsyncClient, mocker):
    spy = mocker.spy(BackgroundTasks, "add_task")
    await create_user(
        "test@davidnevin.net",
        "password",
        async_client,
    )
    confirmation_url = str(spy.call_args[1]["confirmation_url"])
    response = await async_client.get(confirmation_url)
    assert response.status_code == 200
    assert {"detail": "User confirmed."}.items() <= response.json().items()


@pytest.mark.anyio
async def test_activate_user_with_invalid_token(async_client: AsyncClient):
    response = await async_client.get("/confirm/invalid_token")
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


@pytest.mark.anyio
async def test_activate_user_with_expired_token(
    async_client: AsyncClient, mocker
):
    email = "test@davidnevin.net"
    mocker.patch(
        "social.security.confirmation_token_expire_minutes", return_value=-1
    )
    spy = mocker.spy(BackgroundTasks, "add_task")
    await create_user(
        email,
        "password",
        async_client,
    )
    confirmation_url = str(spy.call_args[1]["confirmation_url"])
    response = await async_client.get(confirmation_url)
    assert response.status_code == 401
    assert {"detail": "Token has expired"}.items() <= response.json().items()

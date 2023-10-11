import pytest
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
    assert {"detail": "User created."}.items() <= response.json().items()


@pytest.mark.anyio
async def test_register_user_with_existing_email(
    async_client: AsyncClient, registered_user: dict
):
    response = await create_user(
        registered_user["email"], registered_user["password"], async_client
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

import pytest
from httpx import AsyncClient


async def create_user(
    email: str, password: str, async_client: AsyncClient
) -> dict:
    response = await async_client.post(
        "/register",
        json={"email": email, "password": password},
    )
    return response.json()


@pytest.mark.anyio
async def test_register(async_client: AsyncClient):
    email = "bob@davidnevin.net"
    password = "password"

    response = await async_client.post(
        "/register",
        json={
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 201
    assert {"detail": "User created."}.items() <= response.json().items()

import pytest
from httpx import AsyncClient


async def create_post(body: str, client: AsyncClient) -> dict:
    response = await client.post(
        "/post",
        json={"body": body},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient):
    return await create_post("Test post", async_client)


@pytest.fixture()
async def created_comment(async_client: AsyncClient, created_post: dict):
    response = await async_client.post(
        "/comment",
        json={"body": "Test Comment", "post_id": created_post["id"]},
    )
    return response.json()


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient):
    body = "Hello, world!"
    response = await async_client.post(
        "/post",
        json={
            "body": body,
        },
    )

    assert response.status_code == 201
    assert {"id": 0, "body": body}.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_json_without_body_keyword_should_fail(
    async_client: AsyncClient,
):
    response = await async_client.post(
        "/post",
        json={},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/post")

    assert response.status_code == 200
    assert response.json() == [created_post]


@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict):
    body = "Test comment"

    response = await async_client.post(
        "/comment",
        json={
            "body": body,
            "post_id": created_post["id"],
        },
    )

    assert response.status_code == 201
    assert {"id": 0, "body": body}.items() <= response.json().items()

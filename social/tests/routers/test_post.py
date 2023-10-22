import pytest
from httpx import AsyncClient

from social.security import create_access_token


async def create_post(
    body: str, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_comment(
    body: str, post_id: int, async_client: AsyncClient, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def like_post(
    post_id: int,
    async_client: AsyncClient,
    logged_in_token: str,
) -> dict:
    response = await async_client.post(
        "post/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post(
        "Test Post",
        async_client,
        logged_in_token,
    )


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    return await create_comment(
        body="Test Comment",
        post_id=created_post["id"],
        async_client=async_client,
        logged_in_token=logged_in_token,
    )


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str
):
    body = "Test Post"
    response = await async_client.post(
        "/post",
        json={
            "body": body,
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201
    assert {
        "id": 1,
        "body": body,
        "user_id": confirmed_user["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_create_post_json_without_body_keyword_should_fail(
    async_client: AsyncClient,
    logged_in_token: str,
):
    response = await async_client.post(
        "/post",
        json={},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient,
    confirmed_user: dict,
):
    expired_token = create_access_token(
        confirmed_user["email"], expires_minutes=-1
    )
    body = "Test Post"
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Token has expired"}


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    response = await async_client.get("/post")

    assert response.status_code == 200
    assert response.json() == [{**created_post, "likes": 0}]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        ("new", [3, 2, 1]),
        ("old", [1, 2, 3]),
        ("most_likes", [2, 1, 3]),
    ],
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    await create_post("Test Post 1", async_client, logged_in_token)
    post_2_response = await create_post(
        "Test Post 2", async_client, logged_in_token
    )
    await create_post("Test Post 3", async_client, logged_in_token)

    await like_post(post_2_response["id"], async_client, logged_in_token)

    response = await async_client.get("/post", params={"sorting": sorting})
    assert response.status_code == 200

    data = response.json()
    post_ids = [post["id"] for post in data]
    assert post_ids == expected_order


@pytest.mark.anyio
async def test_gat_all_posts_incorrect_sorting(async_client: AsyncClient):
    response = await async_client.get("/post", params={"sorting": "incorrect"})
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    confirmed_user: dict,
    logged_in_token: str,
):
    body = "Test Comment"

    response = await async_client.post(
        "/comment",
        json={
            "body": body,
            "post_id": created_post["id"],
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": confirmed_user["id"],
    }.items() <= response.json().items()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient,
    created_post: dict,
    created_comment: dict,
):
    response = await async_client.get(f"post/{created_post['id']}/comment")
    assert response.status_code == 200
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_post_empty(
    async_client: AsyncClient,
    created_post: dict,
):
    response = await async_client.get(f"post/{created_post['id']}/comment")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_and_its_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    response = await async_client.get(f"/post/{created_post['id']}")
    assert response.status_code == 200
    assert (
        response.json().items()
        <= {
            "post": {**created_post, "likes": 0},
            "comments": [created_comment],
        }.items()
    )


@pytest.mark.anyio
async def test_get_non_existent_post(async_client: AsyncClient):
    response = await async_client.get("/post/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Post with id 999 not found"}


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient,
    created_post: dict,
    logged_in_token: str,
    confirmed_user: dict,
):
    response = await async_client.post(
        "/post/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "post_id": created_post["id"],
        "user_id": confirmed_user["id"],
    }

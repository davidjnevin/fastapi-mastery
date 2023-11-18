import httpx
import pytest
from databases import Database

from social.database import post_table
from social.tasks import (
    APIResponseException,
    _generate_image_api,
    generate_image_and_add_to_post,
    send_simple_email,
)


@pytest.mark.anyio
async def test_send_simple_email(mock_httpx_client):
    await send_simple_email("test@davidnevin.net", "Test subject", "Test body")
    mock_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_simple_email_with_error(
    mock_httpx_client: httpx.AsyncClient,
):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )

    with pytest.raises(
        APIResponseException, match="API request with status code 500 failed"
    ):
        await send_simple_email(
            "test@example.com", "Test Subject", "Test Body"
        )


@pytest.mark.anyio
async def test_generate_image_api(mock_httpx_client):
    json_data = {"url": "https://example.com/image.png"}

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_data, request=httpx.Request("POST", "//")
    )
    result = await _generate_image_api(
        prompt="a fictional cartoon character from the 90's"
    )
    assert result == json_data


@pytest.mark.anyio
async def test_generate_image_api_server_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )
    with pytest.raises(
        APIResponseException,
        match="API request with status code 500 failed",
    ):
        await _generate_image_api(
            prompt="a fictional cartoon character from the 90's"
        )


@pytest.mark.anyio
async def test_generate_image_api_json_error(mock_httpx_client):
    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200,
        content="Not JSON",
        request=httpx.Request("POST", "//"),
    )
    with pytest.raises(
        APIResponseException,
        match="API response could not be parsed",
    ):
        await _generate_image_api(
            prompt="a fictional cartoon character from the 90's"
        )


@pytest.mark.anyio
async def test_generate_and_add_to_post_success(
    mock_httpx_client: httpx.AsyncClient,
    db: Database,
    created_post: dict,
    confirmed_user: dict,
):
    json_data = {
        "created": 1700323866,
        "data": [
            {
                "revised_prompt": "prompt",
                "url": "https://example.com/image.png",
            }
        ],
    }

    mock_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_data, request=httpx.Request("POST", "//")
    )
    await generate_image_and_add_to_post(
        email=confirmed_user["email"],
        post_id=created_post["id"],
        post_url="/post/1",
        database=db,
        prompt="a fictional cartoon character from the 90's",
    )
    query = post_table.select().where(post_table.c.id == created_post["id"])
    updated_post = await db.fetch_one(query)
    assert updated_post.image_url == json_data["data"][0]["url"]

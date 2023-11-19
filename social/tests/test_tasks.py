from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from databases import Database

from social.config import config
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


mock_response = {"data": [{"url": "https://example.com/image.png"}]}


async def async_mock(*args, **kwargs):
    return mock_response


@pytest.mark.anyio
async def test_generate_image_api(mocker):
    mock_response = Mock()
    mock_response.model_dump.return_value = {
        "data": [{"url": "https://example.com/image.png"}]
    }

    mock_openai_client = mocker.patch("social.tasks.AsyncOpenAI")
    mock_openai_client.return_value.images.generate = AsyncMock(
        return_value=mock_response
    )
    test_prompt = "Test prompt"

    response = await _generate_image_api(prompt=test_prompt)
    expected_output = mock_response.model_dump.return_value
    assert response == expected_output

    mock_openai_client.return_value.images.generate.assert_awaited_once_with(
        model="dall-e-3",
        prompt=test_prompt,
        n=1,
        size=config.OPENAI_IMAGE_SIZE,
    )


@pytest.mark.anyio
async def test_generate_and_add_to_post_success(
    db: Database,
    created_post: dict,
    confirmed_user: dict,
    mocker,
):
    mock_response = {"data": [{"url": "https://example.com/image.png"}]}

    mocker.patch(
        "social.tasks._generate_image_api", return_value=mock_response
    )

    json_data = await generate_image_and_add_to_post(
        email=confirmed_user["email"],
        post_id=created_post["id"],
        post_url="/post/1",
        database=db,
        prompt="a fictional cartoon character from the 90's",
    )
    query = post_table.select().where(post_table.c.id == created_post["id"])
    updated_post = await db.fetch_one(query)
    assert updated_post.image_url == json_data["data"][0]["url"]

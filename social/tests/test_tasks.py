import httpx
import pytest

from social.tasks import APIResponseException, send_simple_email


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

import logging

import httpx

from social.config import config

logger = logging.getLogger(__name__)


class ApiResponseException(Exception):
    pass


async def send_simple_email(to: str, subject: str, body: str):
    logger.debug(f"Sending email to {to[:3]} with subject {subject}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
                auth=("api", config.MAILGUN_API_KEY),
                data={
                    "from": f"David <mailgun@{config.MAILGUN_DOMAIN}>",
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
            )
            response.raise_for_status()
            logger.debug(response.content)

        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending email: {e}")
            raise ApiResponseException(
                f"API request with status code {e.response.status_code} failed"
            ) from e

        logger.debug(f"Email sent to {to[:3]} with subject {subject}")
        return response.json()


async def send_user_registration_email(to: str, confirmation_url: str):
    subject = "Please confirm your email"
    body = f"""
    Hi there,
    Please confirm your email by clicking on the link below:
    {confirmation_url}
    """
    await send_simple_email(to, subject, body)
    logger.debug(f"Confirmation email sent to {to[:3]} with subject {subject}")

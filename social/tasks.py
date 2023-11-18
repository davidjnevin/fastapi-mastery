import logging
from json import JSONDecodeError

import httpx
from databases import Database

from social.config import config
from social.database import post_table

logger = logging.getLogger(__name__)


class APIResponseException(Exception):
    pass


async def send_simple_email(to: str, subject: str, body: str):
    logger.debug(f"Sending email to '{to[:3]}' with subject '{subject[:10]}'")
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
            logger.debug(f"Email sent to {to[:3]} with subject {subject}")
            return response

        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending email: {e}")
            raise APIResponseException(
                f"API request with status code {e.response.status_code} failed"
            ) from e


async def send_user_registration_email(to: str, confirmation_url: str):
    subject = "Please confirm your email"
    body = f"""
    Hi there,
    You have successfully registered signed up!
    Please confirm your email by clicking on the link below:
    {confirmation_url}
    """
    await send_simple_email(to, subject, body)
    logger.debug(f"Confirmation email sent to {to[:3]} with subject {subject}")


async def _generate_image_api(prompt: str):
    logging.debug(f"Generating image from prompt: {prompt[:30]}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                data={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": config.OPENAI_IMAGE_SIZE,
                },
                timeout=45,
            )
            logger.debug(response)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error generating image: {e}")
            raise APIResponseException(
                f"API request with status code {e.response.status_code} failed"
            ) from e
        except (JSONDecodeError, TypeError) as e:
            logger.error(f"Error parsing json: {e}")
            raise APIResponseException(
                f"API response could not be parsed: {e}"
            ) from e


async def generate_image_and_add_to_post(
    email: str,
    post_id: int,
    post_url: str,
    database: Database,
    prompt: str,
):
    try:
        response = await _generate_image_api(prompt)
    except APIResponseException as e:
        logger.error(f"Error generating image: {e}")
        to = email
        subject = "Error generating image"
        body = (
            "Hi there,\nUnfortunately there was an error "
            "generating an image for your post"
        )
        return await send_simple_email(to, subject, body)

    logger.debug("Connection to database to update image_url")
    image_url = response["data"][0]["url"]
    query = (
        post_table.update()
        .where(post_table.c.id == post_id)
        .values(image_url=image_url)
    )
    logger.debug(query)
    await database.execute(query)
    logger.debug(f"Database background task for {post_id} closed")
    to = email
    subject = "Image generated for your post!"
    body = (
        f"Hi there,\nYour image has been generated"
        f" for your post and is available at {post_url}.\n"
    )
    await send_simple_email(to, subject, body)
    return response

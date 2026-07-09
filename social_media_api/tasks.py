import logging
import httpx
from json import JSONDecodeError
from social_media_api.config import config
from social_media_api.database import post_table
from databases import Database

logger = logging.getLogger(__name__)


class APIResponseError(Exception):
    pass


async def send_simple_email(to: str, subject: str, body: str):
    logger.info(f"Sending email to {to[:3]} with subject '{subject[:20]}'")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{config.MAILGUN_API_URL}/{config.MAILGUN_DOMAIN}/messages",
                auth=("api", config.MAILGUN_API_KEY),
                data={
                    "from": f"Sasini Wanigathunga <mailgun@{config.MAILGUN_DOMAIN}>",
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
            )
            response.raise_for_status()
            logger.debug(response.content)
            return response
        except httpx.HTTPStatusError as e:
            raise APIResponseError(
                f"API request failed with status code {e.response.status_code}"
            ) from e

async def send_user_registration_email(email: str, confirmation_url: str):
    return await send_simple_email(
        email,
        "Successfully signed up",
        (
            f"Hi, you have successfully signed up."
            f" Please confirm your email by clicking the following link: {confirmation_url}"
        )
    )

async def _generate_cute_creature_api(prompt: str):
    logger.debug(f"Generating image with prompt: {prompt}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.deepai.org/api/cute-creature-generator",
                headers={"api-key": config.DEEPAI_API_KEY},
                data={"text": prompt},
                timeout=60
            )
            logger.debug(response)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise APIResponseError(
                f"API request failed with status code {e.response.status_code}"
            ) from e
        except (JSONDecodeError, TypeError) as e:
            raise APIResponseError("API response parsing failed") from e

async def generate_and_add_to_post(
        email: str,
        post_id: int,
        post_url: str,
        database: Database,
        prompt: str = "A blue british short hair cat is sitting on a couch",
):
    try:
        response = await _generate_cute_creature_api(prompt)
    except APIResponseError as e:
        return await send_simple_email(
            email,
            "Image Generation Failed",
            (
                f"Hi, {email}: Unfortunately there was an error generating an image"
                "for your post."
            )
        )
    logger.debug("Connecting to database to update post with generated image URL")
    query = (
        post_table.update()
        .where(post_table.c.id == post_id)
        .values(image_url=response.get("output_url"))
    )
    logger.debug(f"Executing query: {query}")
    await database.execute(query)
    logger.debug("Database connection in background task closed")

    await send_simple_email(
        email,
        "Image Generation Successful",
        (
            f"Hi, {email}: Your image has been successfully generated and added to your post."
            f" You can view it here: {post_url}"
        )  
    )
    return response
import logging

import social.database

logger = logging.getLogger(__name__)


async def get_user(email: str):
    logger.debug("Getting user form the database", extra={"email": email})
    query = social.database.user_table.select().where(
        social.database.user_table.c.email == email
    )
    logger.debug(query)
    result = await social.database.database.fetch_one(query)
    if result:
        return result

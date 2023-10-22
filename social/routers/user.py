import logging

from fastapi import APIRouter, HTTPException, Request

import social.security as security
from social.database import database, user_table
from social.models.user import UserIn

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/token", status_code=200)
async def login(user: UserIn) -> dict:
    logger.info("Logging in user")
    db_user = await security.authenticate_user(user.email, user.password)
    if not db_user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password",
        )
    token = security.create_access_token(db_user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", status_code=201)
async def register(user: UserIn, request: Request) -> dict:
    logger.info("Creating user")
    if await security.get_user(user.email):
        raise HTTPException(
            status_code=400,
            detail="A user with that email already registered",
        )
    hased_password = security.get_password_hash(user.password)
    query = user_table.insert().values(
        email=user.email, password=hased_password
    )
    logger.debug(query)
    await database.execute(query)
    return {
        "detail": "User created. Please confirm your email",
        "activation_url": str(
            request.url_for(
                "confirm_email",
                token=security.create_confirmation_token(user.email),
            ),
        ),
    }


@router.get("/confirm/{token}", status_code=200)
async def confirm_email(token: str) -> dict:
    logger.info("Confirming user")
    email = security.get_email_for_token_type(token, "confirmation")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid token",
        )
    query = (
        user_table.update()
        .where(user_table.c.email == email)
        .values(is_active=True)
    )
    logger.debug(query)
    await database.execute(query)
    return {"detail": "User confirmed."}

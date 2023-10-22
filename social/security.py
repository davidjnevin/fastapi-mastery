import datetime
import logging
from typing import Annotated

import fastapi
import fastapi.security
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from social.config import config
from social.database import database, user_table

logger = logging.getLogger(__name__)

JWT_SECRET = config.JWT_SECRET_KEY
JWT_ALGORITHM = config.JWT_ALGORITHM
oauth2_scheme = fastapi.security.OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

credentials_exception = fastapi.HTTPException(
    status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def access_token_expire_minutes():
    return 30


def confirmation_token_expire_minutes():
    return 1440  # 24 hours


def create_access_token(email: str, expires_minutes: int = None):
    logger.debug("Creating access token", extra={"email": email})
    if expires_minutes is None:
        expires_minutes = access_token_expire_minutes()

    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=expires_minutes
    )
    jwt_data = {"sub": email, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(jwt_data, key=JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_confirmation_token(email: str, expires_minutes: int = None):
    logger.debug("Creating email confirmation token", extra={"email": email})
    if expires_minutes is None:
        expires_minutes = confirmation_token_expire_minutes()

    expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=expires_minutes
    )
    jwt_data = {"sub": email, "exp": expire, "type": "confirmation"}
    encoded_jwt = jwt.encode(jwt_data, key=JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_user(email: str):
    logger.debug("Getting user form the database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    logger.debug(query)
    result = await database.fetch_one(query)
    if result:
        return result
    return None


async def authenticate_user(email: str, password: str):
    logger.debug("Authenticating user", extra={"email": email})
    user = await get_user(email)
    if not user:
        raise credentials_exception
    if not verify_password(password, user.password):
        raise credentials_exception
    return user


async def get_current_user(
    token: Annotated[str, fastapi.Depends(oauth2_scheme)]
):
    try:
        payload = jwt.decode(token, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
        type = payload.get("type")
        if type != "access" or type is None:
            raise credentials_exception
    except ExpiredSignatureError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except JWTError as e:
        raise credentials_exception from e
    user = await get_user(email=email)
    if user is None:
        raise credentials_exception
    return user

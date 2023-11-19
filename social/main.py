import logging
from contextlib import asynccontextmanager

import fastapi
import fastapi.exception_handlers
import sentry_sdk
from asgi_correlation_id import CorrelationIdMiddleware

from social.config import config
from social.database import database
from social.logging_conf import configure_logging
from social.routers import healthcheck, post, upload, user

logger = logging.getLogger(__name__)


sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    configure_logging()
    await database.connect()
    yield
    await database.disconnect()


app = fastapi.FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(user.router)
app.include_router(post.router)
app.include_router(healthcheck.router)
app.include_router(upload.router)
# app.include_router(sentry.router)


@app.exception_handler(fastapi.HTTPException)
async def http_exception_handle_logging(request, exc):
    logger.error(f"HTTPException: {exc.status_code}  {exc.detail}")
    return await fastapi.exception_handlers.http_exception_handler(
        request, exc
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

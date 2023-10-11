import logging
from contextlib import asynccontextmanager

import fastapi
import fastapi.exception_handlers
from asgi_correlation_id import CorrelationIdMiddleware

from social.database import database
from social.logging_conf import configure_logging
from social.routers import healthcheck, post

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    configure_logging()
    await database.connect()
    yield
    await database.disconnect()


app = fastapi.FastAPI(lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)

app.include_router(post.router)
app.include_router(healthcheck.router)


@app.exception_handler(fastapi.HTTPException)
async def http_exception_handle_logging(request, exc):
    logger.error(f"HTTPException: {exc.status_code}  {exc.detail}")
    return await fastapi.exception_handlers.http_exception_handler(
        request, exc
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

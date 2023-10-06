import logging
from contextlib import asynccontextmanager

import fastapi

from social.database import database
from social.logging_conf import configure_logging
from social.routers import healthcheck, post

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    configure_logging()
    logger.info("Starting application server")
    await database.connect()
    yield
    await database.disconnect()


app = fastapi.FastAPI(lifespan=lifespan)

app.include_router(post.router)
app.include_router(healthcheck.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

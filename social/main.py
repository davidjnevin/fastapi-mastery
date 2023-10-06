from contextlib import asynccontextmanager

import fastapi

from social.database import database
from social.routers import healthcheck, post


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    await database.connect()
    yield
    await database.disconnect()


app = fastapi.FastAPI(lifespan=lifespan)

app.include_router(post.router)
app.include_router(healthcheck.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

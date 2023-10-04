import fastapi

from social.routers import healthcheck, post

app = fastapi.FastAPI()

app.include_router(post.router)
app.include_router(healthcheck.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)

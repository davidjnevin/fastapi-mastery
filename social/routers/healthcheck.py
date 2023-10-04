import fastapi

router = fastapi.APIRouter()


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

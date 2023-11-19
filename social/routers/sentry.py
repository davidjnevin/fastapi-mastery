import logging

from fastapi import APIRouter

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
    return division_by_zero

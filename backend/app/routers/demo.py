"""Built-in endpoints the monitor can probe, so the project works fully offline."""
import random
import time

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/demo", tags=["Demo targets"])


@router.get("/ok")
def healthy():
    return {"status": "ok"}


@router.get("/slow")
def slow():
    time.sleep(1.3)
    return {"status": "ok but slow"}


@router.get("/flaky")
def flaky():
    if random.random() < 0.35:
        raise HTTPException(503, "Temporarily unavailable")
    return {"status": "ok"}


@router.get("/down")
def down():
    raise HTTPException(503, "Service unavailable")

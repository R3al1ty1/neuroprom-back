from fastapi import APIRouter
from .chat import router as router_chat
from .auth import router as router_auth
from .form import router as router_form

router = APIRouter()

router.include_router(
    router_chat
)

router.include_router(
    router_auth
)

router.include_router(
    router_form
)
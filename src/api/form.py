from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db_helper import db_helper
from core.schemas.form import FormCreate, FormResponse
import crud.form as form_crud

router = APIRouter()

@router.post("/forms/", response_model=FormResponse)
async def create_form(
    form_data: FormCreate,
    db: AsyncSession = Depends(db_helper.session_getter)
):
    """
    Создание новой формы обратной связи.
    """
    return await form_crud.create_form(db, form_data)
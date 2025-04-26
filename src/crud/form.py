from sqlalchemy.ext.asyncio import AsyncSession
from core.models.chat import Form
from core.schemas.form import FormCreate

async def create_form(db: AsyncSession, form_data: FormCreate) -> Form:
    form = Form(
        name=form_data.name,
        email=form_data.email,
        phone=form_data.phone,
        company=form_data.company,
        description=form_data.description
    )
    db.add(form)
    await db.commit()
    await db.refresh(form)
    return form
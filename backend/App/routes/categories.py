"""
app/routes/categories.py
Endpoints simples para listar/criar categorias (admin gere).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models.category import Category
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["Categorias"])


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    default_sla_hours: int
    auto_assign_to_user_id: int | None


class CategoryCreate(BaseModel):
    name: str
    default_sla_hours: int = 24
    auto_assign_to_user_id: int | None = None


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(Category).order_by(Category.name).all()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    body: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if db.query(Category).filter(Category.name == body.name).first():
        raise HTTPException(status_code=400, detail="Já existe uma categoria com esse nome")
    cat = Category(**body.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

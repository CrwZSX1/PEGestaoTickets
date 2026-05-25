"""
app/routes/users.py
Endpoints de gestão de utilizadores (admin only, excepto GET /users/techs).

Endpoints:
  GET    /users               — listar utilizadores (admin)
  POST   /users               — criar utilizador  (admin)
  GET    /users/techs         — listar técnicos+admins (admin/tech — para dropdowns)
  PUT    /users/{id}/role     — alterar perfil    (admin)
  PUT    /users/{id}/active   — activar/desactivar (admin)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import hash_password, require_admin, require_admin_tech
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    UserActiveUpdate, UserCreate, UserOut, UserRoleUpdate,
)

router = APIRouter(prefix="/users", tags=["Utilizadores"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Já existe um utilizador com esse email")

    user = User(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
        active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/techs", response_model=list[UserOut])
def list_techs(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_tech),
):
    """Lista todos os técnicos e admins activos — para preencher dropdowns de atribuição."""
    return (
        db.query(User)
        .filter(
            User.active == True,
            User.role.in_([UserRole.tech, UserRole.admin]),
        )
        .order_by(User.name)
        .all()
    )


@router.put("/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: int,
    body: UserRoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    user.role = body.role
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}/active", response_model=UserOut)
def update_active(
    user_id: int,
    body: UserActiveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id and not body.active:
        raise HTTPException(status_code=400, detail="Não podes desactivar a tua própria conta")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    user.active = body.active
    db.commit()
    db.refresh(user)
    return user

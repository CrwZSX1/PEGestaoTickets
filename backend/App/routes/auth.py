"""
app/routes/auth.py
Endpoints de autenticação:
  POST /auth/login  — devolve JWT + utilizador
  GET  /auth/me     — perfil do utilizador autenticado
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login OAuth2 — espera form-data com `username` (email) e `password`.
    Devolve um token JWT e o perfil do utilizador.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.active or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou password inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return LoginResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Devolve o perfil do utilizador autenticado."""
    return current_user

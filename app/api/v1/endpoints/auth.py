"""
Authentication endpoints.
Maneja login local, login con Google y gestión de sesiones mediante Cookies httpOnly.
"""

from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_

# 1. Librerías de Google
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow

# 2. Imports locales
from app.core.settings import settings
from app.db.session import get_db
from app.models.user import User, UserStatus, UserRole
from app.schemas.user import UserLogin, UserLoginResponse, GoogleLogin
from app.core.security import (
    verify_password,
    create_access_token
)

router = APIRouter()

def set_auth_cookie(response: Response, access_token: str):
    """
    Función auxiliar para configurar la cookie de forma dinámica.
    Implementa seguridad por defecto según el entorno.
    """
    is_prod = settings.ENVIRONMENT == "production"
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        # En prod requiere HTTPS (Secure=True). En local False.
        secure=is_prod,
        # En prod 'none' permite cross-site (Vercel -> Render)
        samesite="lax" if not is_prod else "none",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

@router.post("/login", response_model=UserLoginResponse)
async def login(
    response: Response,
    *,
    db: Session = Depends(get_db),
    user_data: UserLogin
) -> Any:
    """Login tradicional vía JSON que planta una cookie."""
    user = db.query(User).filter(
        or_(User.username == user_data.username, User.email == user_data.username)
    ).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta inactiva")
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(subject=user.id)
    
    # Seteamos la cookie de seguridad
    set_auth_cookie(response, access_token)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.post("/google", response_model=UserLoginResponse)
async def google_login(
    response: Response,
    *,
    db: Session = Depends(get_db),
    data: GoogleLogin
) -> Any:
    """Canje de código Google y creación de sesión segura vía Cookie."""
    try:
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                'openid', 
                'https://www.googleapis.com/auth/userinfo.email', 
                'https://www.googleapis.com/auth/userinfo.profile'
            ],
            redirect_uri='postmessage'
        )

        flow.fetch_token(code=data.token)
        credentials = flow.credentials

        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, 
            request, 
            settings.GOOGLE_CLIENT_ID
        )

        email = id_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Token sin email")

        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            username_suggested = email.split("@")[0]
            user = User(
                username=username_suggested,
                email=email,
                full_name=id_info.get("name", username_suggested),
                password_hash="google-oauth-managed",
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        user.last_login = datetime.utcnow()
        db.commit()
        
        access_token = create_access_token(subject=user.id)
        
        # Seteamos la cookie de seguridad
        set_auth_cookie(response, access_token)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Error en validación segura: {str(e)}"
        )

@router.post("/logout")
async def logout(response: Response):
    """Borra la cookie de sesión del navegador."""
    is_prod = settings.ENVIRONMENT == "production"
    
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=is_prod,
        samesite="lax" if not is_prod else "none"
    )
    return {"message": "Sesión cerrada correctamente"}

@router.post("/login-form", response_model=UserLoginResponse)
async def login_form(
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Login para Swagger UI con soporte de cookies."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    access_token = create_access_token(subject=user.id)
    set_auth_cookie(response, access_token)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }
"""
Authentication endpoints.
Maneja login local, login con Google y gestión de sesiones.
"""

from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_

# 1. Librerías de Google para el flujo seguro
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow

# 2. Imports locales del proyecto
from app.core.settings import settings
from app.db.session import get_db
from app.models.user import User, UserStatus, UserRole
from app.schemas.user import UserLogin, UserLoginResponse, GoogleLogin # <--- Asegúrate que GoogleLogin esté en schemas
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter()

@router.post("/login", response_model=UserLoginResponse)
async def login(
    *,
    db: Session = Depends(get_db),
    user_data: UserLogin
) -> Any:
    """Login tradicional vía JSON."""
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
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.post("/google", response_model=UserLoginResponse)
async def google_login(
    *,
    db: Session = Depends(get_db),
    data: GoogleLogin
) -> Any:
    """
    CANJE DE CÓDIGO (Auth Code Flow):
    El frontend envía un 'code'. El backend lo canjea por tokens
    usando el CLIENT_SECRET que solo nosotros conocemos.
    """
    try:
        # A. Configurar el flujo de intercambio con Google
        # El redirect_uri 'postmessage' es obligatorio cuando usas el popup de React
        # print(f"DEBUG: Usando ID {settings.GOOGLE_CLIENT_ID[:10]}...") 
        # print(f"DEBUG: Usando Secret {settings.GOOGLE_CLIENT_SECRET[:5]}...")

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

        # B. Intercambiar el código por tokens reales
        # 'data.token' ahora contiene el 'code' que mandó el frontend
        flow.fetch_token(code=data.token)
        credentials = flow.credentials

        # C. Verificar la identidad con el ID Token
        # Esto asegura que el token no ha sido manipulado
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, 
            request, 
            settings.GOOGLE_CLIENT_ID
        )

        email = id_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="El token de Google no contiene email")

        # D. Lógica de Persistencia en Neon (Modular)
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Creamos el usuario si no existe (Fricción Cero)
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

        # E. Generar nuestra propia sesión (JWT local)
        user.last_login = datetime.utcnow()
        db.commit()
        
        access_token = create_access_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }

    except Exception as e:
        # Importante: En producción no des detalles del error, pero aquí nos sirve para aprender
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Error en validación segura: {str(e)}"
        )
    
@router.post("/login-form", response_model=UserLoginResponse)
async def login_form(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Login para Swagger UI."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.post("/logout")
async def logout():
    return {"message": "Sesión cerrada correctamente"}
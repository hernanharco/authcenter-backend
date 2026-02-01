"""
Pydantic schemas for User model.
Actualizado a Pydantic v2.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID  # Importante para arreglar la falla del ID
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
import re

from app.models.user import UserRole, UserStatus


# Base schema con campos comunes
class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nombre de usuario único (3-50 caracteres)"
    )
    email: EmailStr = Field(..., description="Correo electrónico válido")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = Field(default=UserRole.USER)

    @field_validator('username')  # v2 usa field_validator
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username solo puede contener letras, números, guiones y guiones bajos')
        return v.lower()


# Schema para crear usuario
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(...)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una minúscula')
        if not re.search(r'\d', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        # En v2, 'values' se accede a través de 'info.data'
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Las contraseñas no coinciden')
        return v


# Schema para login
class UserLogin(BaseModel):
    username: str = Field(..., description="Username o Email")
    password: str = Field(...)
    remember_me: bool = Field(default=False)

# Schema para actualizar usuario (Pydantic v2)
class UserUpdate(BaseModel):
    """
    Esquema para actualizar datos de un usuario existente.
    Todos los campos son opcionales para permitir actualizaciones parciales.
    """
    email: Optional[EmailStr] = Field(None, description="Nuevo correo electrónico")
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = Field(None)
    status: Optional[UserStatus] = Field(None)
    is_active: Optional[bool] = Field(None)

    model_config = ConfigDict(from_attributes=True)


# Schema para respuesta (Aquí arreglamos tu falla)
class UserResponse(UserBase):
    # Cambiamos str por UUID para que Pydantic acepte el dato de Neon
    id: UUID = Field(..., description="ID único del usuario") 
    status: UserStatus
    is_active: bool
    is_locked: bool
    last_login: Optional[datetime] = None # Cambiado a datetime para consistencia
    created_at: datetime
    updated_at: datetime
    
    # v2 usa model_config en lugar de class Config
    model_config = ConfigDict(from_attributes=True)


class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UserPublic(BaseModel):
    id: UUID # También aquí UUID
    username: str
    full_name: str
    role: UserRole
    
    model_config = ConfigDict(from_attributes=True)

class GoogleLogin(BaseModel):
    token: str  # Aquí recibiremos el access_token que envía el frontend
"""
User management endpoints.
Actualizado para Pydantic v2 y soporte de UUID.
"""

from typing import Any, List, Optional
from uuid import UUID # Importante para los IDs
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import (
    UserCreate, UserResponse, UserUpdate, UserPublic
)
from app.core.security import get_password_hash, get_current_active_user


router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def list_users(
    *,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    # Solo ADMIN y MANAGER pueden ver la lista completa
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para listar usuarios"
        )
    
    query = db.query(User)
    
    if search:
        search_filter = or_(
            User.username.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
            User.full_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if role:
        query = query.filter(User.role == role)
    
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=UserResponse)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    # Solo ADMIN crea usuarios nuevos por este medio
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso denegado"
        )
    
    # Validar duplicados
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username ya existe")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email ya existe")
    
    # Pydantic v2 usa model_dump() en lugar de dict()
    user_data = user_in.model_dump() 
    password = user_data.pop("password")
    user_data.pop("confirm_password") 
    
    user_data["password_hash"] = get_password_hash(password)
    
    user = User(**user_data)
    
    # Lógica de activación automática si viene como active
    if user.status == UserStatus.ACTIVE:
        user.is_active = True
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: UUID, # Cambiado a UUID para validación automática
    current_user: User = Depends(get_current_active_user)
) -> Any:
    # Lógica de permisos
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
         # Aquí podrías añadir la lógica de Manager si la necesitas
         raise HTTPException(status_code=403, detail="No tienes permiso")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: UUID, # Cambiado a UUID
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="No encontrado")
    
    # Si no es ADMIN ni es él mismo, fuera
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sin permisos")

    # Obtener datos (Pydantic v2)
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Protegemos campos sensibles si no es ADMIN
    if current_user.role != UserRole.ADMIN:
        for field in ["role", "status", "is_active"]:
            update_data.pop(field, None)

    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: UUID, # Cambiado a UUID
    current_user: User = Depends(get_current_active_user)
) -> Any:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Solo admins")
    
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="No puedes borrarte a ti mismo")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="No encontrado")
    
    # Soft delete
    user.is_active = False
    user.status = UserStatus.INACTIVE
    db.commit()
    return {"message": "Usuario desactivado correctamente"}
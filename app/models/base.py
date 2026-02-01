"""
Base model for SQLAlchemy models.
Este archivo contiene la clase base que todos nuestros modelos heredarán.
Proporciona campos comunes como timestamps y manejo de UUID.
"""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.session import Base


class BaseModel(Base):
    """
    Modelo base con campos comunes para todos los modelos.
    
    Campos incluidos:
    - id: UUID único como clave primaria
    - created_at: Timestamp de creación automático
    - updated_at: Timestamp de última actualización automático
    """
    
    __abstract__ = True  # SQLAlchemy no creará tabla para esta clase
    
    # UUID como clave primaria (más seguro que auto-incremental)
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True,
        comment="Identificador único del registro"
    )
    
    # Timestamp de creación (se establece automáticamente)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="Fecha y hora de creación del registro"
    )
    
    # Timestamp de actualización (se actualiza automáticamente)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Fecha y hora de última actualización del registro"
    )

"""
User model for authentication and authorization.
Este modelo representa a los usuarios del sistema empresarial.
Incluye campos para autenticación, roles y estado de cuenta.
"""

from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class UserRole(enum.Enum):
    """
    Enumeración de roles de usuario.
    Define los diferentes niveles de acceso en el sistema.
    """
    ADMIN = "admin"           # Acceso completo al sistema
    MANAGER = "manager"       # Acceso a gestión de usuarios
    USER = "user"            # Acceso básico limitado
    VIEWER = "viewer"        # Solo lectura


class UserStatus(enum.Enum):
    """
    Enumeración de estados de usuario.
    Controla si un usuario puede acceder al sistema.
    """
    ACTIVE = "active"         # Usuario activo, puede acceder
    INACTIVE = "inactive"     # Usuario inactivo, no puede acceder
    SUSPENDED = "suspended"   # Usuario suspendido temporalmente
    PENDING = "pending"       # Usuario pendiente de aprobación


class User(BaseModel):
    """
    Modelo de usuario para el sistema de autenticación.
    
    Campos principales:
    - username: Nombre de usuario único (para login)
    - email: Correo electrónico único
    - password_hash: Contraseña hasheada (nunca almacenar en texto plano)
    - full_name: Nombre completo del usuario
    - role: Rol del usuario en el sistema
    - status: Estado actual de la cuenta
    - is_active: Bandera booleana para acceso rápido
    """
    
    __tablename__ = "users"
    
    # Campos de autenticación
    username = Column(
        String(50), 
        unique=True, 
        index=True, 
        nullable=False,
        comment="Nombre de usuario único para login"
    )
    
    email = Column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False,
        comment="Correo electrónico único del usuario"
    )
    
    password_hash = Column(
        String(255), 
        nullable=False,
        comment="Contraseña hasheada (bcrypt)"
    )
    
    # Campos de información personal
    full_name = Column(
        String(100), 
        nullable=False,
        comment="Nombre completo del usuario"
    )
    
    # Campos de control de acceso
    role = Column(
        Enum(UserRole), 
        default=UserRole.USER,
        nullable=False,
        comment="Rol del usuario en el sistema"
    )
    
    status = Column(
        Enum(UserStatus), 
        default=UserStatus.PENDING,
        nullable=False,
        comment="Estado de la cuenta del usuario"
    )
    
    is_active = Column(
        Boolean, 
        default=False,
        nullable=False,
        comment="Bandera para control rápido de acceso"
    )
    
    # Campos adicionales para seguridad
    last_login = Column(
        String(50),
        nullable=True,
        comment="Fecha y hora del último login (ISO string)"
    )
    
    failed_login_attempts = Column(
        String(10),
        default="0",
        nullable=False,
        comment="Número de intentos fallidos de login"
    )
    
    is_locked = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indica si la cuenta está bloqueada por seguridad"
    )
    
    def __repr__(self):
        """
        Representación string del objeto User.
        Útil para debugging y logs.
        """
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role.value}')>"
    
    @property
    def is_authenticated(self) -> bool:
        """
        Verifica si el usuario está autenticado y activo.
        Combinación de is_active y status ACTIVE.
        """
        return self.is_active and self.status == UserStatus.ACTIVE
    
    @property
    def is_admin(self) -> bool:
        """
        Verifica si el usuario tiene rol de administrador.
        Atajo para comprobaciones de permisos.
        """
        return self.role == UserRole.ADMIN
    
    def can_login(self) -> bool:
        """
        Determina si el usuario puede iniciar sesión.
        Considera estado, activación y bloqueo.
        """
        return (
            self.is_active and 
            self.status == UserStatus.ACTIVE and 
            not self.is_locked
        )

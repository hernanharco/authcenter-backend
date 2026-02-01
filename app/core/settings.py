from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Clase de configuración centralizada usando Pydantic Settings.
    Mapea automáticamente las variables del archivo .env a atributos de Python.
    """

    # --- Configuración de Pydantic ---
    # env_file=".env" le dice a Pydantic que busque este archivo en la raíz del proyecto.
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"  # Ignora variables en el .env que no estén definidas aquí
    )

    # --- Entorno y Debug ---
    # Si no están en el .env, tomarán estos valores por defecto.
    environment: str = "development"
    debug: bool = True
    
    # --- Base de Datos ---
    # Usamos Optional[str] porque estas variables pueden no estar definidas (ej. falta una en el .env)
    database_url_dev: Optional[str] = None
    database_url_prod: Optional[str] = None
    
    # --- Seguridad ---    
    # Al dejarlo como Optional[str] = None, obligamos a Pydantic a buscarlo en el .env
    SECRET_KEY: Optional[str] = None
    
    # --- Configuración JWT ---
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    
    # --- Configuración Email ---
    email_reset_token_expire_hours: int = 1
    
    # --- API ---
    # Lo dejamos con el valor real de la carpeta
    API_V1_STR: str = "/api/v1" 
    
    # Si algún día creas la v2, simplemente vienes aquí y añades:
    # API_V2_STR: str = "/api/v2"

    # Nuevas variables para CORS
    cors_origins_dev: str = "http://localhost:3000"
    cors_origins_prod: str = ""

    # Variables para Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # --- Propiedades Calculadas ---
    # Las propiedades (@property) se comportan como atributos pero ejecutan lógica.
    @property
    def database_url(self) -> str:
        """
        Selecciona la URL de conexión correcta según el entorno (producción o desarrollo).
        Esto evita que uses la DB de producción en tu PC local por error.
        """
        if self.environment == "production":
            if not self.database_url_prod:
                # Lanzamos un error descriptivo si falta la configuración crítica
                raise ValueError("DATABASE_URL_PROD is required in production environment")
            return self.database_url_prod
        else:
            if not self.database_url_dev:
                raise ValueError("DATABASE_URL_DEV is required in development environment")
            return self.database_url_dev
    
    @property
    def is_production(self) -> bool:
        """Devuelve True si el entorno actual es producción"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Devuelve True si el entorno actual es desarrollo"""
        return self.environment == "development"

    @property
    def allow_origins(self) -> list[str]:
        """Convierte el string del .env en una lista de Python"""
        if self.is_production:
            # .split(",") corta el texto donde haya una coma y crea la lista
            return self.cors_origins_prod.split(",") if self.cors_origins_prod else []
        else:
            return self.cors_origins_dev.split(",")         
        
    @property
    def secret_key_value(self) -> str:
        if not self.SECRET_KEY: # Cambiado a MAYÚSCULAS
            raise ValueError("SECRET_KEY is required")
        return self.SECRET_KEY            

# Instanciamos la clase para que pueda ser importada en el resto del proyecto.
# Al hacer esto, Pydantic lee el .env inmediatamente.
settings = Settings()
from app.db.session import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

def fix_my_user():
    db = SessionLocal()
    try:
        # 1. Buscamos si existe el usuario hernan (el que creamos por SQL)
        user = db.query(User).filter(User.username == "hernan").first()
        
        # Si existe, lo borramos para crearlo bien desde cero
        if user:
            db.delete(user)
            db.commit()
            print("Usuario antiguo borrado.")

        # 2. Creamos el usuario usando tus funciones de seguridad
        new_user = User(
            username="hernan",
            email="hernan.harco@gmail.com",
            full_name="Hernan Arango Cortes",
            # ESTA LÍNEA ES LA CLAVE: Tu código genera el hash correcto
            password_hash=get_password_hash("123456789"), 
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            is_active=True,
            failed_login_attempts="0",
            is_locked=False
        )
        
        db.add(new_user)
        db.commit()
        print("✅ Usuario 'hernan' creado correctamente con hash compatible.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_my_user()
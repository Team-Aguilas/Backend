# Contenido esperado en backend/app/dependencies.py (parcial)

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient # Asegúrate que AsyncIOMotorClient está importado
from bson import ObjectId # Asegúrate que ObjectId está importado
from typing import Optional # Asegúrate que Optional está importado

from app.config import settings
from app.models import UserInDB, TokenData
from app.security import decode_access_token

# --- Global DB client and instance (set by main.py lifespan) ---
mongo_client: Optional[AsyncIOMotorClient] = None
database_instance: Optional[AsyncIOMotorDatabase] = None


# VVVVVV ESTA ES LA FUNCIÓN IMPORTANTE VVVVVV
async def get_db() -> AsyncIOMotorDatabase:
    if database_instance is None:
        # Esto no debería ocurrir si el lifespan se ejecuta correctamente
        raise HTTPException(status_code=503, detail="La base de datos no está disponible.")
    return database_instance
# ^^^^^^ ASEGÚRATE QUE ESTA FUNCIÓN ESTÁ EXACTAMENTE ASÍ ^^^^^^


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    db: AsyncIOMotorDatabase = Depends(get_db), # Esta línea también depende de que get_db esté bien definida
    token: str = Depends(oauth2_scheme)
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    if not ObjectId.is_valid(user_id): # Necesitas importar ObjectId de bson
        raise credentials_exception 

    user_doc = await db.users.find_one({"_id": ObjectId(user_id)}) # Y usarlo aquí
    if user_doc is None:
        raise credentials_exception
    
    return UserInDB(**user_doc)

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    return current_user

async def get_current_active_superuser(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene suficientes privilegios",
        )
    return current_user
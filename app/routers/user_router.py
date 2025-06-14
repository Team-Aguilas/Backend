from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.dependencies import get_db, get_current_active_superuser, get_current_active_user
from app.models import UserCreate, UserRead, UserUpdate, UserInDB
from app.security import get_password_hash

router = APIRouter()
USER_COLLECTION = "users"

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_in: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    existing_user = await db[USER_COLLECTION].find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con este email."
        )
    
    hashed_password = get_password_hash(user_in.password)
    # Crear UserInDB para asegurar todos los campos y generar _id si es necesario
    db_user = UserInDB(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_password
        # is_active, is_superuser tendrán sus valores por defecto de UserInDB
    )
    # Convertir a dict para MongoDB, usando alias (ej: id a _id)
    user_doc_to_insert = db_user.model_dump(by_alias=True, exclude_none=True)

    result = await db[USER_COLLECTION].insert_one(user_doc_to_insert)
    
    created_user_doc = await db[USER_COLLECTION].find_one({"_id": result.inserted_id})
    if not created_user_doc:
         raise HTTPException(status_code=500, detail="Error al crear usuario") # No debería pasar
    return UserRead(**created_user_doc)


@router.get("/", response_model=List[UserRead], dependencies=[Depends(get_current_active_superuser)])
async def read_all_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    users_cursor = db[USER_COLLECTION].find().skip(skip).limit(limit)
    user_docs = await users_cursor.to_list(length=limit)
    return [UserRead(**doc) for doc in user_docs]


@router.get("/{user_id}", response_model=UserRead)
async def read_user_by_id(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # Asegurar que está logueado
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de usuario inválido")
    
    # Un usuario solo puede ver su propio perfil, o un superusuario puede ver cualquiera
    if str(current_user.id) != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para ver este usuario")

    user_doc = await db[USER_COLLECTION].find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UserRead(**user_doc)


@router.put("/{user_id}", response_model=UserRead)
async def update_existing_user(
    user_id: str,
    user_in: UserUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de usuario inválido")

    # Un usuario solo puede actualizar su propio perfil, o un superusuario puede actualizar cualquiera
    if str(current_user.id) != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado para actualizar este usuario")

    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]: # Si se provee nueva contraseña
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay datos para actualizar")

    updated_user_doc = await db[USER_COLLECTION].find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
        return_document=True 
    )
    if not updated_user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado para actualizar")
    return UserRead(**updated_user_doc)

# Podrías añadir una ruta DELETE similar, probablemente solo para superusuarios.
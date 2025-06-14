from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models import Token, UserRead # UserRead para el tipo de retorno de /me
from app.security import create_access_token, verify_password
from app.dependencies import get_db, get_current_active_user
from app.models import UserInDB # Para el tipado

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_token(
    db: AsyncIOMotorDatabase = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user_doc = await db.users.find_one({"email": form_data.username})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = UserInDB(**user_doc) # Convertir doc a modelo Pydantic

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    
    access_token = create_access_token(data={"sub": str(user.id)}) # user.id es el _id
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    # La dependencia ya nos da un UserInDB, Pydantic se encarga de convertirlo a UserRead
    return current_user
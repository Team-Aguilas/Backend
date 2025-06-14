from pydantic import BaseModel, Field, EmailStr, ConfigDict
from bson import ObjectId
from typing import Optional, List
from pydantic_core import core_schema 

# --- ObjectId Handling ---
class PyObjectId(ObjectId):
    @classmethod
    def _validate(cls, v, _validation_info=None): # Método de validación
        if isinstance(v, ObjectId):
            return v
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"'{v}' no es un ObjectId válido")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """
        Define cómo Pydantic debe validar y procesar este tipo.
        PyObjectId se valida usando cls._validate.
        Para JSON, se trata como un string.
        """
        return core_schema.json_or_python_schema(
            python_schema=core_schema.with_info_plain_validator_function(cls._validate),
            json_schema=core_schema.str_schema(pattern=r'^[0-9a-fA-F]{24}$'), # Patrón para ObjectId string
            serialization=core_schema.to_string_ser_schema() # Cómo serializarlo (a string)
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema_obj, handler):
        """
        Define cómo PyObjectId debe representarse en el esquema JSON de OpenAPI.
        Directamente devolvemos el esquema para un string con el patrón de ObjectId.
        """
        return {
            "type": "string",
            "pattern": r"^[0-9a-fA-F]{24}$", # Expresión regular para un ObjectId de 24 caracteres hexadecimales
            "example": "507f1f77bcf86cd799439011", # Un ejemplo de ObjectId
        }

# ... (El resto de tus modelos: DBModelMixin, UserBase, ProductBase, etc., permanecen igual) ...
# Asegúrate que DBModelMixin y otros modelos que usen PyObjectId estén definidos DESPUÉS de PyObjectId.

# --- Base Model for DB objects ---
class DBModelMixin(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    model_config = ConfigDict( # Asegúrate de estar usando ConfigDict aquí
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, PyObjectId: str} # Añade PyObjectId aquí también por si acaso
    )

# --- User Models ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

class UserInDB(DBModelMixin, UserBase): # UserBase ya no tiene _id
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

class UserRead(UserBase): # Esquema para devolver al cliente (sin password)
    id: PyObjectId = Field(alias="_id")
    is_active: bool
    is_superuser: bool
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, json_encoders={ObjectId: str})


# --- Product Models ---
class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    currency: str = Field("COP")
    stock: int = Field(..., ge=0)
    category: str
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None

class ProductInDB(DBModelMixin, ProductBase): # ProductBase no tiene _id
    pass # Hereda _id de DBModelMixin y campos de ProductBase

class ProductRead(ProductBase):
    id: PyObjectId = Field(alias="_id")
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, json_encoders={ObjectId: str})


# --- Token Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None # O email
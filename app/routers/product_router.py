# from fastapi import APIRouter, Depends, HTTPException, status
# from typing import List
# from motor.motor_asyncio import AsyncIOMotorDatabase
# from bson import ObjectId

# from app.dependencies import get_db # , get_current_active_user si se requiere autenticación
# from app.models import ProductCreate, ProductRead, ProductUpdate, ProductInDB
# # from app.models import UserInDB # Para el tipo de current_user

# router = APIRouter()
# PRODUCT_COLLECTION = "products"
# @router.get("/", response_model=List[ProductRead])
# async def list_products(db=Depends(get_db)):
#     cursor = db.products.find()
#     results = []
#     async for doc in cursor:
#         # Pydantic acepta el alias "_id" para poblar "id"
#         # con 'model_dump(by_alias=True)' devolvemos JSON con "_id",
#         # pero si queremos un JSON "id": ...
#         product = ProductInDB(**doc)
#         dump = product.model_dump()  # genera {'id':ObjectId(...), 'name':..., ...}
#         dump["id"] = str(dump.pop("id"))
#         results.append(dump)
#     return results


# @router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
# async def create_new_product(
#     product_in: ProductCreate,
#     db: AsyncIOMotorDatabase = Depends(get_db)
#     # current_user: UserInDB = Depends(get_current_active_user) # Descomentar si se requiere login
# ):
#     db_product = ProductInDB(**product_in.model_dump())
#     product_doc_to_insert = db_product.model_dump(by_alias=True, exclude_none=True)

#     result = await db[PRODUCT_COLLECTION].insert_one(product_doc_to_insert)
#     created_doc = await db[PRODUCT_COLLECTION].find_one({"_id": result.inserted_id})
#     if not created_doc:
#         raise HTTPException(status_code=500, detail="Error al crear producto")
#     return ProductRead(**created_doc)


# @router.get("/", response_model=List[ProductRead])
# async def read_all_products(
#     skip: int = 0,
#     limit: int = 20,
#     db: AsyncIOMotorDatabase = Depends(get_db)
# ):
#     products_cursor = db[PRODUCT_COLLECTION].find().skip(skip).limit(limit)
#     product_docs = await products_cursor.to_list(length=limit)
#     return [ProductRead(**doc) for doc in product_docs]


# @router.get("/{product_id}", response_model=ProductRead)
# async def read_product_by_id(
#     product_id: str,
#     db: AsyncIOMotorDatabase = Depends(get_db)
# ):
#     if not ObjectId.is_valid(product_id):
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de producto inválido")
    
#     product_doc = await db[PRODUCT_COLLECTION].find_one({"_id": ObjectId(product_id)})
#     if not product_doc:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
#     return ProductRead(**product_doc)


# @router.put("/{product_id}", response_model=ProductRead)
# async def update_existing_product(
#     product_id: str,
#     product_in: ProductUpdate,
#     db: AsyncIOMotorDatabase = Depends(get_db)
#     # current_user: UserInDB = Depends(get_current_active_superuser) # Si solo admins pueden editar
# ):
#     if not ObjectId.is_valid(product_id):
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de producto inválido")

#     update_data = product_in.model_dump(exclude_unset=True)
#     if not update_data:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay datos para actualizar")

#     updated_doc = await db[PRODUCT_COLLECTION].find_one_and_update(
#         {"_id": ObjectId(product_id)},
#         {"$set": update_data},
#         return_document=True
#     )
#     if not updated_doc:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado para actualizar")
#     return ProductRead(**updated_doc)


# @router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_existing_product(
#     product_id: str,
#     db: AsyncIOMotorDatabase = Depends(get_db)
#     # current_user: UserInDB = Depends(get_current_active_superuser) # Si solo admins pueden borrar
# ):
#     if not ObjectId.is_valid(product_id):
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de producto inválido")
    
#     delete_result = await db[PRODUCT_COLLECTION].delete_one({"_id": ObjectId(product_id)})
#     if delete_result.deleted_count == 0:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado para eliminar")
#     return





from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.dependencies import get_db, get_current_active_user
from app.models import ProductCreate, ProductRead, ProductUpdate, ProductInDB, UserInDB

router = APIRouter()
PRODUCT_COLLECTION = "products"

@router.get("/", response_model=List[ProductRead])
async def list_products(db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db[PRODUCT_COLLECTION].find()
    results = []
    async for doc in cursor:
        product = ProductInDB(**doc)
        dump = product.model_dump()
        dump["id"] = str(dump.pop("id"))
        results.append(dump)
    return results

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_new_product(
    product_in: ProductCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
):
    # Solo usuarios autenticados pueden crear productos
    db_product = ProductInDB(**product_in.model_dump())
    product_doc_to_insert = db_product.model_dump(by_alias=True, exclude_none=True)

    result = await db[PRODUCT_COLLECTION].insert_one(product_doc_to_insert)
    created_doc = await db[PRODUCT_COLLECTION].find_one({"_id": result.inserted_id})
    if not created_doc:
        raise HTTPException(status_code=500, detail="Error al crear producto")
    return ProductRead(**created_doc)

@router.get("/{product_id}", response_model=ProductRead)
async def read_product_by_id(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de producto inválido")
    product_doc = await db[PRODUCT_COLLECTION].find_one({"_id": ObjectId(product_id)})
    if not product_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return ProductRead(**product_doc)

@router.put("/{product_id}", response_model=ProductRead)
async def update_existing_product(
    product_id: str,
    product_in: ProductUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    # current_user: UserInDB = Depends(get_current_active_superuser) # Para admins
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de producto inválido")
    update_data = product_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay datos para actualizar")
    updated_doc = await db[PRODUCT_COLLECTION].find_one_and_update(
        {"_id": ObjectId(product_id)},
        {"$set": update_data},
        return_document=True
    )
    if not updated_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado para actualizar")
    return ProductRead(**updated_doc)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    # current_user: UserInDB = Depends(get_current_active_superuser) # Para admins
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de producto inválido")
    delete_result = await db[PRODUCT_COLLECTION].delete_one({"_id": ObjectId(product_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado para eliminar")
    return

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Asegúrate que esto está importado
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.routers import product_router, user_router, auth_router
import app.dependencies as global_deps

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicación...")
    # Conectar a MongoDB
    global_deps.mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    global_deps.database_instance = global_deps.mongo_client[settings.MONGO_DB_NAME]
    try:
        await global_deps.mongo_client.admin.command('ping')
        print(f"Conectado a MongoDB: {settings.MONGO_DB_NAME}")
    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")
        global_deps.mongo_client = None # Asegurar que no se use un cliente fallido
        global_deps.database_instance = None
        raise # Re-lanzar para que FastAPI sepa que el inicio falló

    print(f"API {settings.PROJECT_NAME} iniciada.")
    yield
    # Desconectar de MongoDB
    if global_deps.mongo_client:
        global_deps.mongo_client.close()
        print("Conexión a MongoDB cerrada.")
    print("API detenida.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Configuración de CORS (ajusta 'origins' según tu frontend)
origins = [
    "http://localhost:5173",  # Puerto por defecto de Vite para el frontend
    "http://127.0.0.1:5173", # A veces es bueno ser explícito con la IP
    # "http://localhost:3000", # Si tuvieras otro frontend en ese puerto
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Lista de orígenes permitidos
    allow_credentials=True,      # Permite cookies (si las usas)
    allow_methods=["*"],         # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],         # Permite todas las cabeceras
)

# Incluir routers
API_V1_STR = "/api/v1"
app.include_router(auth_router.router, prefix=f"{API_V1_STR}/auth", tags=["Authentication"])
app.include_router(user_router.router, prefix=f"{API_V1_STR}/users", tags=["Users"])
app.include_router(product_router.router, prefix=f"{API_V1_STR}/products", tags=["Products"])

@app.get(f"{API_V1_STR}/healthcheck", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": f"Servicio {settings.PROJECT_NAME} funcionando."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
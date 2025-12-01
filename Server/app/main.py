from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "ForestOS API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Import routers
from app.api.endpoints import auth, plants, user_plants, sensors, watering, alerts

# Include routers with API prefix
API_PREFIX = "/api"

app.include_router(
    auth.router,
    prefix=f"{API_PREFIX}/auth",
    tags=["authentication"]
)

app.include_router(
    plants.router,
    prefix=f"{API_PREFIX}/plants",
    tags=["plants"]
)

app.include_router(
    user_plants.router,
    prefix=f"{API_PREFIX}/user-plants",
    tags=["user-plants"]
)

app.include_router(
    sensors.router,
    prefix=f"{API_PREFIX}/sensors",
    tags=["sensors"]
)

app.include_router(
    watering.router,
    prefix=f"{API_PREFIX}/watering",
    tags=["watering"]
)

app.include_router(
    alerts.router,
    prefix=f"{API_PREFIX}/alerts",
    tags=["alerts"]
)

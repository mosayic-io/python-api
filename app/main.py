from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import get_settings
from app.services.logger import get_logger
# from mosayic.core.firebase import initialize_firebase

logger = get_logger(__name__)
settings = get_settings()
DEBUG_MODE = settings.debug_mode


@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize_firebase()
    logger.info("Application startup: Initializing services...")
    yield


# Set up FastAPI app - docs will be disabled dynamically in production
app = FastAPI(
    title="Mosaygent API",
    lifespan=lifespan,
    generate_unique_id_function=lambda route: route.name,
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
)


# TODO: Set explicit CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_charset_to_json_response(request: Request, call_next):
    """
    This middleware ensures that all JSON responses have the 'charset=utf-8'
    in their 'Content-Type' header. This is crucial for clients that do not
    default to UTF-8, preventing character encoding issues.
    """
    response = await call_next(request)
    if "application/json" in response.headers.get(
        "content-type", ""
    ) and "charset" not in response.headers.get("content-type", ""):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response


# Include routers
# app.include_router(caloratio_router, prefix="/caloratio", tags=["Caloratio"])


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Mosaygent API",
        "debug_mode": DEBUG_MODE,
        "environment": settings.environment
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "mosaygent",
        "debug": DEBUG_MODE,
        "environment": settings.environment
    }

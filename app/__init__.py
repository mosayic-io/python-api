
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


# Set up FastAPI app - docs will be disabled dynamically in production
app = FastAPI(
    lifespan=lifespan,
    generate_unique_id_function=lambda route: route.name
)


# TODO: Set explicit CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Try to load mosaygent dev routes if available (dev dependency). Remove this if not using Mosayic.
try:
    import mosaygent
except ImportError:
    pass

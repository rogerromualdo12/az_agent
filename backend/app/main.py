from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.customers import router as customers_router
from app.config import settings
from app.services.neo4j_service import neo4j_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    neo4j_service.close()


app = FastAPI(
    title="Financial Digital Twin",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.config import settings
from app.routers.ingestion import router as ingestion_router
from app.routers.raw_materials import router as raw_materials_router

app = FastAPI(title="Spoorthi Raw Material Inventory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ingestion_router)
app.include_router(raw_materials_router)


@app.get("/health")
def health():
    return {"status": "ok"}

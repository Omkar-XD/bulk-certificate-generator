from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.certificates import router as certificates_router
from app.api.jobs import router as jobs_router
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Bulk Certificate Generator",
    description="Generate, track, and download certificates in bulk.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(jobs_router)
app.include_router(certificates_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

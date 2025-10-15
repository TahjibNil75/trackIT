from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.main import init_db
from src.auth.routes import auth_router



@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Starting up...")
    await init_db()
    yield
    print("Shutting down...")



version = "v1"
_app = FastAPI(lifespan=lifespan)

version_prefix = f"/api/{version}"



@_app.get(f"{version_prefix}/health")
def root():
    return {"status": "ok"}

_app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=["Auth"])

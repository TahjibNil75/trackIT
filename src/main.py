from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.db.main import init_db
from src.auth.routes import auth_router
from src.ticket.routes import ticket_router
from src.user.routes import user_management_router
from src.comment.routes import comment_router
from src.analytics.routes import analytics_router



@asynccontextmanager
async def lifespan(_app: FastAPI):
    print("Starting up...")
    await init_db()
    yield
    print("Shutting down...")



version = "v1"
_app = FastAPI(lifespan=lifespan)

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

_app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

version_prefix = f"/api/{version}"



@_app.get(f"{version_prefix}/health")
def root():
    return {"status": "ok"}

_app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=["Auth"])
_app.include_router(ticket_router, prefix=f"{version_prefix}/ticket", tags=["Tickets"])
_app.include_router(user_management_router, prefix=f"{version_prefix}/user", tags=["User Management"])
_app.include_router(comment_router, prefix=f"{version_prefix}/comment", tags=["Comment"])
_app.include_router(analytics_router, prefix=f"{version_prefix}/analytics", tags=["Analytics"])

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import interactions, chat

settings = get_settings()

# Create tables on startup (fine for an assignment/demo; use Alembic migrations in real prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-First CRM — HCP Module API",
    description="Log Interaction Screen backend: FastAPI + LangGraph + Groq",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "env": settings.env}

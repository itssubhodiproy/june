import app.models  # noqa: F401
from app.models.base import Base
from app.dependencies import engine
from app.routes import auth, documents, tables, workspaces
from fastapi import FastAPI

app = FastAPI(title="API Server", version="0.1.0")

app.include_router(auth.router, prefix="/api")
app.include_router(workspaces.router, prefix="/api")
app.include_router(tables.router, prefix="/api")
app.include_router(documents.router, prefix="/api")


@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def read_root():
    return {"Hello": "World"}

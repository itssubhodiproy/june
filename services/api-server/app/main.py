import app.models  # noqa: F401
from app.models.base import Base
from app.dependencies import engine
from app.routes import auth, tables, workspaces
from fastapi import FastAPI

app = FastAPI(title="API Server", version="0.1.0")

app.include_router(auth.router)
app.include_router(tables.router)
app.include_router(workspaces.router)


@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
def read_root():
    return {"Hello": "World"}

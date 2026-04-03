from app.db import Base, engine
from fastapi import FastAPI

app = FastAPI(title="API Server", version="0.1.0")

@app.on_event("startup")
def init_db():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"Hello": "World"}
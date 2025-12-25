from fastapi import FastAPI
from src.core.database import Base, engine
from src.api import auth, document, rag, agent, billing
import src.core.logging_config

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "ok"}

app.include_router(auth.router)
app.include_router(document.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(billing.router)
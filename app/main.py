from fastapi import FastAPI
from app.core.database import Base, engine
from app.api import auth

app = FastAPI()

# Create all database tables
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
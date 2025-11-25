from fastapi import FastAPI
from app.core.database import Base, engine

app = FastAPI()

# Create all database tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Hello World!"}
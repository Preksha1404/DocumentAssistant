from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from src.core.database import Base, engine
from src.api import auth, document, rag, agent, billing

app = FastAPI()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/payment-success")
def success_page():
    return HTMLResponse("<h2>Payment Successful</h2>")

@app.get("/payment-cancel")
def cancel_page():
    return HTMLResponse("<h2>Payment Cancelled</h2>")

app.include_router(auth.router)
app.include_router(document.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(billing.router)
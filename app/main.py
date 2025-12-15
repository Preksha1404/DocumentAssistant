from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.core.database import Base, engine
from app.api import auth, document, rag, agent, billing

app = FastAPI()

# Create all database tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/payment-success")
def success_page():
    return HTMLResponse("""
        <h2>Payment Successful</h2>
        <p>You can now return to the application.</p>
    """)

@app.get("/payment-cancel")
def cancel_page():
    return HTMLResponse("""
        <h2>Payment Cancelled</h2>
        <p>Your subscription was not activated.</p>
    """)

app.include_router(auth.router)
app.include_router(document.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(billing.router)
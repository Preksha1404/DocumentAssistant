from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from src.core.database import Base, engine
from src.api import auth, document, rag, agent, billing

app = FastAPI()

# Add CORS middleware (important for web services)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
# Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

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
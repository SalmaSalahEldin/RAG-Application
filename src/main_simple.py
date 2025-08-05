from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes import base_router, data_router, nlp_router
from routes.auth import auth_router
from helpers.config import get_settings
import os

app = FastAPI()

# Serve static files
assets_path = os.path.join(os.path.dirname(__file__), "assets")
if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

@app.get("/")
async def root():
    """Serve the main application interface."""
    return FileResponse(os.path.join(assets_path, "index.html"))

# Include routers
app.include_router(base_router)
app.include_router(auth_router)
app.include_router(data_router)
app.include_router(nlp_router)

# Database dependency
from database import get_db 
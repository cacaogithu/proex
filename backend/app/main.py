from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
from .api.submissions import router as submissions_router
from .api.auth import router as auth_router
from .api.progress import router as progress_router
from .db.database import Database

load_dotenv()

app = FastAPI(title="ProEx Platform", version="1.0.0")

# Security: Configure CORS - allow all origins in development
# For production, set CORS_ORIGINS env var with specific origins
cors_origins = os.getenv("CORS_ORIGINS", "")
if cors_origins:
    allowed_origins = cors_origins.split(",")
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(submissions_router, prefix="/api", tags=["submissions"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(progress_router, prefix="/api", tags=["progress"])

db = Database()

os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("storage/outputs", exist_ok=True)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Serve React App
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Check if file exists in static folder (e.g. favicon.ico)
    static_file_path = os.path.join("static", full_path)
    if os.path.isfile(static_file_path):
        return FileResponse(static_file_path)
        
    # Otherwise return index.html for SPA routing
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

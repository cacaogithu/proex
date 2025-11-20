from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from .api.submissions import router as submissions_router
from .db.database import Database

load_dotenv()

app = FastAPI(title="ProEx Platform", version="1.0.0")

# Security: Configure CORS with specific origins from environment variable
# For development, set CORS_ORIGINS="http://localhost:3000,http://localhost:5173"
# For production, set to your actual frontend domain
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(submissions_router, prefix="/api", tags=["submissions"])

db = Database()

os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("storage/outputs", exist_ok=True)


@app.get("/")
async def root():
    return {
        "message": "ProEx Platform API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

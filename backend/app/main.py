from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from .api.submissions import router as submissions_router
from .db.database import Database

load_dotenv()

app = FastAPI(title="ProEx Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(submissions_router, prefix="/api", tags=["submissions"])

db = Database()

os.makedirs("backend/storage/uploads", exist_ok=True)
os.makedirs("backend/storage/outputs", exist_ok=True)


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

from pathlib import Path
import sys
from fastapi import FastAPI

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.api.forecast import router as forecast_router

app = FastAPI(
    title="AERIS API",
    description="Urban Environmental Intelligence & Digital Twin Backend",
    version="0.1.0",
)

app.include_router(forecast_router)


@app.get("/")
def read_root():
    return {"message": "AERIS Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

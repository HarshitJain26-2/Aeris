from fastapi import FastAPI

app = FastAPI(
    title="AERIS API",
    description="Urban Environmental Intelligence & Digital Twin Backend",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "AERIS Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

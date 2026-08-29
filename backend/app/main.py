from fastapi import FastAPI

from backend.app.modules.academic.adapters.api import router as academic_router

app = FastAPI(title="TAIA")

app.include_router(academic_router)


@app.get("/health")
def health():
    return {"status": "ok"}
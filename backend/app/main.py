from fastapi import FastAPI

app = FastAPI(title="TAIA")


@app.get("/health")
def health():
    return {"status": "ok"}
from fastapi import FastAPI
from backend.api.generate import router as generate_router

app = FastAPI(title="VibeCober Architect API")

app.include_router(generate_router)

@app.get("/")
def root():
    return {"status": "VibeCober backend running"}

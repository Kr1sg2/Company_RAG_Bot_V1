
from fastapi import FastAPI

app = FastAPI(title="LexaAI Backend", docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json")

@app.get("/api/admin/settings/public/branding")
async def get_branding():
    return {"status": "ok", "message": "Backend is running"}

@app.get("/test")
async def test():
    return {"status": "ok"}

#!/usr/bin/env python3
"""
Minimal test to debug app import issues
"""
from fastapi import FastAPI

print("Creating FastAPI app...")
app = FastAPI(title="Test App")

@app.get("/test")
async def ping():
    return {"status": "ok"}

print(f"App created successfully: {app}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8602)
#!/usr/bin/env python3
from fastapi import FastAPI

app = FastAPI(title="Test App")

@app.get("/test")
def test():
    return {"status": "ok"}

if __name__ == "__main__":
    print("App created:", app)
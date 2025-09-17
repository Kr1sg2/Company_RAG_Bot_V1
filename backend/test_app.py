#!/usr/bin/env python3
from fastapi import FastAPI

app = FastAPI(title="Test App")


@app.get("/test")
def ping():
    return {"status": "ok"}


def test_app_exists():
    # simple sanity to avoid pytest return warning
    assert isinstance(app.title, str)


if __name__ == "__main__":
    print("App created:", app)

from fastapi import FastAPI

app = FastAPI(title="dulieuchungkhoan.vn api")


@app.get("/api/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "api"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from .routers import binder, dims, facts, reconcile, stubs

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Latebind 晚维台", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(facts.router)
app.include_router(dims.router)
app.include_router(binder.router)
app.include_router(reconcile.router)
app.include_router(stubs.router)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "latebind"}

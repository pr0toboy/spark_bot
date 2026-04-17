from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import ai, notes, tools, skills, settings, context_route, crypto

app = FastAPI(title="Spark API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai.router)
app.include_router(notes.router)
app.include_router(tools.router)
app.include_router(skills.router)
app.include_router(settings.router)
app.include_router(context_route.router)
app.include_router(crypto.router)


@app.get("/health")
def health():
    return {"status": "ok"}

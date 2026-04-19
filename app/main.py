from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.routes import ai, notes, tools, skills, settings, context_route, crypto, habit, agent as agent_router, backup

_scheduler = BackgroundScheduler(daemon=True)


def _scheduler_tick():
    from datetime import datetime, timezone
    from commands.agent import _init_tables, run_agent
    from context import get_conn

    conn = get_conn()
    _init_tables(conn)
    now = datetime.now(timezone.utc)
    rows = conn.execute(
        "SELECT id, interval_minutes, last_run FROM agents WHERE enabled=1"
    ).fetchall()
    conn.close()

    for aid, interval, last_run in rows:
        if last_run is None:
            run_agent(aid)
        else:
            from datetime import datetime as dt
            elapsed = (now - dt.fromisoformat(last_run)).total_seconds() / 60
            if elapsed >= interval:
                run_agent(aid)


@asynccontextmanager
async def lifespan(_: FastAPI):
    _scheduler.add_job(_scheduler_tick, "interval", minutes=1, id="agent_tick")
    _scheduler.start()
    yield
    _scheduler.shutdown(wait=False)


app = FastAPI(title="Spark API", version="1.0.0", lifespan=lifespan)

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
app.include_router(habit.router)
app.include_router(agent_router.router)
app.include_router(backup.router)


@app.get("/health")
def health():
    return {"status": "ok"}

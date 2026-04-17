from datetime import date, timedelta
from fastapi import APIRouter, HTTPException
from app.models import HabitItem, HabitCreate, HabitStats, HabitCheckResult
from commands.habit import _init_tables, _resolve, _streak, _week_done_set
from context import get_conn

router = APIRouter(prefix="/api/habits", tags=["habits"])


def _conn():
    c = get_conn()
    _init_tables(c)
    return c


def _week_bools(conn, habit_id: int) -> list[bool]:
    today = date.today()
    done = _week_done_set(conn, habit_id)
    return [str(today - timedelta(days=i)) in done for i in range(6, -1, -1)]


def _to_item(conn, row) -> HabitItem:
    hid, name, fn, fd = row[0], row[1], row[2], row[3]
    today_str = str(date.today())
    done_today = bool(conn.execute(
        "SELECT 1 FROM habit_entries WHERE habit_id=? AND date=?", (hid, today_str)
    ).fetchone())
    cur, best = _streak(conn, hid, fn, fd)
    return HabitItem(
        id=hid, name=name, freq_num=fn, freq_den=fd,
        done_today=done_today, streak=cur, best_streak=best,
        week=_week_bools(conn, hid),
    )


@router.get("", response_model=list[HabitItem])
def list_habits():
    c = _conn()
    rows = c.execute(
        "SELECT id, name, freq_num, freq_den FROM habits WHERE archived=0 ORDER BY position, id"
    ).fetchall()
    result = [_to_item(c, r) for r in rows]
    c.close()
    return result


@router.post("", response_model=HabitItem, status_code=201)
def create_habit(req: HabitCreate):
    c = _conn()
    existing = c.execute(
        "SELECT id FROM habits WHERE lower(name)=lower(?)", (req.name,)
    ).fetchone()
    if existing:
        c.close()
        raise HTTPException(status_code=409, detail=f"Habitude « {req.name} » existe déjà.")
    pos = (c.execute("SELECT COALESCE(MAX(position),0) FROM habits").fetchone()[0] or 0) + 1
    c.execute(
        "INSERT INTO habits (name, freq_num, freq_den, created_at, position) VALUES (?,?,?,?,?)",
        (req.name, req.freq_num, req.freq_den, str(date.today()), pos),
    )
    c.commit()
    hid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    row = c.execute("SELECT id, name, freq_num, freq_den FROM habits WHERE id=?", (hid,)).fetchone()
    result = _to_item(c, row)
    c.close()
    return result


@router.post("/{habit_id}/check", response_model=HabitCheckResult)
def check_habit(habit_id: int):
    c = _conn()
    row = c.execute(
        "SELECT id, name, freq_num, freq_den FROM habits WHERE id=? AND archived=0",
        (habit_id,),
    ).fetchone()
    if not row:
        c.close()
        raise HTTPException(status_code=404, detail=f"Habitude #{habit_id} introuvable.")
    hid, name, fn, fd = row
    today_str = str(date.today())
    c.execute(
        "INSERT OR REPLACE INTO habit_entries (habit_id, date, value, notes) VALUES (?,?,1,'')",
        (hid, today_str),
    )
    c.commit()
    cur, best = _streak(c, hid, fn, fd)
    c.close()
    return HabitCheckResult(id=hid, name=name, done_today=True, streak=cur, best_streak=best)


@router.delete("/{habit_id}/check", response_model=HabitCheckResult)
def uncheck_habit(habit_id: int):
    c = _conn()
    row = c.execute(
        "SELECT id, name, freq_num, freq_den FROM habits WHERE id=? AND archived=0",
        (habit_id,),
    ).fetchone()
    if not row:
        c.close()
        raise HTTPException(status_code=404, detail=f"Habitude #{habit_id} introuvable.")
    hid, name, fn, fd = row[0], row[1], row[2], row[3]
    c.execute(
        "DELETE FROM habit_entries WHERE habit_id=? AND date=?", (hid, str(date.today()))
    )
    c.commit()
    cur, best = _streak(c, hid, fn, fd)
    c.close()
    return HabitCheckResult(id=hid, name=name, done_today=False, streak=cur, best_streak=best)


@router.get("/{habit_id}/stats", response_model=HabitStats)
def habit_stats(habit_id: int):
    c = _conn()
    row = c.execute(
        "SELECT id, name, freq_num, freq_den FROM habits WHERE id=? AND archived=0",
        (habit_id,),
    ).fetchone()
    if not row:
        c.close()
        raise HTTPException(status_code=404, detail=f"Habitude #{habit_id} introuvable.")
    hid, name, fn, fd = row[0], row[1], row[2], row[3]
    cur, best = _streak(c, hid, fn, fd)
    total = c.execute("SELECT COUNT(*) FROM habit_entries WHERE habit_id=?", (hid,)).fetchone()[0]
    week_done = c.execute(
        "SELECT COUNT(*) FROM habit_entries WHERE habit_id=? AND date>=?",
        (hid, str(date.today() - timedelta(days=6))),
    ).fetchone()[0]
    month_done = c.execute(
        "SELECT COUNT(*) FROM habit_entries WHERE habit_id=? AND date>=?",
        (hid, str(date.today() - timedelta(days=29))),
    ).fetchone()[0]
    week = _week_bools(c, hid)
    c.close()
    return HabitStats(
        id=hid, name=name, streak=cur, best_streak=best,
        week_done=week_done, month_done=month_done, total=total, week=week,
    )


@router.delete("/{habit_id}")
def delete_habit(habit_id: int):
    c = _conn()
    cur = c.execute(
        "UPDATE habits SET archived=1 WHERE id=? AND archived=0", (habit_id,)
    )
    c.commit()
    c.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Habitude #{habit_id} introuvable.")
    return {"ok": True}

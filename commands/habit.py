import sqlite3
from datetime import date, timedelta
from pathlib import Path
from result import Result
from context import get_conn


def _init_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            freq_num    INTEGER NOT NULL DEFAULT 1,
            freq_den    INTEGER NOT NULL DEFAULT 1,
            type        INTEGER NOT NULL DEFAULT 0,
            target_value REAL NOT NULL DEFAULT 0,
            unit        TEXT NOT NULL DEFAULT '',
            archived    INTEGER NOT NULL DEFAULT 0,
            position    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS habit_entries (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
            date     TEXT NOT NULL,
            value    REAL NOT NULL DEFAULT 1,
            notes    TEXT NOT NULL DEFAULT '',
            UNIQUE(habit_id, date)
        )
    """)
    conn.commit()


def _freq_label(fn: int, fd: int) -> str:
    if fd == 1:
        return "quotidien"
    if fd == 7:
        return f"{fn}×/sem"
    return f"{fn}/{fd}j"


def _week_done_set(conn: sqlite3.Connection, habit_id: int) -> set[str]:
    today = date.today()
    start = str(today - timedelta(days=6))
    end = str(today)
    return {
        r[0] for r in conn.execute(
            "SELECT date FROM habit_entries WHERE habit_id=? AND date BETWEEN ? AND ?",
            (habit_id, start, end),
        ).fetchall()
    }


def _week_view(conn: sqlite3.Connection, habit_id: int) -> str:
    today = date.today()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    done = _week_done_set(conn, habit_id)
    day_labels = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
    return "  ".join(
        f"{day_labels[d.weekday()]}{'✓' if str(d) in done else '·'}"
        for d in days
    )


def _resolve(conn: sqlite3.Connection, name_or_id: str):
    """Return (id, name, freq_num, freq_den, type, unit) or None."""
    if name_or_id.isdigit():
        return conn.execute(
            "SELECT id, name, freq_num, freq_den, type, unit FROM habits WHERE id=? AND archived=0",
            (int(name_or_id),),
        ).fetchone()
    return conn.execute(
        "SELECT id, name, freq_num, freq_den, type, unit FROM habits WHERE lower(name)=lower(?) AND archived=0",
        (name_or_id,),
    ).fetchone()


def _streak(conn: sqlite3.Connection, habit_id: int, freq_num: int, freq_den: int) -> tuple[int, int]:
    """Return (current_streak, best_streak) counted in freq_den-day windows."""
    rows = conn.execute(
        "SELECT date FROM habit_entries WHERE habit_id=? ORDER BY date DESC",
        (habit_id,),
    ).fetchall()
    done_dates = {r[0] for r in rows}
    if not done_dates:
        return 0, 0

    today = date.today()
    min_date = date.fromisoformat(min(done_dates))

    def _window_done(start: date) -> bool:
        end = start + timedelta(days=freq_den - 1)
        return sum(1 for d in done_dates if str(start) <= d <= str(end)) >= freq_num

    windows: list[date] = []
    cur = min_date
    while cur <= today:
        windows.append(cur)
        cur += timedelta(days=freq_den)

    current = 0
    best = 0
    run = 0
    for w in reversed(windows):
        if _window_done(w):
            run += 1
            if run > best:
                best = run
        else:
            if current == 0:
                current = run
            run = 0

    if current == 0:
        current = run
    if run > best:
        best = run
    return current, best


def _cmd_list(conn: sqlite3.Connection, _args: str) -> str:
    habits = conn.execute(
        "SELECT id, name, freq_num, freq_den, type, unit FROM habits WHERE archived=0 ORDER BY position, id"
    ).fetchall()
    if not habits:
        return "Aucune habitude. Crée-en une avec /habit add <nom>"

    today_str = str(date.today())
    lines = []
    for hid, name, fn, fd, htype, unit in habits:
        done_today = conn.execute(
            "SELECT 1 FROM habit_entries WHERE habit_id=? AND date=?", (hid, today_str)
        ).fetchone()
        cur, _ = _streak(conn, hid, fn, fd)
        check = "✓" if done_today else "○"
        streak_str = f"  🔥{cur}" if cur >= 2 else ""
        lines.append(f"  {check} [{hid}] {name}  ({_freq_label(fn, fd)}){streak_str}")
        lines.append(f"      {_week_view(conn, hid)}")
    return "\n".join(lines)


def _cmd_add(conn: sqlite3.Connection, args: str) -> str:
    parts = args.split(None, 2)
    if not parts:
        return "Usage : /habit add <nom> [<freq_num>/<freq_den>j]  ex: /habit add Sport  ou  /habit add Lecture 3/7j"

    name = parts[0]
    freq_num, freq_den = 1, 1
    if len(parts) >= 2:
        freq_raw = parts[1].rstrip("jJ")
        if "/" in freq_raw:
            try:
                fn, fd = freq_raw.split("/")
                freq_num, freq_den = int(fn), int(fd)
            except ValueError:
                return f"Format de fréquence invalide : {parts[1]}  (ex: 3/7j)"
        else:
            return f"Format de fréquence invalide : {parts[1]}  (ex: 1/1j ou 3/7j)"

    if conn.execute("SELECT id FROM habits WHERE lower(name)=lower(?)", (name,)).fetchone():
        return f"L'habitude « {name} » existe déjà."

    pos = (conn.execute("SELECT COALESCE(MAX(position),0) FROM habits").fetchone()[0] or 0) + 1
    conn.execute(
        "INSERT INTO habits (name, freq_num, freq_den, created_at, position) VALUES (?,?,?,?,?)",
        (name, freq_num, freq_den, str(date.today()), pos),
    )
    conn.commit()
    return f"Habitude « {name} » créée ({_freq_label(freq_num, freq_den)}). Coche avec /habit check {name}"


def _cmd_check(conn: sqlite3.Connection, args: str) -> str:
    if not args:
        return "Usage : /habit check <nom|id> [valeur] [note]"
    parts = args.split(None, 2)
    name_or_id = parts[0]
    value = 1.0
    notes = ""
    if len(parts) >= 2:
        try:
            value = float(parts[1])
            if len(parts) >= 3:
                notes = parts[2]
        except ValueError:
            notes = " ".join(parts[1:])

    row = _resolve(conn, name_or_id)
    if not row:
        return f"Habitude « {name_or_id} » introuvable."
    hid, name, fn, fd, _, unit = row
    conn.execute(
        "INSERT OR REPLACE INTO habit_entries (habit_id, date, value, notes) VALUES (?,?,?,?)",
        (hid, str(date.today()), value, notes),
    )
    conn.commit()

    cur, best = _streak(conn, hid, fn, fd)
    streak_msg = ""
    if cur >= 2:
        streak_msg = f"  🔥 Streak : {cur} {'jours' if fd == 1 else 'semaines'}"
        if cur == best and cur >= 3:
            streak_msg += "  🏆 record !"
    val_str = f" ({value} {unit})" if unit else ""
    return f"✓ « {name} » cochée{val_str}{streak_msg}"


def _cmd_uncheck(conn: sqlite3.Connection, args: str) -> str:
    if not args:
        return "Usage : /habit uncheck <nom|id>"
    row = _resolve(conn, args.strip())
    if not row:
        return f"Habitude « {args.strip()} » introuvable."
    hid, name = row[0], row[1]
    conn.execute(
        "DELETE FROM habit_entries WHERE habit_id=? AND date=?", (hid, str(date.today()))
    )
    conn.commit()
    return f"○ « {name} » décochée pour aujourd'hui."


def _cmd_stats(conn: sqlite3.Connection, args: str) -> str:
    if args:
        row = _resolve(conn, args.strip())
        if not row:
            return f"Habitude « {args.strip()} » introuvable."
        habits = [row]
    else:
        habits = conn.execute(
            "SELECT id, name, freq_num, freq_den, type, unit FROM habits WHERE archived=0 ORDER BY position, id"
        ).fetchall()
        if not habits:
            return "Aucune habitude enregistrée."

    today = date.today()
    lines = ["── Stats des habitudes ──"]
    for hid, name, fn, fd, _, unit in habits:
        cur, best = _streak(conn, hid, fn, fd)
        total = conn.execute("SELECT COUNT(*) FROM habit_entries WHERE habit_id=?", (hid,)).fetchone()[0]
        week_done = conn.execute(
            "SELECT COUNT(*) FROM habit_entries WHERE habit_id=? AND date>=?",
            (hid, str(today - timedelta(days=6))),
        ).fetchone()[0]
        month_done = conn.execute(
            "SELECT COUNT(*) FROM habit_entries WHERE habit_id=? AND date>=?",
            (hid, str(today - timedelta(days=29))),
        ).fetchone()[0]
        lines.append(f"\n{name}")
        lines.append(f"  Cette semaine : {week_done}/7 jours  |  Ce mois : {month_done}/30 jours")
        lines.append(f"  Streak actuel : {cur}  |  Record : {best}  |  Total : {total}")
        lines.append(f"  {_week_view(conn, hid)}")
    return "\n".join(lines)


def _cmd_history(conn: sqlite3.Connection, args: str) -> str:
    if not args:
        return "Usage : /habit history <nom|id>"
    row = _resolve(conn, args.strip())
    if not row:
        return f"Habitude « {args.strip()} » introuvable."
    hid, name = row[0], row[1]
    entries = conn.execute(
        "SELECT date, value, notes FROM habit_entries WHERE habit_id=? ORDER BY date DESC LIMIT 30",
        (hid,),
    ).fetchall()
    if not entries:
        return f"Aucune entrée pour « {name} »."
    lines = [f"Historique « {name} » (30 derniers jours) :"]
    for d, v, n in entries:
        note_str = f"  ← {n}" if n else ""
        lines.append(f"  {d}  ✓ {v}{note_str}")
    return "\n".join(lines)


def _cmd_delete(conn: sqlite3.Connection, args: str) -> str:
    if not args:
        return "Usage : /habit delete <nom|id>"
    row = _resolve(conn, args.strip())
    if not row:
        return f"Habitude « {args.strip()} » introuvable."
    hid, name = row[0], row[1]
    conn.execute("UPDATE habits SET archived=1 WHERE id=?", (hid,))
    conn.commit()
    return f"Habitude « {name} » archivée (données conservées)."


def _cmd_import(conn: sqlite3.Connection, args: str) -> str:
    path = Path(args.strip()) if args.strip() else None
    if not path or not path.exists():
        default = Path.home() / "ProtoDocs" / "Loop Habits Backup 2026-04-17 230140.db"
        if default.exists():
            path = default
        else:
            return (
                "Fichier introuvable. Usage : /habit import <chemin_vers_backup.db>\n"
                "Exemple : /habit import ~/ProtoDocs/\"Loop Habits Backup 2026-04-17 230140.db\""
            )

    src = sqlite3.connect(str(path))
    habits_imported = 0
    entries_imported = 0

    for lhid, name, desc, fn, fd, htype, tv, unit, pos in src.execute(
        "SELECT id, name, description, freq_num, freq_den, type, target_value, unit, position FROM Habits WHERE archived=0"
    ).fetchall():
        existing = conn.execute("SELECT id FROM habits WHERE lower(name)=lower(?)", (name,)).fetchone()
        if existing:
            new_hid = existing[0]
        else:
            conn.execute(
                "INSERT INTO habits (name, description, freq_num, freq_den, type, target_value, unit, archived, position, created_at) "
                "VALUES (?,?,?,?,?,?,?,0,?,?)",
                (name, desc or "", fn, fd, htype, tv, unit or "", pos, str(date.today())),
            )
            conn.commit()
            new_hid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            habits_imported += 1

        for ts_ms, val, notes in src.execute(
            "SELECT timestamp, value, notes FROM Repetitions WHERE habit=?", (lhid,)
        ).fetchall():
            d = date.fromtimestamp(ts_ms // 1000).isoformat()
            cur = conn.execute(
                "INSERT OR IGNORE INTO habit_entries (habit_id, date, value, notes) VALUES (?,?,?,?)",
                (new_hid, d, 1.0 if val == 2 else float(val), notes or ""),
            )
            entries_imported += cur.rowcount
        conn.commit()

    src.close()
    return (
        f"Import Loop Habits terminé :\n"
        f"  {habits_imported} habitude(s) importée(s)\n"
        f"  {entries_imported} entrée(s) importée(s)"
    )


def handle(ctx, user_input: str) -> Result:
    args = user_input.removeprefix("/habit").strip()
    conn = get_conn()
    _init_tables(conn)

    if not args:
        msg = _cmd_list(conn, "")
        conn.close()
        return Result.success(msg)

    subcmd, _, rest = args.partition(" ")
    rest = rest.strip()

    dispatch = {
        "add":     lambda: _cmd_add(conn, rest),
        "check":   lambda: _cmd_check(conn, rest),
        "uncheck": lambda: _cmd_uncheck(conn, rest),
        "done":    lambda: _cmd_check(conn, rest),
        "stats":   lambda: _cmd_stats(conn, rest),
        "history": lambda: _cmd_history(conn, rest),
        "delete":  lambda: _cmd_delete(conn, rest),
        "import":  lambda: _cmd_import(conn, rest),
    }

    fn = dispatch.get(subcmd)
    if fn:
        msg = fn()
        conn.close()
        return Result.success(msg)

    if _resolve(conn, subcmd):
        msg = _cmd_check(conn, subcmd)
        conn.close()
        return Result.success(msg)

    conn.close()
    return Result.error(
        f"Sous-commande inconnue : « {subcmd} »\n"
        "Usage : /habit [add|check|uncheck|stats|history|delete|import] [args]"
    )

# Spark Bot Python Rewrite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Réécrire Spark en Python avec persistance JSON et une commande `/ask` alimentée par Claude.

**Architecture:** Classe `SparkBot` avec boucle REPL et dispatch par dictionnaire. Chaque commande est un module avec une fonction `handle(ctx, user_input)`. Le `Context` est un dataclass Python sérialisé en JSON dans `data/spark_data.json`.

**Tech Stack:** Python 3.11+, `anthropic`, `requests`, `pytest`

---

## Structure des fichiers

```
spark_bot/               ← racine du projet (à côté de src/ Rust)
├── SPARK.md             # système prompt de Spark (personnalité IA)
├── main.py              # point d'entrée
├── bot.py               # classe SparkBot : REPL + dispatch
├── context.py           # dataclass Context + persistance JSON
├── requirements.txt     # anthropic, requests
├── data/
│   └── spark_data.json  # persisté entre sessions (auto-créé)
├── commands/
│   ├── __init__.py
│   ├── start.py
│   ├── help.py
│   ├── remember.py
│   ├── recall.py
│   ├── todo.py
│   ├── remind.py
│   ├── pomodoro.py
│   ├── localize.py
│   ├── weather.py
│   └── ask.py
└── tests/
    ├── __init__.py
    ├── test_context.py
    ├── test_bot.py
    └── commands/
        ├── __init__.py
        ├── test_remember.py
        ├── test_recall.py
        ├── test_todo.py
        ├── test_remind.py
        ├── test_localize.py
        ├── test_weather.py
        └── test_ask.py
```

---

## Task 1: Setup du projet

**Files:**
- Create: `requirements.txt`
- Create: `commands/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/commands/__init__.py`

- [ ] **Step 1: Créer requirements.txt**

```
anthropic
requests
pytest
```

- [ ] **Step 2: Créer les dossiers et fichiers vides**

```bash
cd /home/aelio/Nexus_WSL/spark_bot
mkdir -p commands tests/commands data
touch commands/__init__.py tests/__init__.py tests/commands/__init__.py
```

- [ ] **Step 3: Installer les dépendances**

```bash
pip install -r requirements.txt
```

Expected: `Successfully installed anthropic-X.X.X requests-X.X.X`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt commands/__init__.py tests/__init__.py tests/commands/__init__.py
git commit -m "feat: python project setup"
```

---

## Task 2: Context (persistance JSON)

**Files:**
- Create: `context.py`
- Create: `tests/test_context.py`

- [ ] **Step 1: Écrire les tests**

`tests/test_context.py`:
```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from context import Context


def test_context_defaults():
    ctx = Context()
    assert ctx.memory == ""
    assert ctx.todo_list == {}
    assert ctx.chat_history == []


def test_context_save(tmp_path):
    ctx = Context(memory="test")
    data_path = tmp_path / "spark_data.json"
    with patch("context.DATA_PATH", data_path):
        ctx.save()
    saved = json.loads(data_path.read_text())
    assert saved["memory"] == "test"
    assert saved["todo_list"] == {}
    assert saved["chat_history"] == []


def test_context_load(tmp_path):
    data_path = tmp_path / "spark_data.json"
    data_path.write_text(json.dumps({
        "memory": "acheter du pain",
        "todo_list": {"courses": ["pain", "lait"]},
        "chat_history": [],
    }))
    with patch("context.DATA_PATH", data_path):
        ctx = Context.load()
    assert ctx.memory == "acheter du pain"
    assert ctx.todo_list == {"courses": ["pain", "lait"]}


def test_context_load_missing_file(tmp_path):
    with patch("context.DATA_PATH", tmp_path / "missing.json"):
        ctx = Context.load()
    assert ctx.memory == ""
```

- [ ] **Step 2: Vérifier que les tests échouent**

```bash
pytest tests/test_context.py -v
```

Expected: `ImportError: No module named 'context'`

- [ ] **Step 3: Implémenter context.py**

`context.py`:
```python
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

DATA_PATH = Path("data/spark_data.json")


@dataclass
class Context:
    memory: str = ""
    todo_list: dict = field(default_factory=dict)
    chat_history: list = field(default_factory=list)

    def save(self) -> None:
        DATA_PATH.parent.mkdir(exist_ok=True)
        DATA_PATH.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False))

    @classmethod
    def load(cls) -> "Context":
        if DATA_PATH.exists():
            return cls(**json.loads(DATA_PATH.read_text()))
        return cls()
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/test_context.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add context.py tests/test_context.py
git commit -m "feat: context dataclass with JSON persistence"
```

---

## Task 3: SparkBot (REPL + dispatch)

**Files:**
- Create: `bot.py`
- Create: `main.py`
- Create: `tests/test_bot.py`

- [ ] **Step 1: Écrire les tests**

`tests/test_bot.py`:
```python
from unittest.mock import patch, MagicMock, call
from context import Context
from bot import SparkBot


def make_bot():
    bot = SparkBot.__new__(SparkBot)
    bot.ctx = Context()
    bot.commands = {"/fake": MagicMock()}
    return bot


def test_dispatch_known_command():
    bot = make_bot()
    with patch("builtins.input", side_effect=["/fake arg", "/exit"]):
        with patch("builtins.print"):
            bot.run()
    bot.commands["/fake"].assert_called_once_with(bot.ctx, "/fake arg")


def test_dispatch_unknown_command(capsys):
    bot = make_bot()
    with patch("builtins.input", side_effect=["/inconnu", "/exit"]):
        bot.run()
    out = capsys.readouterr().out
    assert "inconnue" in out.lower()


def test_exit_saves_context():
    bot = make_bot()
    with patch("builtins.input", return_value="/exit"):
        with patch.object(bot.ctx, "save") as mock_save:
            with patch("builtins.print"):
                bot.run()
    mock_save.assert_called_once()


def test_empty_input_ignored():
    bot = make_bot()
    with patch("builtins.input", side_effect=["", "/exit"]):
        with patch("builtins.print"):
            bot.run()
    bot.commands["/fake"].assert_not_called()
```

- [ ] **Step 2: Vérifier que les tests échouent**

```bash
pytest tests/test_bot.py -v
```

Expected: `ImportError: No module named 'bot'`

- [ ] **Step 3: Implémenter bot.py**

`bot.py`:
```python
from context import Context
from commands import (
    start, help as help_cmd, remember, recall,
    todo, remind, pomodoro, localize, weather, ask,
)


class SparkBot:
    def __init__(self):
        self.ctx = Context.load()
        self.commands = {
            "/start":    start.handle,
            "/help":     help_cmd.handle,
            "/remember": remember.handle,
            "/recall":   recall.handle,
            "/todo":     todo.handle,
            "/remind":   remind.handle,
            "/pomodoro": pomodoro.handle,
            "/localize": localize.handle,
            "/weather":  weather.handle,
            "/ask":      ask.handle,
        }

    def run(self):
        print("Salut, je suis Spark. Tape /help ou /exit.")
        while True:
            user_input = input("› ").strip()
            if not user_input:
                continue
            if user_input == "/exit":
                self.ctx.save()
                print("À bientôt !")
                break
            cmd = user_input.split()[0]
            handler = self.commands.get(cmd)
            if handler:
                handler(self.ctx, user_input)
            else:
                print("Commande inconnue. Tape /help.")
```

- [ ] **Step 4: Créer main.py**

`main.py`:
```python
from bot import SparkBot


def main():
    SparkBot().run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Créer des stubs vides pour tous les modules commands** (pour que l'import dans bot.py fonctionne)

```bash
for cmd in start help remember recall todo remind pomodoro localize weather ask; do
    echo "def handle(ctx, user_input: str) -> None: pass" > commands/$cmd.py
done
```

- [ ] **Step 6: Vérifier que les tests passent**

```bash
pytest tests/test_bot.py -v
```

Expected: `4 passed`

- [ ] **Step 7: Commit**

```bash
git add bot.py main.py commands/*.py tests/test_bot.py
git commit -m "feat: SparkBot REPL with command dispatch"
```

---

## Task 4: /help et /start

**Files:**
- Modify: `commands/help.py`
- Modify: `commands/start.py`

Ces deux commandes n'ont pas d'état — pas de tests d'intégration nécessaires, on vérifie uniquement l'output.

- [ ] **Step 1: Implémenter commands/help.py**

```python
COMMANDS = [
    ("/start",    "Démarrer une nouvelle tâche"),
    ("/remember", "Mémoriser une information"),
    ("/recall",   "Afficher ce que Spark a mémorisé"),
    ("/todo",     "Gérer une liste de tâches"),
    ("/remind",   "Créer un rappel  (ex: /remind boire, 10min)"),
    ("/pomodoro", "Lancer un minuteur Pomodoro (4 cycles 25min/5min)"),
    ("/localize", "Me localiser dans le monde (IP)"),
    ("/weather",  "Afficher la météo actuelle"),
    ("/ask",      "Poser une question à l'IA"),
    ("/help",     "Afficher cette aide"),
    ("/exit",     "Quitter Spark"),
]


def handle(ctx, user_input: str) -> None:
    print("Commandes disponibles :")
    for cmd, desc in COMMANDS:
        print(f"  {cmd:<12} — {desc}")
```

- [ ] **Step 2: Implémenter commands/start.py**

```python
def handle(ctx, user_input: str) -> None:
    print("🚀 Prêt à démarrer. Que veux-tu faire ?")
```

- [ ] **Step 3: Tester manuellement**

```bash
python main.py
```

Taper `/help` → vérifier que la liste s'affiche. Taper `/exit`.

- [ ] **Step 4: Commit**

```bash
git add commands/help.py commands/start.py
git commit -m "feat: /help and /start commands"
```

---

## Task 5: /remember et /recall

**Files:**
- Modify: `commands/remember.py`
- Modify: `commands/recall.py`
- Create: `tests/commands/test_remember.py`

- [ ] **Step 1: Écrire les tests**

`tests/commands/test_remember.py`:
```python
from unittest.mock import patch
from context import Context
from commands import remember, recall


def test_remember_stores_input():
    ctx = Context()
    with patch("builtins.input", return_value="acheter du pain"):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                remember.handle(ctx, "/remember")
    assert ctx.memory == "acheter du pain"


def test_remember_saves_context():
    ctx = Context()
    with patch("builtins.input", return_value="test"):
        with patch("builtins.print"):
            with patch.object(ctx, "save") as mock_save:
                remember.handle(ctx, "/remember")
    mock_save.assert_called_once()


def test_recall_with_memory(capsys):
    ctx = Context(memory="acheter du pain")
    recall.handle(ctx, "/recall")
    assert "acheter du pain" in capsys.readouterr().out


def test_recall_empty(capsys):
    ctx = Context()
    recall.handle(ctx, "/recall")
    assert "rien" in capsys.readouterr().out.lower() or "vide" in capsys.readouterr().out.lower()
```

- [ ] **Step 2: Vérifier que les tests échouent**

```bash
pytest tests/commands/test_remember.py -v
```

Expected: `FAILED` (stubs retournent `None`, assertions échouent)

- [ ] **Step 3: Implémenter commands/remember.py**

```python
def handle(ctx, user_input: str) -> None:
    print("Que dois-je me souvenir ?")
    ctx.memory = input("› ").strip()
    ctx.save()
    print("Ok, je m'en souviendrai !")
```

- [ ] **Step 4: Implémenter commands/recall.py**

```python
def handle(ctx, user_input: str) -> None:
    if ctx.memory:
        print(f"Je me souviens de : {ctx.memory}")
    else:
        print("Je n'ai rien en mémoire.")
```

- [ ] **Step 5: Vérifier que les tests passent**

```bash
pytest tests/commands/test_remember.py -v
```

Expected: `4 passed`

- [ ] **Step 6: Commit**

```bash
git add commands/remember.py commands/recall.py tests/commands/test_remember.py
git commit -m "feat: /remember and /recall commands"
```

---

## Task 6: /todo

**Files:**
- Modify: `commands/todo.py`
- Create: `tests/commands/test_todo.py`

- [ ] **Step 1: Écrire les tests**

`tests/commands/test_todo.py`:
```python
from unittest.mock import patch
from context import Context
from commands import todo


def test_create_list():
    ctx = Context()
    inputs = iter(["liste1", "/exit"])
    with patch("builtins.input", side_effect=inputs):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                # simulate /new then /exit
                todo._create_list(ctx)
    assert "liste1" in ctx.todo_list


def test_create_list_duplicate(capsys):
    ctx = Context(todo_list={"courses": []})
    with patch("builtins.input", return_value="courses"):
        todo._create_list(ctx)
    assert "existe" in capsys.readouterr().out


def test_remove_list():
    ctx = Context(todo_list={"courses": ["pain"]})
    with patch("builtins.input", return_value="courses"):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                todo._remove_list(ctx)
    assert "courses" not in ctx.todo_list


def test_remove_list_missing(capsys):
    ctx = Context()
    with patch("builtins.input", return_value="inexistant"):
        todo._remove_list(ctx)
    assert "existe" in capsys.readouterr().out.lower() or "n'existe" in capsys.readouterr().out.lower()
```

- [ ] **Step 2: Vérifier que les tests échouent**

```bash
pytest tests/commands/test_todo.py -v
```

Expected: `FAILED` (fonctions pas encore définies)

- [ ] **Step 3: Implémenter commands/todo.py**

```python
def handle(ctx, user_input: str) -> None:
    print("📒 Gestionnaire de listes")
    _show_lists(ctx.todo_list)
    while True:
        cmd = input("› ").strip()
        if cmd == "/new":
            _create_list(ctx)
        elif cmd == "/show":
            _show_list(ctx.todo_list)
        elif cmd == "/edit":
            _edit_list(ctx)
        elif cmd == "/remove":
            _remove_list(ctx)
        elif cmd == "/exit":
            print("Fin du gestionnaire.")
            break
        else:
            print("Commandes : /new, /show, /edit, /remove, /exit")


def _show_lists(todo_list: dict) -> None:
    if not todo_list:
        print("Il n'y a pas de liste.")
    else:
        print("Listes existantes :")
        for name in todo_list:
            print(f"  - {name}")


def _create_list(ctx) -> None:
    name = input("Nom de la nouvelle liste : ").strip()
    if name in ctx.todo_list:
        print("❗ Une liste avec ce nom existe déjà.")
    else:
        ctx.todo_list[name] = []
        ctx.save()
        print(f"✅ Liste '{name}' créée.")


def _show_list(todo_list: dict) -> None:
    name = input("Quelle liste afficher ? ").strip()
    if name not in todo_list:
        print("❌ Liste introuvable.")
    elif not todo_list[name]:
        print("📭 La liste est vide.")
    else:
        print(f"📋 Contenu de '{name}' :")
        for item in todo_list[name]:
            print(f"  - {item}")


def _remove_list(ctx) -> None:
    name = input("Quelle liste supprimer ? ").strip()
    if name in ctx.todo_list:
        del ctx.todo_list[name]
        ctx.save()
        print(f"✅ Liste '{name}' supprimée.")
    else:
        print("❗ Cette liste n'existe pas.")


def _edit_list(ctx) -> None:
    name = input("Quelle liste éditer ? ").strip()
    if name not in ctx.todo_list:
        print("❌ Liste introuvable.")
        return
    items = ctx.todo_list[name]
    while True:
        print(f"(édition de '{name}') Tape /add, /remove, /show ou /exit :")
        cmd = input("› ").strip()
        if cmd == "/add":
            item = input("Nom du nouvel élément : ").strip()
            items.append(item)
            ctx.save()
            print("✅ Ajouté.")
        elif cmd == "/remove":
            item = input("Nom de l'élément à supprimer : ").strip()
            if item in items:
                items.remove(item)
                ctx.save()
                print("✅ Supprimé.")
            else:
                print("❌ Élément non trouvé.")
        elif cmd == "/show":
            if not items:
                print("📭 La liste est vide.")
            else:
                for i in items:
                    print(f"  - {i}")
        elif cmd == "/exit":
            break
        else:
            print("Commandes : /add, /remove, /show, /exit")
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/commands/test_todo.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add commands/todo.py tests/commands/test_todo.py
git commit -m "feat: /todo command with sub-REPL"
```

---

## Task 7: /remind

**Files:**
- Modify: `commands/remind.py`
- Create: `tests/commands/test_remind.py`

- [ ] **Step 1: Écrire les tests**

`tests/commands/test_remind.py`:
```python
from unittest.mock import patch, MagicMock
from context import Context
from commands import remind


def test_parse_duration_minutes():
    assert remind._parse_duration("10min") == 600
    assert remind._parse_duration("10 minutes") == 600
    assert remind._parse_duration("1 minute") == 60


def test_parse_duration_seconds():
    assert remind._parse_duration("30s") == 30
    assert remind._parse_duration("30 secondes") == 30


def test_parse_duration_hours():
    assert remind._parse_duration("1h") == 3600
    assert remind._parse_duration("2 heures") == 7200


def test_parse_duration_invalid():
    assert remind._parse_duration("blabla") is None
    assert remind._parse_duration("") is None


def test_remind_creates_timer(capsys):
    ctx = Context()
    with patch("threading.Timer") as mock_timer:
        mock_timer.return_value = MagicMock()
        remind.handle(ctx, "/remind boire de l'eau, 10min")
    mock_timer.assert_called_once_with(600, mock_timer.return_value.args[1] if False else mock_timer.call_args[0][1])
    assert "✅" in capsys.readouterr().out


def test_remind_invalid_format(capsys):
    ctx = Context()
    remind.handle(ctx, "/remind sans virgule")
    assert "❌" in capsys.readouterr().out


def test_remind_invalid_duration(capsys):
    ctx = Context()
    remind.handle(ctx, "/remind boire, demain")
    assert "❌" in capsys.readouterr().out
```

- [ ] **Step 2: Vérifier que les tests échouent**

```bash
pytest tests/commands/test_remind.py -v
```

Expected: `FAILED`

- [ ] **Step 3: Implémenter commands/remind.py**

```python
import re
import threading

# Rappels en mémoire vive uniquement (non persistés)
_active_reminders: list[dict] = []


def _parse_duration(s: str) -> int | None:
    """Retourne la durée en secondes, ou None si invalide."""
    s = s.strip().lower()
    patterns = [
        (r"^(\d+)\s*(?:s|seconde|secondes)$", 1),
        (r"^(\d+)\s*(?:m|min|minute|minutes)$", 60),
        (r"^(\d+)\s*(?:h|heure|heures)$", 3600),
        (r"^(\d+)\s*(?:j|jour|jours)$", 86400),
    ]
    for pattern, multiplier in patterns:
        m = re.match(pattern, s)
        if m:
            return int(m.group(1)) * multiplier
    return None


def handle(ctx, user_input: str) -> None:
    if user_input.strip() == "/remind list":
        _list_reminders()
        return

    rest = user_input.removeprefix("/remind").strip()
    if "," not in rest:
        print("❌ Format : /remind <message>, <durée>  (ex: /remind boire de l'eau, 10min)")
        return

    message, duration_str = rest.rsplit(",", 1)
    message = message.strip()
    seconds = _parse_duration(duration_str)

    if seconds is None:
        print("❌ Durée invalide. Ex: 10min, 1h, 30s, 1 jour")
        return

    reminder = {"message": message}
    _active_reminders.append(reminder)

    def _fire():
        print(f"\n🔔 Rappel : {message}")
        if reminder in _active_reminders:
            _active_reminders.remove(reminder)

    threading.Timer(seconds, _fire).start()
    print(f"✅ Rappel créé : '{message}' dans {seconds}s")


def _list_reminders() -> None:
    if not _active_reminders:
        print("📭 Aucun rappel actif.")
    else:
        print("📋 Rappels actifs :")
        for r in _active_reminders:
            print(f"  - {r['message']}")
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/commands/test_remind.py -v
```

Expected: `6 passed`  
Note: Le test `test_remind_creates_timer` vérifie que `threading.Timer` est appelé avec la bonne durée (600s).

- [ ] **Step 5: Commit**

```bash
git add commands/remind.py tests/commands/test_remind.py
git commit -m "feat: /remind command with threaded timer"
```

---

## Task 8: /pomodoro

**Files:**
- Modify: `commands/pomodoro.py`

Pas de test unitaire (logique = `time.sleep` en boucle). On vérifie le comportement manuellement.

- [ ] **Step 1: Implémenter commands/pomodoro.py**

```python
import time


def handle(ctx, user_input: str) -> None:
    work_secs = 25 * 60
    break_secs = 5 * 60
    print("🍅 Pomodoro démarre — 25min travail / 5min pause × 4 cycles")
    print("(Ctrl+C pour annuler)\n")

    try:
        for cycle in range(1, 5):
            print(f"Cycle {cycle}/4")
            _countdown(work_secs, "💼 Travail")
            print("\n⏰ Pause !")
            _countdown(break_secs, "⏸️  Pause")
            print("\n⏰ Fin de la pause !")
        print("\n🎉 Pomodoro terminé !")
    except KeyboardInterrupt:
        print("\n⛔ Pomodoro interrompu.")


def _countdown(seconds: int, label: str) -> None:
    for remaining in range(seconds, 0, -1):
        m, s = divmod(remaining, 60)
        print(f"\r{label} : {m:02d}:{s:02d}", end="", flush=True)
        time.sleep(1)
    print(f"\r{label} : 00:00", flush=True)
```

- [ ] **Step 2: Tester manuellement avec des valeurs réduites**

Modifier temporairement `work_secs = 3` et `break_secs = 2`, lancer `python main.py`, taper `/pomodoro`, vérifier le décompte. Remettre les vraies valeurs ensuite.

- [ ] **Step 3: Commit**

```bash
git add commands/pomodoro.py
git commit -m "feat: /pomodoro command with 4 cycles"
```

---

## Task 9: /localize

**Files:**
- Modify: `commands/localize.py`
- Create: `tests/commands/test_localize.py`

- [ ] **Step 1: Écrire les tests**

`tests/commands/test_localize.py`:
```python
from unittest.mock import patch, MagicMock
from context import Context
from commands import localize


MOCK_RESPONSE = {
    "ip": "1.2.3.4",
    "city": "Paris",
    "region": "Île-de-France",
    "country": "FR",
    "loc": "48.8534,2.3488",
    "org": "AS12345 Free SAS",
}


def test_localize_displays_info(capsys):
    ctx = Context()
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_RESPONSE
    with patch("requests.get", return_value=mock_resp):
        localize.handle(ctx, "/localize")
    out = capsys.readouterr().out
    assert "Paris" in out
    assert "1.2.3.4" in out
    assert "Île-de-France" in out


def test_localize_handles_error(capsys):
    ctx = Context()
    import requests
    with patch("requests.get", side_effect=requests.RequestException("timeout")):
        localize.handle(ctx, "/localize")
    assert "❌" in capsys.readouterr().out
```

- [ ] **Step 2: Vérifier que les tests échouent**

```bash
pytest tests/commands/test_localize.py -v
```

Expected: `FAILED`

- [ ] **Step 3: Implémenter commands/localize.py**

```python
import requests


def handle(ctx, user_input: str) -> None:
    print("🔍 Localisation en cours...")
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        print(f"🌍 IP : {data.get('ip', 'Inconnue')}")
        print(f"📍 Ville : {data.get('city', 'Inconnue')}")
        print(f"🗺️  Région : {data.get('region', 'Inconnue')}")
        print(f"🇺🇳 Pays : {data.get('country', 'Inconnu')}")
        print(f"🛰️  Coordonnées : {data.get('loc', 'Inconnues')}")
        print(f"🏢 Fournisseur : {data.get('org', 'Inconnu')}")
    except requests.RequestException:
        print("❌ Erreur de connexion à l'API.")
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/commands/test_localize.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add commands/localize.py tests/commands/test_localize.py
git commit -m "feat: /localize command with IP geolocation"
```

---

## Task 10: /weather

**Files:**
- Modify: `commands/weather.py`
- Create: `tests/commands/test_weather.py`

- [ ] **Step 1: Écrire les tests**

`tests/commands/test_weather.py`:
```python
from unittest.mock import patch, MagicMock, call
from context import Context
from commands import weather


MOCK_IPINFO = {"ip": "1.2.3.4", "city": "Paris", "loc": "48.8534,2.3488"}
MOCK_WEATHER = {"current_weather": {"temperature": 15.2, "windspeed": 12.5, "weathercode": 3}}


def test_weather_displays_info(capsys):
    ctx = Context()
    mock_resp = MagicMock()
    mock_resp.json.side_effect = [MOCK_IPINFO, MOCK_WEATHER]
    with patch("requests.get", return_value=mock_resp):
        weather.handle(ctx, "/weather")
    out = capsys.readouterr().out
    assert "Paris" in out
    assert "15.2" in out
    assert "12.5" in out
    assert "☁️" in out  # code 3 = Couvert


def test_weather_handles_error(capsys):
    ctx = Context()
    import requests
    with patch("requests.get", side_effect=requests.RequestException("timeout")):
        weather.handle(ctx, "/weather")
    assert "❌" in capsys.readouterr().out


def test_wc_emoji_known_code():
    emoji, desc = weather._wc_emoji(0)
    assert emoji == "☀️"
    assert "dégagé" in desc.lower()


def test_wc_emoji_unknown_code():
    emoji, desc = weather._wc_emoji(999)
    assert emoji == "❓"
```

- [ ] **Step 2: Vérifier que les tests échouent**

```bash
pytest tests/commands/test_weather.py -v
```

Expected: `FAILED`

- [ ] **Step 3: Implémenter commands/weather.py**

```python
import requests


def _wc_emoji(code: int) -> tuple[str, str]:
    table = {
        0:  ("☀️",      "Ciel dégagé"),
        1:  ("🌤️",     "Plutôt clair"),
        2:  ("⛅",      "Partiellement nuageux"),
        3:  ("☁️",      "Couvert"),
        45: ("🌫️",     "Brouillard"),
        48: ("🌫️",     "Brouillard givrant"),
        51: ("🌦️",     "Bruine faible"),
        53: ("🌦️",     "Bruine"),
        55: ("🌦️",     "Bruine forte"),
        61: ("🌦️",     "Pluie faible"),
        63: ("🌧️",     "Pluie"),
        65: ("🌧️",     "Pluie forte"),
        66: ("🌧️❄️",  "Pluie verglaçante faible"),
        67: ("🌧️❄️",  "Pluie verglaçante forte"),
        71: ("❄️",      "Neige faible"),
        73: ("❄️",      "Neige"),
        75: ("❄️",      "Neige forte"),
        77: ("🌨️",     "Grains de neige"),
        80: ("🌦️",     "Averses faibles"),
        81: ("🌧️",     "Averses"),
        82: ("🌧️🌧️", "Averses fortes"),
        85: ("🌨️",     "Averses de neige faibles"),
        86: ("🌨️",     "Averses de neige fortes"),
        95: ("⛈️",      "Orage"),
        96: ("⛈️",      "Orage avec grêle"),
        99: ("⛈️",      "Orage avec forte grêle"),
    }
    return table.get(code, ("❓", "Inconnu"))


def handle(ctx, user_input: str) -> None:
    print("⛅ Météo en cours...")
    try:
        loc = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat, lon = loc["loc"].split(",")
        city = loc.get("city", "Inconnue")

        params = {"latitude": lat, "longitude": lon, "current_weather": "true"}
        data = requests.get(
            "https://api.open-meteo.com/v1/forecast", params=params, timeout=5
        ).json()
        current = data["current_weather"]

        emoji, desc = _wc_emoji(current["weathercode"])
        print(f"📍 {city}")
        print(f"{emoji} {desc}")
        print(f"🌡️  {current['temperature']}°C")
        print(f"💨 {current['windspeed']} km/h")
    except (requests.RequestException, KeyError):
        print("❌ Impossible de récupérer la météo.")
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/commands/test_weather.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add commands/weather.py tests/commands/test_weather.py
git commit -m "feat: /weather command with Open-Meteo API"
```

---

## Task 11: /ask (IA Claude)

**Files:**
- Modify: `commands/ask.py`
- Create: `tests/commands/test_ask.py`
- Create: `SPARK.md`

- [ ] **Step 1: Créer SPARK.md**

`SPARK.md`:
```markdown
Tu es Spark, un assistant CLI personnel. Tu es direct, concis et utile.
Tu réponds toujours en français.
Tu as accès au contexte de l'utilisateur (mémoire et listes todo) et tu peux t'y référer pour personnaliser tes réponses.
Tu n'es pas bavard — tu vas droit au but.
```

- [ ] **Step 2: Écrire les tests**

`tests/commands/test_ask.py`:
```python
from unittest.mock import patch, MagicMock
from context import Context
from commands import ask


def make_mock_response(text: str):
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


def test_ask_sends_message_and_stores_history():
    ctx = Context()
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response("Voici ma réponse.")
    with patch("anthropic.Anthropic", return_value=mock_client):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                ask.handle(ctx, "/ask Quelle est la météo ?")
    assert len(ctx.chat_history) == 2
    assert ctx.chat_history[0] == {"role": "user", "content": "Quelle est la météo ?"}
    assert ctx.chat_history[1] == {"role": "assistant", "content": "Voici ma réponse."}


def test_ask_includes_spark_context_in_system():
    ctx = Context(memory="je m'appelle Alexis", todo_list={"travail": ["PR review"]})
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response("OK")
    with patch("anthropic.Anthropic", return_value=mock_client):
        with patch("builtins.print"):
            with patch.object(ctx, "save"):
                ask.handle(ctx, "/ask test")
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert "je m'appelle Alexis" in call_kwargs["system"]
    assert "PR review" in call_kwargs["system"]


def test_ask_empty_message(capsys):
    ctx = Context()
    ask.handle(ctx, "/ask")
    assert "Usage" in capsys.readouterr().out
    assert len(ctx.chat_history) == 0


def test_ask_saves_context():
    ctx = Context()
    mock_client = MagicMock()
    mock_client.messages.create.return_value = make_mock_response("OK")
    with patch("anthropic.Anthropic", return_value=mock_client):
        with patch("builtins.print"):
            with patch.object(ctx, "save") as mock_save:
                ask.handle(ctx, "/ask test")
    mock_save.assert_called_once()
```

- [ ] **Step 3: Vérifier que les tests échouent**

```bash
pytest tests/commands/test_ask.py -v
```

Expected: `FAILED`

- [ ] **Step 4: Implémenter commands/ask.py**

```python
import anthropic
from pathlib import Path

_SPARK_MD = Path("SPARK.md")


def handle(ctx, user_input: str) -> None:
    msg = user_input.removeprefix("/ask").strip()
    if not msg:
        print("Usage : /ask <question>")
        return

    base_system = _SPARK_MD.read_text() if _SPARK_MD.exists() else "Tu es Spark, un assistant CLI."
    spark_context = (
        f"\n\nContexte utilisateur :\n"
        f"Mémoire : {ctx.memory or 'vide'}\n"
        f"Todos : {ctx.todo_list or 'aucun'}"
    )
    system = base_system + spark_context

    ctx.chat_history.append({"role": "user", "content": msg})

    response = anthropic.Anthropic().messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=system,
        messages=ctx.chat_history,
    )

    reply = response.content[0].text
    ctx.chat_history.append({"role": "assistant", "content": reply})
    ctx.save()
    print(f"Spark : {reply}")
```

- [ ] **Step 5: Vérifier que les tests passent**

```bash
pytest tests/commands/test_ask.py -v
```

Expected: `4 passed`

- [ ] **Step 6: Vérifier la clé API**

```bash
echo $ANTHROPIC_API_KEY
```

Si vide : `export ANTHROPIC_API_KEY=sk-ant-...`

- [ ] **Step 7: Commit**

```bash
git add commands/ask.py tests/commands/test_ask.py SPARK.md
git commit -m "feat: /ask command with Claude and persistent history"
```

---

## Task 12: Vérification finale

- [ ] **Step 1: Lancer tous les tests**

```bash
pytest tests/ -v
```

Expected: tous les tests passent.

- [ ] **Step 2: Test de bout en bout**

```bash
python main.py
```

Vérifier manuellement :
- `/help` → liste complète
- `/remember` → saisir un texte → `/recall` → texte affiché
- `/todo` → `/new` → nom → `/exit`
- `/remind boire de l'eau, 5s` → attendre 5s → message affiché
- `/localize` → IP et ville affichés
- `/weather` → météo affichée
- `/ask Bonjour` → réponse de Claude
- `/exit` → relancer → `/recall` vérifie que la mémoire est persistée

- [ ] **Step 3: Commit final**

```bash
git add .
git commit -m "feat: complete Python rewrite of Spark bot"
```

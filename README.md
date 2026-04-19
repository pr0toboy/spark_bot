![image](documentation/logo_nom.png)

# Spark

**Spark is a hybrid personal agent** — it combines deterministic manual tools (reminders, notes, todo lists, timers…) with a multi-provider AI layer (Anthropic, Groq, GLM). You can drive it with explicit slash commands or plain natural language: Spark routes your intent to the right tool automatically.

| Layer | Description |
|---|---|
| **CLI** (`spark`) | REPL Python — runs in any terminal |
| **API** (`app/`) | FastAPI backend exposing the CLI over HTTP |
| **Android app** (`flutter_app/`) | Flutter client — APK built via GitHub Actions |

---

## What makes Spark a hybrid agent

Most AI assistants are purely conversational. Most CLI tools are purely deterministic. Spark is both:

- **Manual tools** execute instantly, offline, with no tokens spent — reminders, notes, todo lists, pomodoro, weather, quotes, logs.
- **AI tools** (`/ai`) handle open-ended questions, reasoning, and writing, with access to the same manual tools (Obsidian vault read/write) via an agentic tool-use loop.
- **Natural language routing** — type anything without a `/` prefix and Spark's router picks the right command automatically. `"remind me to drink water in 20min"` becomes `/remind drink water, 20min`.

This means Spark never wastes a network call on a task a simple function can handle, but always has a reasoning engine available when the task requires it.

---

## Installation (CLI + API)

```bash
git clone <repo>
cd spark_bot
python -m venv venv
source venv/bin/activate
pip install -e .
```

The `spark` command is then available in the terminal.

> Access it without activating the venv:
> ```bash
> # ~/.local/bin/spark
> #!/bin/bash
> exec /path/to/spark_bot/venv/bin/spark "$@"
> ```

### Start the backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On a Raspberry Pi the `spark.service` systemd unit starts it automatically at boot.

---

## Prerequisites

- Python 3.11+
- At least one AI API key: **Anthropic**, **Groq**, or **ZhipuAI (GLM)**

---

## Android app

Download the latest APK from [Releases](../../releases/tag/latest) and install it.

> Enable "Unknown sources" in Settings → Security if needed.

The app connects to the backend via a configurable URL in **Settings → Server URL** (e.g. `http://100.x.x.x:8000` over Tailscale).

The APK build is automated via GitHub Actions (`.github/workflows/build_apk.yml`) and published on every push.

---

## Usage modes

### Slash commands — direct, instant
Every tool is reachable with a `/command`. No AI involved, no latency.

```
/remind drink water, 30min
/note called Alice back
/todo add groceries milk
/pomodoro
```

### Natural language — automatic routing
Type anything without `/` and Spark detects your intent and dispatches to the right command.

```
› remind me to take my meds in 1h
✨ Spark → /remind take my meds, 1h

› note that the server is back online
✨ Spark → /note the server is back online

› add bread to my groceries list
✨ Spark → /todo add groceries bread
```

If no specific command matches, Spark falls back to `/ai`.

### AI mode — reasoning + vault
`/ai` gives you a full conversational AI with memory, skills, and optional Obsidian vault access (read/write notes as tool calls).

```
/ai summarize my notes on project X
/ai what should I work on today based on my todo lists?
```

---

## Commands

### Core

| Command | Description |
|---|---|
| `/start` | Introduce yourself and start |
| `/help` | Show all commands (`/help <cmd>` for details) |
| `/exit` | Quit |

### AI (`/ai`)

| Command | Description |
|---|---|
| `/ai <question>` | Ask the AI (Anthropic / Groq / GLM) |
| `/ai history` | Show conversation history |
| `/ai clear` | Clear history |
| `/ai compact` | Summarize and compact history (saves tokens) |
| `/ai edit` | Edit `SPARK.md` (AI personality / system prompt) |

The active provider is Anthropic if a key is configured, then Groq, then GLM.  
The Obsidian vault is automatically available to the AI if enabled (`/tools enable obsidian`).

### Notes

| Command | Description |
|---|---|
| `/note <text>` | Save a note (also written to the vault if configured) |
| `/note list` | List the last 50 notes |
| `/note delete <id>` | Delete a note |
| `/note vault <path>` | Set the Obsidian vault path |
| `/note export` | Export all notes to the vault as `.md` files |

### Todo lists

| Command | Description |
|---|---|
| `/todo` | List all lists |
| `/todo new <name>` | Create a new list |
| `/todo show <name>` | Display a list |
| `/todo add <name> <item>` | Add an item |
| `/todo remove <name> <item>` | Remove an item |
| `/todo delete <name>` | Delete a list |

### Skills

| Command | Description |
|---|---|
| `/skills` | List active skills |
| `/skills presets` | List available presets |
| `/skills add <name>` | Add a skill (preset or custom) |
| `/skills remove <name>` | Remove a skill |
| `/skills show <name>` | Show skill instructions |

**Presets:** `superpower` (structured reasoning), `cromagnon` (ultra-simple answers)

### Tools (AI integrations)

| Command | Description |
|---|---|
| `/tools` | List tools and their status |
| `/tools enable obsidian` | Enable vault read/write for `/ai` |
| `/tools disable obsidian` | Disable vault access |

### Auth & Models

| Command | Description |
|---|---|
| `/login anthropic` | Save Anthropic API key |
| `/login groq` | Save Groq API key |
| `/login glm` | Save ZhipuAI (GLM) API key |
| `/model` | Show active models |
| `/model list` | All available models |
| `/model anthropic <model>` | Set Anthropic model |
| `/model groq <model>` | Set Groq model |
| `/model glm <model>` | Set GLM model |

### Productivity (manual tools)

| Command | Description |
|---|---|
| `/remember <info>` | Persist information in AI memory |
| `/recall` | Display memory |
| `/remind <msg>, <duration>` | Set a reminder (`10min`, `2h`, `30s`) |
| `/pomodoro` | 4 Pomodoro cycles (25min work / 5min break) |
| `/log` | Action journal |
| `/quote` | Random inspirational quote |
| `/weather` | Current weather (IP-based) |
| `/localize` | IP geolocation |

---

## AI providers

| Provider | Priority | Models |
|---|---|---|
| **Anthropic** | 1st | claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5 |
| **Groq** | 2nd | llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768, gemma2-9b-it |
| **GLM (ZhipuAI)** | 3rd | glm-4-plus, glm-4, glm-4-air, glm-4-flash, glm-z1-flash |

Spark uses whichever provider has a configured key, in priority order.  
Environment variables `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `GLM_API_KEY` are supported as fallbacks.

---

## Architecture

```
spark_bot/
├── main.py              # CLI entry point (spark = main:main)
├── bot.py               # REPL + command dispatch + natural language routing
├── context.py           # SQLite persistence (Context dataclass)
├── result.py            # Result type (ok, message, redirect)
├── SPARK.md             # Custom AI personality / system prompt (git-ignored)
├── commands/
│   ├── ai.py            # AI + agentic vault loop (Anthropic, Groq, GLM)
│   ├── spark.py         # Natural language intent router
│   ├── note.py          # Notes + Obsidian export
│   ├── todo.py          # Todo lists
│   ├── remind.py        # Reminders
│   ├── pomodoro.py      # Pomodoro timer
│   ├── tools.py         # Tool enable/disable
│   ├── skills.py        # AI skills injected into system prompt
│   ├── login.py         # API key storage
│   ├── model.py         # Model selection
│   └── ...
├── app/
│   ├── main.py          # FastAPI app
│   ├── deps.py          # Context injection
│   ├── models.py        # Pydantic schemas
│   └── routes/          # ai, notes, habits, crypto, agents, skills, tools, settings, backup
├── flutter_app/
│   ├── lib/             # Dart — screens + services + models
│   └── pubspec.yaml
├── .github/workflows/
│   └── build_apk.yml    # APK build + GitHub Release
├── tests/
├── pyproject.toml
└── data/spark.db        # SQLite (auto-created, git-ignored)
```

---

## Configuration

API keys are set via `/login <provider>` and stored in `data/spark.db`.  
Environment variables are supported as fallbacks.

Create `SPARK.md` at the root to customize the AI personality (git-ignored, reloaded on every call).

The default Obsidian vault path is `data/vault/` inside the project. Override with `/note vault <path>`.

---

## Tests

```bash
pytest
```

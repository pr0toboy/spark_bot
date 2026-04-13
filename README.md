![image](documentation/logo_nom.png)

# Spark

**Spark** est un assistant personnel en trois couches :

| Couche | Description |
|---|---|
| **CLI** (`spark`) | REPL Python dans le terminal |
| **API** (`app/`) | Backend FastAPI exposant le CLI en HTTP |
| **App Android** (`flutter_app/`) | Application Flutter — APK buildé via GitHub Actions |

---

## Installation (CLI + API)

```bash
git clone <repo>
cd spark_bot
python -m venv venv
source venv/bin/activate
pip install -e .
```

La commande `spark` est ensuite disponible dans le terminal.

> Pour y accéder sans activer le venv :
> ```bash
> # ~/.local/bin/spark
> #!/bin/bash
> exec /path/to/spark_bot/venv/bin/spark "$@"
> ```

### Lancer le backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

En production (Raspberry Pi) : le service `spark.service` démarre automatiquement au boot via systemd.

---

## Prérequis

- Python 3.11+
- Clé API Anthropic et/ou Groq (au moins une pour `/ai`)

---

## App Android

Télécharge le dernier APK depuis [Releases](../../releases/tag/latest) et installe-le.

> Activer "Sources inconnues" dans Paramètres → Sécurité si besoin.

L'app se connecte au backend via une URL configurable dans **Paramètres → URL du serveur** (ex : `http://100.x.x.x:8000` via Tailscale).

Le build APK est automatisé via GitHub Actions (`.github/workflows/build_apk.yml`) et publié à chaque push.

---

## Commandes CLI

### Essentiels

| Commande | Description |
|---|---|
| `/start` | Se présenter et démarrer |
| `/help` | Afficher l'aide |
| `/exit` | Quitter |

### IA (`/ai`)

| Commande | Description |
|---|---|
| `/ai <question>` | Poser une question |
| `/ai history` | Afficher l'historique |
| `/ai clear` | Vider l'historique |
| `/ai compact` | Résumer et compacter l'historique |
| `/ai edit` | Modifier `SPARK.md` |

### Notes

| Commande | Description |
|---|---|
| `/note <texte>` | Enregistrer une note |
| `/note list` | Lister les 50 dernières notes |
| `/note delete <id>` | Supprimer une note |
| `/note vault <chemin>` | Configurer le vault Obsidian |
| `/note export` | Exporter vers le vault |

### Skills

| Commande | Description |
|---|---|
| `/skills` | Lister les skills actifs |
| `/skills presets` | Lister les presets |
| `/skills add <nom>` | Ajouter un skill |
| `/skills remove <nom>` | Supprimer un skill |
| `/skills show <nom>` | Afficher les instructions |

**Presets :** `superpower` (raisonnement structuré), `cromagnon` (réponses ultra-simples)

### Outils

| Commande | Description |
|---|---|
| `/tools` | Lister les outils |
| `/tools enable obsidian` | Activer l'accès vault pour `/ai` |
| `/tools disable obsidian` | Désactiver l'accès vault |

### Auth & Modèles

| Commande | Description |
|---|---|
| `/login anthropic` | Enregistrer la clé Anthropic |
| `/login groq` | Enregistrer la clé Groq |
| `/model` | Modèles actifs |
| `/model list` | Tous les modèles disponibles |
| `/model anthropic <model>` | Choisir le modèle Anthropic |
| `/model groq <model>` | Choisir le modèle Groq |

### Productivité

| Commande | Description |
|---|---|
| `/remember <info>` | Mémoriser une information |
| `/recall` | Afficher la mémoire |
| `/todo` | Listes de tâches |
| `/remind <msg>, <durée>` | Rappel (ex : `10min`, `1h`) |
| `/pomodoro` | 4 cycles Pomodoro (25min/5min) |
| `/log` | Journal des actions |
| `/quote` | Citation inspirante |
| `/weather` | Météo actuelle |

---

## Architecture

```
spark_bot/
├── main.py              # Entrée CLI (spark = main:main)
├── bot.py               # REPL + dispatch commandes
├── context.py           # Persistance SQLite
├── result.py            # Type Result(ok, message)
├── SPARK.md             # System prompt personnalisé (ignoré par git)
├── commands/
│   ├── ai.py            # IA + boucle agentique vault (Anthropic & Groq)
│   ├── note.py          # Notes + export Obsidian
│   ├── tools.py         # Activation/désactivation outils
│   ├── skills.py        # Skills injectés dans /ai
│   ├── login.py         # Clés API
│   ├── model.py         # Sélection modèle
│   └── ...
├── app/
│   ├── main.py          # FastAPI app
│   ├── deps.py          # Injection Context
│   ├── models.py        # Schémas Pydantic
│   └── routes/          # ai, notes, skills, tools, settings
├── flutter_app/
│   ├── lib/             # Dart — screens + services + models
│   ├── pubspec.yaml
│   └── STANDALONE_PLAN.md  # Plan migration app autonome (sans Pi)
├── .github/workflows/
│   └── build_apk.yml    # Build + release APK Android
├── tests/
├── pyproject.toml
└── data/spark.db        # SQLite (créé automatiquement, ignoré par git)
```

---

## Configuration

Les clés API se configurent via `/login anthropic` ou `/login groq`. Elles sont stockées dans `data/spark.db`. Les variables d'environnement `ANTHROPIC_API_KEY` et `GROQ_API_KEY` sont supportées en fallback.

Spark utilise Anthropic en priorité. Sans clé Anthropic, il bascule sur Groq (`llama-3.3-70b-versatile`).

Crée `SPARK.md` à la racine pour personnaliser la personnalité de l'IA (ignoré par git, rechargé à chaque appel).

---

## Tests

```bash
pytest
```

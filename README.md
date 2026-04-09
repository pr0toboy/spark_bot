![image](documentation/logo_nom.png)

# Spark – Bot CLI personnel

**Spark** est un assistant CLI personnel en Python. Il tourne dans le terminal, retient des informations, gère des listes de tâches, envoie des rappels, et peut répondre à des questions via l'IA Claude.

## Installation

```bash
git clone <repo>
cd spark_bot
python -m venv venv
source venv/bin/activate
pip install -e .
```

La commande `spark` est ensuite disponible dans le terminal (dans le venv activé).

> Pour y accéder sans activer le venv à chaque fois, crée un alias ou un script wrapper dans `~/.local/bin/spark`.

## Prérequis

- Python 3.11+
- Une clé API Anthropic et/ou Groq (au moins une requise pour `/ask`)

## Commandes

| Commande | Description |
|---|---|
| `/start` | Se présenter et démarrer une session |
| `/login anthropic` | Enregistrer la clé API Anthropic |
| `/login groq` | Enregistrer la clé API Groq |
| `/model` | Afficher les modèles actifs |
| `/model anthropic <model>` | Choisir le modèle Anthropic |
| `/model groq <model>` | Choisir le modèle Groq |
| `/model list` | Lister tous les modèles disponibles |
| `/remember <info>` | Mémoriser une information |
| `/recall` | Afficher ce que Spark a mémorisé |
| `/todo` | Gérer des listes de tâches (REPL interne) |
| `/remind <msg>, <durée>` | Créer un rappel (ex: `10min`, `1h`, `30s`) |
| `/pomodoro` | Lancer 4 cycles Pomodoro (25min/5min) |
| `/localize` | Afficher la localisation IP |
| `/weather` | Afficher la météo actuelle |
| `/ask <question>` | Poser une question à l'IA Claude |
| `/ask history` | Afficher l'historique de conversation |
| `/ask clear` | Vider l'historique |
| `/ask compact` | Résumer et compacter l'historique |
| `/ask edit` | Modifier `SPARK.md` (personnalité de l'IA) |
| `/note <texte>` | Enregistrer une note |
| `/quote` | Afficher une citation inspirante |
| `/log` | Journal des actions |
| `/help` | Afficher l'aide |
| `/exit` | Quitter |

## Architecture

```
spark_bot/
├── main.py          # Point d'entrée (spark = main:main)
├── bot.py           # REPL principal et dispatch des commandes
├── context.py       # Persistance SQLite (Context, get_conn)
├── result.py        # Type Result(ok, message)
├── SPARK.md         # Personnalité/système prompt de l'IA (optionnel, local)
├── commands/        # Un fichier par commande
│   ├── ask.py       # IA (Anthropic ou Groq selon les clés présentes)
│   ├── login.py     # Enregistrement des clés API
│   ├── model.py     # Sélection du modèle par provider
│   ├── log.py       # Journal + add_entry()
│   ├── note.py
│   ├── remind.py
│   ├── todo.py      # REPL interne pour les listes
│   └── ...
├── tests/
├── pyproject.toml
└── data/spark.db    # Base SQLite (créée automatiquement, ignorée par git)
```

## Configuration de la clé API

Lance `/login anthropic` ou `/login groq` au premier démarrage. La clé est stockée dans `data/spark.db` (ignoré par git) et rechargée automatiquement. Les variables d'environnement `ANTHROPIC_API_KEY` et `GROQ_API_KEY` sont aussi supportées en fallback.

Spark utilise Anthropic en priorité si les deux clés sont présentes. Sans clé Anthropic, il bascule automatiquement sur Groq (`llama-3.3-70b-versatile`).

## Personnaliser Spark

Crée un fichier `SPARK.md` à la racine du projet pour définir la personnalité et le contexte système utilisés par `/ask`. Ce fichier est ignoré par git (config personnelle).

## Tests

```bash
pytest
```

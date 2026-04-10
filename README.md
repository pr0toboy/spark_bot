![image](documentation/logo_nom.png)

# Spark – Bot CLI personnel

**Spark** est un assistant CLI personnel en Python. Il tourne dans le terminal, retient des informations, gère des listes de tâches, envoie des rappels, répond à des questions via l'IA, et s'intègre avec un vault Obsidian.

## Installation

```bash
git clone <repo>
cd spark_bot
python -m venv venv
source venv/bin/activate
pip install -e .
```

La commande `spark` est ensuite disponible dans le terminal.

> Pour y accéder sans activer le venv, crée un wrapper dans `~/.local/bin/spark` :
> ```bash
> #!/bin/bash
> exec /path/to/spark_bot/venv/bin/spark "$@"
> ```

## Prérequis

- Python 3.11+
- Une clé API Anthropic et/ou Groq (au moins une requise pour `/ai`)

## Commandes

### Essentiels

| Commande | Description |
|---|---|
| `/start` | Se présenter et démarrer une session |
| `/help` | Afficher l'aide |
| `/exit` | Quitter |

### IA (`/ai`)

| Commande | Description |
|---|---|
| `/ai <question>` | Poser une question à l'IA |
| `/ai history` | Afficher l'historique de conversation |
| `/ai clear` | Vider l'historique |
| `/ai compact` | Résumer et compacter l'historique (économise des tokens) |
| `/ai edit` | Modifier `SPARK.md` (personnalité de l'IA) |

L'historique est automatiquement tronqué aux 10 derniers messages pour limiter les tokens.

### Vault Obsidian

| Commande | Description |
|---|---|
| `/note vault <chemin>` | Configurer le dossier vault Obsidian |
| `/note export` | Exporter toutes les notes vers le vault |
| `/tools enable obsidian` | Donner à `/ai` l'accès lecture/écriture aux notes |
| `/tools disable obsidian` | Révoquer l'accès |

Une fois le vault activé, `/ai` peut lister, lire et modifier les fichiers `.md` du vault directement.

### Skills IA

Les skills sont des instructions injectées dans le system prompt de `/ai`.

| Commande | Description |
|---|---|
| `/skills` | Lister les skills actifs |
| `/skills presets` | Lister les presets disponibles |
| `/skills add <nom>` | Ajouter un skill (preset auto si connu, interactif sinon) |
| `/skills add <nom> <texte>` | Ajouter un skill en une ligne |
| `/skills remove <nom>` | Supprimer un skill |
| `/skills show <nom>` | Afficher les instructions d'un skill |

**Presets disponibles :**
- `superpower` — raisonnement structuré, markdown, réponses exhaustives
- `cromagnon` — réponses ultra-simples, phrases courtes, analogies caverne

### Notes

| Commande | Description |
|---|---|
| `/note <texte>` | Enregistrer une note (écrit aussi dans le vault si configuré) |
| `/note list` | Lister les 50 dernières notes |
| `/note delete <id>` | Supprimer une note |

### Outils

| Commande | Description |
|---|---|
| `/tools` | Lister les outils avec leur statut |
| `/tools enable <outil>` | Activer un outil |
| `/tools disable <outil>` | Désactiver un outil |

### Modèles & Authentification

| Commande | Description |
|---|---|
| `/login anthropic` | Enregistrer la clé API Anthropic |
| `/login groq` | Enregistrer la clé API Groq |
| `/model` | Afficher les modèles actifs |
| `/model list` | Lister tous les modèles disponibles |
| `/model anthropic <model>` | Choisir le modèle Anthropic |
| `/model groq <model>` | Choisir le modèle Groq |

### Productivité

| Commande | Description |
|---|---|
| `/remember <info>` | Mémoriser une information |
| `/recall` | Afficher ce que Spark a mémorisé |
| `/todo` | Gérer des listes de tâches (REPL interne) |
| `/remind <msg>, <durée>` | Créer un rappel (ex: `10min`, `1h`) |
| `/pomodoro` | Lancer 4 cycles Pomodoro (25min/5min) |
| `/log` | Journal des actions |
| `/quote` | Afficher une citation inspirante |
| `/localize` | Afficher la localisation IP |
| `/weather` | Afficher la météo actuelle |

## Architecture

```
spark_bot/
├── main.py           # Point d'entrée (spark = main:main)
├── bot.py            # REPL principal et dispatch des commandes
├── context.py        # Persistance SQLite (Context, get_conn)
├── result.py         # Type Result(ok, message)
├── SPARK.md          # Personnalité/system prompt (optionnel, ignoré par git)
├── commands/
│   ├── ai.py         # IA + boucle agentique vault (Anthropic & Groq)
│   ├── note.py       # Notes + export Obsidian (.md avec frontmatter YAML)
│   ├── tools.py      # Activation/désactivation des outils
│   ├── skills.py     # Instructions custom injectées dans /ai
│   ├── login.py      # Clés API
│   ├── model.py      # Sélection du modèle
│   ├── log.py        # Journal
│   └── ...
├── tests/
├── pyproject.toml
└── data/spark.db     # SQLite (créé automatiquement, ignoré par git)
```

## Configuration API

Lance `/login anthropic` ou `/login groq` au premier démarrage. Les clés sont stockées dans `data/spark.db` et rechargées automatiquement. Les variables d'environnement `ANTHROPIC_API_KEY` et `GROQ_API_KEY` sont supportées en fallback.

Spark utilise Anthropic en priorité. Sans clé Anthropic, il bascule sur Groq (`llama-3.3-70b-versatile`).

## Personnaliser Spark

Crée `SPARK.md` à la racine pour définir la personnalité et le contexte de l'IA. Ce fichier est ignoré par git. Les modifications prennent effet immédiatement (lecture à chaque appel).

## Tests

```bash
pytest
```

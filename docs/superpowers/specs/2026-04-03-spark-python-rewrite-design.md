# Spark Bot — Réécriture Python

**Date :** 2026-04-03
**Statut :** Approuvé

## Contexte

Spark est un bot CLI interactif (REPL) écrit en Rust. L'objectif est de le réécrire en Python pour faciliter l'intégration d'une IA (Claude API) tout en conservant la même expérience utilisateur : commandes slash, boucle interactive, handlers isolés.

## Objectifs

- Réécrire toutes les commandes existantes en Python
- Ajouter la persistance JSON entre sessions (mémoire, todos, historique IA)
- Ajouter `/ask` : commande IA avec historique conversationnel et accès au contexte Spark
- Compléter `/weather` avec l'API Open-Meteo (météo réelle basée sur la géolocalisation IP)
- Utiliser un fichier `SPARK.md` comme système prompt (personnalité et instructions de Spark)

## Architecture

### Structure du projet

```
spark_bot/
├── SPARK.md                  # Système prompt : personnalité et instructions de Spark
├── main.py                   # Point d'entrée : instancie SparkBot et appelle run()
├── bot.py                    # Classe SparkBot : boucle REPL + dispatch par dictionnaire
├── context.py                # Dataclass Context + chargement/sauvegarde JSON
├── data/
│   └── spark_data.json       # Données persistées (mémoire, todos, historique IA)
└── commands/
    ├── __init__.py
    ├── start.py
    ├── remember.py
    ├── recall.py
    ├── todo.py
    ├── remind.py
    ├── pomodoro.py
    ├── localize.py
    ├── weather.py
    ├── ask.py
    └── help.py
```

### Dispatch (bot.py)

`SparkBot` maintient un dictionnaire `{ "/commande": handler }`. La boucle REPL extrait le premier mot de l'input, cherche le handler, et l'appelle. Interface uniforme pour tous les handlers :

```python
def handle(ctx: Context, input: str) -> None
```

`/exit` est géré directement dans la boucle (sauvegarde puis break).

### Persistance (context.py)

`Context` est un dataclass Python avec :
- `memory: str` — mémoire libre de l'utilisateur (`/remember`)
- `todo_list: dict[str, list[str]]` — listes de tâches (`/todo`)
- `chat_history: list[dict]` — historique des messages IA (`/ask`)

Chargé depuis `data/spark_data.json` au démarrage, sauvegardé après chaque interaction IA et à la sortie. Les rappels actifs (`/remind`) restent en mémoire vive uniquement — ils ne survivent pas aux redémarrages.

### Commande `/ask` (ask.py)

- `SPARK.md` est lu au démarrage comme système prompt
- Le contexte Spark (mémoire + todos) est appendé au system prompt à chaque appel
- L'historique complet `chat_history` est transmis à Claude → mémoire conversationnelle persistée entre sessions
- Modèle : `claude-opus-4-6`

### Commande `/weather` (weather.py)

Deux appels API sans clé :
1. `https://ipinfo.io/json` → latitude, longitude, ville
2. `https://api.open-meteo.com/v1/forecast` → météo actuelle (température, vitesse du vent, code météo WMO)

La fonction `wc_emoji(code)` mappe les codes WMO vers emoji + description (reprise de `weather.rs`).

### Commandes inchangées (portage direct)

| Commande | Comportement |
|---|---|
| `/start` | Message d'accueil |
| `/remember` | Demande un texte, stocke dans `ctx.memory`, sauvegarde |
| `/recall` | Affiche `ctx.memory` |
| `/todo` | Sous-REPL : `/new`, `/show`, `/edit`, `/remove`, `/exit` |
| `/remind` | Parse durée, spawn thread, affiche rappel après délai |
| `/pomodoro` | 4 cycles travail/pause avec timer affiché |
| `/localize` | Affiche IP, ville, région, pays, coords, fournisseur |
| `/help` | Affiche la liste des commandes et descriptions |

## Dépendances Python

```
anthropic
requests
```

Pas de framework CLI (Typer, Click) — le REPL est géré manuellement pour conserver l'expérience interactive.

## Ce qui n'est pas dans le scope

- Interface graphique ou web
- Authentification utilisateur
- Persistance des rappels entre sessions
- Commandes IA implicites (langage naturel sans `/ask`)

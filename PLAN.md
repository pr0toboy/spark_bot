# PLAN — Spark Web & Mobile App

> Document de référence pour reprendre le travail à tout moment.
> Mettre à jour la section **État actuel** après chaque session.

---

## Objectif

Rendre Spark accessible depuis un navigateur web et une application mobile (iOS/Android) via Flutter, tout en réutilisant le code Python existant.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Flutter App                          │
│  (web + iOS + Android)                                  │
│                                                         │
│  ChatScreen  NotesScreen  SettingsScreen                │
│       │            │            │                       │
│       └────────────┴────────────┘                       │
│                 ApiService (http)                       │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP REST
                       │ (localhost:8000 en dev)
┌──────────────────────▼──────────────────────────────────┐
│              FastAPI Backend  (app/)                    │
│                                                         │
│  /api/ai        POST  — question → réponse IA           │
│  /api/notes     GET   — lister les notes                │
│  /api/notes     POST  — créer une note                  │
│  /api/notes/:id DELETE — supprimer une note             │
│  /api/tools     GET   — état des outils                 │
│  /api/tools     POST  — enable/disable                  │
│  /api/skills    GET   — lister les skills               │
│  /api/skills    POST  — ajouter/modifier                │
│  /api/skills/:name DELETE — supprimer                   │
│  /api/settings  GET   — modèles actifs                  │
│  /api/settings  POST  — clés API, modèles               │
│  /api/context   GET   — mémoire, todos, historique      │
│                                                         │
│  Réutilise : commands/, context.py, result.py           │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│           Code Spark existant (inchangé)                │
│  commands/ai.py  commands/note.py  commands/skills.py   │
│  commands/tools.py  context.py  data/spark.db           │
└─────────────────────────────────────────────────────────┘
```

---

## Décisions techniques

| Sujet | Choix | Raison |
|---|---|---|
| Backend | FastAPI + uvicorn | Async, Pydantic natif, auto-doc Swagger |
| Frontend | Flutter | Web + iOS + Android depuis une seule base de code |
| HTTP client Flutter | `http` package | Simple, pas de dépendance lourde |
| État Flutter | `provider` | Léger, suffisant pour une app personnelle |
| Auth | Aucune (v1) | App personnelle, single-user |
| Base de données | SQLite existant (`data/spark.db`) | Réutilisation directe |
| CORS | Activé pour tous en dev | À restreindre en production |
| Streaming IA | Non (v1), SSE prévu en v2 | Simplifie le premier MVP |

---

## Structure des fichiers

```
spark_bot/
├── app/                        ← Backend FastAPI
│   ├── main.py                 ← App FastAPI, CORS, inclusion des routes
│   ├── models.py               ← Pydantic request/response models
│   └── routes/
│       ├── ai.py               ← POST /api/ai
│       ├── notes.py            ← CRUD /api/notes
│       ├── tools.py            ← GET/POST /api/tools
│       ├── skills.py           ← CRUD /api/skills
│       ├── settings.py         ← GET/POST /api/settings
│       └── context_route.py    ← GET /api/context
├── flutter_app/                ← Frontend Flutter
│   ├── pubspec.yaml
│   └── lib/
│       ├── main.dart           ← MaterialApp, routes
│       ├── config.dart         ← BASE_URL configurable
│       ├── models/
│       │   ├── message.dart
│       │   ├── note.dart
│       │   └── skill.dart
│       ├── services/
│       │   └── api_service.dart ← Tous les appels HTTP
│       └── screens/
│           ├── chat_screen.dart    ← Écran principal (IA)
│           ├── notes_screen.dart   ← Liste + création de notes
│           └── settings_screen.dart ← Clés API, modèles, tools, skills
├── PLAN.md                     ← Ce fichier
└── pyproject.toml              ← Ajouter fastapi, uvicorn
```

---

## Lancer l'environnement de dev

### Backend
```bash
cd spark_bot
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
# Swagger UI : http://localhost:8000/docs
```

### Flutter (web)
```bash
cd spark_bot/flutter_app
flutter run -d chrome
# ou
flutter run -d web-server --web-port 3000
```

### Flutter (mobile)
```bash
flutter run -d android   # ou -d ios
# Changer BASE_URL dans lib/config.dart vers l'IP locale du serveur
```

---

## État actuel

### ✅ Complété (session 1 — 2026-04-10)
- [x] Branche `app` créée depuis `master`
- [x] PLAN.md rédigé
- [x] Backend FastAPI — `app/` complet et importable
  - `app/main.py` — FastAPI app avec CORS
  - `app/deps.py` — `load_ctx()` helper
  - `app/models.py` — Pydantic models (AiRequest/Response, Note, Tool, Skill, Settings, Context)
  - `app/routes/ai.py` — POST /api/ai, GET/DELETE /api/ai/history, POST /api/ai/compact
  - `app/routes/notes.py` — GET/POST /api/notes, DELETE /api/notes/{id}, POST /api/notes/export
  - `app/routes/tools.py` — GET/POST /api/tools
  - `app/routes/skills.py` — GET/POST /api/skills, GET /api/skills/presets, DELETE /api/skills/{name}
  - `app/routes/settings.py` — GET/POST /api/settings, GET /api/settings/models
  - `app/routes/context_route.py` — GET /api/context
  - fastapi + uvicorn ajoutés à pyproject.toml et installés dans le venv
- [x] Flutter app — `flutter_app/` scaffoldé
  - `pubspec.yaml` configuré (http, provider, shared_preferences, intl)
  - `lib/config.dart` — BASE_URL configurable
  - `lib/models/` — message.dart, note.dart, skill.dart
  - `lib/services/api_service.dart` — tous les appels HTTP, singleton, gestion erreurs
  - `lib/screens/chat_screen.dart` — chat IA avec historique, scroll auto, progress bar
  - `lib/screens/notes_screen.dart` — liste + création + suppression
  - `lib/screens/settings_screen.dart` — clés API, tools toggle, skills CRUD, presets
  - `lib/main.dart` — MaterialApp + NavigationBar (Chat / Notes / Paramètres)

### 🔲 Reste à faire (prochaines sessions)
- [ ] Tests backend (pytest pour les routes FastAPI)
- [ ] Streaming SSE pour `/api/ai` (réponse progressive)
- [ ] Écran Vault Obsidian dans Flutter (config + export)
- [ ] Historique de conversation dans l'UI chat
- [ ] Page `/api/docs` protégée en production
- [ ] Packaging : Dockerfile pour le backend
- [ ] Build Flutter web → servir depuis FastAPI (`/` → `flutter_app/build/web`)

---

## Comment reprendre

1. `git checkout app` — se remettre sur la branche
2. Lire la section **État actuel** ci-dessus
3. Prendre le premier item de **Reste à faire**
4. Lancer backend + Flutter en dev (voir **Lancer l'environnement**)
5. Après chaque session : mettre à jour **État actuel** dans ce fichier

---

## Variables d'environnement

Aucune variable requise en dev — tout est lu depuis `data/spark.db`.
En production :
```
SPARK_DB_PATH=/data/spark.db   # optionnel, override du chemin SQLite
```

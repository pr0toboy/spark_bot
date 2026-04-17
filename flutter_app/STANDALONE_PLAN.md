# Plan : Spark Android standalone (sans serveur)

## Objectif

Rendre l'app Flutter entièrement autonome sur Android.  
Plus besoin de Raspberry Pi ni de backend Python.  
L'app appelle les APIs IA directement et stocke tout en local.

---

## Ce qui change

| Actuel | Cible |
|---|---|
| Flutter → FastAPI (Pi) → Anthropic/Groq | Flutter → Anthropic/Groq directement |
| Notes dans SQLite sur le Pi | Notes dans `sqflite` sur l'appareil |
| Settings/Skills dans `context.json` sur le Pi | Settings/Skills dans `shared_preferences` |
| `ApiService` HTTP vers localhost | Logique embarquée dans des services Dart |

---

## Nouvelles dépendances `pubspec.yaml`

- `sqflite` + `path` — base de données notes locale
- `flutter_secure_storage` — stockage chiffré des clés API
- (déjà présent) `shared_preferences` — settings, skills, historique chat

---

## Architecture cible

```
lib/
  services/
    ai_service.dart        # Appels Anthropic + Groq (remplace api_service.dart pour /api/ai)
    notes_service.dart     # CRUD notes via sqflite (remplace /api/notes)
    settings_service.dart  # Lecture/écriture settings (remplace /api/settings)
    skills_service.dart    # CRUD skills (remplace /api/skills)
    tools_service.dart     # État des outils (remplace /api/tools)
  models/                  # inchangé
  screens/                 # inchangé (branchés sur les nouveaux services)
  main.dart                # init des services au démarrage
```

`ApiService` est supprimé.

---

## Détail par service

### `ai_service.dart`
- Lit la clé API et le modèle depuis `settings_service`
- Construit le system prompt (SPARK.md embarqué en asset ou hardcodé)
- Appelle `https://api.anthropic.com/v1/messages` via `http`
- Gère l'historique en mémoire (trimming à 10 messages)
- Méthodes : `sendMessage()`, `getHistory()`, `clearHistory()`

### `notes_service.dart`
- Initialise une table `notes (id, timestamp, content)` via `sqflite`
- Méthodes : `getNotes()`, `createNote()`, `deleteNote()`
- Pas d'export Obsidian (feature desktop uniquement)

### `settings_service.dart`
- Stocke les clés API dans `flutter_secure_storage` (chiffré)
- Stocke le modèle choisi dans `shared_preferences`
- Méthodes : `getApiKey()`, `setApiKey()`, `getModel()`, `setModel()`

### `skills_service.dart`
- Stocke les skills en JSON dans `shared_preferences`
- Presets embarqués en dur dans le code (copie de `commands/skills.py::PRESETS`)
- Méthodes : `getSkills()`, `upsertSkill()`, `deleteSkill()`, `getPresets()`

### `tools_service.dart`
- État des outils dans `shared_preferences`
- Méthodes : `getTools()`, `setTool()`

---

## Écrans — changements minimes

- `chat_screen.dart` → utilise `AiService` au lieu de `ApiService().sendMessage()`
- `notes_screen.dart` → utilise `NotesService`
- `settings_screen.dart` → utilise `SettingsService` + `SkillsService` + `ToolsService`
  - Supprime la section "Connexion / URL serveur" (devenu inutile)

---

## Workflow CI — changements

- Aucun changement de structure, le build APK reste identique
- Supprimer `config.dart` (déjà fait)

---

## Ce qu'on perd

- Intégration Obsidian vault (export de notes vers le Pi) — feature desktop only
- Historique persistant entre réinstallations (sauf si on ajoute export/import)

---

## Ordre d'implémentation

1. Ajouter les dépendances dans `pubspec.yaml`
2. Écrire `settings_service.dart` (requis par tous les autres)
3. Écrire `ai_service.dart`
4. Écrire `notes_service.dart`
5. Écrire `skills_service.dart` + `tools_service.dart`
6. Brancher les écrans sur les nouveaux services
7. Supprimer `api_service.dart`
8. Build + test APK

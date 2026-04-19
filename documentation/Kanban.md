# Kanban — Spark

## À faire

### Fonctionnalités
- /translate : traduction rapide d'un mot ou d'une phrase
- /define : définition d'un mot
- Widget recap journalier (météo + todos + habitudes)
- Mode hors-ligne partiel (cache local des données)
- Graphe de notes interactif dans l'app Flutter

### Améliorations
- Pagination de l'historique de chat
- Recherche dans les notes
- Tri/filtrage des agents par type
- Notifications locales (rappels habitudes)

---

## En cours

---

## Terminé

### Backend (Python / FastAPI)
- Architecture FastAPI + SQLite (tables : notes, habits, habit_entries, agents, crypto_wallets, crypto_alerts, kv, logs)
- Route IA `/api/ai` — Claude (Anthropic) + Groq + GLM, historique persisté
- `/api/notes` — CRUD + export Obsidian + graphe de liens
- `/api/habits` — tracker d'habitudes avec streaks et stats hebdomadaires
- `/api/crypto` — marché, tendances, portfolio multi-wallet, alertes de prix
- `/api/agents` — agents automatisés (email IMAP, RSS/web filtré par IA)
- `/api/skills` — skills personnalisés + presets
- `/api/tools` — activation/désactivation des outils IA
- `/api/settings` — clés API (Anthropic, Groq, GLM), modèles
- `/api/backup/export` + `/api/backup/import` — backup JSON complet
- Firebase push notifications
- Sécurité : protection prompt injection, path traversal, limites d'input
- /download (yt-dlp)

### Flutter (Mobile Android)
- 7 écrans : Chat, Notes, Habits, Crypto, Agents, Commandes, Paramètres
- Thème Spark (pastel chaud, dark/light, Material 3)
- Rendu Markdown dans le chat
- Navigation bar avec IndexedStack (état préservé)
- Export/Import backup via share sheet + file picker
- Firebase Messaging (push notifications)
- Icône de lancement Spark (adaptive icon, toutes densités)
- Nom de l'app : **Spark**
- Timeout HTTP 30s sur toutes les requêtes
- v1.9.2+13 — publiée sur GitHub Releases

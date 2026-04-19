# Suivi du projet Spark

## Architecture actuelle

**Backend** : Python 3.11 · FastAPI · SQLite (stdlib) · Anthropic / Groq / GLM
**Frontend** : Flutter 3 · Android · Material 3
**Infra** : serveur local (LAN), Firebase pour les push notifications
**Distribution** : GitHub Releases (APK)

---

## Versions publiées

| Version | Date | Changements clés |
|---------|------|-----------------|
| v1.9.2 | 2026-04-19 | Icône Spark (logo.jpg), nom "Spark", timeout HTTP 30s, robustesse sécurité |
| v1.9.1 | 2026-04-19 | Icône de lancement Android (flutter_launcher_icons) |
| v1.9.0 | 2026-04-19 | Export/Import backup JSON complet |
| v1.8.x | 2026-04 | Thème Spark pastel + rendu Markdown |
| v1.7.x | 2026-04 | Agents IA (email IMAP, RSS/web) + Firebase push |
| v1.6.0 | — | /download yt-dlp, sécurité renforcée |
| v1.5.x | — | Crypto portfolio, rename wallet, graph fix |
| v1.4.x | — | Habit tracker + stats |
| ≤ v1.3 | — | CLI Rust (archivé) |

---

## État des modules backend

| Module | Route | Statut |
|--------|-------|--------|
| IA Chat | `/api/ai` | ✅ |
| Notes | `/api/notes` | ✅ |
| Habitudes | `/api/habits` | ✅ |
| Crypto | `/api/crypto` | ✅ |
| Agents | `/api/agents` | ✅ |
| Skills | `/api/skills` | ✅ |
| Outils | `/api/tools` | ✅ |
| Paramètres | `/api/settings` | ✅ |
| Backup | `/api/backup` | ✅ |
| Push (Firebase) | `/api/agents/push` | ✅ |

---

## Notes techniques

- La DB SQLite est dans `data/spark.db`, créée automatiquement au démarrage
- Les clés API (Anthropic, Groq, GLM) sont stockées dans le contexte serveur, jamais écrasées à l'import d'un backup
- Le backup JSON (`spark_backup_YYYY-MM-DD.json`) couvre : notes, habitudes, agents, wallets crypto, alertes, skills, contexte utilisateur
- L'APK est signé en release Flutter (minification activée, tree-shaking icons)

# Ajouter des tests unitaires
✅ Fait — 56 tests couvrant context, bot, et toutes les commandes.

# Améliorer l'UX : menu contextuel
Plutôt que de demander à chaque fois quoi faire, tu pourrais afficher un menu après chaque commande ou proposer des suggestions.

# Externaliser les textes
Tu pourrais stocker les messages (d'accueil, d'aide, etc.) dans un fichier .json ou .toml pour les modifier sans recompiler.

# Implémenter une tâche en arrière plan

# Base de données
✅ Fait — SQLite via sqlite3 (stdlib), tables kv + logs, DB dans data/spark.db.

## Indexation des fichiers
Créer un catalogue des fichiers stockés pour une recherche rapide

# Crée un module par tâche
✅ Fait — chaque commande est un module dans commands/.

# table de dispatch dynamique

# Structure ton contexte partagé
✅ Fait — Context dataclass avec name, memory, todo_list, chat_history. Persisté en SQLite.

# Plugin

# Mettre plutot des handler
✅ Fait — chaque commande expose handle(ctx, user_input) -> Result.

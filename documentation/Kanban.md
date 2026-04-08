# Kanban

## À faire
### Nouveautés
- /translate : traduction rapide d'un mot ou d'une phrase (via API LibreTranslate ou DeepL)
- /define : définition d'un mot (via dictionnaire en ligne)



________________________________________________________________________________________________________________________

## En cours

## Tâches régulières :
- Commenter




________________________________________________________________________________________________________________________

## Terminé
### Commandes
- /help : liste des commandes disponibles
- /start : message de bienvenue + configuration initiale (nom de l'utilisateur)
- /remember : Spark retient une info (inline ou interactif)
- /recall : retrouve une info mémorisée
- /pomodoro
- /localize : détecte ton emplacement (via IP)
- /todo : gérer une liste de tâches (ajouter, supprimer, lister)
- /remind : créer un rappel
- /weather : météo actuelle via Open-Meteo
- /ask : poser une question à Claude (historique persisté)
- /log : journal des actions (auto-log, filtrage, clear)
- /note : enregistrer une note rapide (inline, interactif, list, delete)
- /quote : citation inspirante (API ZenQuotes + fallback local)

### Améliorations
- Séparation en modules
- Liste des commandes à un seul endroit
- /remove list dans todo
- Améliorer les threads
- Commandes retournent des Result au lieu de print
- Base de données SQLite (remplace JSON) + tables logs + notes
- /remember supporte le mode inline et interactif
- Context enrichi : champ `name` persisté en base

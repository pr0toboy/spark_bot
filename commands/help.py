from result import Result

COMMANDS = [
    ("/start",    "Démarrer une nouvelle session"),
    ("/ai",       "Poser une question à l'IA  (history | clear | compact | edit)"),
    ("/remember", "Mémoriser une information"),
    ("/recall",   "Afficher ce que Spark a mémorisé"),
    ("/todo",     "Gérer des listes de tâches  (new | show | add | remove | delete)"),
    ("/remind",   "Créer un rappel  (ex: /remind boire, 10min)"),
    ("/note",     "Enregistrer une note  (list | delete <id> | vault <path> | export)"),
    ("/log",      "Journal des actions  (ex: /log | /log clear | /log /remind)"),
    ("/login",    "Enregistrer une clé API  (anthropic | groq)"),
    ("/model",    "Choisir le modèle IA  (list | anthropic <m> | groq <m>)"),
    ("/tools",    "Activer/désactiver des outils  (list | enable <outil> | disable <outil>)"),
    ("/skills",   "Gérer les skills de l'IA  (list | presets | add <nom> | remove | show)"),
    ("/pomodoro", "Lancer un minuteur Pomodoro (4 cycles 25min/5min)"),
    ("/localize", "Me localiser dans le monde (IP)"),
    ("/weather",  "Afficher la météo actuelle"),
    ("/quote",    "Afficher une citation inspirante"),
    ("/help",     "Afficher cette aide  (ex: /help ai)"),
    ("/exit",     "Quitter Spark"),
]

DETAILS = {
    "start": """\
/start — Démarrer une session
  Lance l'accueil de Spark.
  • Premier lancement : demande ton prénom et le sauvegarde.
  • Lancements suivants : affiche un message de bienvenue personnalisé.""",

    "ai": """\
/ai — Intelligence artificielle
  /ai <question>     Poser une question à Spark (Anthropic ou Groq).
  /ai history        Afficher l'historique de la conversation en cours.
  /ai clear          Vider l'historique.
  /ai compact        Résumer et compacter l'historique (économise des tokens).
  /ai edit           Modifier SPARK.md (personnalité/system prompt de l'IA).

  Le provider actif est Anthropic si une clé est configurée, sinon Groq.
  Le vault Obsidian est utilisé automatiquement s'il est activé (/tools enable obsidian).""",

    "remember": """\
/remember — Mémoire persistante
  /remember <info>   Sauvegarde une information dans la mémoire de Spark.
  Cette mémoire est injectée dans le contexte de chaque appel /ai.
  Voir : /recall pour afficher ce qui est mémorisé.""",

    "recall": """\
/recall — Afficher la mémoire
  Affiche toutes les informations mémorisées via /remember.""",

    "todo": """\
/todo — Listes de tâches
  /todo                         Liste toutes les listes et leur nombre d'éléments.
  /todo new <nom>               Crée une nouvelle liste.
  /todo show <nom>              Affiche le contenu d'une liste.
  /todo add <nom> <élément>     Ajoute un élément à une liste.
  /todo remove <nom> <élément>  Supprime un élément d'une liste.
  /todo delete <nom>            Supprime une liste entière.""",

    "remind": """\
/remind — Rappels
  /remind <message>, <durée>   Crée un rappel dans la durée indiquée.
  Exemples :
    /remind boire de l'eau, 30min
    /remind appeler Alice, 2h
  Durées supportées : s (secondes), min (minutes), h (heures).""",

    "note": """\
/note — Notes
  /note <texte>          Enregistre une note (écrite aussi dans le vault si configuré).
  /note list             Liste les 50 dernières notes.
  /note delete <id>      Supprime une note par son ID.
  /note vault            Affiche le chemin du vault Obsidian actuel.
  /note vault <chemin>   Configure le dossier vault Obsidian.
  /note export           Exporte toutes les notes vers le vault en fichiers .md.""",

    "log": """\
/log — Journal des actions
  /log                  Affiche les 20 dernières actions enregistrées.
  /log clear            Vide le journal.
  /log <commande>       Filtre le journal par commande (ex: /log /remind).""",

    "login": """\
/login — Clés API
  /login anthropic   Enregistre la clé API Anthropic (Claude).
  /login groq        Enregistre la clé API Groq (Llama).
  Les clés sont stockées dans data/spark.db.
  Les variables d'environnement ANTHROPIC_API_KEY et GROQ_API_KEY sont supportées en fallback.""",

    "model": """\
/model — Sélection du modèle IA
  /model                      Affiche les modèles actifs.
  /model list                 Liste tous les modèles disponibles.
  /model anthropic <modèle>   Choisit le modèle Anthropic à utiliser.
  /model groq <modèle>        Choisit le modèle Groq à utiliser.""",

    "tools": """\
/tools — Outils externes
  /tools                     Liste les outils disponibles et leur statut.
  /tools enable obsidian     Active l'accès lecture/écriture au vault Obsidian pour /ai.
  /tools disable obsidian    Désactive l'accès vault.
  Le vault doit être configuré via /note vault <chemin> pour qu'obsidian soit fonctionnel.""",

    "skills": """\
/skills — Skills IA
  Les skills sont des instructions injectées dans le system prompt de /ai.
  /skills                    Liste les skills actifs.
  /skills presets            Liste les presets disponibles.
  /skills add <nom>          Ajoute un preset connu ou demande les instructions.
  /skills add <nom> <texte>  Ajoute un skill en une ligne.
  /skills remove <nom>       Supprime un skill.
  /skills show <nom>         Affiche les instructions d'un skill.

  Presets :
    superpower  — raisonnement structuré, réponses exhaustives en markdown.
    cromagnon   — réponses ultra-simples, phrases courtes, analogies cave.""",

    "pomodoro": """\
/pomodoro — Minuteur Pomodoro
  Lance 4 cycles de travail/pause : 25 min de travail, 5 min de pause.
  Affiche une notification à la fin de chaque cycle.""",

    "localize": """\
/localize — Localisation IP
  Affiche la localisation géographique approximative basée sur l'adresse IP publique.""",

    "weather": """\
/weather — Météo
  Affiche la météo actuelle basée sur la localisation IP.""",

    "quote": """\
/quote — Citation
  Affiche une citation inspirante aléatoire.""",

    "help": """\
/help — Aide
  /help          Affiche la liste de toutes les commandes.
  /help <cmd>    Affiche l'aide détaillée d'une commande (sans le slash).
  Exemple : /help ai, /help note, /help skills""",

    "exit": """\
/exit — Quitter
  Ferme le REPL Spark proprement.""",
}


assert set(DETAILS) == {cmd.lstrip("/") for cmd, _ in COMMANDS}, "COMMANDS/DETAILS mismatch"

_TOPICS = [cmd.lstrip("/") for cmd, _ in COMMANDS]


def handle(ctx, user_input: str) -> Result:
    topic = user_input.removeprefix("/help").strip().lstrip("/")

    if topic:
        detail = DETAILS.get(topic)
        if detail:
            return Result.success(detail)
        return Result.error(
            f"Pas d'aide pour « {topic} ».\n"
            "Commandes disponibles : " + ", ".join(_TOPICS)
        )

    lines = ["Commandes disponibles (tape /help <cmd> pour le détail) :"]
    for cmd, desc in COMMANDS:
        lines.append(f"  {cmd:<12} — {desc}")
    return Result.success("\n".join(lines))

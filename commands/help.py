from result import Result

COMMANDS = [
    ("/start",    "Démarrer une nouvelle session"),
    ("/ai",       "Poser une question à l'IA  (history | clear | compact | edit)"),
    ("/remember", "Mémoriser une information"),
    ("/recall",   "Afficher ce que Spark a mémorisé"),
    ("/todo",     "Gérer une liste de tâches"),
    ("/remind",   "Créer un rappel  (ex: /remind boire, 10min)"),
    ("/note",     "Enregistrer une note  (list | delete <id> | vault <path> | export)"),
    ("/log",      "Journal des actions  (ex: /log | /log clear | /log /remind)"),
    ("/login",    "Enregistrer une clé API  (anthropic | groq)"),
    ("/model",    "Choisir le modèle IA  (list | anthropic <m> | groq <m>)"),
    ("/pomodoro", "Lancer un minuteur Pomodoro (4 cycles 25min/5min)"),
    ("/localize", "Me localiser dans le monde (IP)"),
    ("/weather",  "Afficher la météo actuelle"),
    ("/quote",    "Afficher une citation inspirante"),
    ("/help",     "Afficher cette aide"),
    ("/exit",     "Quitter Spark"),
]


def handle(ctx, user_input: str) -> Result:
    lines = ["Commandes disponibles :"]
    for cmd, desc in COMMANDS:
        lines.append(f"  {cmd:<12} — {desc}")
    return Result.success("\n".join(lines))

from result import Result

COMMANDS = [
    ("/start",    "Démarrer une nouvelle tâche"),
    ("/remember", "Mémoriser une information"),
    ("/recall",   "Afficher ce que Spark a mémorisé"),
    ("/todo",     "Gérer une liste de tâches"),
    ("/remind",   "Créer un rappel  (ex: /remind boire, 10min)"),
    ("/pomodoro", "Lancer un minuteur Pomodoro (4 cycles 25min/5min)"),
    ("/localize", "Me localiser dans le monde (IP)"),
    ("/weather",  "Afficher la météo actuelle"),
    ("/ask",      "Poser une question à l'IA"),
    ("/note",     "Enregistrer une note  (ex: /note <texte>, /note list, /note delete <id>)"),
    ("/quote",    "Afficher une citation inspirante"),
    ("/log",      "Voir le journal des actions  (ex: /log, /log clear, /log /remind)"),
    ("/help",     "Afficher cette aide"),
    ("/exit",     "Quitter Spark"),
]


def handle(ctx, user_input: str) -> Result:
    lines = ["Commandes disponibles :"]
    for cmd, desc in COMMANDS:
        lines.append(f"  {cmd:<12} — {desc}")
    return Result.success("\n".join(lines))

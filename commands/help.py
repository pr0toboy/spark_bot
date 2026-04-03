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
    ("/help",     "Afficher cette aide"),
    ("/exit",     "Quitter Spark"),
]


def handle(ctx, user_input: str) -> None:
    print("Commandes disponibles :")
    for cmd, desc in COMMANDS:
        print(f"  {cmd:<12} — {desc}")

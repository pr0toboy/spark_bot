from result import Result
from commands.ai import _resolve_provider, _chat

_ROUTER_SYSTEM = """\
Tu es le routeur de commandes de Spark. Analyse l'intention de l'utilisateur \
et réponds avec UNE SEULE ligne : la commande Spark complète, prête à exécuter.

Commandes disponibles :
  /remind <message>, <durée>     rappel temporel (durées : s, min, h)
  /note <texte>                  enregistrer une note rapide
  /todo new <nom>                créer une liste de tâches
  /todo add <liste> <élément>    ajouter un élément à une liste
  /todo show <liste>             afficher une liste
  /todo remove <liste> <él>      supprimer un élément
  /todo delete <liste>           supprimer une liste
  /remember <info>               mémoriser une information persistante
  /weather                       météo actuelle
  /quote                         citation inspirante
  /pomodoro                      minuteur pomodoro 25min/5min
  /log                           journal des actions
  /ai <question>                 question libre à l'IA

Règles :
- Réponds UNIQUEMENT avec la commande complète sur une seule ligne.
- Si aucune commande ne correspond mieux, utilise /ai <texte>.
- Ne génère jamais /login, /model, /tools, /skills, /start, /exit.\
"""


def handle(ctx, user_input: str) -> Result:
    text = user_input.removeprefix("/spark").strip()
    if not text:
        return Result.error("Usage : /spark <intention>\nExemple : /spark rappelle-moi de boire dans 20min")

    try:
        reply, _ = _chat(
            ctx,
            _ROUTER_SYSTEM,
            [{"role": "user", "content": text}],
            max_tokens=64,
        )
    except ValueError as e:
        return Result.error(str(e))

    command = reply.strip().splitlines()[0].strip()
    if not command.startswith("/"):
        command = f"/ai {text}"

    print(f"✨ Spark → {command}")
    return Result.dispatch(command)

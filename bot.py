from context import Context
from commands import (
    start, help as help_cmd, remember, recall,
    todo, remind, pomodoro, localize, weather, ask, log, note, quote, login, model,
)


class SparkBot:
    def __init__(self):
        self.ctx = Context.load()
        self.commands = {
            "/start":    start.handle,
            "/help":     help_cmd.handle,
            "/remember": remember.handle,
            "/recall":   recall.handle,
            "/todo":     todo.handle,
            "/remind":   remind.handle,
            "/pomodoro": pomodoro.handle,
            "/localize": localize.handle,
            "/weather":  weather.handle,
            "/ask":      ask.handle,
            "/log":      log.handle,
            "/note":     note.handle,
            "/quote":    quote.handle,
            "/login":    login.handle,
            "/model":    model.handle,
        }

    def run(self):
        greeting = f"Content de te revoir, {self.ctx.name} !" if self.ctx.name else "Salut, je suis Spark !"
        print(f"{greeting} Tape /help ou /exit.")
        while True:
            user_input = input("› ").strip()
            if not user_input:
                continue
            if user_input == "/exit":
                self.ctx.save()
                print("À bientôt !")
                break
            cmd = user_input.split()[0]
            handler = self.commands.get(cmd)
            if handler:
                result = handler(self.ctx, user_input)
                log.add_entry(cmd, user_input.removeprefix(cmd).strip())
                if result and result.message:
                    print(result.message)
            else:
                print("Commande inconnue. Tape /help.")

from context import Context
from commands import (
    start, help as help_cmd, remember, recall,
    todo, remind, pomodoro, localize, weather, ask,
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
        }

    def run(self):
        print("Salut, je suis Spark. Tape /help ou /exit.")
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
                handler(self.ctx, user_input)
            else:
                print("Commande inconnue. Tape /help.")

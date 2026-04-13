from context import Context
from commands import (
    start, help as help_cmd, remember, recall,
    todo, remind, pomodoro, localize, weather, ai, log, note, quote, login, model, tools, skills, spark,
)
from commands.help import COMMANDS

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style


_STYLE = Style.from_dict({
    "prompt":      "ansigreen bold",
    "completion-menu.completion": "bg:#1e1e1e #ffffff",
    "completion-menu.completion.current": "bg:#0066cc #ffffff bold",
})


class _CommandCompleter(Completer):
    def __init__(self, commands: list[tuple[str, str]]):
        self._commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return
        for cmd, desc in self._commands:
            if cmd.startswith(text):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=cmd,
                    display_meta=desc,
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
            "/ai":       ai.handle,
            "/log":      log.handle,
            "/note":     note.handle,
            "/quote":    quote.handle,
            "/login":    login.handle,
            "/model":    model.handle,
            "/tools":    tools.handle,
            "/skills":   skills.handle,
            "/spark":    spark.handle,
        }
        self._session = PromptSession(
            completer=_CommandCompleter(COMMANDS),
            style=_STYLE,
            complete_while_typing=True,
        )

    def run(self):
        greeting = f"Content de te revoir, {self.ctx.name} !" if self.ctx.name else "Salut, je suis Spark !"
        print(f"{greeting} Tape /help ou /exit.")
        while True:
            try:
                user_input = self._session.prompt("› ").strip()
            except (EOFError, KeyboardInterrupt):
                self.ctx.save()
                print("\nÀ bientôt !")
                break
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
                if result and result.redirect:
                    user_input = result.redirect
                    cmd = user_input.split()[0]
                    handler = self.commands.get(cmd)
                    if handler:
                        result = handler(self.ctx, user_input)
                        log.add_entry(cmd, user_input.removeprefix(cmd).strip())
                if result and result.message:
                    print(result.message)
            else:
                print("Commande inconnue. Tape /help.")

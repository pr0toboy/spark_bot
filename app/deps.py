from app.context import Context


def load_ctx() -> Context:
    return Context.load()

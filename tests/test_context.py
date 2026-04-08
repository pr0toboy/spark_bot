from context import Context


def test_context_defaults():
    ctx = Context()
    assert ctx.name == ""
    assert ctx.memory == ""
    assert ctx.todo_list == {}
    assert ctx.chat_history == []


def test_context_save_and_load(tmp_path):
    db = tmp_path / "spark.db"
    ctx = Context(name="Alexis", memory="test", todo_list={"courses": ["pain", "lait"]})
    ctx.save(db_path=db)

    loaded = Context.load(db_path=db)
    assert loaded.name == "Alexis"
    assert loaded.memory == "test"
    assert loaded.todo_list == {"courses": ["pain", "lait"]}
    assert loaded.chat_history == []


def test_context_load_missing_db(tmp_path):
    ctx = Context.load(db_path=tmp_path / "missing.db")
    assert ctx.name == ""
    assert ctx.memory == ""
    assert ctx.todo_list == {}


def test_context_save_overwrites(tmp_path):
    db = tmp_path / "spark.db"
    ctx = Context(memory="v1")
    ctx.save(db_path=db)

    ctx.memory = "v2"
    ctx.save(db_path=db)

    loaded = Context.load(db_path=db)
    assert loaded.memory == "v2"


def test_context_chat_history_persisted(tmp_path):
    db = tmp_path / "spark.db"
    ctx = Context(chat_history=[{"role": "user", "content": "bonjour"}])
    ctx.save(db_path=db)

    loaded = Context.load(db_path=db)
    assert loaded.chat_history == [{"role": "user", "content": "bonjour"}]

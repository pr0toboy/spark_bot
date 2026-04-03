import json
import pytest
from pathlib import Path
from unittest.mock import patch
from context import Context


def test_context_defaults():
    ctx = Context()
    assert ctx.memory == ""
    assert ctx.todo_list == {}
    assert ctx.chat_history == []


def test_context_save(tmp_path):
    ctx = Context(memory="test")
    data_path = tmp_path / "spark_data.json"
    with patch("context.DATA_PATH", data_path):
        ctx.save()
    saved = json.loads(data_path.read_text())
    assert saved["memory"] == "test"
    assert saved["todo_list"] == {}
    assert saved["chat_history"] == []


def test_context_load(tmp_path):
    data_path = tmp_path / "spark_data.json"
    data_path.write_text(json.dumps({
        "memory": "acheter du pain",
        "todo_list": {"courses": ["pain", "lait"]},
        "chat_history": [],
    }))
    with patch("context.DATA_PATH", data_path):
        ctx = Context.load()
    assert ctx.memory == "acheter du pain"
    assert ctx.todo_list == {"courses": ["pain", "lait"]}


def test_context_load_missing_file(tmp_path):
    with patch("context.DATA_PATH", tmp_path / "missing.json"):
        ctx = Context.load()
    assert ctx.memory == ""

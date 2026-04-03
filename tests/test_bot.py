from unittest.mock import patch, MagicMock, call
from context import Context
from bot import SparkBot


def make_bot():
    bot = SparkBot.__new__(SparkBot)
    bot.ctx = Context()
    bot.commands = {"/fake": MagicMock()}
    return bot


def test_dispatch_known_command():
    bot = make_bot()
    with patch("builtins.input", side_effect=["/fake arg", "/exit"]):
        with patch("builtins.print"):
            bot.run()
    bot.commands["/fake"].assert_called_once_with(bot.ctx, "/fake arg")


def test_dispatch_unknown_command(capsys):
    bot = make_bot()
    with patch("builtins.input", side_effect=["/inconnu", "/exit"]):
        bot.run()
    out = capsys.readouterr().out
    assert "inconnue" in out.lower()


def test_exit_saves_context():
    bot = make_bot()
    with patch("builtins.input", return_value="/exit"):
        with patch.object(bot.ctx, "save") as mock_save:
            with patch("builtins.print"):
                bot.run()
    mock_save.assert_called_once()


def test_empty_input_ignored():
    bot = make_bot()
    with patch("builtins.input", side_effect=["", "/exit"]):
        with patch("builtins.print"):
            bot.run()
    bot.commands["/fake"].assert_not_called()

from unittest.mock import patch
from context import Context
from commands import note


def test_note_inline(tmp_path):
    ctx = Context()
    result = note.handle(ctx, "/note acheter du pain", db_path=tmp_path / "spark.db")
    assert result.ok
    assert "acheter du pain" in result.message


def test_note_interactive(tmp_path):
    ctx = Context()
    with patch("builtins.input", return_value="appeler maman"):
        with patch("builtins.print"):
            result = note.handle(ctx, "/note", db_path=tmp_path / "spark.db")
    assert result.ok
    assert "appeler maman" in result.message


def test_note_empty_interactive(tmp_path):
    ctx = Context()
    with patch("builtins.input", return_value=""):
        with patch("builtins.print"):
            result = note.handle(ctx, "/note", db_path=tmp_path / "spark.db")
    assert not result.ok
    assert "❌" in result.message


def test_note_list_empty(tmp_path):
    ctx = Context()
    result = note.handle(ctx, "/note list", db_path=tmp_path / "spark.db")
    assert result.ok
    assert "Aucune" in result.message


def test_note_list(tmp_path):
    db = tmp_path / "spark.db"
    ctx = Context()
    note.handle(ctx, "/note première note", db_path=db)
    note.handle(ctx, "/note deuxième note", db_path=db)

    result = note.handle(ctx, "/note list", db_path=db)
    assert result.ok
    assert "première note" in result.message
    assert "deuxième note" in result.message


def test_note_delete(tmp_path):
    db = tmp_path / "spark.db"
    ctx = Context()
    note.handle(ctx, "/note à supprimer", db_path=db)

    listed = note._list(db_path=db)
    note_id = listed.message.split("[")[1].split("]")[0]

    result = note.handle(ctx, f"/note delete {note_id}", db_path=db)
    assert result.ok
    assert "supprimée" in result.message

    after = note._list(db_path=db)
    assert "Aucune" in after.message


def test_note_delete_invalid_id(tmp_path):
    ctx = Context()
    result = note.handle(ctx, "/note delete 999", db_path=tmp_path / "spark.db")
    assert not result.ok


def test_note_delete_bad_arg(tmp_path):
    ctx = Context()
    result = note.handle(ctx, "/note delete abc", db_path=tmp_path / "spark.db")
    assert not result.ok
    assert "Usage" in result.message


# --- Tests Obsidian Vault ---

def test_note_vault_set(tmp_path):
    ctx = Context()
    vault_dir = tmp_path / "MyVault"
    with patch.object(ctx, "save"):
        result = note.handle(ctx, f"/note vault {vault_dir}", db_path=tmp_path / "spark.db")
    assert result.ok
    assert str(vault_dir) in result.message
    assert ctx.vault_path == str(vault_dir)


def test_note_vault_show(tmp_path):
    ctx = Context(vault_path="/some/path")
    result = note.handle(ctx, "/note vault", db_path=tmp_path / "spark.db")
    assert result.ok
    assert "/some/path" in result.message


def test_note_vault_show_unconfigured(tmp_path):
    ctx = Context()
    result = note.handle(ctx, "/note vault", db_path=tmp_path / "spark.db")
    assert result.ok
    assert "non configuré" in result.message


def test_note_writes_md_to_vault(tmp_path):
    vault_dir = tmp_path / "vault"
    db = tmp_path / "spark.db"
    ctx = Context(vault_path=str(vault_dir))

    result = note.handle(ctx, "/note idée de projet", db_path=db)
    assert result.ok
    assert "→ Vault" in result.message

    md_files = list(vault_dir.glob("*.md"))
    assert len(md_files) == 1

    content = md_files[0].read_text()
    assert "idée de projet" in content
    assert "tags:" in content
    assert "spark" in content
    assert "id:" in content


def test_note_no_vault_no_md(tmp_path):
    ctx = Context()
    db = tmp_path / "spark.db"
    result = note.handle(ctx, "/note sans vault", db_path=db)
    assert result.ok
    assert "→ Vault" not in result.message


def test_note_export(tmp_path):
    vault_dir = tmp_path / "vault"
    db = tmp_path / "spark.db"
    ctx = Context(vault_path=str(vault_dir))

    note._add("note un", db_path=db)
    note._add("note deux", db_path=db)

    result = note._export(ctx, db_path=db)
    assert result.ok
    assert "2" in result.message

    md_files = list(vault_dir.glob("*.md"))
    assert len(md_files) == 2


def test_note_export_no_vault(tmp_path):
    ctx = Context()
    result = note._export(ctx, db_path=tmp_path / "spark.db")
    assert not result.ok
    assert "vault" in result.message.lower()


def test_note_export_empty(tmp_path):
    vault_dir = tmp_path / "vault"
    ctx = Context(vault_path=str(vault_dir))
    result = note._export(ctx, db_path=tmp_path / "spark.db")
    assert result.ok
    assert "Aucune" in result.message


def test_vault_md_frontmatter(tmp_path):
    vault_dir = tmp_path / "vault"
    db = tmp_path / "spark.db"
    ctx = Context(vault_path=str(vault_dir))

    note.handle(ctx, "/note test frontmatter", db_path=db)

    md_file = list(vault_dir.glob("*.md"))[0]
    text = md_file.read_text()

    assert text.startswith("---\n")
    assert "created:" in text
    assert "tags:" in text
    assert "  - spark" in text
    assert "  - note" in text
    assert "test frontmatter" in text

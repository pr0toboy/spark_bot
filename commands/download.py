import shutil
import subprocess
from pathlib import Path

from result import Result

_DEFAULT_DIR = Path.home() / "Downloads"
_ALLOWED_SCHEMES = ("http://", "https://", "ftp://")


def handle(ctx, user_input: str) -> Result:
    args = user_input.removeprefix("/download").strip()

    if not args:
        return Result.error(
            "Usage : /download <url> [audio] [-o <dossier>]\n"
            "  /download https://youtu.be/xxx\n"
            "  /download https://youtu.be/xxx audio\n"
            "  /download https://youtu.be/xxx -o ~/Videos"
        )

    if shutil.which("yt-dlp") is None:
        return Result.error("❌ yt-dlp introuvable. Installe-le : pip install yt-dlp")

    parts = args.split()
    url = parts[0]
    rest = parts[1:]

    if not any(url.startswith(s) for s in _ALLOWED_SCHEMES):
        return Result.error("❌ URL invalide. Seuls http://, https:// et ftp:// sont acceptés.")

    audio_only = "audio" in rest
    if audio_only:
        rest = [p for p in rest if p != "audio"]

    output_dir = _DEFAULT_DIR
    if "-o" in rest:
        idx = rest.index("-o")
        if idx + 1 < len(rest):
            output_dir = Path(rest[idx + 1]).expanduser().resolve()
        rest = rest[:idx] + rest[idx + 2:]

    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = ["yt-dlp", "--progress", "-o", str(output_dir / "%(title)s.%(ext)s")]

    if audio_only:
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    else:
        cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]

    cmd.append(url)

    print(f"⬇  Téléchargement vers {output_dir} …")

    try:
        subprocess.run(cmd, check=True)
        return Result.success(f"✅ Terminé → {output_dir}")
    except subprocess.CalledProcessError as e:
        return Result.error(f"❌ Erreur yt-dlp (code {e.returncode})")
    except Exception as e:
        return Result.error(f"❌ Erreur : {e}")

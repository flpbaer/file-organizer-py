"""Configuração das pastas e do diretório alvo.

O diretório organizado vem (nesta ordem) do argumento de linha de comando,
da variável de ambiente FILE_ORGANIZER_TARGET ou de ~/Downloads.
Não é preciso mais trocar paths no meio do código.
"""

import os
from pathlib import Path

DEFAULT_TARGET = Path.home() / "Downloads"

ENV_TARGET = "FILE_ORGANIZER_TARGET"

# Pasta de destino -> extensões que vão para ela.
FOLDERS: dict[str, tuple[str, ...]] = {
    "Images": (
        "jpg",
        "img",
        "svg",
        "jpeg",
        "jfif",
        "avif",
        "png",
        "mp4",
        "mp3",
    ),
    "Compressed": ("zip", "rar", "7z"),
    "Installers": ("deb", "tar.xz", "tar.gz"),
    "Documents": ("pdf", "xlsx", "ods", "xls", "docx", "json"),
}


def resolve_target(target: str | os.PathLike[str] | None = None) -> Path:
    """Descobre qual diretório deve ser organizado."""
    raw = target or os.environ.get(ENV_TARGET) or DEFAULT_TARGET
    return Path(raw).expanduser().resolve()

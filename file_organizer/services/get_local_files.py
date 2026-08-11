"""Local onde irá buscar os arquivos."""

from pathlib import Path


def get_local_files(directory: Path) -> list[Path]:
    """Lista apenas os arquivos (ignora subpastas) do diretório."""
    if not directory.is_dir():
        raise NotADirectoryError(f"Diretório não encontrado: {directory}")

    return sorted(item for item in directory.iterdir() if item.is_file())

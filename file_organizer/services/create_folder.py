"""Cria uma pasta para certo tipo de arquivo.

Exemplo: na pasta de imagem só vai imagem, e assim por diante.
"""

from pathlib import Path


def create_folder(directory: Path, name: str) -> Path:
    """Cria (se ainda não existir) a pasta de destino e devolve o caminho."""
    folder = directory / name
    folder.mkdir(parents=True, exist_ok=True)
    return folder

"""Move o arquivo para a pasta de destino criada."""

import shutil
from pathlib import Path


def move_file(source: Path, destination_folder: Path) -> Path:
    """Move ``source`` para dentro de ``destination_folder``.

    Se já existir um arquivo com o mesmo nome no destino, um sufixo numérico
    é adicionado (``foto.png`` -> ``foto (1).png``) para não sobrescrever nada.
    """
    destination = _available_path(destination_folder / source.name)
    shutil.move(str(source), str(destination))
    return destination


def _available_path(destination: Path) -> Path:
    if not destination.exists():
        return destination

    stem, suffix = destination.stem, destination.suffix
    counter = 1
    while True:
        candidate = destination.with_name(f"{stem} ({counter}){suffix}")
        if not candidate.exists():
            return candidate
        counter += 1

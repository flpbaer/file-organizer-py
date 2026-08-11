"""Regra central: descobre a pasta de cada arquivo e faz a organização."""

from dataclasses import dataclass
from pathlib import Path

from .config import FOLDERS, resolve_target
from .services import create_folder, get_local_files, move_file


@dataclass
class Result:
    """Resumo do que aconteceu em uma execução."""

    target: Path
    moved: list[tuple[Path, Path]]
    skipped: list[Path]
    errors: list[tuple[Path, Exception]]


def build_extension_map(folders: dict[str, tuple[str, ...]]) -> list[tuple[str, str]]:
    """Lista de ``(extensão, pasta)`` da mais longa para a mais curta.

    A ordem importa para extensões compostas: ``arquivo.tar.gz`` deve casar com
    ``tar.gz`` antes de casar com ``gz``.
    """
    pairs = [
        (extension.lower(), folder)
        for folder, extensions in folders.items()
        for extension in extensions
    ]
    return sorted(pairs, key=lambda pair: len(pair[0]), reverse=True)


def folder_for(file: Path, extension_map: list[tuple[str, str]]) -> str | None:
    """Pasta de destino do arquivo, ou ``None`` se a extensão for desconhecida."""
    name = file.name.lower()
    for extension, folder in extension_map:
        if name.endswith(f".{extension}"):
            return folder
    return None


def organize(
    target: str | Path | None = None,
    folders: dict[str, tuple[str, ...]] | None = None,
    dry_run: bool = False,
) -> Result:
    """Organiza os arquivos do diretório alvo em pastas por tipo."""
    directory = resolve_target(target)
    folders = folders or FOLDERS
    extension_map = build_extension_map(folders)

    files = get_local_files(directory)
    result = Result(target=directory, moved=[], skipped=[], errors=[])

    for file in files:
        folder_name = folder_for(file, extension_map)
        if folder_name is None:
            result.skipped.append(file)
            continue

        try:
            destination_folder = directory / folder_name
            if dry_run:
                result.moved.append((file, destination_folder / file.name))
                continue

            destination_folder = create_folder(directory, folder_name)
            result.moved.append((file, move_file(file, destination_folder)))
        except OSError as error:  # permissão, disco cheio, arquivo em uso...
            result.errors.append((file, error))

    return result

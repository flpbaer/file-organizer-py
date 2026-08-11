"""Interface de linha de comando."""

import argparse
import sys

from .config import DEFAULT_TARGET, ENV_TARGET, FOLDERS
from .organizer import organize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-organizer",
        description="Organiza os arquivos de uma pasta em subpastas por tipo.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help=(
            "Pasta a organizar. Se omitido, usa a variável de ambiente "
            f"{ENV_TARGET} ou {DEFAULT_TARGET}."
        ),
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Apenas mostra o que seria movido, sem mexer em nada.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Mostra somente o resumo final.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        result = organize(target=args.target, folders=FOLDERS, dry_run=args.dry_run)
    except (NotADirectoryError, PermissionError) as error:
        print(f"erro: {error}", file=sys.stderr)
        return 1

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}Organizando {result.target}")

    if not args.quiet:
        for source, destination in result.moved:
            print(f"  {source.name} -> {destination.parent.name}/{destination.name}")

    for source, error in result.errors:
        print(f"  falha em {source.name}: {error}", file=sys.stderr)

    print(
        f"{len(result.moved)} arquivo(s) movido(s), "
        f"{len(result.skipped)} ignorado(s), "
        f"{len(result.errors)} com erro."
    )
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

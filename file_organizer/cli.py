"""Interface de linha de comando."""

import argparse
import sys
from pathlib import Path

from .config import DEFAULT_TARGET, ENV_TARGET, FOLDERS, OTHERS_FOLDER
from .organizer import Result, organize, organize_others

# Respostas aceitas na pergunta sobre a pasta Others.
_YES = ("s", "si", "sim", "y", "yes")
_NO = ("n", "no", "nao", "não", "")


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
    parser.add_argument(
        "--others",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            f"Responde de antemão se os arquivos não organizados vão para "
            f"{OTHERS_FOLDER}/. Sem a flag, a pergunta é feita no terminal."
        ),
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
    _report(result, quiet=args.quiet)

    if result.skipped and _wants_others(args.others, result, prefix):
        moves, errors = len(result.moved), len(result.errors)
        organize_others(result, dry_run=args.dry_run)
        _report(result, quiet=args.quiet, from_move=moves, from_error=errors)

    print(
        f"{len(result.moved)} arquivo(s) movido(s), "
        f"{len(result.skipped)} ignorado(s), "
        f"{len(result.errors)} com erro."
    )
    return 1 if result.errors else 0


def _report(
    result: Result,
    quiet: bool = False,
    from_move: int = 0,
    from_error: int = 0,
) -> None:
    """Imprime os moves e os erros ainda não reportados."""
    if not quiet:
        for source, destination in result.moved[from_move:]:
            print(f"  {source.name} -> {destination.parent.name}/{destination.name}")

    for source, error in result.errors[from_error:]:
        print(f"  falha em {source.name}: {error}", file=sys.stderr)


def _wants_others(flag: bool | None, result: Result, prefix: str = "") -> bool:
    """Decide se os arquivos sem pasta vão para ``Others``.

    A flag ``--others/--no-others`` tem a palavra final; sem ela, pergunta no
    terminal. Fora de um terminal (pipe, cron, testes) o padrão é não mover.
    """
    if flag is not None:
        return flag

    if not sys.stdin.isatty():
        return False

    _list_skipped(result.skipped)
    return _confirm(
        f"{prefix}Criar {OTHERS_FOLDER}/ e mover esse(s) "
        f"{len(result.skipped)} arquivo(s) para lá? [s/N] "
    )


def _list_skipped(skipped: list[Path], limit: int = 10) -> None:
    print(f"\n{len(skipped)} arquivo(s) não foram organizados:")
    for file in skipped[:limit]:
        print(f"  {file.name}")
    if len(skipped) > limit:
        print(f"  ... e outros {len(skipped) - limit}")


def _confirm(question: str) -> bool:
    """Pergunta até receber uma resposta compreensível. Ctrl+C/EOF = não."""
    while True:
        try:
            answer = input(question).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False

        if answer in _YES:
            return True
        if answer in _NO:
            return False
        print("Responda s (sim) ou n (não).")


if __name__ == "__main__":
    raise SystemExit(main())

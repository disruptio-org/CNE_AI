"""CLI utilitário para gerar CSV (e opcionalmente ZIP) dos operadores A e B."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable
import argparse
import tempfile
import zipfile

from cne_ai.docx_tables import extract_tables, export_tables_to_csv

OPERATORS = {
    "A": "operator_a_table",
    "B": "operator_b_table",
}


def _parse_arguments(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extrai as tabelas de um DOCX e gera CSV para os operadores A e B. "
            "O resultado pode ser guardado em pastas ou num único ZIP."
        )
    )
    parser.add_argument("input", type=Path, help="Caminho para o documento DOCX")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("resultados_operadores"),
        help=(
            "Destino dos ficheiros gerados. Quando usado com --zip define o nome do ficheiro "
            "ZIP (por omissão: resultados_operadores.zip)."
        ),
    )
    parser.add_argument(
        "--zip",
        action="store_true",
        help="Guarda os resultados num ficheiro ZIP em vez de pastas.",
    )
    return parser.parse_args(list(argv))


def _export_to_directories(tables, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for operator, basename in OPERATORS.items():
        operator_dir = destination / f"Operador_{operator}"
        export_tables_to_csv(tables, operator_dir, basename=basename)


def _export_to_zip(tables, zip_path: Path) -> None:
    if zip_path.suffix != ".zip":
        zip_path = zip_path.with_suffix(".zip")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        _export_to_directories(tables, temp_root)

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for file_path in temp_root.rglob("*.csv"):
                arcname = file_path.relative_to(temp_root)
                bundle.write(file_path, arcname)


def main(argv: Iterable[str] | None = None) -> int:
    namespace = _parse_arguments([] if argv is None else argv)

    if not namespace.input.exists():
        raise FileNotFoundError(f"DOCX não encontrado: {namespace.input}")

    tables = extract_tables(namespace.input)
    if not tables:
        raise ValueError("O documento não contém tabelas com dados.")

    if namespace.zip:
        _export_to_zip(tables, namespace.output)
    else:
        destination = namespace.output
        if destination.exists() and destination.is_file():
            raise ValueError("O destino escolhido é um ficheiro. Escolha uma pasta ou use --zip.")
        _export_to_directories(tables, destination)

    return 0


if __name__ == "__main__":  # pragma: no cover - ponto de entrada CLI
    import sys

    raise SystemExit(main(sys.argv[1:]))

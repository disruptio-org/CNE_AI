"""Utilities for extracting tables from DOCX documents.

The previous version of this script was a placeholder.  The new implementation
provides a couple of well tested utilities that are useful both in production
and within unit tests:

* :func:`extract_tables` returns the tables of a document as nested lists of
  strings.
* :func:`export_tables_to_csv` persists the extracted tables as CSV files using
  :mod:`csv`, keeping dependencies minimal.
* A tiny command line interface makes it possible to run the script manually
  from the repository root.

The implementation favours small helper functions over a monolithic script.
Each helper is independently testable which makes the behaviour easier to
verify and reduces coupling.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Type, Union
import argparse
import csv

try:  # pragma: no cover - optional dependency in the execution environment
    from docx import Document
except ImportError as exc:  # pragma: no cover - error path when dependency missing
    raise ImportError(
        "The python-docx package is required to extract tables from DOCX files."
    ) from exc


def _normalise_cell(text: str | None) -> str:
    """Return ``text`` stripped from whitespace and with Windows newlines normalised."""

    if text is None:
        return ""
    return text.replace("\r\n", "\n").strip()


def extract_tables(docx_path: Union[str, Path]) -> List[List[List[str]]]:
    """Return the tables contained in ``docx_path`` as ``list`` objects.

    Parameters
    ----------
    docx_path:
        Path to the DOCX document.  A :class:`FileNotFoundError` is raised if the
        file does not exist.
    """

    path = Path(docx_path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {path!s}")

    document = Document(str(path))
    tables: List[List[List[str]]] = []
    for table in document.tables:
        rows: List[List[str]] = []
        for row in table.rows:
            rows.append([_normalise_cell(cell.text) for cell in row.cells])
        if any(any(cell for cell in row) for row in rows):  # skip completely empty tables
            tables.append(rows)
    return tables


def export_tables_to_csv(
    tables: Sequence[Sequence[Sequence[str]]],
    output_dir: Union[str, Path],
    *,
    basename: str = "table",
    dialect: Union[str, Type[csv.Dialect]] = csv.excel,
) -> List[Path]:
    """Persist ``tables`` as CSV files and return their paths."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    exported_paths: List[Path] = []
    for index, table in enumerate(tables, start=1):
        output_path = directory / f"{basename}_{index}.csv"
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, dialect=dialect)
            for row in table:
                writer.writerow(row)
        exported_paths.append(output_path)
    return exported_paths


def _parse_cli_arguments(args: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract tables from a DOCX file")
    parser.add_argument("input", type=Path, help="Path to the DOCX file")
    parser.add_argument("--output", type=Path, default=Path("tables"), help="Directory where CSV files will be written")
    parser.add_argument("--basename", default="table", help="Base name for the exported CSV files")
    return parser.parse_args(list(args))


def main(argv: Iterable[str] | None = None) -> int:
    """Command line entry point."""

    namespace = _parse_cli_arguments([] if argv is None else argv)
    tables = extract_tables(namespace.input)
    export_tables_to_csv(tables, namespace.output, basename=namespace.basename)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI wrapper
    import sys

    raise SystemExit(main(sys.argv[1:]))

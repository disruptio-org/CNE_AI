"""Utilities for working with tables embedded in DOCX documents."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Type, Union
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
    """Return the tables contained in ``docx_path`` as ``list`` objects."""

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


__all__ = ["extract_tables", "export_tables_to_csv"]

"""CLI wrapper around :mod:`cne_ai.docx_tables`.

This script intentionally keeps the command line interface minimal and
delegates the heavy lifting to :func:`cne_ai.docx_tables.extract_tables` and
:func:`cne_ai.docx_tables.export_tables_to_csv`.  The arrangement mirrors the
longer explanatory docstring that used to live in this file while keeping the
actual implementation centralised in the shared module.  Doing so prevents
merge conflicts caused by duplicated logic and ensures both the web app and the
standalone utilities stay in sync.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable
import argparse

from cne_ai.docx_tables import extract_tables, export_tables_to_csv


def _parse_cli_arguments(args: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract tables from a DOCX file")
    parser.add_argument("input", type=Path, help="Path to the DOCX file")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tables"),
        help="Directory where CSV files will be written",
    )
    parser.add_argument(
        "--basename",
        default="table",
        help="Base name for the exported CSV files",
    )
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

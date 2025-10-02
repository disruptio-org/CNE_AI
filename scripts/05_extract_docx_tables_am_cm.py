"""Command line helpers for extracting DOCX tables.

The heavy lifting lives in :mod:`cne_ai.docx_tables`; this module simply wires
those utilities into a small CLI so that analysts can run the extraction from
the repository root.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import argparse

from cne_ai.docx_tables import export_tables_to_csv, extract_tables


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

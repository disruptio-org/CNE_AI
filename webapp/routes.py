"""HTTP routes powering the front-end document processor."""
from __future__ import annotations

from pathlib import Path
from typing import Dict
import io
import tempfile
import zipfile

from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from cne_ai.docx_tables import extract_tables, export_tables_to_csv

OPERATORS: Dict[str, Dict[str, str]] = {
    "A": {"basename": "operator_a_table"},
    "B": {"basename": "operator_b_table"},
}


def init_app(app: Flask) -> None:
    """Register routes on ``app``."""

    @app.route("/", methods=["GET", "POST"])
    def index() -> str | Response:
        if request.method == "POST":
            file = request.files.get("document")
            if file is None or file.filename == "":
                flash("Por favor selecione um ficheiro DOCX antes de continuar.")
                return redirect(url_for("index"))
            try:
                return _handle_upload(file)
            except FileNotFoundError:
                flash("O ficheiro enviado não pôde ser encontrado.")
            except ValueError as exc:
                flash(str(exc))
            except Exception as exc:  # pragma: no cover - defensive fallback
                flash(f"Ocorreu um erro inesperado: {exc}")
        return render_template("index.html")


def _handle_upload(file: FileStorage) -> Response:
    """Process ``file`` and return a ZIP file with the operator CSVs."""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / secure_filename(file.filename)
        file.save(temp_path)

        tables = extract_tables(temp_path)
        if not tables:
            raise ValueError("O documento não contém tabelas com dados.")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for operator, options in OPERATORS.items():
                export_dir = Path(temp_dir) / f"operator_{operator.lower()}"
                csv_paths = export_tables_to_csv(
                    tables,
                    export_dir,
                    basename=options["basename"],
                )
                for csv_path in csv_paths:
                    arcname = f"Operador_{operator}/{csv_path.name}"
                    bundle.write(csv_path, arcname=arcname)

        zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="operadores_csv.zip",
    )

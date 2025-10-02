"""Flask application factory for the document processing UI."""
from __future__ import annotations

from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application instance."""

    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = "dev"

    from . import routes  # noqa: WPS433  (late import to avoid circular dependency)

    routes.init_app(app)
    return app


__all__ = ["create_app"]

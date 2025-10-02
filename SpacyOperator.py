"""Utility helpers for building lightweight spaCy pipelines.

This module exposes a :class:`SpacyOperator` class that simplifies the
construction of small rule based named entity recognition pipelines.  The
original project shipped with a placeholder file which made the tests for this
kata rather uninteresting.  The implementation below focuses on a couple of
quality of life improvements:

* friendly error messages when configuration files or pattern files are
  missing or malformed;
* the ability to load JSON and JSON Lines pattern files;
* a small, well documented API that is easy to unit test.

The implementation purposefully relies on the lightweight ``spacy.blank``
constructor to avoid the need of heavyweight pre-trained models.  That makes
the class quick to spin up in a testing environment while still exposing the
same interfaces used by real projects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple, Union
from collections.abc import MutableMapping
import configparser
import json

try:
    import spacy
    from spacy.language import Language
    from spacy.pipeline import EntityRuler
except ImportError as exc:  # pragma: no cover - dependency guarded at runtime
    raise ImportError(
        "SpacyOperator requires the `spacy` package. Install it with `pip install spacy`."
    ) from exc

PatternInput = Union[str, Path, Sequence[MutableMapping[str, object]]]


def _normalise_language(language: str) -> str:
    """Return ``language`` without surrounding quotes and in lowercase.

    The configuration files bundled with the kata include entries written as
    ``'pt'`` which would otherwise fail when passed directly to
    :func:`spacy.blank`.  Normalising the value keeps the public API concise
    while staying forgiving towards slightly unconventional configuration
    files.
    """

    cleaned = language.strip().strip("\"'")
    if not cleaned:
        raise ValueError("Language entry in configuration file cannot be empty.")
    return cleaned.lower()


def _load_config(path: Union[str, Path]) -> configparser.ConfigParser:
    """Load a spaCy configuration file.

    The project only requires a couple of settings, therefore the use of
    :mod:`configparser` keeps the implementation dependency free.
    """

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path!s}")

    parser = configparser.ConfigParser()
    parser.read(config_path)
    if "nlp" not in parser:
        raise KeyError("The configuration file must contain an [nlp] section.")
    return parser


def _read_patterns_from_file(path: Union[str, Path]) -> List[MutableMapping[str, object]]:
    """Parse patterns from ``path``.

    Supports both JSON and JSON Lines formats.  Empty lines are ignored which
    allows developers to keep files human friendly.  The function raises a
    :class:`ValueError` when the file contains malformed JSON so that the caller
    can display a precise error message to the user.
    """

    patterns_path = Path(path)
    if not patterns_path.exists():
        raise FileNotFoundError(f"Pattern file not found: {patterns_path!s}")

    text = patterns_path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    try:
        if patterns_path.suffix.lower() == ".jsonl":
            patterns: List[MutableMapping[str, object]] = []
            for line_number, raw_line in enumerate(text.splitlines(), start=1):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:  # pragma: no cover - error path
                    raise ValueError(
                        f"Invalid JSON on line {line_number} of {patterns_path!s}: {exc.msg}"
                    ) from exc
                if not isinstance(record, MutableMapping):
                    raise ValueError(
                        "Each pattern in a JSONL file must be a JSON object (mapping)."
                    )
                patterns.append(record)
            return patterns
        data = json.loads(text)
    except json.JSONDecodeError as exc:  # pragma: no cover - error path
        raise ValueError(f"Pattern file {patterns_path!s} contains invalid JSON: {exc.msg}") from exc

    if isinstance(data, MutableMapping):
        return [data]
    if isinstance(data, list):
        invalid = [item for item in data if not isinstance(item, MutableMapping)]
        if invalid:
            raise ValueError("All patterns in the JSON file must be JSON objects (mappings).")
        return list(data)
    raise ValueError("Pattern file must contain either an object or a list of objects.")


@dataclass
class SpacyOperator:
    """Convenience wrapper around a spaCy :class:`~spacy.language.Language` object.

    Parameters
    ----------
    nlp:
        A spaCy :class:`~spacy.language.Language` instance that will be used to
        process text.  In most cases developers will create instances using the
        :meth:`from_config` factory.
    """

    nlp: Language
    _ruler: Optional[EntityRuler] = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_config(
        cls,
        config_path: Union[str, Path],
        *,
        patterns: Optional[PatternInput] = None,
        overwrite_ents: bool = False,
    ) -> "SpacyOperator":
        """Instantiate the operator from a configuration file.

        Parameters
        ----------
        config_path:
            Location of the configuration file.  Only the ``[nlp]`` section is
            required and the ``lang`` option dictates which blank pipeline will
            be used.
        patterns:
            Optional patterns to be registered in an :class:`EntityRuler`.  They
            can be provided either as a sequence of dictionaries or as a path to
            a JSON/JSONL file on disk.
        overwrite_ents:
            Whether the created ruler should replace existing entities in the
            document.  Mirrors spaCy's ``EntityRuler`` option.
        """

        parser = _load_config(config_path)
        language = _normalise_language(parser.get("nlp", "lang", fallback="en"))
        nlp = spacy.blank(language)
        operator = cls(nlp)
        if patterns:
            operator.add_patterns(patterns, overwrite_ents=overwrite_ents)
        return operator

    # ------------------------------------------------------------------
    # Pattern management
    # ------------------------------------------------------------------
    def _ensure_ruler(self, overwrite_ents: bool) -> EntityRuler:
        """Return the :class:`EntityRuler`, creating it if necessary."""

        if self._ruler is None:
            self._ruler = self.nlp.add_pipe("entity_ruler", config={"overwrite_ents": overwrite_ents})
        else:
            # spaCy exposes the flag via the ``overwrite" attribute on the ruler.
            self._ruler.overwrite = overwrite_ents
        return self._ruler

    def add_patterns(self, patterns: PatternInput, *, overwrite_ents: bool = False) -> None:
        """Load patterns into the pipeline's entity ruler.

        ``patterns`` accepts either a path to a JSON/JSONL file or a sequence of
        dictionaries already in memory.  Invalid entries raise a
        :class:`ValueError` explaining the problem so callers can surface a
        useful error message.
        """

        if isinstance(patterns, (str, Path)):
            loaded_patterns = _read_patterns_from_file(patterns)
        else:
            loaded_patterns = list(patterns)
            invalid = [item for item in loaded_patterns if not isinstance(item, MutableMapping)]
            if invalid:
                raise ValueError("All patterns must be mappings with spaCy keys such as 'label' and 'pattern'.")
        if not loaded_patterns:
            return
        ruler = self._ensure_ruler(overwrite_ents)
        ruler.add_patterns(list(loaded_patterns))

    # ------------------------------------------------------------------
    # Text processing helpers
    # ------------------------------------------------------------------
    def __call__(self, text: str) -> spacy.tokens.Doc:
        """Process a single ``text`` and return the resulting doc."""

        if not isinstance(text, str):
            raise TypeError("text must be a string")
        return self.nlp(text)

    def pipe(self, texts: Iterable[str]) -> Iterator[spacy.tokens.Doc]:
        """Process multiple texts using spaCy's efficient :meth:`Language.pipe`."""

        return self.nlp.pipe(texts)

    def extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Return ``(entity, label)`` tuples found in ``text``."""

        doc = self(text)
        return [(ent.text, ent.label_) for ent in doc.ents]


__all__ = ["SpacyOperator"]
{
  "name": "CNE Codex Dev",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  "postCreateCommand": "python -m venv .venv && . .venv/bin/activate && pip install -e ./cne_ai && pip install -r requirements.txt || true",
  "mounts": [
    "source=${localWorkspaceFolder}/cne_ai,target=/workspaces/cne_ai,type=bind",
    "source=${localWorkspaceFolder}/models,target=/opt/cne_ai/models,type=bind"
  ],
  "containerEnv": {
    "CNE_AI_CONFIG": "/workspaces/CNE/cne_ai_config.yaml"
  },
  "forwardPorts": [],
  "remoteUser": "vscode"
}

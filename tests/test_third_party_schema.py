"""third-party.json must match third-party.schema.json.

install.py reads third-party.json without validating it, and a misspelled key
(e.g. `extra_link`) is silently ignored, so a skill would just not install.
The schema forbids unknown keys; this test runs it.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REAL_REPO = Path(__file__).resolve().parent.parent


def _schema() -> dict:
    return json.loads((REAL_REPO / "third-party.schema.json").read_text(encoding="utf-8"))


def test_committed_third_party_json_matches_schema():
    data = json.loads((REAL_REPO / "third-party.json").read_text(encoding="utf-8"))
    jsonschema.validate(data, _schema())


def test_schema_rejects_a_misspelled_install_key():
    data = {"plugins": [{"name": "x", "platforms": {}, "install": {
        "source": "vendor/x",
        "generate": {"scan_dir": "skills", "link_dir": "~/.agents/skills", "extra_link": ["~/.claude/skills"]},
    }}]}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, _schema())

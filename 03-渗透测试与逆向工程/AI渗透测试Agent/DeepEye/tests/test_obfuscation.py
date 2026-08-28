"""Tests for core.obfuscation."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pytest
from core.obfuscation import obfuscate_payload, known_techniques


def test_case_manipulation():
    out = obfuscate_payload("' OR 1=1", ["case_manipulation"])
    assert any("oR" in p or "Or" in p or p != "' OR 1=1" for p in out)


def test_url_encoding():
    out = obfuscate_payload(" ", ["url_encoding"])
    assert "%20" in out
    out2 = obfuscate_payload("<script>", ["url_encoding"])
    assert any("%3C" in p or "%3c" in p for p in out2)


def test_unknown_technique():
    with pytest.raises(KeyError) as ei:
        obfuscate_payload("x", ["nope"])
    assert "nope" in str(ei.value)
    assert known_techniques()

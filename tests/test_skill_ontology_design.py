"""Static checks for the ontology-design skill and its examples.

The platform contract test lives in the Dream Insights source repo; this only
guards that the public copy stays self-consistent (files exist, JSON parses,
expected sidecars match their example, links resolve).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".claude" / "skills" / "dream-insights-ontology-design" / "SKILL.md"
EXAMPLES = ROOT / "examples" / "ontology-design"
NAMES = ["good-leadshook-quiz", "bad-contact-statuses", "bad-double-route"]


def test_skill_front_matter_name() -> None:
    text = SKILL.read_text()
    assert text.startswith("---\n")
    assert "\nname: dream-insights-ontology-design\n" in text


@pytest.mark.parametrize("name", NAMES)
def test_example_and_sidecar(name: str) -> None:
    doc = json.loads((EXAMPLES / f"{name}.json").read_text())
    expected = json.loads((EXAMPLES / f"{name}.expected.json").read_text())
    assert expected["example"] == f"{name}.json"
    assert doc["entities"], "example must define entities"
    for key in ("breaks_extraction", "worth_fixing"):
        assert isinstance(expected[key], list)


def test_good_example_is_clean_and_bad_examples_are_not() -> None:
    good = json.loads((EXAMPLES / "good-leadshook-quiz.expected.json").read_text())
    assert good["breaks_extraction"] == [] and good["worth_fixing"] == []
    for name in NAMES[1:]:
        bad = json.loads((EXAMPLES / f"{name}.expected.json").read_text())
        assert bad["breaks_extraction"] or bad["worth_fixing"]


def test_skill_relative_links_resolve() -> None:
    text = SKILL.read_text()
    for target in re.findall(r"\]\(([^)#]+)\)", text):
        if target.startswith("http"):
            continue
        assert (SKILL.parent / target).resolve().exists(), target


def test_no_private_source_paths_or_secrets() -> None:
    text = SKILL.read_text()
    assert "app/" not in text
    assert "di_admin_" not in text
    for path in EXAMPLES.glob("*.json"):
        body = path.read_text()
        assert not re.search(r"di_(user|admin|fleet)_[A-Za-z0-9]{8,}", body), path

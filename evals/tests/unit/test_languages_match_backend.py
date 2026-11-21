"""The harness never imports the backend (README), so its language list is its own copy. This reads the
backend's `CourseLanguage` from source and fails when the two differ (spec 021 §4.9): a new course language
must reach `--language` and the judge in the same change."""

import ast
from pathlib import Path

from harness.config import LANGUAGES
from harness.judge import LANGUAGE_NAMES

LANGUAGE_PY = Path(__file__).resolve().parents[3] / "backend" / "app" / "domain" / "language.py"


def _backend_course_languages() -> tuple[str, ...]:
    tree = ast.parse(LANGUAGE_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        names = [t.id for t in getattr(node, "targets", []) if isinstance(t, ast.Name)]
        if isinstance(node, ast.Assign) and "CourseLanguage" in names:
            subscript = node.value
            assert isinstance(subscript, ast.Subscript)
            elements = subscript.slice.elts if isinstance(subscript.slice, ast.Tuple) else [subscript.slice]
            return tuple(ast.literal_eval(e) for e in elements)
    raise AssertionError(f"no CourseLanguage in {LANGUAGE_PY}")


def test_the_harness_languages_are_the_backends() -> None:
    assert LANGUAGES == _backend_course_languages()


def test_the_judge_names_every_language() -> None:
    assert set(LANGUAGE_NAMES) == set(LANGUAGES)

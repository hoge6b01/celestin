"""Spec 021 task 4.5: the prompt library reads the German files like the others and, German being offered, requires
them, naming a missing one.

The mechanics are pinned for French and English in `test_prompt_library_languages.py` and for Dutch in
`test_prompt_library_nl.py`; these cover the fourth language on a copy of the real tree."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.domain.errors import PromptInvalid, PromptUnavailable
from app.services import prompts
from app.services.prompts import PromptLibrary, file_name

PROMPTS = Path(__file__).resolve().parents[2] / "prompts"
AUTHORING_SET = [
    "subjects/mathematics.de.md", "templates/mathematics.pack.de.md", "subjects/sciences.de.md",
    "templates/sciences.pack.de.md", "subjects/languages.de.md", "templates/languages.pack.de.md",
    "subjects/general.de.md", "templates/general.pack.de.md", "authoring/pack.de.md", "authoring/curriculum.de.md",
    "transcription/transcribe.de.md", "transcription/verify.de.md", "transcription/work.de.md",
]
TUTOR_SET = [
    "tutor.de.md",
    *(f"modes/{mode}{part}.de.md" for mode in ("parcours", "discussion", "revision") for part in ("", ".opening")),
]


@pytest.fixture
def root(tmp_path: Path) -> Path:
    copy = tmp_path / "prompts"
    shutil.copytree(PROMPTS, copy)
    return copy


def test_file_names_carry_the_german_language() -> None:
    assert file_name("tutor", "de") == "tutor.de.md"
    assert prompts.subject_file("sciences", "de") == "subjects/sciences.de.md"
    assert prompts.template_file("mathematics", "de") == "templates/mathematics.pack.de.md"
    assert prompts.authoring_curriculum_file("de") == "authoring/curriculum.de.md"
    assert prompts.work_file("de") == "transcription/work.de.md"


def test_the_german_files_exist_and_are_german() -> None:
    library = PromptLibrary(PROMPTS)
    for name in AUTHORING_SET + TUTOR_SET:
        assert (PROMPTS / name).is_file(), name
    assert "Lernpfad" in library.authoring_curriculum("de") and "Kapitel" in library.authoring_pack("de")
    assert len({library.transcribe(language) for language in ("fr", "en", "nl", "de")}) == 4
    assert library.subject("mathematics", "de").startswith("## Das Fach: Mathematik")


def test_templates_are_parsed_for_german_and_know_it() -> None:
    library = PromptLibrary(PROMPTS)
    for subject in ("mathematics", "sciences", "languages", "general"):
        template = library.template(subject, "de")  # type: ignore[arg-type]
        assert template.language == "de" and template.exercises_section == 6
        assert template is library.template(subject, "de")  # type: ignore[arg-type]
    assert library.template("mathematics", "de").headings[-1] == (7, "Zu prüfende Punkte")



def test_german_is_one_of_the_other_languages_templates() -> None:
    library = PromptLibrary(PROMPTS)
    assert [t.language for t in library.other_templates("sciences", "fr")] == ["en", "nl", "de"]
    assert [t.language for t in library.other_templates("sciences", "de")] == ["fr", "en", "nl"]



def test_an_offered_german_requires_its_files_and_names_the_missing_one(root: Path) -> None:
    required = PromptLibrary(root).required()
    assert set(AUTHORING_SET + TUTOR_SET) <= set(required)
    PromptLibrary(root).check()  # every German file is there and parses
    (root / "subjects" / "sciences.de.md").unlink()
    with pytest.raises(PromptInvalid, match=r"\.de\.md"):  # the first German file missing, by name
        PromptLibrary(root).check()


def test_health_lists_a_broken_german_file_with_its_language(root: Path) -> None:
    library = PromptLibrary(root)
    (root / "authoring" / "pack.de.md").unlink()
    (root / "templates" / "sciences.pack.de.md").write_text("---\nsubject: nope\n---\n", encoding="utf-8")
    broken = library.unavailable()
    assert "templates/sciences.pack.de.md" in broken and "authoring/pack.de.md" in broken
    assert not any(not name.endswith(".de.md") for name in broken)
    with pytest.raises(PromptUnavailable):
        library.authoring_pack("de")
    library.authoring_pack("nl")  # the other sets are untouched

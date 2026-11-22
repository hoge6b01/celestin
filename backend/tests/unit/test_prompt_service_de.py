"""Spec 021 R3, task 5.3: the German system text is its own cached prefix, pinned like the French, English and Dutch ones.

`system_text_sha_de.txt` and `system_text_sha_de_discussion.txt` were generated once from the German prompt set and the
German sequences chapter (`folgen_de`), read by a person, and pinned. Delete a file and rerun to regenerate it after an
intended change to a German prompt, the pack or the curriculum.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.config import get_settings
from app.services import curriculum_render, prompt_service
from app.services.prompts import PromptLibrary
from scripts.chapter_files import load_chapter_dir
from tests.conftest import GERMAN_LESSON_DIR

RENDER = Path(__file__).parents[1] / "fixtures" / "render"


def _rendering(voice: bool, mode: str = "parcours") -> str:
    prompts = PromptLibrary(get_settings().prompts_dir)
    chapter = load_chapter_dir(GERMAN_LESSON_DIR, "mathematics", prompts, language="de")
    return prompt_service.render_system_text(
        prompts.tutor("de"),
        prompts.subject("mathematics", "de"),
        chapter.pack,
        curriculum_render.overview(chapter.curriculum, mode, "de"),  # type: ignore[arg-type]
        prompts.mode(mode, "de"),  # type: ignore[arg-type]
        prompts.mode_opening(mode, "de"),  # type: ignore[arg-type]
        voice=voice,
    )


def _pinned(name: str, text: str) -> None:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    path = RENDER / name
    if not path.exists():
        path.write_text(digest + "\n")
    assert digest == path.read_text().strip()


def test_the_german_text_rendering_is_byte_stable() -> None:
    text = _rendering(voice=False)
    _pinned("system_text_sha_de.txt", text)
    assert "## Das Fach: Mathematik" in text and "## Lernpfad des Kapitels" in text
    assert "laut gesprochen" not in text and "laut miteinander" not in text


def test_the_german_discussion_rendering_is_byte_stable() -> None:
    text = _rendering(voice=False, mode="discussion")
    _pinned("system_text_sha_de_discussion.txt", text)
    assert "## Das Gespräch" in text
    assert "kein Werkzeug, um einen Abschnitt zu öffnen" in text
    assert "complete_section(id" not in text.split("## Das Gespräch")[0].split("Lernpfad des Kapitels")[0]


def test_the_german_voice_rendering_carries_both_voice_blocks() -> None:
    text = _rendering(voice=True)
    assert "Wenn wir laut miteinander sprechen" in text and "Mathematik laut gesprochen" in text
    assert "<!-- VOICE -->" not in text and "<!-- /VOICE -->" not in text


def test_the_german_rendering_carries_no_french_english_or_dutch_prompt_text() -> None:
    for mode in ("parcours", "discussion"):
        text = _rendering(voice=True, mode=mode)
        for other in (
            "Ta seule source", "Parcours du chapitre", "à voix haute", "Hors sujet",
            "Your only source", "Chapter path", "out loud", "Off-topic",
            "Je enige bron", "Traject van het hoofdstuk", "hardop", "Buiten het onderwerp",
        ):
            assert other not in text, other


def test_the_four_languages_render_four_prefixes() -> None:
    from tests.unit.test_prompt_service import _real_rendering
    from tests.unit.test_prompt_service_en import _rendering as english
    from tests.unit.test_prompt_service_nl import _rendering as dutch

    renderings = {_real_rendering(voice=False), english(voice=False), dutch(voice=False), _rendering(voice=False)}
    assert len(renderings) == 4

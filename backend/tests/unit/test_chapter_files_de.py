"""Spec 021 tasks 5.2 and 7.1: the German fixture chapters the probes run on. Each passes the validation the editors
apply (the German template, every reference resolving) and holds the facts the probes rely on, in NRW notation."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.language import COURSE_LANGUAGES
from app.services.prompts import PromptLibrary
from scripts.chapter_files import load_chapter_dir

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
CHAPTERS = FIXTURES / "chapters"
PROMPTS = PromptLibrary(Path(__file__).resolve().parents[2] / "prompts")

GERMAN_CHAPTERS = [
    ("folgen_de", "mathematics", "Arithmetische und geometrische Folgen"),
    ("statistik_de", "mathematics", "Beschreibende Statistik mit einem Merkmal"),
    ("koordinatengeometrie_de", "mathematics", "Koordinatengeometrie in der Ebene"),
    ("ungleichungen_de", "mathematics", "Intervalle und lineare Ungleichungen"),
    ("gleichfoermige_bewegung_de", "sciences", "Gleichförmige geradlinige Bewegung"),
]


def pack(name: str) -> str:
    return (CHAPTERS / name / "pack.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(("directory", "subject", "title"), GERMAN_CHAPTERS)
def test_each_german_chapter_validates_against_its_german_template(directory: str, subject: str, title: str) -> None:
    chapter = load_chapter_dir(CHAPTERS / directory, subject, PROMPTS, language="de")  # type: ignore[arg-type]
    assert chapter.language == "de" and chapter.title == title
    assert chapter.curriculum.sections[-1].kind in ("practise", "synthesis")


@pytest.mark.parametrize(("directory", "subject", "title"), GERMAN_CHAPTERS)
def test_a_german_chapter_is_not_valid_in_another_language(directory: str, subject: str, title: str) -> None:
    from scripts.chapter_files import ChapterFilesInvalid

    for language in [code for code in COURSE_LANGUAGES if code != "de"]:
        with pytest.raises(ChapterFilesInvalid):
            load_chapter_dir(CHAPTERS / directory, subject, PROMPTS, language=language)  # type: ignore[arg-type]


@pytest.mark.parametrize("directory", [d for d, _, _ in GERMAN_CHAPTERS])
def test_the_german_fixtures_use_the_nrw_notation_and_no_decimal_point(directory: str) -> None:
    import re

    text = re.sub(r"^#.*$|§\s*\d+(?:\.\d+)*", "", pack(directory), flags=re.MULTILINE)  # headings and references
    assert not re.search(r"(?<![\w.])\d+\.\d+(?![\w.])", text), "a decimal point in a German pack"
    assert "Keine." in text or "Nichts im Material" in text


def test_the_statistics_chapter_draws_its_nested_sets_and_every_chart() -> None:
    text = pack("statistik_de").casefold()
    for name in ("kreisdiagramm", "säulendiagramm", "histogramm", "summenhäufigkeitspolygon", "boxplot"):
        assert name in text
    assert "mengendiagramm mit ineinanderliegenden mengen" in text and "stichprobe" in text


def test_the_geometry_chapter_marks_points_with_a_cross_and_has_its_right_angle_at_b() -> None:
    text = pack("koordinatengeometrie_de")
    assert "Kreuz" in text and "kartesisches Koordinatensystem" in text
    assert "rechten Winkel bei $B$" in text and "$B(3 \\mid 4)$" in text


def test_the_inequalities_chapter_draws_its_bounds_as_brackets() -> None:
    text = pack("ungleichungen_de")
    assert "Zahlengerade" in text and "Mengendiagramm" in text
    assert "Klammer" in text and "Kreis" not in text and "Kapitel" not in text.splitlines()[0]
    assert "]-\\infty ; 4[" in text or "]−∞ ; 4[" in text


def test_the_motion_chapter_keeps_its_wrong_answer_and_leaves_it_out_of_the_path() -> None:
    chapter = load_chapter_dir(CHAPTERS / "gleichfoermige_bewegung_de", "sciences", PROMPTS, language="de")
    assert [s.id for s in chapter.curriculum.sections] == ["bewegung", "gleichfoermig", "ueben"]
    assert chapter.curriculum.sections[-1].exercises == ["6.1.1", "6.2.1", "6.2.2"]
    assert "| $x$ (m) | 1,0 | 2,5 | 4,0 | 5,5 | 7,0 |" in chapter.pack
    assert "360\\,\\mathrm{km}$ (die Antwort der Lösung; siehe § 7)" in chapter.pack


@pytest.mark.parametrize("name", ["maths_statistik_de.txt", "physik_gleichfoermig_de.txt"])
def test_the_german_materials_are_german_and_carry_the_figures_the_chapters_describe(name: str) -> None:
    text = (FIXTURES / "material" / name).read_text(encoding="utf-8")
    assert "[Abbildung:" in text or "Diagramm" in text
    lowered = text.lower()
    assert "chapitre" not in lowered and "chapter" not in lowered and "hoofdstuk" not in lowered

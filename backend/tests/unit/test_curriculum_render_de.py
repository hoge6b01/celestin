"""Spec 021 R5.1, R5.2: the path as the model reads it in a German course.

The other languages are pinned by their own files and goldens, which this file does not touch; the German goldens
(`*_de.txt`) are generated once, read by the user, and pinned.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from app.domain.curriculum import KIND_LABELS
from app.domain.progress import Progress
from app.services import curriculum_render as render
from tests.fixtures.curricula import curriculum

CUR = curriculum("valid_de.yaml")
SNAPSHOTS = Path(__file__).parent.parent / "fixtures" / "render"
DE = "de"


def check(name: str, text: str) -> None:
    """Snapshot files are committed; regenerate by deleting one and rerunning."""
    path = SNAPSHOTS / f"{name}_de.txt"
    if not path.exists():
        path.write_text(text, encoding="utf-8")
    assert text == path.read_text(encoding="utf-8")


def test_overview_in_both_modes() -> None:
    text = render.overview(CUR, "parcours", DE)
    assert "1. `intro` (Lektion) — Einleitung. Verstehen, worum es geht." in text
    assert "2. `exos` (Übungen)" in text and "3. `bilan` (Zusammenfassung)" in text
    check("overview", text)
    discussion = render.overview(CUR, "discussion", DE)
    assert "start_section" not in discussion and "Lernpfad-Modus" in discussion
    check("overview_discussion", discussion)


def test_the_overview_is_byte_stable_and_differs_from_the_others() -> None:
    assert render.overview(CUR, "parcours", DE) == render.overview(curriculum("valid_de.yaml"), "parcours", DE)
    assert render.overview(CUR, "parcours", DE) != render.overview(CUR)
    assert render.overview(CUR, "parcours", DE) != render.overview(CUR, "parcours", "nl")


@pytest.mark.parametrize(
    ("section", "review", "name"),
    [("intro", False, "brief_teach"), ("exos", False, "brief_practise"), ("intro", True, "brief_review")],
)
def test_briefs(section: str, review: bool, name: str) -> None:
    text = render.brief(CUR, CUR.get(section), review, DE)
    assert text.startswith(f"Abschnitt „{CUR.get(section).label}“ (")
    assert ("Wiederholung: Dieser Abschnitt ist schon abgeschlossen" in text) is review
    check(name, text)


def test_a_teach_brief_lists_the_outline_and_a_practice_brief_the_exercises() -> None:
    teach = render.brief(CUR, CUR.get("intro"), False, DE)
    assert "Ablauf:\n1. Die Definition wiederholen.\n2. Kontrollfrage." in teach
    assert "Abgeschlossen, wenn: Die Kontrollfrage ist beantwortet." in teach
    practise = render.brief(CUR, CUR.get("exos"), False, DE)
    assert "Typische Aufgaben: 6.1.1; 6.1.2." in practise
    assert "Zu tun: 2 Aufgabe(n), eine nach der anderen." in practise and "Ablauf" not in practise


def test_completion() -> None:
    assert render.completion(None, CUR.get("exos"), DE) == (
        "Abschnitt abgeschlossen. Nächster Abschnitt: „2. Übungen“ (Übungen), id: exos."
    )
    assert render.completion(None, None, DE) == "Abschnitt abgeschlossen. Kapitel abgeschlossen."


@pytest.mark.parametrize(
    ("name", "progress", "phrase"),
    [
        ("state_empty", Progress(), 'start_section("intro")'),
        ("state_active", Progress(done=frozenset({"intro"}), active="exos"), "Aktueller Abschnitt: „2. Übungen“ (Übungen)."),
        ("state_between", Progress(done=frozenset({"intro"})), "Als Nächstes: „2. Übungen“"),
        ("state_complete", Progress(done=frozenset({"intro", "exos", "bilan"})), "Kapitel abgeschlossen."),
    ],
)
def test_state_messages(name: str, progress: Progress, phrase: str) -> None:
    text = render.state_message(CUR, progress, None, "parcours", DE)
    assert phrase in text and len(text) < 400
    check(name, text)


@pytest.mark.parametrize(
    ("name", "progress", "phrase"),
    [
        ("state_discussion_empty", Progress(), "Der nächste wäre „1. Einleitung“ (Lektion)"),
        ("state_discussion_active", Progress(active="exos"), "Aktueller Abschnitt im Lernpfad: „2. Übungen“"),
        ("state_discussion_complete", Progress(done=frozenset({"intro", "exos", "bilan"})), "Der ganze Lernpfad ist erledigt"),
    ],
)
def test_discussion_state_names_no_tool(name: str, progress: Progress, phrase: str) -> None:
    text = render.state_message(CUR, progress, None, "discussion", DE)
    assert phrase in text and "start_section" not in text
    check(name, text)


@pytest.mark.parametrize(
    ("when", "expected"),
    [
        (datetime(2026, 10, 8, 10, 5), "Donnerstag, 8. Oktober, 10:05 Uhr (vormittags)"),
        (datetime(2026, 9, 11, 11, 59), "Freitag, 11. September, 11:59 Uhr (vormittags)"),
        (datetime(2026, 9, 11, 12, 0), "Freitag, 11. September, 12:00 Uhr (nachmittags)"),
        (datetime(2026, 9, 11, 17, 59), "Freitag, 11. September, 17:59 Uhr (nachmittags)"),
        (datetime(2026, 12, 20, 18, 0), "Sonntag, 20. Dezember, 18:00 Uhr (abends)"),
        (datetime(2026, 1, 5, 0, 7), "Montag, 5. Januar, 0:07 Uhr (vormittags)"),
    ],
)
def test_moment(when: datetime, expected: str) -> None:
    assert render.moment(when, DE) == expected


def test_the_state_message_opens_with_the_time_in_the_courses_language() -> None:
    text = render.state_message(CUR, Progress(), datetime(2026, 10, 8, 10, 5), "parcours", DE)
    assert text.startswith("Es ist Donnerstag, 8. Oktober, 10:05 Uhr (vormittags).\nStand des Lernpfads: ")


def test_the_german_kind_labels() -> None:
    assert KIND_LABELS["de"] == {"teach": "Lektion", "practise": "Übungen", "synthesis": "Zusammenfassung"}

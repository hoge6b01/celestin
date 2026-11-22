"""Spec 021 R4.1, R4.4: the transcription's marks in a German course. The other languages stay in their own files."""

from __future__ import annotations

from app.domain.pack import chapter_title
from app.domain.transcription import (
    MARKERS,
    apply_uncertain,
    count_markers,
    handwritten_numbers,
    validate_batch,
)

DE_BATCH = "--- page 3 ---\nGetippte Zeile\n[handschriftlich: 330]\n--- page 4 ---\n[leere Seite]"


def test_the_german_marks() -> None:
    de = MARKERS["de"]
    assert (de.handwritten, de.uncertain, de.illegible, de.empty_page) == (
        "[handschriftlich", "[unsicher", "[unleserlich]", "[leere Seite]",
    )
    assert de.nothing == "[nichts lesbar]"


def test_a_german_batch_is_validated_with_the_page_markers_only() -> None:
    text, issues = validate_batch(DE_BATCH, [3, 4], "de")
    assert issues == [] and text is not None
    assert text.startswith("--- page 3 ---\n\nGetippte Zeile") and "--- page 4 ---\n\n[leere Seite]" in text


def test_the_issues_are_worded_in_german() -> None:
    assert validate_batch("--- page 3 ---\nx", [3, 4], "de")[1][0].message == "fehlende Markierung für Seite 4"
    assert validate_batch("--- page 3 ---\nx\n--- page 5 ---\ny", [3], "de")[1][0].message == "unerwartete Seite 5"
    assert "falscher Reihenfolge" in validate_batch("--- page 4 ---\nx\n--- page 3 ---\ny", [3, 4], "de")[1][0].message
    assert validate_batch("--- page 1 ---\n\n--- page 2 ---\nx", [1, 2], "de")[1][0].message == (
        "leere Seite ohne „[leere Seite]“"
    )


def test_marks_are_counted_and_rewritten_in_german() -> None:
    text = "vor [handschriftlich: 12] und [unsicher: 4 oder 9] und [unleserlich]\n[handschriftlich: 330 m]"
    counts = count_markers(text, "de")
    assert (counts.handwritten, counts.uncertain, counts.illegible) == (2, 1, 1)
    page = "--- page 1 ---\nGetippte Zeile 7\n[handschriftlich] $33 \\cdot 10 = $ 330"
    candidates = handwritten_numbers(page, "de")
    assert [line for _, line in candidates] == ["[handschriftlich] $33 \\cdot 10 = $ 330"]
    index, line = candidates[0]
    rewritten = apply_uncertain(page, [(index, line, "[handschriftlich] $33 \\cdot 10 = $ [unsicher: 330 oder 350]")], "de")
    assert "[unsicher: 330 oder 350]" in rewritten
    assert apply_uncertain(page, [(index, line, "[handschriftlich] 999")], "de") == page
    assert apply_uncertain(page, [(index, line, "[onzeker: x]")], "de") == page


def test_an_uncertain_point_keeps_its_bar() -> None:
    """Design §1 decision 2: the readings are separated by « oder », so a German point's `|` is never ambiguous;
    the code reads only the mark's opening."""
    line = "[handschriftlich] Scheitelpunkt S(2 | 3)"
    page = f"--- page 1 ---\n{line}"
    new = "[handschriftlich] Scheitelpunkt [unsicher: S(2 | 3) oder S(2 | 8)]"
    rewritten = apply_uncertain(page, [(1, line, new)], "de")
    assert rewritten.endswith(new)
    assert count_markers(rewritten, "de").uncertain == 1


def test_another_languages_mark_is_not_counted_in_a_german_course() -> None:
    assert count_markers("[manuscrit : 12] [illisible] [handgeschreven: 3]", "de").handwritten == 0


def test_chapter_numbering_words_are_stripped_in_german() -> None:
    assert chapter_title("Kapitel 3: Folgen", "de") == "Folgen"
    assert chapter_title("Kap. 2 – Gleichförmige Bewegung", "de") == "Gleichförmige Bewegung"
    assert chapter_title("Lektion 4) Statistik", "de") == "Statistik"
    assert chapter_title("Thema IV. Geometrie", "de") == "Geometrie"
    assert chapter_title("Teil 2 Funktionen", "de") == "Funktionen"
    assert chapter_title("4) Verhältnisse", "de") == "Verhältnisse"
    assert chapter_title("Kapitel Nr. 3: Folgen", "de") == "Folgen"
    # not a numbering: a word that starts like a keyword, a title that is only words
    assert chapter_title("Teilchen und Wellen", "de") == "Teilchen und Wellen"
    assert chapter_title("Modulation von Signalen", "de") == "Modulation von Signalen"
    assert chapter_title("Kapitelübersicht Analysis", "de") == "Kapitelübersicht Analysis"
    # the other languages' words are not German numbering
    assert chapter_title("Chapitre 3 : Suites", "de").startswith("Chapitre")

"""Spec 021 R4.5, R5: what the code builds for the model in a German course, beside the French, English and Dutch pins.

`test_model_text_by_language.py` pins the English rows and `test_model_text_nl.py` the Dutch ones; French is pinned by
the original tests. These cover the German rows of the same tables: the path's refusals, the tools' words, the history
estimate, the authoring words, the declarations, and the German chapter numbering words.
"""

from __future__ import annotations

import json

import pytest

from app.api.schemas.chat import LearnerEntry, ToolEntry
from app.domain.errors import ToolValidationError
from app.domain.messages.issues import issue_text
from app.domain.pack import ContentIssue, chapter_title
from app.domain.progress import Progress
from app.services import history, path
from app.services.authoring.agent import _repair_message
from app.services.authoring.words import AGENT_WORDS
from app.services.tools import registry
from app.services.tools.context import SAVE_FAILED, TurnContext
from tests.fixtures.curricula import ctx_for, curriculum

CUR = curriculum("valid_de.yaml")


def run(name: str, args: dict, ctx: TurnContext):
    return registry.execute(name, json.dumps(args), ctx)


def refusal(name: str, args: dict, ctx: TurnContext) -> str:
    with pytest.raises(ToolValidationError) as raised:
        run(name, args, ctx)
    return raised.value.message


def test_path_refusals_in_german() -> None:
    assert path.can_start(CUR, "nope", "de") == (
        "Abschnitt „nope“ gibt es nicht. Abschnitte des Kapitels: intro, exos, bilan."
    )
    assert path.can_start(CUR, "exos", "de") is None  # spec 019: no section is locked
    assert path.can_skip(CUR, Progress(done=frozenset({"exos"})), "exos", "de") == (
        "Abschnitt „2. Übungen“ ist schon abgeschlossen: Er kann nicht übersprungen werden."
    )
    assert path.can_complete(CUR, Progress(), "intro", "de") == "Kein Abschnitt ist in Arbeit. Beginne einen mit start_section."
    assert path.can_complete(CUR, Progress(active="intro"), "exos", "de") == (
        "Nur der aktuelle Abschnitt kann abgeschlossen werden: „1. Einleitung“ (id: intro)."
    )
    assert path.can_complete(CUR, Progress(active="intro"), "intro", "de") is None


def test_the_sections_tools_refuse_in_the_courses_language() -> None:
    ctx = ctx_for(name="valid_de.yaml", language="de")
    assert "gibt es nicht" in refusal("start_section", {"section_id": "nope"}, ctx)
    assert "gibt es nicht" in refusal("skip_section", {"section_id": "nope"}, ctx)
    run("start_section", {"section_id": "exos"}, ctx)  # a later section opens
    skipped = run("skip_section", {"section_id": "exos"}, ctx).output
    assert skipped == "Abschnitt übersprungen. Nächster Abschnitt: „1. Einleitung“ (Lektion), id: intro."
    ctx.progress = Progress(done=frozenset({"exos"}))
    assert "schon abgeschlossen" in refusal("skip_section", {"section_id": "exos"}, ctx)
    brief = run("start_section", {"section_id": "intro"}, ctx).output
    assert brief.startswith("Abschnitt „1. Einleitung“ (Lektion)")


def test_propose_next_step_output() -> None:
    assert run("propose_next_step", {}, ctx_for(language="de")).output == (
        "Button „Nächster Schritt“ aktiviert. Beende deinen Zug und warte, bis die Schülerin oder der Schüler klickt "
        "oder antwortet."
    )


def test_a_failed_save_is_told_in_german() -> None:
    def boom(_: Progress) -> None:
        raise RuntimeError("db down")

    ctx = TurnContext.from_progress(CUR, [], None, save=boom, language="de")  # type: ignore[arg-type]
    assert refusal("start_section", {"section_id": "intro"}, ctx) == SAVE_FAILED["de"]
    assert SAVE_FAILED["de"] == "Ich konnte deinen Fortschritt nicht speichern. Versuch es noch einmal."


def test_registry_refusals_in_german() -> None:
    ctx = ctx_for(language="de")
    with pytest.raises(ToolValidationError, match=r"Ungültige JSON-Argumente: "):
        registry.execute("start_section", "{nope", ctx)
    with pytest.raises(ToolValidationError, match="Die Argumente müssen ein JSON-Objekt sein."):
        registry.execute("start_section", "[1]", ctx)
    with pytest.raises(ToolValidationError, match=r"Ungültige Argumente\. \(Basis\)|Ungültige Argumente\. section_id"):
        registry.execute("start_section", "{}", ctx)
    with pytest.raises(ToolValidationError, match="Das Werkzeug 'nope' ist hier nicht verfügbar. Verfügbare Werkzeuge: "):
        registry.execute("nope", "{}", ctx)


def test_the_declarations_of_a_german_course_are_the_french_ones() -> None:
    """Spec 021 R5: no overlay until the German probes say a description leaks."""
    for mode in ("parcours", "discussion", "revision"):
        assert registry.declarations(mode, "de") == registry.declarations(mode, "fr")  # type: ignore[arg-type]
        assert registry.realtime_declarations(mode, "de") == registry.realtime_declarations(mode, "fr")  # type: ignore[arg-type]
    assert registry.TOOL_TEXT["de"] == {}


def test_history_estimates_german_between_french_and_english() -> None:
    entries = [LearnerEntry(kind="learner", text="x" * 340), ToolEntry(kind="tool", name="t", arguments={})]
    fr, de, en = (history.estimate_tokens(entries, language) for language in ("fr", "de", "en"))  # type: ignore[arg-type]
    assert fr > de > en
    assert history.CHARS_PER_TOKEN["de"] == 3.4


def test_the_repair_request_is_in_german() -> None:
    issues = [
        ContentIssue(
            "§ 5", "section « ## 5. Vocabulaire » manquante", "pack.section_missing", {"number": 5, "text": "Fachwortschatz"}
        )
    ]
    request = _repair_message(AGENT_WORDS["de"].the_document, issues, "de")
    assert request.startswith(
        "Das Dokument hält die Regeln nicht ein:\n- § 5: Abschnitt „## 5. Fachwortschatz“ fehlt oder hat den falschen Titel"
    )
    assert request.endswith("Gib das Dokument vollständig und korrigiert noch einmal zurück.")
    path_request = _repair_message(AGENT_WORDS["de"].the_path, issues[:0], "de")
    assert path_request.endswith("Gib den Lernpfad vollständig und korrigiert noch einmal zurück.")


def test_the_reason_a_german_course_reads_is_the_catalogs_german_sentence() -> None:
    coded = ContentIssue("§ 4.2", "titre manquant", "pack.title_missing", {})
    assert issue_text(coded, "de") == "das Dokument muss mit einem Titel beginnen, „# Titel des Kapitels“"
    assert issue_text(coded, "fr") == "titre manquant"  # French is the message byte for byte
    assert issue_text(ContentIssue("x", "raw message"), "de") == "raw message"  # an uncoded one stays as written


def test_a_curriculum_title_loses_the_german_numbering_words() -> None:
    from app.domain.curriculum import curriculum_from_json

    data = curriculum("valid_de.yaml").model_dump(mode="json")
    data["title"] = "Lektion 3 – Minikapitel"
    assert curriculum_from_json(data, "de").title == "Minikapitel"
    assert curriculum_from_json(data).title == "Lektion 3 – Minikapitel"  # the French reading leaves it
    assert chapter_title("Kapitel 3: Folgen", "de") == "Folgen"

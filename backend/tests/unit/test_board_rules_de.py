"""Spec 021 R6, §4.6: the tool rules in a German course.

The other languages stay in their own files, untouched. German writes intervals as French does (outward brackets,
`;`), points with a bar (`P(2 | −1,5)`, the NRW form), a decimal comma, and groups thousands with a dot by hand
(`12.500`). One accepted and one refused sentence per `PACK_WORDS` entry, the hole phrases, the points and intervals.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import TypeAdapter

from app.domain.expression import FUNCTIONS
from app.domain.figure import Figure
from app.domain.plot import PlotBlock
from app.services.tools.figures import COORDS, DEGREES, INTERVAL, LENGTH, _bare, _number, figure_refusal
from app.services.tools.flowcharts import HOLE_WORDS, _plain_words
from app.services.tools.plots import COMMA, GROUPS, MEMBERS, PACK_WORDS, PACK_WORDS_BY_LANGUAGE, gives_away, plot_refusal
from tests.unit.test_board_rules_by_language import FLOWCHARTS, refused
from tests.unit.test_figure_models import VALID as FIGURES

DE = "de"
PLOT: TypeAdapter[PlotBlock] = TypeAdapter(PlotBlock)
FIGURE: TypeAdapter[Any] = TypeAdapter(Figure)


def P(**changes: Any) -> PlotBlock:
    base: dict[str, Any] = {"type": "plot", "x_range": [-5, 5], "y_range": [-5, 5], "x_title": "$x$", "y_title": "$y$"}
    return PLOT.validate_python({**base, **changes})


def rule(plot: PlotBlock, pack: str | None, language: str = DE) -> str | None:
    found = plot_refusal(plot, "blocks[0]", pack, language)  # type: ignore[arg-type]
    return None if found is None else found[0]


# --- the pack must name the function, in German ------------------------------------------------------------------

PACK_SENTENCES = [
    ("e^x", "Die Exponentialfunktion zur Basis $e$.", True),
    ("e^x", "$\\exp x$", True),
    ("e^x", "Die e-Funktion und ihre Ableitung.", True),
    ("e^x", "Exponentielles Wachstum einer Population.", False),
    ("e^x", "Das Wachstum ist exponentiell.", False),
    ("ln(x)", "Der natürliche Logarithmus, $\\ln x$.", True),
    ("ln(x)", "Der Logarithmus zur Basis $e$.", True),
    ("ln(x)", "Eine logarithmische Skala.", False),
    ("ln(x)", "Der Logarithmus zur Basis 10.", False),
    ("log(x)", "Der Zehnerlogarithmus.", True),
    ("log(x)", "Der dekadische Logarithmus, $\\lg x$.", True),
    ("log(x)", "Der Logarithmus zur Basis 10.", True),
    ("log(x)", "Der natürliche Logarithmus, $\\ln x$.", False),
    ("log(x)", "Eine logarithmische Skala.", False),
    ("cbrt(x)", "Die Kubikwurzel.", True),
    ("cbrt(x)", "Die dritte Wurzel aus $x$.", True),
    ("cbrt(x)", "$\\sqrt[3]{x}$", True),
    ("cbrt(x)", "Die Quadratwurzel $\\sqrt{x}$.", False),
    ("cbrt(x)", "$\\sqrt[4]{x}$", False),
    ("sin(x)", "$\\sin x$", True),
    ("sin(x)", "Der Sinus eines spitzen Winkels ist Gegenkathete durch Hypotenuse.", True),
    ("sin(x)", "Der Kosinus eines spitzen Winkels.", False),
    ("sin(x)", "$\\sinh x$ und $\\arcsin x$", False),
    ("cos(x)", "Der Kosinus.", True),
    ("cos(x)", "$\\cos x$", True),
    ("cos(x)", "Der Sinus eines spitzen Winkels.", False),
    ("cos(x)", "$\\cosh x$", False),
    ("tan(x)", "Der Tangens eines Winkels.", True),
    ("tan(x)", "$\\tan x$", True),
    ("tan(x)", "Sinus, Kosinus und Tangens.", True),
    ("tan(x)", "Die Gleichung der Tangente in A.", False),
    ("tan(x)", "Die Tangente an den Graphen im Punkt mit x = 1.", False),
    ("tan(x)", "$\\tanh x$ und $\\arctan x$", False),
]


@pytest.mark.parametrize("expr,pack,allowed", PACK_SENTENCES)
def test_the_german_pack_names_the_function_not_the_word(expr: str, pack: str, allowed: bool) -> None:
    plot = P(x_range=[0.5, 1.5], y_range=[-5, 25], curves=[{"expr": expr}])
    assert rule(plot, pack) == (None if allowed else "pack_function")


def test_every_german_entry_has_a_sentence_it_accepts_and_one_it_refuses() -> None:
    assert set(PACK_WORDS_BY_LANGUAGE["de"]) == set(PACK_WORDS) == set(FUNCTIONS) - {"sqrt", "abs"}
    named = {"e^x": "exp"}
    seen = {(named.get(expr, expr.split("(")[0]), allowed) for expr, _, allowed in PACK_SENTENCES}
    assert seen == {(name, allowed) for name in PACK_WORDS_BY_LANGUAGE["de"] for allowed in (True, False)}


def test_each_languages_pack_licenses_only_its_own_words() -> None:
    plot = P(x_range=[0.5, 1.5], y_range=[-5, 25], curves=[{"expr": "ln(x)"}])
    assert rule(plot, "Der natürliche Logarithmus") is None
    assert rule(plot, "De natuurlijke logaritme") == "pack_function"
    assert rule(plot, "Le logarithme népérien") == "pack_function"
    assert rule(plot, "Der natürliche Logarithmus", "fr") == "pack_function"


# --- what an open exercise may not show -------------------------------------------------------------------------


def test_the_member_separators() -> None:
    assert COMMA["de"] is COMMA["fr"] and GROUPS["de"] is GROUPS["en"]
    assert MEMBERS["de"].split("2 | 3") == ["2 ", " 3"] and MEMBERS["de"].split("2 ; 3") == ["2 ", " 3"]


@pytest.mark.parametrize(
    ("text", "gives"),
    [
        ("S(2 | 3)", True),
        ("$S(2 \\mid 3)$", True),
        ("$S(2 \\vert -1{,}5)$", True),
        ("(x_S | 2)", True),
        ("(2 ; 3)", True),
        ("(1, 4)", True),
        ("]2 ; 3[", True),
        ("[0 ; 5]", True),
        ("]−∞ ; 2]", True),
        ("(2, 5]", True),
        ("(0,5)", False),
        ("(cm | s)", False),
        ("$f$", False),
        ("Weg (m)", False),
        ("f(x) = 2", True),
    ],
)
def test_gives_away_in_german(text: str, gives: bool) -> None:
    assert gives_away(text, DE) is gives


def test_a_bar_point_is_german_only() -> None:
    """The structural fix of §4.3: a bar is a member separator in German and nowhere else."""
    assert gives_away("S(2 | 3)", "de") is True
    for language in ("fr", "en", "nl"):
        assert gives_away("S(2 | 3)", language) is False


# --- hand-written notation in a figure ---------------------------------------------------------------------------


def figure(base: str, language: str = DE, **changes: Any) -> tuple[str, str] | None:
    return figure_refusal(FIGURE.validate_python({**FIGURES[base], **changes}), "blocks[0]", language)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "label",
    ["A = ]2 ; 3[", "B = ]2, 3[", "$[0 ; 5]$", "$]-\\infty ; 2]$", "P(2 | 3)", "$P(2 \\mid -1{,}5)$", "P = (2 ; 3)", "P = (2, 3)"],
)
def test_a_hand_written_interval_or_point_is_refused_in_a_german_caption(label: str) -> None:
    found = figure("sets", caption=label)
    assert found is not None and found[0] == "label_notation", (label, found)


@pytest.mark.parametrize("caption", ["Die Mengen A und B", "Eine Menge mit 12 Elementen", "Abbildung 3", "Betrag |x|"])
def test_a_german_caption_is_not_read_as_notation(caption: str) -> None:
    assert figure("sets", caption=caption) is None


def test_the_patterns_are_recognised() -> None:
    for text in ("]2 ; 3[", "]2, 3[", "[0 ; 5]", "]−∞ ; 2]", "[2 ; 5[", "(2 ; 3)"):
        assert INTERVAL["de"].search(_bare(text)), text
    for text in ("P(2 | −1,5)", "(2|3)", "(2 ; −1,5)", "(2, 3)", "(−3 ; 4)"):
        assert COORDS["de"].search(_bare(text)), text
    assert not COORDS["de"].search(_bare("Der Kreis")) and not COORDS["de"].search(_bare("(|x|)"))
    assert not COORDS["fr"].search(_bare("P(2 | 3)"))  # the bar is German


# --- numbers -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "value"),
    [("2,5", 2.5), ("12", 12.0), ("0,45", 0.45), ("12.500", 12500.0), ("1.500,5", 1500.5), ("0.125", 0.125), ("10000", 10000.0), ("1000,5", 1000.5)],
)
def test_a_german_number_has_a_decimal_comma_and_dot_thousands(text: str, value: float) -> None:
    assert _number(text, DE) == value


def test_measures_are_read_the_german_way() -> None:
    assert DEGREES["de"].match("37,5°") and LENGTH["de"].match("3,5cm")
    found = LENGTH["de"].match("1.500m")
    assert found and _number(found.group(1), DE) * 1000 == 1_500_000  # 1.500 m is 1500 m


# --- flowchart holes ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Auszufüllen", "auszufüllen", "Noch auszufüllen", "Ergänze", "Ergänzen", "Zu ergänzen", "??? zu bestimmen",
        "zu finden", "Fehlender Schritt", "fehlt", "Schritt fehlt", "Kasten 3", "Kasten 3 auszufüllen", "Lücke",
        "leer", "leeres Feld", "Versteckter Schritt", "unbekannt", "Unbekannter Wert", "tbd",
        "Wert fehlt", "Feld nr 2", "Kasten 3 von dir auszufüllen", "Von dir zu ergänzen",
    ],
)
def test_a_german_hole_phrase_is_a_hole(text: str) -> None:
    assert HOLE_WORDS["de"].fullmatch(_plain_words(text)), text


@pytest.mark.parametrize(
    "text",
    ["Ist der Quotient konstant?", "Berechne die Differenz", "Trage den Term in die Tabelle ein", "Schritt ausführen", "Ja", "Ende"],
)
def test_an_ordinary_german_step_is_not_a_hole(text: str) -> None:
    assert not HOLE_WORDS["de"].fullmatch(_plain_words(text)), text


def test_a_hole_in_a_flowchart_is_refused_through_the_tool_in_german() -> None:
    def with_text(text: str) -> dict[str, Any]:
        nodes = [dict(n) for n in FLOWCHARTS["method"]["nodes"]]
        nodes[2]["text"] = text
        return {**FLOWCHARTS["method"], "nodes": nodes}

    assert "marque un trou" in (refused(with_text("Auszufüllen"), DE) or "")
    assert refused(with_text("Ist der Quotient konstant?"), DE) is None
    assert refused(with_text("In te vullen"), DE) is None  # a Dutch hole is not a German one

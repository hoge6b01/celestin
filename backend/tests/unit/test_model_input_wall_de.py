"""Spec 021 R2, task 5.5: the wall around the model, with four course languages.

`test_model_input_wall.py` pins the French and the English halves and `test_model_input_wall_nl.py` the Dutch one; this
adds German: a German course hands the provider the same input whatever the account's interface language, and a French,
an English, a Dutch and a German course hand it four different inputs, each equal to its own pinned rendering."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.domain.locale import LOCALES
from tests.unit.test_model_input_wall import _developer_text, _run

RENDER = Path(__file__).parents[1] / "fixtures" / "render"


def _dump(calls: list) -> str:
    return json.dumps(calls, ensure_ascii=False, sort_keys=True)


async def test_the_provider_gets_the_same_input_whatever_the_interface_language_of_a_german_course(make_client) -> None:
    runs = [_dump(await _run(make_client, locale, language="de")) for locale in LOCALES]
    assert len(runs) == 4 and len(set(runs)) == 1


async def test_four_courses_hand_the_provider_four_different_inputs_each_equal_to_its_pin(make_client) -> None:
    french = await _run(make_client, "de", language="fr")  # a German interface on each course
    english = await _run(make_client, "de", language="en")
    dutch = await _run(make_client, "de", language="nl")
    german = await _run(make_client, "de", language="de")
    assert len({_dump(french), _dump(english), _dump(dutch), _dump(german)}) == 4
    sha = lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest()  # noqa: E731
    assert sha(_developer_text(french)) == (RENDER / "system_text_sha.txt").read_text().strip()
    assert sha(_developer_text(english)) == (RENDER / "system_text_sha_en.txt").read_text().strip()
    assert sha(_developer_text(dutch)) == (RENDER / "system_text_sha_nl.txt").read_text().strip()
    assert sha(_developer_text(german)) == (RENDER / "system_text_sha_de.txt").read_text().strip()
    assert "Lernpfad des Kapitels" in _developer_text(german)
    assert "Stand des Lernpfads" in german[0]["input"][-1]["content"][0]["text"]
    for other in ("Parcours du chapitre", "Chapter path", "Traject van het hoofdstuk"):
        assert other not in _developer_text(german)

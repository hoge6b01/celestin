"""Spec 021 task 5.7: a photo of a German student's work is read with the German prompt and the German marks."""

from __future__ import annotations

from types import SimpleNamespace

from app.api.routes.work import _NOTHING
from app.config import Settings
from app.services.work_reading import _DOUBT, _PHOTO_LABEL, WorkReader
from tests.fixtures.fake_completion import FakeCompletion, text
from tests.unit.test_authoring_agent_de import PROMPTS


class _Documents:
    async def prepare(self, photos, *, min_pixels):  # noqa: ANN001, ANN201
        return SimpleNamespace(pages=[SimpleNamespace(data_url="data:image/jpeg;base64,AA==", jpeg=b"AA")])


def reader(fake: FakeCompletion) -> WorkReader:
    settings = Settings(openai_api_key="k", _env_file=None)
    return WorkReader(fake, _Documents(), PROMPTS, settings, SimpleNamespace(config=None))  # type: ignore[arg-type]


async def test_the_photo_is_read_with_the_german_prompt_and_label() -> None:
    fake = FakeCompletion([text("$x + 3 = 7$\n$x = 7 - 3 = 4$\n[unsicher: 4 oder 9]")])
    result = await reader(fake).read(b"photo", "de", "u1")
    assert result.startswith("$x + 3 = 7$") and "[unsicher: 4 oder 9]" in result
    (call,) = fake.calls
    assert call["instructions"] == [PROMPTS.work("de")]
    assert call["input"][0]["content"][0]["text"] == _PHOTO_LABEL["de"] == (
        "Hier ist das Foto der Arbeit der Schülerin oder des Schülers."
    )


def test_the_german_marks_are_recognised_by_the_route_and_the_log() -> None:
    assert {"[nichts lesbar]", "[niets leesbaar]", "[rien de lisible]", "[nothing legible]"} <= _NOTHING
    assert len(_DOUBT.findall("a [unsicher: 1 oder 7] b [onzeker: 1 | 7] c [uncertain: 2 | 3] d [incertain: 4 | 5]")) == 4

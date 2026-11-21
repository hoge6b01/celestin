"""Spec 021 R2, R3, R4, task 8.2: a German course end to end over HTTP, against the scripted providers. The Dutch
equivalent is `test_dutch_course.py`, the English one `test_english_course.py`."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.providers.base import Completed, TextDelta
from tests.conftest import CHAPTER_ID, COURSE_ID, LESSON, sign_in, use_fake_authoring
from tests.fixtures.fake_completion import data, text
from tests.fixtures.fake_llm import FakeLLM
from tests.integration.test_courses_endpoint import _upload
from tests.unit.test_authoring_agent_de import DUTCH_PACK, ENGLISH_PACK, FRENCH_PACK, PACK, PROMPTS, curriculum_for

READ = text("--- page 1 ---\n" + "Die eingefügte deutsche Lektion über lineare Funktionen. " * 20)
AUTHOR = [text(PACK), data(curriculum_for(PACK))]
SUBJECTS = ("mathematics", "sciences", "languages", "general")


async def _german_course(client: AsyncClient, subject: str = "mathematics") -> str:
    created = await client.post("/api/courses", json={"name": "Mathematik", "subject": subject, "language": "de"})
    assert created.status_code == 201, created.text
    assert created.json()["language"] == "de"
    return created.json()["id"]


async def _ready_chapter(client: AsyncClient) -> tuple[str, str, object]:
    fake = use_fake_authoring(client.app, [READ, *AUTHOR])
    course_id = await _german_course(client)
    chapter_id = (await _upload(client, course_id)).json()["id"]
    await client.app.state.authoring.wait_idle()
    return course_id, chapter_id, fake


@pytest.mark.parametrize("subject", SUBJECTS)
async def test_every_subject_takes_a_german_course(client: AsyncClient, subject: str) -> None:
    course_id = await _german_course(client, subject)
    assert (await client.get(f"/api/courses/{course_id}")).json()["language"] == "de"
    assert {c["id"]: c["language"] for c in (await client.get("/api/courses")).json()["courses"]}[course_id] == "de"


async def test_german_is_offered_for_every_subject(client: AsyncClient) -> None:
    subjects = (await client.get("/api/subjects")).json()["subjects"]
    assert [s["id"] for s in subjects] == list(SUBJECTS)
    assert all("de" in s["languages"] for s in subjects)


@pytest.mark.parametrize("language", ["es", "de-DE", "DE", ""])
async def test_an_unsupported_german_spelling_is_refused(client: AsyncClient, language: str) -> None:
    r = await client.post("/api/courses", json={"name": "X", "subject": "sciences", "language": language})
    assert r.status_code == 422 and r.json()["code"] == "invalid_language"


async def test_the_language_of_a_german_course_cannot_be_changed(client: AsyncClient) -> None:
    course_id = await _german_course(client)
    for language in ("fr", "en", "nl"):
        r = await client.patch(f"/api/courses/{course_id}", json={"name": "Mathematik", "language": language})
        assert r.status_code == 422
    assert (await client.get(f"/api/courses/{course_id}")).json()["language"] == "de"


async def test_a_german_document_becomes_a_german_chapter(client: AsyncClient) -> None:
    course_id, chapter_id, fake = await _ready_chapter(client)
    assert fake.calls[0]["instructions"] == [PROMPTS.transcribe("de")]  # type: ignore[attr-defined]
    assert fake.calls[1]["instructions"][0] == PROMPTS.authoring_pack("de")  # type: ignore[attr-defined]
    detail = (await client.get(f"/api/courses/{course_id}")).json()
    (row,) = detail["chapters"]
    assert detail["language"] == "de" and row["ready"] and row["title"] == "Lineare Funktionen"
    lesson = (await client.get(f"/api/courses/{course_id}/chapters/{chapter_id}")).json()
    assert lesson["language"] == "de" and [s["id"] for s in lesson["sections"]] == ["definition", "graphen"]
    content = (await client.get(f"/api/courses/{course_id}/chapters/{chapter_id}/content")).json()
    assert content["language"] == "de" and content["pack"].startswith("# Lineare Funktionen")


async def test_a_german_pack_edit_is_validated_against_the_german_template(client: AsyncClient) -> None:
    course_id, chapter_id, _ = await _ready_chapter(client)
    url = f"/api/courses/{course_id}/chapters/{chapter_id}"
    content = (await client.get(f"{url}/content")).json()
    edited = content["pack"].replace("Lineare Funktionen", "Lineare Funktionen, überarbeitet", 1)
    saved = await client.put(f"{url}/pack", json={"version": content["version"], "pack": edited})
    assert saved.status_code == 200, saved.text
    assert saved.json()["pack"].startswith("# Lineare Funktionen, überarbeitet")


@pytest.mark.parametrize(
    ("pack", "french", "german"),
    [
        (
            FRENCH_PACK,
            "le document suit le modèle en français, mais ce cours est en allemand",
            "das Dokument folgt der Vorlage auf Französisch, aber dieser Kurs ist auf Deutsch",
        ),
        (
            ENGLISH_PACK,
            "le document suit le modèle en anglais, mais ce cours est en allemand",
            "das Dokument folgt der Vorlage auf Englisch, aber dieser Kurs ist auf Deutsch",
        ),
        (
            DUTCH_PACK,
            "le document suit le modèle en néerlandais, mais ce cours est en allemand",
            "das Dokument folgt der Vorlage auf Niederländisch, aber dieser Kurs ist auf Deutsch",
        ),
    ],
)
async def test_a_pack_in_another_language_is_a_language_mismatch(
    client: AsyncClient, pack: str, french: str, german: str
) -> None:
    course_id, chapter_id, _ = await _ready_chapter(client)
    url = f"/api/courses/{course_id}/chapters/{chapter_id}"
    content = (await client.get(f"{url}/content")).json()
    refused = await client.put(f"{url}/pack", json={"version": content["version"], "pack": pack})
    assert refused.status_code == 422 and refused.json()["code"] == "content_invalid"
    assert refused.json()["issues"][0]["message"] == french
    await client.patch("/api/auth/me", json={"locale": "de"})  # the account's language, not the course's
    again = await client.put(f"{url}/pack", json={"version": content["version"], "pack": pack})
    assert again.json()["issues"][0]["message"] == german
    assert (await client.get(f"{url}/content")).json()["version"] == content["version"]  # nothing changed


async def test_the_french_course_refuses_a_german_pack(client: AsyncClient) -> None:
    url = f"/api/courses/{COURSE_ID}/chapters/{CHAPTER_ID}"
    content = (await client.get(f"{url}/content")).json()
    refused = await client.put(f"{url}/pack", json={"version": content["version"], "pack": PACK})
    assert refused.status_code == 422
    assert refused.json()["issues"][0]["message"] == "le document suit le modèle en allemand, mais ce cours est en français"


# --- the tutor ------------------------------------------------------------------------------------------------


async def test_a_german_turn_is_built_from_the_german_prompt_files(make_client) -> None:
    llm = FakeLLM([[TextDelta("Hallo!"), Completed(usage={"input_tokens": 9})]])
    client, _ = make_client(llm, language="de")
    async with client:
        r = await client.post("/api/chat", json={"course_id": client.course_id, "chapter_id": client.chapter_id, "message": None})
        assert r.status_code == 200, r.text
    system = llm.calls[0]["input"][0]["content"][0]["text"]
    assert "Du bist Célestin" in system and "## Das Fach: Mathematik" in system
    assert "Tu es Célestin" not in system and "You are Célestin" not in system and "Je bent Célestin" not in system
    trailing = llm.calls[0]["input"][-1]["content"][0]["text"]
    assert "Stand des Lernpfads" in trailing


async def test_a_german_discussion_is_a_german_prefix_with_the_board_tools_only(make_client) -> None:
    llm = FakeLLM([[TextDelta("Erzähl."), Completed(usage={"input_tokens": 9})]])
    client, _ = make_client(llm, language="de")
    async with client:
        url = f"/api/courses/{client.course_id}/chapters/{client.chapter_id}/discussion"
        started = await client.post(url)
        assert started.status_code == 201, started.text
        r = await client.post(
            "/api/discussion/turn",
            json={
                "course_id": client.course_id,
                "chapter_id": client.chapter_id,
                "conversation_id": started.json()["conversation"]["id"],
                "message": "Was ist eine Folge?",
            },
        )
        assert r.status_code == 200, r.text
    system = llm.calls[0]["input"][0]["content"][0]["text"]
    assert "Du bist Célestin" in system and "## Das Gespräch" in system and "Hier gibt es keinen Lernpfad" in system
    assert {t["name"] for t in llm.tools} == {"display_board", "clear_board"}


# --- privacy --------------------------------------------------------------------------------------------------


async def test_another_students_german_course_is_a_404(client: AsyncClient) -> None:
    course_id, chapter_id, _ = await _ready_chapter(client)
    _, other = sign_in(client.app, email="bob@example.de", name="Bob", lesson=False)
    url = f"/api/courses/{course_id}"
    for target in (url, f"{url}/chapters/{chapter_id}", f"{url}/chapters/{chapter_id}/content"):
        assert (await client.get(target, headers=other)).status_code == 404, target
    turn = await client.post("/api/chat", json={"course_id": course_id, "chapter_id": chapter_id, "message": None}, headers=other)
    assert turn.status_code == 404
    assert (await client.get("/api/courses", headers=other)).json() == {"courses": []}
    assert LESSON["course_id"] == COURSE_ID

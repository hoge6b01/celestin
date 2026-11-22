"""Spec 021 task 4.4: the runner authors a German course from a document and stores a valid German chapter (the
HTTP end-to-end is `tests/integration/test_german_course.py`, once German is offered, spec 021 phase 8)."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.db.repositories import Repositories
from app.services.ai_settings import load_ai_config
from app.services.authoring.agent import AuthoringAgent
from app.services.authoring.runner import AuthoringRunner
from tests.fixtures.fake_clients import FixedAiConfig
from tests.fixtures.fake_completion import FakeCompletion, data, text
from tests.unit.test_authoring_agent_de import PACK, PROMPTS, curriculum_for
from tests.unit.test_authoring_runner import document

READ = text("--- page 1 ---\n" + "Die eingefügte deutsche Lektion über lineare Funktionen. " * 20)



@pytest.fixture
def world(repos: Repositories):
    user = repos.users.create("a@b.de", "Lea", "h")
    course = repos.courses.create(user.id, "Mathematik", "mathematics", max_courses=30, language="de")
    return repos, user, course


def runner(repos: Repositories, script) -> tuple[AuthoringRunner, FakeCompletion]:
    fake = FakeCompletion(script)
    settings = Settings(openai_api_key="k", _env_file=None)
    ai = FixedAiConfig(load_ai_config(settings))
    return AuthoringRunner(AuthoringAgent(fake, PROMPTS, settings, ai), repos, settings, ai), fake  # type: ignore[arg-type]


async def test_a_german_document_becomes_a_ready_german_chapter(world) -> None:
    repos, user, course = world
    r, fake = runner(repos, [READ, text(PACK), data(curriculum_for(PACK))])
    chapter = await r.start_document(user, course, None, document())
    await r.wait_idle()
    owned = repos.chapters.get_owned(user.id, course.id, chapter.id)
    assert owned is not None and owned.course.language == "de"
    assert owned.chapter.authoring_state == "idle" and owned.chapter.ready
    assert owned.chapter.title == "Lineare Funktionen"
    assert owned.chapter.pack.startswith("# Lineare Funktionen")
    assert fake.calls[0]["instructions"] == [PROMPTS.transcribe("de")]
    assert fake.calls[1]["instructions"][0] == PROMPTS.authoring_pack("de")


async def test_a_french_pack_for_a_german_course_fails_the_run_after_its_repairs(world) -> None:
    from tests.unit.test_authoring_agent_de import FRENCH_PACK

    repos, user, course = world
    r, _ = runner(repos, [READ, text(FRENCH_PACK), text(FRENCH_PACK), text(FRENCH_PACK)])
    chapter = await r.start_document(user, course, None, document())
    await r.wait_idle()
    owned = repos.chapters.get_owned(user.id, course.id, chapter.id)
    assert owned is not None and owned.chapter.authoring_state == "failed" and owned.chapter.authoring_error == "unstructured"

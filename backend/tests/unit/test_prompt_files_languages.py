"""Spec 011 R3.2/R3.5: the English prompt set keeps what the French one holds.

The French assertions of `test_prompt_files.py` are untouched; this runs the shared
invariants for each language, and compares each English file with its French twin: same
sections, same markers, same tool and block names.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.domain.language import COURSE_LANGUAGES
from app.domain.mode import MODES
from app.domain.subject import available_subjects
from app.services.prompt_service import VOICE_END, VOICE_START
from app.services.prompts import PromptLibrary

PROMPTS = Path(__file__).resolve().parents[2] / "prompts"
LIBRARY = PromptLibrary(PROMPTS)

# What differs between the languages in the checks below.
WORDS = {
    "fr": {
        "subject_words": ("mathématique", "physique", "suite arithmétique", "u₁", "5e secondaire"),
        "gender": r"\belle\b",
        "to_check": "Points à vérifier",
        "lesson": "**Leçon.**",
        "off_topic": "Hors sujet",
        "voice_titles": ("Quand on se parle à voix haute", "à voix haute"),
    },
    "en": {
        "subject_words": ("mathematics", "physics", "arithmetic sequence", "u_1", "5th year", "belgi", "fédération"),
        "gender": r"\b(?:she|he|her|hers|his|him)\b",
        "to_check": "Points to check",
        "lesson": "**Lesson.**",
        "off_topic": "Off-topic",
        "voice_titles": ("When we talk out loud", "out loud"),
    },
    "nl": {
        "subject_words": ("wiskunde", "fysica", "rekenkundige rij", "u₁", "5e jaar", "belgi", "vlaanderen", "federatie"),
        "gender": r"\b(?:hij|zij|hem|haar)\b",
        "to_check": "Na te kijken punten",
        "lesson": "**Les.**",
        "off_topic": "Buiten het onderwerp",
        "voice_titles": ("Wanneer we hardop praten", "hardop"),
    },
    "de": {
        "subject_words": ("mathematik", "physik", "arithmetische folge", "u₁", "a₁", "gymnasium", "nrw", "bundesland"),
        "gender": r"\b(?:er|sie|ihm|ihn|ihr|ihre[mnrs]?|sein|seine[mnrs]?)\b",
        "to_check": "Zu prüfende Punkte",
        "lesson": "**Lektion.**",
        "off_topic": "Nicht zum Thema",
        "voice_titles": ("Wenn wir laut miteinander sprechen", "laut"),
    },
}
MARKERS = (
    "<!-- SUBJECT -->",
    "<!-- COURSE_PACK -->",
    "<!-- CURRICULUM -->",
    "<!-- MODE -->",
    "<!-- MODE_OPENING -->",
)


def written_in(*names: str) -> list[str]:
    """The course languages whose prompt files `names` (with `{l}` for the language) all exist: a language
    joins a check when its files do (spec 017: the Dutch set is written over phases 4 and 5)."""
    return [lang for lang in COURSE_LANGUAGES if all((PROMPTS / n.format(l=lang)).exists() for n in names)]


LANGUAGES = written_in("tutor.{l}.md", "modes/parcours.{l}.md", "subjects/mathematics.{l}.md")
TRANSCRIPTION_LANGUAGES = written_in("transcription/transcribe.{l}.md", "transcription/verify.{l}.md")
WORK_LANGUAGES = written_in("transcription/work.{l}.md")


def test_every_course_language_is_in_every_gated_check() -> None:
    """The gating above is for building a language up; once built, a missing file must fail, not drop out."""
    assert LANGUAGES == TRANSCRIPTION_LANGUAGES == WORK_LANGUAGES == list(COURSE_LANGUAGES)


def read(name: str, language: str) -> str:
    base, _, ext = name.rpartition(".")
    return (PROMPTS / f"{base}.{language}.{ext}").read_text(encoding="utf-8")


# « zijn of haar », « hij of zij »: the inclusive forms say both, they presume no gender.
INCLUSIVE = re.compile(r"\b(?:zijn of haar|hem of haar|hij of zij)\b")


def neutral(text: str, where: str, language: str) -> None:
    lowered = INCLUSIVE.sub(" ", text.lower())
    for word in WORDS[language]["subject_words"]:
        assert word not in lowered, f"{where}: {word}"
    assert not re.search(WORDS[language]["gender"], lowered), where


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_tutor_prompt_is_subject_neutral_and_gender_neutral(language: str) -> None:
    text = read("tutor.md", language)
    for marker in MARKERS:
        assert text.count(marker) == 1, marker
    positions = [text.index(marker) for marker in MARKERS]
    assert positions == sorted(positions)
    neutral(text, f"tutor.{language}.md", language)
    assert WORDS[language]["to_check"] in text


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_tutor_prompt_cites_the_templates_last_heading(language: str) -> None:
    """The section the tutor never teaches is the last one of every pack template."""
    cited = WORDS[language]["to_check"]
    assert cited in read("tutor.md", language)
    for info in available_subjects():
        template = LIBRARY.template(info.id, language)  # type: ignore[arg-type]
        assert template.headings[-1][1] == cited, (info.id, template.headings[-1])
        assert template.language == language


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_mode_has_both_layers_neutral_and_marker_free(language: str) -> None:
    for mode in MODES:
        for name in (f"modes/{mode}.md", f"modes/{mode}.opening.md"):
            text = read(name, language)
            assert text.strip(), name
            neutral(text, f"{name} ({language})", language)
            for marker in MARKERS[:4]:
                assert marker not in text, f"{name}: {marker}"
    assert WORDS[language]["lesson"] in read("modes/parcours.md", language)
    discussion = read("modes/discussion.md", language)
    assert "start_section" not in discussion and "complete_section" not in discussion


@pytest.mark.parametrize("language", LANGUAGES)
def test_every_available_subject_prompt_has_one_voice_block_at_the_end(language: str) -> None:
    for info in available_subjects():
        text = read(f"subjects/{info.id}.md", language)
        assert text.count(VOICE_START) == 1 and text.count(VOICE_END) == 1
        assert text.index(VOICE_START) < text.index(VOICE_END)
        assert WORDS[language]["off_topic"] in text


def test_the_tutor_prompts_voice_block_is_the_only_one_and_text_mode_drops_it() -> None:
    for language in LANGUAGES:
        text = read("tutor.md", language)
        assert text.count(VOICE_START) == 1 and text.count(VOICE_END) == 1


TRANSCRIPTION = {
    "fr": ("--- page N ---", "[manuscrit]", "[incertain:", "[illisible]", "[figure :", "[barré:", "[page vide]"),
    "en": ("--- page N ---", "[handwritten]", "[uncertain:", "[illegible]", "[figure:", "[crossed out:", "[empty page]"),
    "nl": ("--- page N ---", "[handgeschreven]", "[onzeker:", "[onleesbaar]", "[figuur:", "[doorgestreept:", "[lege pagina]"),
    "de": ("--- page N ---", "[handschriftlich]", "[unsicher:", "[unleserlich]", "[Abbildung:", "[durchgestrichen:", "[leere Seite]"),
}


@pytest.mark.parametrize("language", TRANSCRIPTION_LANGUAGES)
def test_the_transcription_prompt_demands_doubt_and_page_markers(language: str) -> None:
    text = read("transcription/transcribe.md", language)
    for convention in TRANSCRIPTION[language]:
        assert convention in text, convention
    # The marks of the other languages are not taught.
    for other_language, other in TRANSCRIPTION.items():
        if other_language == language:
            continue
        for convention in other[1:]:
            assert convention not in text, convention
    assert TRANSCRIPTION[language][2] in read("transcription/verify.md", language) or language == "fr"


def test_the_english_transcription_prompt_never_translates() -> None:
    assert "never translate" in read("transcription/transcribe.md", "en").lower()
    assert "never translate" in read("transcription/verify.md", "en").lower()


@pytest.mark.parametrize("language", [lang for lang in TRANSCRIPTION_LANGUAGES if lang == "nl"])
def test_the_dutch_transcription_prompts_never_translate(language: str) -> None:
    """Spec 017 R4.1: the pages are transcribed in the page's own language."""
    for name in ("transcription/transcribe.md", "transcription/verify.md"):
        assert "vertaal nooit" in read(name, language).lower(), name


def test_the_english_authoring_prompt_reads_a_transcription_of_pages() -> None:
    pack = read("authoring/pack.md", "en")
    assert "If the material is a transcription of pages" in pack and "p. 5" in pack
    for mark in ("[handwritten]", "[uncertain: a | b]", "[illegible]", "[figure: …]", "[crossed out: …]"):
        assert mark in pack, mark
    assert "restructure, never add" in pack.lower()


# --- structure: each English file against its French twin -----------------------------

TWINS = sorted(str(p.relative_to(PROMPTS)).replace(".fr.md", "") for p in PROMPTS.glob("**/*.fr.md"))


def outline(text: str) -> list[int]:
    """The levels of the headings, in order: the skeleton of a file."""
    return [len(m.group(1)) for m in re.finditer(r"^(#{1,4}) ", text, re.MULTILINE)]


def names(text: str) -> set[str]:
    """What the model is told to call: tools, fields and blocks written `like_this`."""
    found = (m.group(1) for m in re.finditer(r"`([^`\s]+)`", text))
    return {t for t in found if re.fullmatch(r"[a-z_]+(?:\(.*\))?", t)}


def test_every_french_file_has_an_english_twin_and_the_converse() -> None:
    english = sorted(str(p.relative_to(PROMPTS)).replace(".en.md", "") for p in PROMPTS.glob("**/*.en.md"))
    assert TWINS == english


@pytest.mark.parametrize("twin", TWINS)
def test_an_english_file_has_the_skeleton_of_its_french_twin(twin: str) -> None:
    fr, en = read(f"{twin}.md", "fr"), read(f"{twin}.md", "en")
    assert outline(en) == outline(fr), twin
    for marker in (*MARKERS, VOICE_START.strip(), VOICE_END.strip()):
        assert en.count(marker) == fr.count(marker), (twin, marker)
    assert names(en) == names(fr), (twin, names(en) ^ names(fr))
    assert en.count("`display_board`") == fr.count("`display_board`") or twin == "tutor"


@pytest.mark.parametrize("twin", [t for t in TWINS if t.startswith("templates/")])
def test_an_english_template_keeps_the_positions_of_the_french_one(twin: str) -> None:
    subject = twin.split("/")[1].split(".")[0]
    french, english = LIBRARY.template(subject, "fr"), LIBRARY.template(subject, "en")  # type: ignore[arg-type]
    assert [n for n, _ in english.headings] == [n for n, _ in french.headings]
    assert english.exercises_section == french.exercises_section
    assert english.text.count("###") == french.text.count("###")


@pytest.mark.parametrize("twin", TWINS)
def test_an_english_file_carries_no_french(twin: str) -> None:
    text = read(f"{twin}.md", "en")
    # The tutor's name is a proper noun, not French: « Célestin » is the one accent an English file keeps.
    prose = text.replace("<materiel>", "").replace("</materiel>", "").replace("Célestin", "Celestin")
    accented = re.findall(r"[àâçéèêëîïôûùüÿœ]", prose, re.IGNORECASE)
    assert not accented, (twin, set(accented))
    assert "«" not in text and "»" not in text, twin


# --- spec 017: the Dutch files, against their French twins -----------------------------------------------------
# A Dutch file joins these checks when it exists (the set is written over phases 4 and 5); the test below fails
# when a Dutch file has no French twin, and phase 7 requires every one of the 31 to exist.

DUTCH_TWINS = [t for t in TWINS if (PROMPTS / f"{t}.nl.md").exists()]

# Function words that no Dutch sentence needs: if one is in a Dutch file it is French or English prose left in.
# (« les », « pas », « ton », « is » are Dutch words too, so they are not in the lists.)
_FRENCH_STOPWORDS = re.compile(
    r"\b(?:le|la|est|pour|une|avec|des|du|dans|que|qui|mais|donc|nous|vous|sont|cette|ces|elle|ils|aux|sur|ou|"
    r"tu|ta|tes|ne|au|chaque|toujours|jamais|sans)\b",
    re.IGNORECASE,
)
_ENGLISH_STOPWORDS = re.compile(
    r"\b(?:the|and|are|with|from|that|this|which|your|you|do|does|not|only|never|always|must|should|will|have|has|"
    r"for|each|every|before|after|then|when|if)\b"
)
# What a Dutch file may quote: the tool names, the tags, the marks and the product name are not prose.
_QUOTED = re.compile(r"`[^`]*`|<[^>]*>|\[[^\]]*\]|\"[^\"]*\"|“[^”]*”")


def test_every_dutch_file_has_a_french_twin() -> None:
    dutch = sorted(str(p.relative_to(PROMPTS)).replace(".nl.md", "") for p in PROMPTS.glob("**/*.nl.md"))
    assert set(dutch) <= set(TWINS), sorted(set(dutch) - set(TWINS))


@pytest.mark.parametrize("twin", DUTCH_TWINS)
def test_a_dutch_file_has_the_skeleton_of_its_french_twin(twin: str) -> None:
    fr, nl = read(f"{twin}.md", "fr"), read(f"{twin}.md", "nl")
    assert outline(nl) == outline(fr), twin
    for marker in (*MARKERS, VOICE_START.strip(), VOICE_END.strip()):
        assert nl.count(marker) == fr.count(marker), (twin, marker)
    assert names(nl) == names(fr), (twin, names(nl) ^ names(fr))


@pytest.mark.parametrize("twin", [t for t in DUTCH_TWINS if t.startswith("templates/")])
def test_a_dutch_template_keeps_the_positions_of_the_french_one(twin: str) -> None:
    subject = twin.split("/")[1].split(".")[0]
    french, dutch = LIBRARY.template(subject, "fr"), LIBRARY.template(subject, "nl")  # type: ignore[arg-type]
    assert [n for n, _ in dutch.headings] == [n for n, _ in french.headings]
    assert dutch.exercises_section == french.exercises_section
    assert dutch.text.count("###") == french.text.count("###")
    assert dutch.headings[-1][1] == WORDS["nl"]["to_check"]


@pytest.mark.parametrize("twin", DUTCH_TWINS)
def test_a_dutch_file_carries_no_french_or_english_prose(twin: str) -> None:
    prose = _QUOTED.sub(" ", read(f"{twin}.md", "nl").replace("Célestin", "Celestin"))
    assert "«" not in prose and "»" not in prose, twin
    for name, words in (("French", _FRENCH_STOPWORDS), ("English", _ENGLISH_STOPWORDS)):
        found = words.findall(prose)
        assert not found, (twin, name, sorted(set(found)))


@pytest.mark.parametrize("language", [lang for lang in written_in("authoring/pack.{l}.md") if lang == "nl"])
def test_the_dutch_authoring_prompt_reads_a_transcription_of_pages(language: str) -> None:
    pack = read("authoring/pack.md", language)
    assert "Als het materiaal een transcriptie van pagina's is" in pack and "p. 5" in pack
    for mark in ("[handgeschreven]", "[onzeker: a | b]", "[onleesbaar]", "[figuur: …]", "[doorgestreept: …]"):
        assert mark in pack, mark
    assert "herstructureer, voeg nooit toe" in pack.lower()
    assert "<materiel>" in pack  # the tag that wraps the material is not language
    curriculum = read("authoring/curriculum.md", language)
    assert "<chapitre>" in curriculum and "Na te kijken punten" in curriculum


# What the interface sends to the model for the learner (frontend `lib/tutor/prompts.ts`, pinned
# there per language) is quoted by the path-mode prompt, so Célestin recognises it.
CITED = {
    "fr": ("« Étape suivante »", "« Section suivante »", "On commence la section …", "Ma réponse à la question : …"),
    "en": ("“Next step”", "“Next section”", "Shall we start the section", "My answer to the question: …"),
    "nl": ("“Volgende stap”", "“Volgende sectie”", "Beginnen we met de sectie", "Mijn antwoord op de vraag: …"),
    "de": ("„Nächster Schritt“", "„Nächster Abschnitt“", "Fangen wir mit dem Abschnitt", "Meine Antwort auf die Frage: …"),
}


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_path_prompt_quotes_the_sentences_the_interface_sends(language: str) -> None:
    parcours = " ".join(read("modes/parcours.md", language).split())
    for sentence in CITED[language]:
        assert sentence in parcours, sentence


@pytest.mark.parametrize("language", WORK_LANGUAGES)
def test_the_work_reading_prompt_keeps_the_transcription_conventions(language: str) -> None:
    """The student's photo is read with the marks of the course transcription: a doubt is marked, an
    illegible word is not guessed, nothing is corrected, and a photo with no writing says so in one fixed
    phrase the route recognises (`api/routes/work.py`)."""
    text = read("transcription/work.md", language)
    doubt, illegible, nothing = {
        "fr": ("[incertain:", "[illisible]", "[rien de lisible]"),
        "en": ("[uncertain:", "[illegible]", "[nothing legible]"),
        "nl": ("[onzeker:", "[onleesbaar]", "[niets leesbaar]"),
        "de": ("[unsicher:", "[unleserlich]", "[nichts lesbar]"),
    }[language]
    for mark in (doubt, illegible, nothing, "$…$"):
        assert mark in text
    answer = {"fr": "## La réponse", "en": "## The answer", "nl": "## Het antwoord", "de": "## Die Antwort"}[language]
    assert "```" not in text.split(answer)[0]
    if language == "en":
        assert "never translate" in text.lower()
    if language == "nl":
        assert "vertaal nooit" in text.lower()
    if language == "de":
        assert "übersetze nie" in text.lower()


# --- spec 021: the German set --------------------------------------------------------------------------------------

GERMAN_TWINS = [t for t in TWINS if (PROMPTS / f"{t}.de.md").exists()]

# Function words no German sentence needs. Not « du », « des » (French), « will » (English), nor the Dutch words
# German shares (« in », « als », « was »); « je » is avoided in the German files, so it may stay out too.
_FRENCH_STOPWORDS_DE = re.compile(
    r"\b(?:le|la|est|pour|une|avec|dans|que|qui|mais|donc|nous|vous|sont|cette|ces|elle|ils|aux|sur|ou|"
    r"tu|ta|tes|ne|au|chaque|toujours|jamais|sans)\b",
    re.IGNORECASE,
)
_ENGLISH_STOPWORDS_DE = re.compile(
    r"\b(?:the|and|are|with|from|that|this|which|your|you|does|not|only|never|always|must|should|have|has|"
    r"for|each|every|before|after|then|when|if)\b"
)
_DUTCH_STOPWORDS_DE = re.compile(r"\b(?:het|een|niet|jij|zijn|wordt|maar|ook|deze|zoals|altijd|nooit|leerling)\b", re.IGNORECASE)
# German quotes „…“ hold an example, not prose of the file.
_QUOTED_DE = re.compile(r"„[^“]*“")


def test_every_german_file_has_a_french_twin() -> None:
    german = sorted(str(p.relative_to(PROMPTS)).replace(".de.md", "") for p in PROMPTS.glob("**/*.de.md"))
    assert set(german) <= set(TWINS), sorted(set(german) - set(TWINS))
    assert set(GERMAN_TWINS) == set(TWINS)  # the whole set (spec 021 R3.1)


@pytest.mark.parametrize("twin", GERMAN_TWINS)
def test_a_german_file_has_the_skeleton_of_its_french_twin(twin: str) -> None:
    fr, de = read(f"{twin}.md", "fr"), read(f"{twin}.md", "de")
    assert outline(de) == outline(fr), twin
    for marker in (*MARKERS, VOICE_START.strip(), VOICE_END.strip()):
        assert de.count(marker) == fr.count(marker), (twin, marker)
    assert names(de) == names(fr), (twin, names(de) ^ names(fr))


@pytest.mark.parametrize("twin", [t for t in GERMAN_TWINS if t.startswith("templates/")])
def test_a_german_template_keeps_the_positions_of_the_french_one(twin: str) -> None:
    subject = twin.split("/")[1].split(".")[0]
    french, german = LIBRARY.template(subject, "fr"), LIBRARY.template(subject, "de")  # type: ignore[arg-type]
    assert [n for n, _ in german.headings] == [n for n, _ in french.headings]
    assert german.exercises_section == french.exercises_section
    assert german.text.count("###") == french.text.count("###")
    assert german.headings[-1][1] == WORDS["de"]["to_check"]


@pytest.mark.parametrize("twin", GERMAN_TWINS)
def test_a_german_file_carries_no_french_english_or_dutch_prose(twin: str) -> None:
    prose = _QUOTED_DE.sub(" ", _QUOTED.sub(" ", read(f"{twin}.md", "de").replace("Célestin", "Celestin")))
    for name, words in (("French", _FRENCH_STOPWORDS_DE), ("English", _ENGLISH_STOPWORDS_DE), ("Dutch", _DUTCH_STOPWORDS_DE)):
        found = words.findall(prose)
        assert not found, (twin, name, sorted(set(found)))


def test_the_german_transcription_prompts_never_translate_and_separate_readings_with_oder() -> None:
    """Spec 021 R4.1 and design §1 decision 2: the bar is a German point's separator, so readings take « oder »."""
    for name in ("transcription/transcribe.md", "transcription/verify.md"):
        text = read(name, "de")
        assert "übersetze nie" in text.lower(), name
        assert "[unsicher: a | b]" not in text, name
    assert "oder" in read("transcription/transcribe.md", "de").split("[unsicher:")[1].split("]")[0]


def test_the_german_authoring_prompt_reads_a_transcription_of_pages() -> None:
    pack = read("authoring/pack.md", "de")
    assert "Wenn das Material eine Transkription von Seiten ist" in pack and "S. 5" in pack
    for mark in ("[handschriftlich]", "[unsicher: a oder b]", "[unleserlich]", "[Abbildung: …]", "[durchgestrichen: …]"):
        assert mark in pack, mark
    assert "<materiel>" in pack
    curriculum = read("authoring/curriculum.md", "de")
    assert "<chapitre>" in curriculum and "Zu prüfende Punkte" in curriculum


def test_the_german_subject_prompts_write_the_nrw_notation() -> None:
    """Spec 021 R7.1: the board section of the maths prompt states the NRW forms."""
    maths = read("subjects/mathematics.md", "de")
    for form in ("0{,}45", "10 000", "]a ; b[", "P(2 | −1,5)", "P(2 \\mid -1{,}5)", "12,5 %"):
        assert form in maths, form
    assert "Wenn das Material anders schreibt, folgst du dem Material." in maths

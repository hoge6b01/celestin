# 021 — German (Germany): a fourth interface and course language

## 1. Introduction

Célestin speaks French, English and Dutch (specs 010, 011, 017). This epic adds **German as written and taught in Germany** (`de`) as a fourth **interface language** and a fourth **course language**, end to end: a German student registers in German, creates a German course, uploads German material and is taught in German, with the board drawing German school notation.

Spec 017 proved the structure: a language is `by_language` tables, a `*.{lang}.md` prompt set, a message catalog, a notation row, fixtures. `documentation/course-language.md` (« Adding things → A language ») and `documentation/i18n.md` (« Another language ») record the order that kept every step green; this epic follows them. Where `de` needs a change outside those places, the epic fixes the structure and says so.

**What differs from Dutch.** Dutch reused the Belgian-French notation by reference. German does not: German school notation has its own shapes (points written `P(2 | −1,5)`, semicolon separators, its own grouping of thousands), so German gets **its own notation row** on both sides and its own rule patterns, and the transcription marks must not collide with the vertical bar of a German point (§5).

Vocabulary (unchanged from 010, 011, 017):

- **Interface language** — `users.locale`. Buttons, errors, statuses, accessibility text. Never reaches the model.
- **Course language** — `courses.language`. Immutable. The language of the material, pack, curriculum, Célestin's speech, voice and the board's notation.
- **`de`** — the code for both. It stands for *German as taught in Germany*: standard German (Standarddeutsch, current orthography with `ß`) with the school vocabulary and the notation of German secondary schools, the way `fr` stands for French-speaking Belgian. `de`, `de-DE`, `de-AT`, `de-CH` browsers all resolve to `de` (primary-subtag rule of spec 010).

Scope:

- `de` in `Locale` and `CourseLanguage` (both sides), the interface catalogs, the settings screen and the create-course form.
- A German prompt set beside the others, for the four subjects and the three modes (parcours, discussion, révision).
- German authoring and transcription (marks, pack templates, numbering words, agent words, issue texts).
- Every `by_language` table, tool-rule vocabulary and notation pattern, the board's German notation, the learner sentences, voice and dictation.
- German fixtures, goldens, probes, the scripts' `--language de`, and the evals harness.
- Documentation, `CLAUDE.md` and the brief updated to say four languages.

Out of scope:

- Austrian and Swiss conventions and vocabulary (`de-AT`, `de-CH`: Swiss `ss`, Austrian school terms, any other notation). They are served by `de` as Germany's conventions; no variant (the structure does not preclude one later).
- Dialects; Célestin writes standard German.
- Per-Bundesland curricula: the pack restricts methods and vocabulary to the student's material; no prompt imposes one Land's terms.
- Any fifth language; changing a course's language; translating a course or a conversation; detecting the material's language.
- Content we author ourselves (brief §11): the work is prompts, templates, rules and fixtures, never course content.

## 2. Alignment with product vision

| Brief v2.0 | How this epic serves it |
|---|---|
| §3.1 the student's teacher's language | German students are served in their teachers' language. Open question 4 of the brief (« other languages (German)? ») is answered for German. |
| §5.1 it teaches the student's course; §5.2, §8 nothing invented | German authoring restructures the German material and never translates or adds (R4). |
| §5.3 withholds answers; §5.4 mechanical verdicts | The tool rules recognise German notation and vocabulary, so the same checker and the same leak rules hold in German (R6, R9). |
| §6.8 the interface | German joins French, English and Dutch at the user's choice (R1). |
| §9 trust: answer-leak rate below 1 %, no formula outside the pack | Reported per course language, German included (R9.3). |

Deviations from the brief, `CLAUDE.md` and the documentation:

1. `specs/product.md` (lines 17, 33, 84, 95, 172, 187 and open question 4 at line 265) and the `CLAUDE.md` bullets for specs 010, 011 and the notation invariant gain German: German courses use German school notation (R7.1), Célestin speaks German with « du ».
2. Documentation that says « French, English or Dutch » (`i18n.md`, `course-language.md`, `README.md`) is updated (R10). The `specs/index.md` lines of 010, 011 and 017 stay as history.

## 3. Requirements

### R1 — German as an interface language

**As a** German-speaking user, **I want** the application in German, **so that** I can use it in my own language.

Acceptance criteria:

1. `de` is a `Locale` on both sides (`app/domain/locale.py`, `src/lib/locale.ts`, `project.inlang/settings.json`). French stays the base locale and the default.
2. A backend catalog (`app/domain/messages/de.py`) and a frontend catalog (`messages/de.json`) hold every key the French ones hold, with the same `{variables}` and plural forms; `test_messages.py`, `npm run i18n:check` and the catalog parity tests fail on a missing or extra key. Plurals use German's one/other rule. `WHERE_WORDS` (`domain/messages/issues.py`) has a German row.
3. `Accept-Language` resolution picks `de` for `de`, `de-DE`, `de-AT`, `de-CH`, by quality order then position, on both sides, pinned by the shared `accept_language_cases.json` (both copies gain `de` cases, including `de-DE;q=0.8,fr;q=0.9` → `fr`). A browser listing no supported language still sees French.
4. The settings screen's language section lists « Français », « English », « Nederlands » and « Deutsch », each by its own name, and marks the current one. Registration stores the language the visitor was seeing. Existing accounts keep their language (no data change).
5. `<html lang="de">` for a German interface; the server-rendered sign-in and registration pages come out German on the first response; `Vary: Accept-Language` and `Cache-Control` behaviour unchanged.
6. `PATCH /api/auth/me` accepts `de` and still answers `422` for an unsupported value, with a message in the request's language.
7. Every error, status, marker label, content-issue reason and subject label the server writes for the student exists in German (`TutorError.message("de")`, `render_issue`, `event_of`, `marker_for`).
8. Interface numbers and sizes (`lib/i18n-format.ts`) use `de-DE`.
9. The product name « Célestin » stays untranslated (`APP_NAME`).
10. The German copy is written by us in the register of the French copy: clear, friendly, every user addressed with **« du »**, administrators included (as the French copy uses « tu »), gender-neutral wording where a person is named (« Lehrkraft »), no anglicisms where a common German word exists. It is **reviewed by the user (a native speaker)** before the spec is marked Implemented; until then its status says « German copy and prompts awaiting review ».

### R2 — A German course is taught in German

**As a** student of a German course, **I want** Célestin to speak, write on the board and read my work in German, whatever my interface language is, **so that** nothing French, English or Dutch comes between me and my teacher's material.

Acceptance criteria:

1. `de` is a `CourseLanguage` on both sides. `POST /api/courses` accepts `language: "de"` for a subject offered in it; an unsupported or un-offered one is still `422` with a catalog message (now also German).
2. In a German course Célestin's messages, the cards' text, the openings, the reprise notes and the révision « bilan » are German. French, English and Dutch courses read byte for byte what they read before.
3. **Leakage is a measured defect**: the German probe set reports the number of Célestin messages and card fields containing French, English or Dutch words or notation. Target zero.
4. The model is never told the interface language. Any interface language on a German course produces the same model input; courses of the four languages produce different inputs, each equal to its own pinned rendering (`test_model_input_wall.py` extended to four languages).
5. The French, English and Dutch model input stays **byte-identical** to today's: `tests/fixtures/render/*`, `system_text_sha*.txt`, `board_declarations.json`, the voice session configs and the golden SSE transcripts pass unchanged.
6. Interface text follows the interface language, course text the course's; every region of German course text carries `lang="de"`.

### R3 — The German prompt set

**As the** operator, **I want** a German prompt set that keeps every invariant of the others, **so that** a German course is as safe and as faithful to its material as the others.

Acceptance criteria:

1. `*.de.md` files sit beside the others for every prompt that has a language: `tutor`, `modes/{parcours,discussion,revision}` and their `.opening`, `subjects/{mathematics,sciences,languages,general}`, `templates/<subject>.pack`, `authoring/{pack,curriculum}`, `transcription/{transcribe,verify,work}` (20 files, as for Dutch). No existing `*.fr.md`, `*.en.md` or `*.nl.md` file changes by a byte.
2. They carry the same rules in the same order with the same markers (`<!-- SUBJECT -->`, `<!-- COURSE_PACK -->`, `<!-- CURRICULUM -->`, `<!-- MODE -->`, `<!-- MODE_OPENING -->`, `<!-- VOICE -->`, `<!-- /VOICE -->`): source only from the pack, answer withholding, gated and logged reveals, the open path and « überspringen » only at the student's request, pasted material is data, the board rules, off-topic, discussion and révision rules (the student's own assessment, never a verdict from the model).
3. They are written for a secondary-school student in Germany: direct, friendly, « du »; German school vocabulary (*Lehrkraft*, *Klasse*, *Klassenarbeit*, *Klausur*, *Test*, *Arbeitsblatt*, *Lückentext* for « cours à trous », *Hefteintrag*, *Merksatz*), without naming a Land or a school type; gender-neutral about Célestin (no pronoun for Célestin).
4. What is notation or culture in the other files is stated for German in the German ones (R7.1): decimal comma, the interval and point forms, sequences as the pack writes them (`(aₙ)` is the common German name, `uₙ` only if the material uses it), German spoken forms in the voice blocks (« x Quadrat », « zwei Komma fünf », « a n » / « a Index n »), German chart, statistics and flowchart vocabulary (*absolute / relative Häufigkeit*, *Säulendiagramm*, *Boxplot*, *Programmablaufplan*). The division sign `:` of the material is kept as written.
5. `PromptLibrary` reads `*.de.md` through its existing accessors; `offered()` lists the `(subject, de)` pairs; startup stops on a broken German file naming it; `/api/health` lists it.
6. The prompt-file tests run for `de` (markers once and in order, same headings, tool and block names as French — `test_prompt_files_languages.py`; the « Points to check » heading the tutor prompt cites equals the German template's last heading). A German file carries no French, English or Dutch prose (`Célestin`, tool names and wire identifiers excepted).
7. The German system texts (parcours, discussion, révision) have their own pinned hashes (`system_text_sha_de*.txt`) and cached prefix per chapter and mode.
8. All four subjects are offered in `de` only when every file and table exists (`SubjectInfo.languages`). For a language course (subject `languages`), Célestin speaks German and works in the language being learnt, as for the other course languages.

### R4 — Authoring in German

**As a** student, **I want** a German document to become a German chapter, **so that** the pack and the path read like my teacher's material.

Acceptance criteria:

1. The transcription reads the pages in German and writes what it sees, in the page's own language; **it never translates**. Marks (`MARKERS["de"]`) in German: `[handschriftlich]`, `[unsicher: a | b]`, `[unleserlich]`, `[leere Seite]`, `[Abbildung: …]`, `[durchgestrichen: …]` (exact names fixed by the design). `--- page N ---` unchanged. `count_markers`, `handwritten_numbers`, `apply_uncertain`, `validate_batch` work on them, **including an uncertain reading that contains a German point `P(2 | 3)`** (§5.2); French, English and Dutch sources keep validating.
2. The pack and curriculum prompts write German from German material and add nothing the material does not hold (brief §5.2).
3. German pack templates for the four subjects have the same numbered structure, required-section positions and sentinels as the French (« Keine. », « Nichts im Material. », « im Material nicht korrigiert » or equivalents fixed by the design). `index_pack` compares headings to the template of the course's language; a pack in another language's template fails with `pack.wrong_language` for every pair that involves `de`.
4. `chapter_title` and the curriculum title cleaning strip German chapter-numbering words (`Kapitel 3:`, `Lektion 2 –`, `Thema 4)`, `Teil`, `Modul`, `Einheit`, `Abschnitt`, with abbreviations such as `Kap.` and Roman numerals); other languages unchanged.
5. `AGENT_WORDS["de"]`, `_LANGUAGE_NAMES_FR["de"]` (« allemand »), the repair prompts and `issue_text(issue, "de")` are German; the student's editor still shows the reason in the **interface** language.
6. `authoring_eval` and `document_eval` take `--language de` and run on a German document per subject; the runs are read against the French ones.

### R5 — Text built for the model follows the course language

**As the** operator, **I want** what the code builds every turn to be German in a German course, **so that** the model is not surrounded by another language.

Acceptance criteria:

1. `curriculum_render` (`WORDS`: overview, brief, completion, state, discussion state, opening hints; `REPRISE`; `REVISION`: the révision summary and the outcome words for `solid`, `shaky`, `todo`) renders in German, with German weekday and month names and time-of-day wording. French, English and Dutch renderings are byte-identical; German goldens (`tests/fixtures/render/*_de.txt`) are added, read by a person, then pinned.
2. `KIND_LABELS`, the path refusals (`services/path.py`), `SAVE_FAILED`, `_UNKNOWN`, `_OUTPUT`, the registry and result `_WORDS`, `_PHOTO_LABEL` have a German row. Wire values (`teach`, `practise`, `synthesis`, `solid`, `shaky`, `todo`) do not change. These tables do not import the interface catalog.
3. `CHARS_PER_TOKEN` has a German row (long compounds tokenise differently from French; measured or justified in the design) so German history is neither over- nor under-trimmed.
4. **Tool declarations and rule refusals** stay as for English and Dutch: the declarations are the same for every language (`TOOL_TEXT` empty) and the refusals stay French until German probe evidence shows leakage; the design states what evidence flips it. The outcome required: no French in a German course's speech or cards.
5. Every `by_language(...)` table in `app/` and `scripts/` has a German row; `test_by_language_tables.py` passes with four languages; `test_no_language_branches.py` passes (no `== "de"` branch).

### R6 — The tool rules recognise German notation and vocabulary

**As the** operator, **I want** the board tools to accept and refuse the right things in German, **so that** answer-withholding and no-invention rules work in German as in the other languages.

Acceptance criteria:

1. `plots.py`: `PACK_WORDS_BY_LANGUAGE["de"]` so that the German names of the sine, cosine, tangent, natural logarithm (`ln`), common logarithm (`lg`, *Zehnerlogarithmus*), cube root (*Kubikwurzel*, *dritte Wurzel*) and exponential function (*Exponentialfunktion*, *e-Funktion*) count as the pack naming the function; one accepted and one refused sentence per entry. `COMMA` and `GROUPS` have German rows (decimal comma; a German pair is read with `|` or `;` as separator, per R7.1).
2. `flowcharts.py`: `HOLE_WORDS["de"]` (« ergänze », « ergänzen », « fehlt », « leer », « Lücke », « auszufüllen », « noch zu bestimmen », and the like) so the `placeholder` rule is not silently off.
3. `figures.py`: `INTERVAL`, `COORDS`, `NUMBER`, `DEGREES`, `LENGTH` recognise German hand-written notation: `]a; b[`, `(a; b)`, `[a; b]`, `]−∞; 2]`, `[a; b)` and the comma-separated forms, points `P(2 | −1,5)` and `(2; −1,5)`, decimal comma, and the grouping of R7.1 (`1,5` is 1.5; `12 500` is twelve thousand five hundred; how a hand-written `12.500` is read is fixed by the design). The existing French, English and Dutch cases are untouched. The board writes the NRW forms (R7.1); the rules also accept the forms in use elsewhere in Germany, since hand-written work and other Länder's material vary.
4. The shared case tables (`notation_cases.json`, `layer_cases.json`, `capacity.json`, `expression_cases.json`) gain German cases in both copies, formatted with prettier. `domain/expression.py` keeps accepting only a decimal point.
5. Rules read the language from `ctx.language`; existing rule tests pass without edit. `test_language_is_passed.py` passes.

### R7 — The board draws in German school notation

**As a** student in Germany, **I want** numbers, intervals, points and statistical words on the board written the way my teacher writes them, **so that** I never translate the board.

Acceptance criteria:

1. **German notation**, as written in North Rhine-Westphalia's Gymnasium material (the first users are at a Gymnasium in Cologne; evidence §5.1): decimal comma; percentage `12,5 %` with a space; points `P(2 | −1,5)` with a vertical bar; intervals with outward brackets and a semicolon, `]a; b[`, `[a; b[`, `]a; b]`, `[a; b]`, `]−∞; 2]` (no round-bracket form); four-digit numbers ungrouped (`1000`), five digits and more grouped with a space (`10 000`, `11 768`), never a dot; sequences as the material writes them. Where a course's material writes otherwise, Célestin follows the material in its text and the board's formatter stays on the convention.
2. `charts/format.ts` gains its **own** `GERMAN` notation (not a reference to `FRENCH`), selected by `notationFor("de")` and read by `useNotation()`. The words the board adds are German (« Absolute Häufigkeit / Relative Häufigkeit / Prozent », « Minimum / unteres Quartil / Median / oberes Quartil / Maximum », fixed by the design); wire identifiers (`measure: "effectif" | "frequence" | "pourcentage"`) do not change. The point formatter is a notation field, so the vertical-bar form needs no component change.
3. Accessibility descriptions of the drawing blocks keep the interface language for the sentences and take the course's notation for the numbers inside.
4. `lib/tutor/prompts.ts`: the sentences the interface sends to the model for the learner (review, start, next step, next section, skip, answer, révision self-assessment, voice-tool failure) exist in German, never from the interface catalog; the other languages byte for byte.
5. The transcription-mark names of the source editor, the course language badge (« Deutsch »), the create-course form's language select and its note, and `CourseLanguageProvider` handle `de`; no component names a language except the tables.
6. Tests: formatter tables (existing cases unchanged, German added to the shared `notation_cases.json`), learner sentences, and the language sweeps: a German interface on French, English and Dutch courses, the other interfaces on a German course, with no sentence in the wrong language for its kind (`foreignTextOutside("de")` finds French, English and Dutch words outside a region carrying its own `lang`).

### R8 — Voice and dictation in German

**As a** student, **I want** to talk to Célestin and dictate in German, **so that** the spoken lesson matches the written one.

Acceptance criteria:

1. The Realtime session's input transcription language hint is `de` for a German course (a bias, not a constraint); the instructions come from the German prompt files with the German spoken-maths forms. Dictation gets the `de` hint for every subject except `languages` (unchanged rule: a language course gets no hint).
2. French, English and Dutch session configs are byte-identical; a German case is added to `test_voice_service.py`.
3. `voice_smoke` and `voice_probe` take `--language de`; the probe reads the German spoken forms.

### R9 — Measuring it

**As the** operator, **I want** German held to the standard of the other languages, **so that** « it works in German » is evidence.

Acceptance criteria:

1. German fixtures per offered subject: material, valid pack, curriculum, chapter directory, written to the German templates, so the whole path (parcours, discussion, révision) is testable offline with the scripted fakes.
2. `scripts/probe.py --language de` runs the guardrail, drawing and révision probes on the German chapters. Its German flags: a decimal point where the convention is the comma, wrong interval or point notation, French, English or Dutch words (leakage), answer leaks, formulas outside the pack, an injection attempt in German.
3. The report states, per course language, the answer-leak rate (target below 1 %), formulas or methods outside the pack (target zero) and the leakage count (target zero).
4. `smoke`, `seed`, `authoring_eval`, `document_eval`, `voice_smoke`, `voice_probe` take `--language de`; `smoke` fails on a cache miss in German; each (language, mode) has its own prefix.
5. `evals/` accepts `de` wherever it accepts a course language (`harness/config.py` `LANGUAGES`) and runs the German chapters; it still reads `backend/` and changes nothing in it.
6. Tests that pin a language's text keep their text; tests that become per-language are parametrised over `COURSE_LANGUAGES` / `LOCALES`, not copied. New goldens are produced once, read by a person, then pinned.
7. Probe transcripts are read by the user (a native speaker) before the epic is closed; findings are recorded in the spec.

### R10 — Documentation

**As a** maintainer, **I want** the documentation to say four languages, **so that** it is true.

Acceptance criteria:

1. `documentation/i18n.md`, `documentation/course-language.md` (including its per-language table list, which lacks `REPRISE`, `REVISION`, `NUMBER`, `_PHOTO_LABEL` and the result `_WORDS` today), `README.md`, `CLAUDE.md`, `specs/product.md` and `specs/index.md` updated per §2. « Adding things → A language » is checked against what this epic needed and corrected where the claim « files and tables » did not hold.
2. The Known limits record: Germany's conventions only (no `de-AT`, `de-CH`), refusals French, German copy and prompts written by us and reviewed by the user.

## 4. Non-functional requirements

### 4.1 Architecture

1. **No component names a language.** `de` appears in `Locale`/`CourseLanguage`, the catalogs, `by_language` tables, prompt files, notation table, autonym list, fixtures and goldens. Any other place the implementation must touch is listed in the design as a defect of the structure and fixed so the next language does not need it.
2. **No fallback.** A language missing a model-facing resource is not offered; no German path falls back to another language.
3. **The wall holds.** Model-facing modules take the course language, never the interface `locale` nor the catalog.
4. **Wire identifiers do not change**: tool names, enums, section and card kinds, rule codes, `measure` values, révision outcomes, the SSE contract. The frontend types change only by gaining `"de"`.
5. **No migration expected.** `users.locale` and `courses.language` are strings without database enums (specs 010, 011, 017); the design verifies it, and any constraint found is dropped by a migration with a working `downgrade`.
6. **The other languages do not move.** Edits to existing tests are limited to parametrising over the language lists; no French, English or Dutch golden is regenerated.
7. `nl` follows French notation by reference; `de` must not: the German notation is its own row everywhere a notation is tabled.

### 4.2 Performance and cost

1. Cached prefix per chapter and mode unchanged in size and behaviour; a chapter has one language.
2. Tables and regexes are built once at import; Paraglide ships the four catalogs in one build, and the bundle growth is reported in the design.

### 4.3 Security and privacy

1. A language from a request is validated against the supported list before use and never interpolated into a path.
2. Pasted material is data in German too; the German prompts carry the instruction and the probes include an injection attempt in German.
3. Nothing new is logged about a student; ownership checks unchanged.

### 4.4 Reliability and quality

1. A missing or broken German file stops startup naming it; `/api/health` reports it while running.
2. Offline tests drive everything with scripted fakes: catalog parity, `Accept-Language` cases, `CreateCourseRequest` with `de`, per-language `PromptLibrary`, the German authoring path from material to valid pack and curriculum, marks including the `|` case, `index_pack` with mismatched templates, render goldens, rule tables, formatters, learner sentences, voice config, the wall test, the table-coverage test.
3. Real-model checks are the probes of R9; none runs under `pytest`.

### 4.5 Usability

1. A student tells a German course from the others at a glance (badge « Deutsch »).
2. A user is never shown a sentence in the wrong language for its kind.
3. At 400 px wide, with German (long compounds, e.g. « Häufigkeitsverteilung ») everywhere: no overflow or truncated control. Long words wrap or hyphenate (`lang="de"` enables hyphenation).

## 5. Open questions for the design (and the user)

1. **German notation (R7.1) — resolved** for the first users (Hansa-Gymnasium, Cologne, NRW). Germany uses both `]a; b[` and `(a; b)`, and the comma or semicolon in pairs; NRW's Gymnasium material settles it. Counted in Klett's *Lambacher Schweizer Mathematik NRW* (Einführungsphase excerpt W700517, and the *Abi-Coach* with the NRW Leistungskurs Abitur 2019, 736095): points `P(n|n)` 30 times, never with `;`; intervals `[a;b]`, `]a;b[`, `]a;b]`, `[a;b[`, never round brackets; `20 000`, `11 768` grouped with a space, `1000`, `4000` not grouped; `12,5 %` with a space 81 times out of 85. The school's own textbook list was not found online; the NRW Zentralabitur and its textbooks are common to the Land's Gymnasien. Sequences are not settled (rare in NRW's curriculum): the material decides. Hand-written work still varies, so the rules (R6.3) keep accepting `(2; 3)`, `(a; b)` and dot-grouped numbers.
2. **The `|` collision.** `[unsicher: a | b]` separates readings with `|`, which is also the German point separator. The design chooses: another separator for the German mark, or a parse that tolerates `|` inside parentheses; either way `apply_uncertain` and `validate_batch` are tested on `P(2 | 3)`.
3. **Interface register — resolved.** « du » everywhere, administrators' screens included, as the French copy uses « tu » throughout (user's decision).
4. **Tool declarations and refusals** (R5.4): evidence-driven, as for English and Dutch.
5. **`CHARS_PER_TOKEN` for German**: measured or estimated.
6. **Review.** The user reviews the German copy, prompts and probe transcripts (R1.10, R9.7); the spec's status line depends on it.
7. **Dutch review debt.** Spec 017's Dutch copy is still unreviewed; this epic does not change it, but a sweep that now finds German words must not start failing on Dutch text it accepted before.

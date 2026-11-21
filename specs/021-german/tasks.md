# 021 — Tasks

Phases are testable increments in dependency order. Each ends with a check the user can run. Requirement ids (`R1`…) refer to `requirements.md`, section numbers (`§`) to `design.md`. Tick tasks as they land; record design deviations in « Deviations ».

Branch `feature/021-german`, started from `main` **after the user has committed** the root `CLAUDE.md` edits and `specs/021-german/` (the working tree holds them uncommitted when this plan is written). Commit nothing; the user commits.

Checks for every phase that touches a side: backend `cd backend && uv run pytest`; frontend `cd frontend && npm run typecheck && npm run lint && npm test` (`npm i` first if `node_modules` is missing); `npm run i18n:check` when a catalog changes; `cd evals && uv run pytest` when `evals/` changes. Offline only: tests drive scripted fakes; no phase except 9.6 calls a provider.

Load-bearing constraints across the epic:

- **French, English and Dutch do not move.** No file in `tests/fixtures/render/*` (fr, `_en`, `_nl`), `system_text_sha*.txt`, `board_declarations.json`, `error_messages_fr.json`, `status_messages_fr.json`, `markers_fr.json`, the golden SSE transcripts, or any existing `*.fr.md`/`*.en.md`/`*.nl.md` prompt changes. `git diff --stat` on them is empty at every phase end.
- **`de` is not offered until phase 8** (`SubjectInfo.languages` stays three codes; `/api/subjects` and the create form unchanged until then). The interface language is user-visible from phase 2, which is intended.
- **German copy, prompts and goldens are written by us.** Nothing is pinned until the user has read it (tasks marked **READ**). The spec status carries « German copy and prompts awaiting review » until the user says otherwise.
- **Notation: NRW forms** (requirements §5.1, design §1 decision 1). The board writes `(2 | −1,5)`, `[2 ; 5[`, `12,5 %`, `1000`, `10 000`; the rules also accept the forms used elsewhere.
- **Glossary** (design App. A) is used everywhere: `Lernpfad`, `Abschnitt`, `Gespräch`, `Wiederholung`, `Rückblick`, `Heft`, `Überspringen`, `Nächster Schritt`, `Nächster Abschnitt`, « du ».

## Phase 0 — Structural fixes before the fourth language (§4.3, §4.9)

**Goal:** no place needs more than a table row to learn `de`, the leak path for `|` points is closed in advance, and `de` is no longer the tests' example of an unsupported code. French, English and Dutch behave exactly as before. **Done when** the whole suite passes (backend, frontend, evals) with no `de` anywhere in a `Literal`.

- [x] 0.1 Replace `de` as « unsupported code » by `es` in every test that uses it (backend: `test_language`, `test_locale`, `test_locale_of`, `test_scripts_language`, `test_probe_flags_en`, `test_courses_endpoint`, `test_dutch_course`, `test_auth_endpoint`, `test_dictation_endpoint`; frontend: `course-language.test.tsx`, `locale.test.ts`, `i18n.test.tsx`, `i18n-server.test.ts`; evals: `tests/unit/test_config.py`), and the shared `accept_language_cases.json` row `de-DE` → `es-ES` in **both** copies (prettier, byte-equal). `test_by_language_tables.py` adds `xx` instead of `de` as its hypothetical language. Test: the suites pass; `grep -rn '"de' backend/tests frontend/src evals/tests` finds no refusal case left on `de`.
- [x] 0.2 `tools/plots.py`: `MEMBERS = by_language(fr=_MEMBERS, en=_MEMBERS, nl=_MEMBERS)` with `_MEMBERS = re.compile(";")`; `_gives_values` splits with `MEMBERS[language]` (§4.3 1); `gives_away` builds `flat` with `\mid` and `\vert` replaced by `|`. Tests (`test_board_rules`, `_en`, `_nl`, `test_plot_rules*`): every existing `gives_away` case unchanged; new: `gives_away(r"$(2 \mid 3)$", lang)` behaves as `"(2|3)"` for fr/en/nl (not a giveaway in those languages: no row splits on `|`, pinned).
- [x] 0.3 `tools/figures._bare`: `_TEX_DELIMITER` gains `\mid` and `\vert` → `|`. Tests (`test_figure_rules*`): existing cases unchanged; `_bare(r"$P(2 \mid -1{,}5)$") == "P(2|-1,5)"`.
- [x] 0.4 `domain/subject.py`: one module constant `OFFERED = ("fr", "en", "nl")` read by the four `SubjectInfo`s. Test `test_subjects` unchanged.
- [x] 0.5 `scripts/probe.py`: `_LEAK` becomes a `by_language` table (fails at import for a missing language); `FOREIGN_LEAK`/`LEAK_FLAGS` take the language name from a `LANGUAGE_NAME` `by_language` row (« néerlandais » for `nl`, French report). Tests `test_probe_flags_nl`, `test_probe_flags_en`: flag texts byte-identical.
- [x] 0.6 Tests that count three languages are derived from the lists: `test_scripts_language` (`len(COURSE_LANGUAGES)`), `test_authoring_agent_nl`, `test_revision_rendering`, `test_prompt_library_languages` (`len(COURSE_LANGUAGES) * len(expected)`; `other_templates` compared to `[l for l in COURSE_LANGUAGES if l != x]`); literal parametrisations `["fr","en","nl"]` → `COURSE_LANGUAGES` (`test_probe_revision`, `test_probe_flags_en`, `test_revision_input_wall` unpacking by name kept through a dict, evals `test_config`).
- [x] 0.7 `evals/`: new `tests/unit/test_languages_match_backend.py` reads `backend/app/domain/language.py` with `ast` (no import) and asserts `harness/config.LANGUAGES` equals the `CourseLanguage` `Literal` and `judge.LANGUAGE_NAMES` has exactly those keys. `evals/models.example.toml` comment `fr | en` → the real list.
- [x] 0.8 `test_no_language_branches.py`: `CODES` gains `"de"`. Run the three suites.

**Verify:** `cd backend && uv run pytest`; `cd frontend && npm test`; `cd evals && uv run pytest`; `git diff --stat backend/tests/fixtures/render backend/prompts` is empty.

## Phase 1 — The interface language, backend (R1.1, R1.2, R1.6, R1.7)

**Goal:** a user can have `locale = "de"`; every server message for the student exists in German. **Done when** catalog parity, locale and error tests pass in four languages.

- [x] 1.1 `domain/locale.py`: `Locale = Literal["fr","en","nl","de"]`; `CATALOGS["de"]`. Tests `test_locale`: `LOCALES == ("fr","en","nl","de")`; `parse_accept_language` for `de`, `de-DE`, `de-AT`, `de-CH`, `de-DE;q=0.8,fr;q=0.9` → fr, `fr,de;q=0.8` → fr, `de;q=0` → fr, `es,de;q=0.5` → de (inline cases; the shared JSON follows in 2.3).
- [x] 1.2 `domain/messages/de.py`: the 143 keys of `fr.py`, same `{fields}`, `*.one`/`*.other`; `language.de` added to `fr.py` (`allemand`), `en.py` (`German`), `nl.py` (`Duits`); `de.py` has `language.fr/en/nl/de` (`Französisch`, `Englisch`, `Niederländisch`, `Deutsch`). « du », glossary. Tests `test_messages`: parity over four catalogs, `set(CATALOGS) == set(LOCALES)`, plural forms. **READ** (German copy).
- [x] 1.3 `WHERE_WORDS["de"]` (App. A: `Titel`, `Kapitel`, `Lernpfad`; `Aufgabe \1`, `Abschnitt Nr. \1`). Tests `test_issue_messages`: each pattern; `render_issue(·, "de")` on a coded and an uncoded issue.
- [x] 1.4 Errors and statuses in `de`: `TutorError.message("de")`, `event_of(·,"de")`, `marker_for(·,"de")`, subject labels, chapter title prefix. Tests: `test_error_languages`, `test_display_messages`, `test_issue_messages` gain the `de` assertions (other languages untouched).
- [x] 1.5 Auth: `PATCH /api/auth/me` accepts `de`, `422` for `es`; registering with `Accept-Language: de-DE` stores `de`. Tests `test_auth_endpoint`, `test_error_languages` (a wrong password under `Accept-Language: de` answers in German).

**Verify:** `uv run pytest`; with the backend running, `curl -s -X POST localhost:8000/api/auth/login -H 'Content-Type: application/json' -H 'Accept-Language: de-DE' -d '{"email":"x@y.de","password":"nope"}'` answers in German.

## Phase 2 — The interface language, frontend (R1.3 to R1.5, R1.8, R1.9, R7.6 for the interface)

**Goal:** the whole application can be used in German; « Deutsch » is in the settings list; no screen mixes languages. **Done when** `i18n:check`, typecheck, lint, tests and the sweeps pass.

- [x] 2.1 `lib/locale.ts` (`LOCALES`, `AUTONYM.de = "Deutsch"`), `lib/i18n-format.ts` (`INTL_TAG.de = "de-DE"`), `lib/error-page.ts` (`TEXT.de`, App. A), `project.inlang/settings.json`. Tests: `locale`, `i18n-format` (a German number, size, date), `error-page` (German page for `Accept-Language: de`), settings list shows four autonyms.
- [x] 2.2 `messages/de.json`: the 726 keys of `fr.json`, same `{variables}`, plural selector `one`/`other`, glossary and « du » throughout (admin screens included); `Célestin` untranslated. **READ** (German copy; pending: the user clicks through, 9.3). Test: `npm run i18n:check`.
- [x] 2.3 Shared `accept_language_cases.json`: the `de` rows of 1.1 in **both** copies. Tests: frontend `accept_language_cases` test, backend `test_locale` byte-equality.
- [x] 2.4 Sweep: `foreignTextOutside(root, "de")` detector with French, English and Dutch whole-word lists (§5.5); `en`, `nl` detectors unchanged. The sweeps run for `["en","nl","de"]`; German twins of `dutch-sweep`, `dutch-lesson-sweep`, `dutch-discussion-sweep` where their content is language-specific. Tests: the detector finds a French, an English and a Dutch word on a German screen and ignores them inside a `lang` region; every swept screen passes in German.
- [x] 2.5 `:lang(de) { hyphens: auto; overflow-wrap: break-word; }` in `styles.css`. Test: `<html lang="de">` under `de` (`i18n` tests); the 400 px check is manual.

**Verify:** `cd frontend && npm run i18n:check && npm run typecheck && npm run lint && npm test`. Both servers running: « Einstellungen » → « Deutsch »: page, menu and title change at once; open a course, a lesson, a discussion, a révision, `/admin`: no French, English or Dutch chrome, every user addressed with « du »; a private window with a `de-DE` browser shows `/login` in German; at 400 px nothing overflows.

## Phase 3 — The course language, backend tables and rules (R2.1, R4.1, R4.3 to R4.5, R5, R6)

**Goal:** everything the code builds for the model and every tool rule knows `de`; no German course is offered. 3.1 to 3.6 are one atomic step (every `by_language` table refuses at import until it has its row); the suite runs at 3.7. **Done when** each table's German test passes and the other languages' tests pass untouched.

- [x] 3.1 `domain/language.py`: `CourseLanguage` gains `"de"`; `tests/conftest.py` gains `german_offered` (patches `SUBJECTS` to four codes; the real list moves in 8.1). Tests `test_language`: `COURSE_LANGUAGES` four codes, `require_language("de")` passes, `"es"` raises; the offered-list pins keep three codes.
- [x] 3.2 Authoring tables: `MARKERS["de"]`, `_NUMBERING_BY_LANGUAGE["de"]` (`_KEYWORD_DE`), `_LANGUAGE_NAMES_FR["de"] = "allemand"`, `KIND_LABELS["de"]`, `CHARS_PER_TOKEN["de"] = 3.4`, `AGENT_WORDS["de"]`, `_PHOTO_LABEL["de"]` (App. A). Tests `test_transcription_de`: counts, handwritten numbers, `validate_batch` with the four batch sentences, and `apply_uncertain`/`count_markers` on `[unsicher: P(2 | 3) oder P(2 | 8)]`; `chapter_title` (`Kapitel 3:`, `Kap. 2 –`, `Lektion 4)`, `Thema IV.`, `Teilchen` and `Modulation` untouched); `issue_text(·,"de")`; history estimate ratio.
- [x] 3.3 Model-facing words: `curriculum_render.WORDS/REPRISE/REVISION["de"]`, `path.WORDS["de"]`, `pace._OUTPUT`, `section._UNKNOWN`, `context.SAVE_FAILED`, `registry._WORDS`, `result._WORDS`, `TOOL_TEXT["de"] = {}`; from the English rows with the glossary, days/months/parts and révision outcomes from App. A. Tests `test_curriculum_render_de` (every function; `moment()` words and boundaries; **goldens `tests/fixtures/render/*_de.txt` generated once, READ, then pinned**), `test_model_text_by_language`, `test_path`, `test_reprise_note`, `test_revision_rendering`, `test_curriculum_render_skipped` gain `de`; `declarations(mode,"de")` equals the French snapshot. **READ** (model-facing German).
- [x] 3.4 Rules (§4.6): `figures.COORDS["de"]` (`_COORDS_BAR` union), `INTERVAL["de"]`, `NUMBER["de"] = _german_number`, `DEGREES/LENGTH["de"]` (`_NUMBER_DE`); `plots.MEMBERS["de"] = [;|]`, `GROUPS["de"]`, `COMMA["de"]`, `PACK_WORDS_BY_LANGUAGE["de"]`; `flowcharts.HOLE_WORDS["de"]`. Tests `test_board_rules_de`: one accepted and one refused sentence per `PACK_WORDS` entry (`Tangens` counts, `Tangente` does not; `Exponentialfunktion` counts, `exponentielles Wachstum` does not; `lg` counts); hole phrases (`auszufüllen`, `fehlender Schritt`, `Kasten 3`, `tbd` refused, an ordinary step accepted); `gives_away("S(2 | 3)","de")` and `gives_away(r"$S(2 \mid 3)$","de")` true, `gives_away("(cm | s)","de")` false; `COORDS["de"]` on `P(2|3)`, `(2;3)`, `(2,3)`; intervals `]2 ; 3[`, `(2;3)`, `]2, 3[`; `_german_number`: `12.500` → 12500, `1.500,5` → 1500.5, `1,5` → 1.5, `0.125` → 0.125, `10000` → 10000; angle `37,5°`, length `1.500 m` → 1500 m on an exercise's figure.
- [x] 3.5 Shared `notation_cases.json` (both copies, byte-equal, prettier): `de` rows (`[2 ; 5[`, `]2 ; 5]`, `[2 ; 5]`, `]2 ; 5[`, `]−∞ ; 2]`, `[5 ; +∞[`, `(2 | −1,5)`, `12,5 %`, `1000`, `10 000`) and backend-only `recognised` rows (`P(2|3)`, `(2;3)`, `(2, 3)`, `]2, 3[`, `12.500`, `1.500,5`, `0.125`). Test `test_notation_cases` over `COURSE_LANGUAGES`.
- [x] 3.6 `scripts/` rows that need no fixture: `voice_probe` (`PROBES`, `UNSPEAKABLE` for `de`: « x Quadrat », « zwei Komma fünf »), `probe._LEAK`/`LANGUAGE_NAME` `de` rows (« allemand »). Tests `test_scripts_language`.
- [x] 3.7 Run the whole suite; `test_by_language_tables` lists the same modules, none missing; `test_language_is_passed` and `test_no_language_branches` pass.

**Verify:** `cd backend && uv run pytest`; `uv run python -c "import datetime as d; from app.services import curriculum_render as r; print(r.moment(d.datetime(2026,10,8,10,5), 'de'))"` prints `Donnerstag, 8. Oktober, 10:05 Uhr (vormittags)`.

## Phase 4 — Authoring in German: templates, authoring and transcription prompts, fixtures (R3, R4)

**Goal:** a German document becomes a valid German pack and path with the scripted fakes. **Done when** the German authoring path test and the prompt-file tests pass.

- [x] 4.1 `prompts/templates/{mathematics,sciences,languages,general}.pack.de.md` (App. A titles, `exercises_section: 6`, sentinels `Keine.`, `Nichts im Material.`, `im Material nicht korrigiert`). Tests `test_prompt_files_languages` over four languages: twins exist both ways, heading numbers, `exercises_section` and `###` counts equal the French.
- [x] 4.2 `prompts/authoring/{pack,curriculum}.de.md`, `prompts/transcription/{transcribe,verify,work}.de.md` from the English twins: German marks with `[unsicher: a oder b]`, « übersetze nie », `<materiel>` is data, NRW notation in what the transcription writes as seen. Tests: the per-language prompt tests (page markers, doubt, no translation, data); no French, English or Dutch prose in a German file (three stop-word lists; `Célestin`, tool names, wire identifiers excepted). **READ**.
- [x] 4.3 Fixtures: `packs/{maths_valid_de,sciences_valid_de}.md`, `curricula/valid_de.yaml`, `material/maths_quadratisch_de.txt`, `material/injection_de.txt`, in NRW notation. Tests: `index_pack` accepts each pack with the German template and refuses it with the French, English and Dutch ones (`pack.wrong_language`, every pair with `de`); `valid_de.yaml` validates against the German maths pack.
- [x] 4.4 Authoring path with fakes (`test_authoring_agent_de`, as `_nl`): material → transcription (German marks counted) → pack → curriculum, with a pack repair (renamed German heading) and a curriculum repair; repair messages German (`AGENT_WORDS["de"]`, `issue_text`); injection material is data. `test_authoring_runner_de`: `AuthoringRunner` stores a valid German chapter under `german_offered`.
- [x] 4.5 `PromptLibrary` over four languages (`test_prompt_library_languages`, `test_prompt_library_de`); `required()` lists only offered languages until 8.1; `unavailable()` names a missing German file when `de` is patched in.

**Verify:** `uv run pytest tests/unit/test_authoring_agent_de.py tests/unit/test_prompt_files_languages.py -q`.

## Phase 5 — The German tutor: tutor, mode and subject prompts, pins, voice (R2, R3, R8)

**Goal:** a German turn in each mode is assembled from German files and its cached prefix is pinned; voice and dictation follow. **Done when** the German system-text hashes, the wall test and the voice test pass.

- [x] 5.1 `prompts/tutor.de.md`, `modes/{parcours,discussion,revision}.de.md` and `.opening.de.md`, `subjects/{mathematics,sciences,languages,general}.de.md` from the English twins (§6: « Auf die Tafel schreiben » in NRW notation with `P(2 \mid -1{,}5)`, voice blocks, statistics/flowchart words, glossary labels). Tests: skeleton parity (headings, markers once and in order, tool and block names), subject-, mode- and gender-neutral tutor prompt, cites `Zu prüfende Punkte` (= every German template's last heading), every mode has both files, the cited button labels equal `de.json`'s. **READ**.
- [x] 5.2 Fixtures and script rows: `chapters/folgen_de/{pack.md,curriculum.yaml}` and the German révision fixture twin; `seed.COURSE_NAME_BY_LANGUAGE["de"]`, `chapter_files.DEFAULT_CHAPTER_DIRS["de"]` and `REVISION_CHAPTER_DIRS` row, `smoke.SECOND_TURN["de"]`, `conftest.py` German lesson row. Tests: `test_seed --language de`, `load_chapter_dir` validates `folgen_de`, `test_chapter_files_de`.
- [x] 5.3 Pins: `system_text_sha_de.txt`, `_de_discussion.txt`, `_de_revision.txt` (created once, **READ**, pinned); each (language, mode) has its own prefix.
- [x] 5.4 Turn tests: `test_prompt_service_de`, `test_course_language_turn`, `test_revision_endpoint` gain `de`: a German chapter's model input equals its pinned rendering in each mode; `registry.declarations(mode,"de")` is the French bytes.
- [x] 5.5 The wall (`test_model_input_wall`, `test_revision_input_wall`): a German course under `fr`, `en`, `nl`, `de` accounts → identical input; four courses → four inputs, each equal to its pin.
- [x] 5.6 Voice and dictation: German instructions with the voice block, `"transcription": {"language": "de"}`, `realtime_declarations(mode,"de")` = French bytes; dictation hint `de` except `languages`. Tests `test_voice_service` (other configs byte-identical, German case added), `test_dictation_endpoint`.
- [x] 5.7 Work reading in German (`_PHOTO_LABEL["de"]`, `work.de.md`): `test_work_reading_de`, `test_work_endpoint` for a German course.

**Verify:** `uv run pytest`; `uv run python -m scripts.seed --email a@x.de --password '…' --language de` creates a German seed chapter.

## Phase 6 — The course language, frontend (R7)

**Goal:** the board draws NRW notation and the page knows a German course. **Done when** formatter, learner-sentence and `lang` tests pass in four languages.

- [x] 6.1 `lib/course-language.tsx` (`COURSE_LANGUAGES` four codes), `lib/tutor/prompts.ts` `LEARNER_SENTENCES.de` (every key, App. A), `lib/tutor/transcription-markers.ts` `MARKER_EXAMPLES.de`. Tests: provider default and nesting, learner sentences per language, cited-sentence parity against `modes/*.de.md` (read from `backend/prompts`), the source hint renders the German marks; other languages byte-identical.
- [x] 6.2 `charts/format.ts`: `GERMAN` as an explicit object (§5.2), `NOTATION.de`. Tests: the shared `notation_cases.json` `de` rows (formatter writes each `text`, `(2 | −1,5)` included), `notation-views` over four languages, a histogram, a box plot (`unteres Quartil`, `Median`) and a pie chart under `de`; French formatter tests untouched.
- [x] 6.3 Create form, course card, header, chapter bar: four autonyms, `lang="de"` on German course text. Tests: `create-course-form` (lists what the server lists), `course-language`, the sweeps: a German interface on French, English and Dutch courses; the other interfaces on a German course.

**Verify:** `cd frontend && npm run typecheck && npm run lint && npm test`.

## Phase 7 — Probes and remaining fixtures (R9.1 to R9.6)

**Goal:** the German probe sets exist and run dry; the evals harness takes `de`. **Done when** the offline probe tests pass and `probe --language de --dry-run` loads every chapter.

- [x] 7.1 Fixtures: `chapters/{statistik_de,koordinatengeometrie_de,ungleichungen_de,gleichfoermige_bewegung_de}` and `material/{maths_statistik_de,physik_gleichfoermig_de}.txt` in NRW notation (or German material the user supplies, design §14.2). Tests: each validates against its German template and the curriculum rules.
- [x] 7.2 `scripts/probe.py`: `de` rows for every `probe_tables` entry, `OUT_DE` and the other output paths, `GUARDRAIL_PROBES_DE`, `DISCUSSION_PROBES_DE`, `REVISION_PROBES_DE` (leak requests, formula outside the pack, skipping only on request, off-topic, the student's own révision assessment, a German injection), drawing probe rows, `DRAWING_SETS_BY_LANGUAGE["de"]`; `bad_notation` for German (decimal point, thousands comma, English intervals, a point without `|`); `has_foreign` takes the course language and checks the other three (new `DUTCH_STOPWORDS`, §4.8). Tests `test_probe_flags_de`: each flag fires on a sample and stays silent on correct German in NRW notation; `PROBE_LANGUAGES == list(COURSE_LANGUAGES)` passes.
- [x] 7.3 `smoke`, `voice_smoke`, `voice_probe`, `authoring_eval` (`FIXTURES["de"]`), `document_eval` take `--language de`. Tests `test_scripts_language`, `test_scripts_import`.
- [x] 7.4 `evals/`: `LANGUAGES`, `--language` `choices`, `judge.LANGUAGE_NAMES["de"]`, `README.md`; the guard test of 0.7 passes; the leakage gate fires for a German run with leakage (`test_metrics`).

**Verify:** `cd backend && uv run pytest && uv run python -m scripts.probe --language de --dry-run`; `cd evals && uv run pytest`.

## Phase 8 — Offer German (R1, R2, R3.8, R10)

**Goal:** a student creates a German course and is taught in German. **Done when** the integration tests pass with the real `SUBJECTS` and the manual check is made.

- [x] 8.1 `domain/subject.OFFERED` gains `"de"`; `german_offered` removed where the real list now serves; the pinned lists move to four codes in the same edit: `test_language`, `test_subjects`, `test_courses_endpoint`, `test_dutch_course`, `course-language.test.tsx`, `i18n-format.test.ts`, `notation-views.test.tsx`, `create-course-form`. `PromptLibrary.required()` now requires every German file.
- [x] 8.2 Integration `test_german_course` (as `test_dutch_course`): create a German course per subject, `422` for `es`, `PATCH` of `language` refused, a German chapter from a document with the scripted fakes, the lesson view, a turn with the German prefix, a discussion, a révision with a recorded self-assessment, DTOs carry `language: "de"`, another student's German course is a 404.
- [x] 8.3 Documentation (R10, design §12): `documentation/i18n.md`, `course-language.md` (four languages; the table list completed; NRW notation; « Adding things → A language » with the `MEMBERS` and « unsupported code » lessons), `README.md`, root `CLAUDE.md` (spec 010/011 bullets, the notation invariant: German courses use NRW notation), `backend/CLAUDE.md`, `specs/product.md` (requirements §2 lines, open question 4 answered).

**Verify:** `cd backend && uv run pytest`, `cd frontend && npm test`. Rebuild the Docker image (`docker build -t celestin:local .`) and recreate the container as in `documentation/docker.md`; register under a German browser, create a « Mathematik » course in German, drop a German worksheet (real provider; costs money), open the lesson: Célestin writes German with « du », the board shows `0,45`, `]2 ; 5[`, `P(2 | −1,5)`, `Absolute Häufigkeit`; a French, an English and a Dutch course behave as before.

## Phase 9 — Close and real-model checks (R9.7)

**Goal:** the documentation is true and the status honest. **Done when** the checks pass and `specs/index.md` says what was and was not run and read.

- [x] 9.1 Full suites: backend, frontend (`i18n:check`, typecheck, lint, test), evals; `git status` shows no regenerated French, English or Dutch golden.
- [ ] 9.2 Bundle growth (client JS before/after `de`, `NITRO_PRESET=node-server npm run build`) in Findings.
- [ ] 9.3 **READ** by the user, in one pass if not done earlier: `de.json`, `de.py`, the 20 prompt files, the render goldens, the system-text renderings. Corrections applied; pins regenerated only for `de`.
- [x] 9.4 `specs/index.md`: Implemented, with the review status and which of 9.6 ran.
- [x] 9.5 Commit hygiene check for the user: the list of new and changed files per area, to commit in reviewable pieces.
- [ ] 9.6 **Run by hand** (spends the OpenAI key): `smoke --language de` (cache OK per mode), `probe --language de` then `--charts --flowcharts --figures --plots` and the révision set, `voice_smoke`/`voice_probe --language de`, `authoring_eval --language de`, `document_eval --language de` on a real worksheet from the school. The user reads the transcripts. Record in Findings: answer-leak rate (< 1 %), formulas outside the pack (0), leakage (0), the `TOOL_TEXT["de"]` decision, `CHARS_PER_TOKEN` against `ai_usage`, any notation the user corrects.

## Findings

- **Suites at the end of the epic:** backend 5465 passed, 12 skipped (from 4945 before the epic); frontend 1845 (from 1787), `i18n:check` « messages ok (fr, en, nl, de) », typecheck clean, lint 0 errors (the 30 react-refresh warnings predate the epic); evals 61 (from 58).
- **9.2 bundle growth: not measured.** It needs a build of the base commit beside this one; the German catalog is 726 messages, the size of the Dutch one (spec 017 measured +3.0 % gzipped client JS for a catalog of that size).
- **`CHARS_PER_TOKEN["de"] = 3.4`** is the Dutch estimate; checking it against `ai_usage` needs a real run (9.6), **not done**.
- **9.6 was not run** (it spends the provider key and needs the user to read the transcripts): the answer-leak rate, formulas outside the pack, language leakage and the `TOOL_TEXT["de"]` decision (it stays `{}`) are unmeasured. Offline: `probe --language de --dry-run` (and `--charts`, `--flowcharts`, `--figures`, `--plots`, `--revision`) loads the five German chapters and checks every probe.
- **9.3 READ is pending**: `de.json`, `de.py`, the 20 prompt files, the `*_de.txt` render goldens and the three German system-text pins (`system_text_sha_de*.txt`) were written by us. The catalog sub-agent's open wording choices are listed under Deviations (1.2/2.2).
- Probe flag choice: a German `12.500` in Célestin's text is a *notation* flag (the board writes `12 500`), never a leak; the rules read it as twelve thousand five hundred.

## Deviations

Recorded as they appear. Known from planning:

- Phase 0 is larger than 017's because `de` was the tests' unsupported-code example and because the `|` point needed a member-separator table (`MEMBERS`) before any German row; both are in the design (§4.3, §4.9).
- `expression_cases.json`, `layer_cases.json`, `capacity.json` stay untouched (language-free), against R6.4's list (design §13).
- 0.5: `_LEAK` is a `by_language` table (fr = `None`, « no check »); the flag texts stay named constants (`FRENCH_LEAK`, `FOREIGN_LEAK`, and a German one in phase 7) rather than being built from `LANGUAGE_NAME`: the Dutch tests compare the constant byte for byte, and a per-language constant is as safe once `_LEAK` fails at import.
- 0.6: counts that follow the prompt files (`test_scripts_language`, `test_prompt_library_languages`) are derived from `subject.OFFERED`, not `COURSE_LANGUAGES`: the library requires files only for offered languages, so the tests stay green through phases 3–7 and move with 8.1. Literal parametrisations whose cases need per-language data (`test_probe_revision`, `test_probe_flags_en`, `test_revision_input_wall`) stay literal and gain `"de"` in the phase that adds the data (5, 7); evals `test_config` is parametrised over `LANGUAGES`.
- 1.2/2.2: the catalogs were written by a sub-agent from the English ones with the design's glossary; its open wording choices (« Wiederholen » for the review action, « Unterhaltung » for a lesson transcript so « Gespräch » stays the discussion mode, « Rückblick » for the recap card, « Lernende », « Weitere Fächer ») are left for the user's click-through. The model-facing `REPRISE` kinds follow the interface (« Rückblick » for `recap`).
- 2.4: the German sweeps are twins of the Dutch ones: a German interface on a Dutch course (`german-sweep`) and on French courses (lesson, discussion), as the Dutch originals do; German *courses* are swept in phase 6. One test-only streamed error (`overloaded`, no catalog key) is written in German in the test.
- 3.6 / 5.2 / 7.3 / 7.4: the `scripts/` rows (`seed`, `smoke`, `voice_probe`, `chapter_files`, `authoring_eval`, `probe._LEAK`) had to land with 3.1, not later: they are `by_language` tables and refuse to import without a `de` row. They point at fixtures that came with phases 4–5 (`folgen_de`, `statistik_de`, the `*_de.txt` materials).
- 3.4: German hole words accept inflected forms and a leading « von dir » (« Versteckter Schritt », « Von dir zu ergänzen »), read on `_plain_words` text (no umlaut, `ß` → `ss`).
- 3.5: no backend-only `recognised` rows were added to the shared `notation_cases.json` (the frontend formatter iterates every row); the hand-written German forms (`P(2|3)`, `(2;3)`, `12.500`, `1.500,5`, `0.125`) are pinned in `test_board_rules_de.py` instead.
- 5.x: the German révision fixture is the pair `folgen_de` + `statistik_de` (`REVISION_CHAPTER_DIRS["de"]`), no separate directory. `curriculum_render._DATE` became a `by_language` table so a German self-assessment reads « wackelt (12. November) »; the other languages' bytes are unchanged.
- 6.x: the frontend course-language part of phase 6 landed with phase 3 (the shared notation table gained `de` rows then). There is no frontend test that reads the backend prompt files for cited-sentence parity (none existed for Dutch either); the backend's `CITED["de"]` and the frontend's pinned German learner sentences hold the same texts.
- 7.2: the German probe set lives in `scripts/probe.py` like the Dutch one; the Dutch flag text `FOREIGN_LEAK` stays a constant (byte-identical), German has its own `GERMAN_LEAK`. Two shared probe patterns gained German forms only (« erste Glied ist $a_1$ », German „…“ quotes in the flowchart word check).
- 8.1: the temporary `german_offered` fixture and the « not offered yet » tests were removed once `subject.OFFERED` gained `de`.
- Catalog wording: the German interface copy calls the lesson transcript « Unterhaltung » (« Gespräch » is the discussion mode) and the recap card « Rückblick ».
- /simplify pass at the end: the date format of a self-assessment is a `date` field of `curriculum_render.Words` (no separate `_DATE` table); `_NUMBER_DE` is built from `_THOUSANDS_DOT`; `figures._bare` undoes the LaTeX delimiters with one compiled pattern; `plots._gives_values` splits once; the hole-word patterns of en/nl/de come from one helper (same bytes); in `scripts/probe.py` the stop-word lists share a base (`_stopwords(words, *shared)`), German quotes „…“ joined `_QUOTED_MATERIAL`, `LEAK_FLAGS` is derived from `_LEAK`, and the Dutch notation check uses `_round`. Kept on purpose: `subject.OFFERED` (the gate that staged the offering), `_LEAK` as a `by_language` table, the separate `_ZERO_INDEX_DE` (unifying it would flag `a_0` in English courses).
- 0.1 also moved the `de,en;q=0.5` / `de,nl;q=0.5` Accept-Language cases (the `de` there stood for « unsupported ») to `es`.

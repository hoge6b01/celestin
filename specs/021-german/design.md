# 021 — German (Germany): design

## 1. Overview

`de` becomes a fourth **interface language** (`Locale`) and a fourth **course language** (`CourseLanguage`). Spec 017 proved that a language is mostly **rows, files and fixtures**: `by_language` tables that refuse at import, `*.{lang}.md` prompt files, `Record<…>` tables on the frontend, and the guard `test_no_language_branches.py`. This design adds the `de` rows and files and fixes the places where German breaks an assumption the three existing languages share (§4.3).

**The one real difference is the point.** NRW Gymnasium material writes `P(2 | 4)`, intervals `[0 ; 1]`, `]a ; b[`, numbers `1000`, `10 000`, `12,5 %` (requirements §5.1). Everything but the point is the French notation. But the backend reads a pair's members as split by `;` or `,` only: a German `S(2 | 3)` on an open exercise's drawing would not be recognised as coordinates and **would leak the answer**. §4.3 makes the member separator a per-language table before any `de` row exists.

Decisions on the open points of the requirements (§5):

| # | Question | Decision |
|---|---|---|
| 1 | German notation | NRW forms (requirements §5.1). Board: decimal comma; `1000`, `10 000` (the French `fr-BE` "min2" grouping, same output); `12,5 %`; intervals `[a; b]`, `]a; b[`, `[a; b[`, `]a; b]`, `]−∞; 2]`, no space before the semicolon (own formatter; corrected after the textbook check, §5.1 addendum of the requirements); points `(2 \| −1,5)`; list separator `; `. Held in `GERMAN` (frontend, an explicit object, §5.2), the `*_DE` rule rows (backend, §4.6), `notation_cases.json` rows, and the German subject prompts. |
| 2 | `\|` in `[unsicher: a \| b]` | No code reads inside the mark: `count_markers`, `handwritten_numbers`, `apply_uncertain` and `validate_batch` only look for the prefix (`MARKERS[...].uncertain`). The German mark separates readings with **« oder »**: `[unsicher: P(2 \| 3) oder P(2 \| 8)]`. Only the German transcription prompts and `MARKER_EXAMPLES.de` say it; a test pins that `apply_uncertain` and `count_markers` accept such a line. |
| 3 | Register | « du » everywhere, administrators included. |
| 4 | Declarations / refusals | As English and Dutch: `TOOL_TEXT["de"] = {}`, declarations byte-equal to the French ones, refusals stay French; flipped only by German probe evidence (a French refusal sentence echoed in a German course's speech or card). |
| 5 | `CHARS_PER_TOKEN` | `3.4` (as Dutch, the closest language), checked against `ai_usage` (input tokens ÷ prompt characters) after the first German runs. |
| 6 | Review | The user (native speaker) reads the catalogs, the 20 prompt files, the render goldens and the probe transcripts. Status « German copy and prompts awaiting review » until then. |
| 7 | Dutch review debt and sweeps | Existing detectors (`en`, `nl`) unchanged; a new `de` detector (§5.5). A German course under another interface is marked `lang="de"` and so outside every other detector. |

## 2. Architecture

```
POST /api/courses {language:"de"} ──▶ require_language + require_offered ──▶ courses.language = "de"    (no migration: free strings)
     │
CourseRecord.language ─▶ LessonChapter.language ─▶ TurnContext.language                 (011 plumbing: unchanged)
     │                          │                        │
     │                          │                        ├─ by_language tables            +de row each           (§4.2)
     │                          │                        ├─ rule patterns / readers       +de: French shapes + `|` pairs (§4.6)
     │                          │                        │     plots.MEMBERS (new table, §4.3): `;` (fr, en, nl) · `;` or `|` (de)
     │                          │                        └─ registry.declarations(mode,"de")  == fr bytes
     │                          ├─ PromptLibrary: prompts/*.de.md   (20 files)                                   (§6)
     │                          └─ VoiceService: transcription hint "de"
     ▼
AuthoringRunner ─▶ AuthoringAgent.run(…, language="de")   MARKERS · numbering words · AGENT_WORDS · templates *.pack.de.md

users.locale = "de" ─▶ messages/de.py · frontend messages/de.json (Paraglide) · Accept-Language de, de-DE, de-AT, de-CH       (§4.1, §5.1)
Frontend: NOTATION.de = GERMAN · LEARNER_SENTENCES.de · MARKER_EXAMPLES.de · AUTONYM/INTL_TAG/error-page.de · create form
```

**Staged offering** (as 011 and 017): `SubjectInfo.languages` stays `("fr", "en", "nl")` until the last phase; `de` is built and tested underneath (tests patch `SUBJECTS`, as the `dutch_offered` fixture did), then switched on in one edit with the pinned language lists. The interface language is user-visible as soon as its catalogs exist.

## 3. Data models

No database change: `users.locale` and `courses.language` are `String(8)` with default `'fr'` and no check constraint (migrations 0006, 0007; `test_head_matches_the_models`). No DTO change beyond the `Literal`.

```python
# domain/locale.py      Locale = Literal["fr", "en", "nl", "de"]          # LOCALES via get_args: fr, en, nl, de
# domain/language.py    CourseLanguage = Literal["fr", "en", "nl", "de"]
# domain/subject.py     SubjectInfo(..., ("fr", "en", "nl", "de"))       # last phase only
```
```ts
// lib/locale.ts           LOCALES = ["fr", "en", "nl", "de"] as const;  AUTONYM.de = "Deutsch"
// lib/course-language.tsx COURSE_LANGUAGES = ["fr", "en", "nl", "de"] as const
// project.inlang/settings.json  "locales": ["fr", "en", "nl", "de"]
```

`Accept-Language`: `de`, `de-DE`, `de-AT`, `de-CH` → `de` (primary-subtag rule, unchanged code).

## 4. Backend

### 4.1 Types, catalog, locale

- `Locale`, `CourseLanguage` gain `"de"`.
- `app/domain/messages/de.py`: `MESSAGES` with the 143 keys of `fr.py`, same `{fields}`, plural keys `*.one`/`*.other`; `CATALOGS["de"]`. `plural_category` already gives German's rule (one iff 1) in its non-French branch. New keys in every catalog: `language.de` (`allemand` / `German` / `Duits` / `Deutsch`); `de.py` has `language.fr`/`en`/`nl` (`Französisch`, `Englisch`, `Niederländisch`).
- `domain/messages/issues.WHERE_WORDS["de"]` (App. A).

### 4.2 Per-language tables: the `de` rows

Every table below gains `de=`; each fails at import until it has it (`test_by_language_tables.py`).

| Table | Module | `de` row |
|---|---|---|
| `MARKERS` | `domain/transcription.py` | App. A |
| `_NUMBERING_BY_LANGUAGE` | `domain/pack.py` | `_NUMBERING_DE`, built like the Dutch one from `_KEYWORD_DE` (App. A) |
| `_LANGUAGE_NAMES_FR` | `domain/pack.py` | `"allemand"` |
| `KIND_LABELS` | `domain/curriculum.py` | `teach: Lektion`, `practise: Übungen`, `synthesis: Zusammenfassung` |
| `WORDS`, `REPRISE`, `REVISION` | `services/curriculum_render.py` | from the English rows field by field (App. A glossary); days, months, parts and révision outcomes in App. A |
| `WORDS` | `services/path.py` | from the English row (App. A glossary) |
| `SAVE_FAILED`, `_UNKNOWN`, `_OUTPUT`, `_WORDS` (registry, result) | `tools/context.py`, `section.py`, `pace.py`, `registry.py`, `result.py` | from the English rows (App. A glossary) |
| `TOOL_TEXT` | `tools/registry.py` | `{}` |
| `CHARS_PER_TOKEN` | `services/history.py` | `3.4` |
| `AGENT_WORDS` | `services/authoring/words.py` | from the English row (App. A glossary) |
| `_PHOTO_LABEL` | `services/work_reading.py` | `Hier ist das Foto der Arbeit der Schülerin oder des Schülers.` |
| `PACK_WORDS_BY_LANGUAGE`, `GROUPS`, `COMMA`, `MEMBERS` (new) | `tools/plots.py` | §4.6, App. A |
| `HOLE_WORDS` | `tools/flowcharts.py` | App. A |
| `INTERVAL`, `COORDS`, `NUMBER`, `DEGREES`, `LENGTH` | `tools/figures.py` | §4.6 |

Rows of the other languages keep their names and bytes.

### 4.3 Structural fixes (before any `de` row)

Each change keeps the French, English and Dutch behaviour, pinned by their existing tests.

1. **`tools/plots._gives_values`** splits a group's members with a hard-coded `";" in group` / `group.split(";")`, then falls back to `COMMA[language]`. A German pair `(2 | 3)` has neither and counts one value: `gives_away` misses it. New table, next to `COMMA`:
   ```python
   _MEMBERS = re.compile(";")                    # the course's separator, never prose's
   _MEMBERS_DE = re.compile(r"[;|]")             # German points: (2 | 3); intervals keep `;`
   MEMBERS = by_language(fr=_MEMBERS, en=_MEMBERS, nl=_MEMBERS, de=_MEMBERS_DE)

   def _gives_values(group, language):
       if MEMBERS[language].search(group):
           return any(_VALUE.search(m) for m in MEMBERS[language].split(group))
       return sum(1 for m in COMMA[language].split(group) if _VALUE.search(m)) >= 2
   ```
   An absolute value in a group (`(|−2|)`) is then read as giving a value in German: refused on an open exercise's label, the safe direction (one rewrite).
2. **`tools/figures.COORDS`** has no shape with `|`: the `de` row adds one (§4.6). Not a structural change, but the reason `notation_cases.json` gains `recognised` rows for `P(2|3)`.
3. **`de` is the tests' « unsupported language ».** About twenty tests (backend, frontend, evals) and the shared `accept_language_cases.json` row `{"header": "de-DE", "expected": "fr"}` use `de` as the example of a code that is refused. They switch to `es` (Spanish, not planned) **before** `de` enters any `Literal`, so they keep testing a refusal. `test_by_language_tables.py` adds a hypothetical `de` language to prove each table refuses it: it switches to `xx`. List in §4.9.
4. The hand-written language lists outside a table (§4.9) become `by_language` tables or gain a guard test, so that a missing `de` fails at import or in a test, not at runtime.

`test_no_language_branches.py` already forbids `language == "<code>"` comparisons in `app/` and `scripts/`; its `CODES` gains `"de"`.

### 4.4 Prompt library and subjects

`file_name(base, language)` builds `base.de.md`; `PromptLibrary` iterates the offered languages: no code change. `SubjectInfo.languages` gains `"de"` in the last phase. `/api/health` lists a broken German file by name.

### 4.5 Authoring

- `MARKERS["de"]`, `_NUMBERING_BY_LANGUAGE["de"]`, `AGENT_WORDS["de"]`, `_LANGUAGE_NAMES_FR["de"]` (§4.2). The transcription prompt names `[handschriftlich]`, `[unsicher: a oder b]`, `[unleserlich]`, `[leere Seite]`, `[Abbildung: …]`, `[durchgestrichen: …]`, and « übersetze nie ».
- Four templates `templates/<subject>.pack.de.md`: same `exercises_section: 6`, same seven headings in the same positions (App. A). With four languages `other_templates` has three entries; `index_pack` reports `pack.wrong_language` for the first whose headings match, for every pair involving `de`.
- `issue_text(issue, "de")` reads the `de` catalog entry for the issue's code: every `issue.*` key exists in `de.py`.

### 4.6 Tool rules

Rule functions read `ctx.language`. Both readers must see a LaTeX bar as `|`: `figures._bare()` gains `\mid` and `\vert` → `|` in `_TEX_DELIMITER`, and `plots.gives_away` replaces them the same way when it builds `flat`. Without this, `P(2 \mid -1{,}5)` — how the German prompt tells Célestin to write a point — would slip past both rules. For the other languages it changes nothing (no row of theirs splits on `|`; their tests pin it).

```python
# figures.py
_COORDS_BAR = re.compile(rf"\({_BOUND}[^;|()]*\|{_BOUND}[^;|()]*\)")     # (2|-1,5), the NRW point
_COORDS_DE = re.compile(f"(?:{_COORDS_NL.pattern})|(?:{_COORDS_BAR.pattern})")
_INTERVAL_DE = _INTERVAL_NL          # board `]a;b[`; by hand also `(a;b)`, `]a,b[`, `(a,b]`
_NUMBER_DE = r"([1-9]\d{0,2}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)"     # 1.500 is thousands in German
_DEGREES_DE = re.compile(rf"^(?:[^=]*=)?{_NUMBER_DE}°$")
_LENGTH_DE = re.compile(rf"^(?:[^=]*=)?{_NUMBER_DE}(mm|cm|dm|m|km)?$")

def _german_number(text: str) -> float:
    """`12.500` and `1.500,5` group thousands with a dot; anything else is a decimal comma (`1,5`, `0.125`)."""
    if re.fullmatch(r"[1-9]\d{0,2}(?:\.\d{3})+(?:,\d+)?", text):
        text = text.replace(".", "")
    return float(text.replace(",", "."))

NUMBER = by_language(..., de=_german_number)

# plots.py
_GROUPS_DE = _GROUPS_EN              # outward brackets, and the mixed ones written by hand
_COMMA_DE = _COMMA                   # `(0,5)` is one value, `(1, 4)` a pair
# MEMBERS["de"] = [;|]  (§4.3)
```

- A space-grouped `10 000` is `10000` after `_bare`: read correctly by every row.
- A decimal alone in brackets (`]0,5[`, `(2,5)`) is read as an interval or a pair, as for Dutch: refused on an open exercise's label, the safe direction.
- `PACK_WORDS_BY_LANGUAGE["de"]`, `HOLE_WORDS["de"]`: App. A; one accepted and one refused sentence per entry fix the final patterns.
- Shared case tables: `notation_cases.json` (both copies) gains `de` rows: the formatter writes `text` (`[2 ; 5[`, `]−∞ ; 2]`, `(2 | −1,5)`, `12,5 %`, `10 000`, `1000`), and the backend `INTERVAL["de"]`/`COORDS["de"]`/`NUMBER["de"]` recognise and read it back; backend-only `recognised` rows for `P(2|3)`, `(2;3)`, `(2, 3)`, `]2, 3[`, `12.500` (→ 12500), `1.500,5` (→ 1500.5), `0.125` (→ 0.125). `expression_cases.json`, `layer_cases.json`, `capacity.json` are language-free: untouched (the requirement listed them; nothing in them is language data).

### 4.7 Voice, declarations, history

`VoiceService` passes `"de"` as the Realtime input-transcription hint; dictation passes `"de"` except for the `languages` subject (unchanged rule). `registry.declarations(mode, "de")` = French bytes (`board_declarations.json` untouched). `history.estimate_tokens(…, "de")` uses 3.4.

### 4.8 Scripts and evals

`--language de` for `seed`, `smoke`, `probe`, `voice_smoke`, `voice_probe`, `authoring_eval`, `document_eval` (each validates against `COURSE_LANGUAGES`); their `by_language` tables (`DEFAULT_CHAPTER_DIRS`, `COURSE_NAME_BY_LANGUAGE`, `SECOND_TURN`, `voice_probe` words, `authoring_eval.FIXTURES`, `probe_tables`) gain `de` rows.

- **Probe flags (German)**: `bad_notation` flags a decimal point between digits outside a pack quote (`0.45`), a thousands comma (`12,500`), English intervals (`(a, b)`, `[a, b)`), and a point written `(2 ; 3)` or `(2, 3)` where the board writes `(2 | 3)` (a notation flag, not a leak). `leakage_flags` checks French, English and Dutch: `FRENCH_STOPWORDS`, `ENGLISH_STOPWORDS` (existing), and a new `DUTCH_STOPWORDS` of words that are not German (`het`, `een`, `niet`, `jij`, `zijn`, `wordt`, `maar`, `ook`, `deze`, `welke`).
- **Probe sets**: `GUARDRAIL_PROBES_DE`, `DISCUSSION_PROBES_DE`, `REVISION_PROBES_DE` (the English sets translated: leak requests, formula outside the pack, off-topic, skipping only on request, the student's own révision assessment, a prompt injection in German); the drawing probes on German chapters with their per-language rows (`STEPS`, `CLOSING`, `FLOWCHART_WORD`, `FIGURE_NAMES`, `CONVENTION`, `RIGHT_ANGLE`, `WRITTEN_INTERVAL`, `SAMPLE_WORD`).
- **Report**: « Rapport — cours en allemand … »; leakage « mots français, anglais ou néerlandais ».
- **`evals/`**: `harness/config.LANGUAGES` and the `--language` `choices` gain `"de"`; the leakage gate applies to any non-French course, as today.

### 4.9 Inventory of hand-written language lists

From a sweep of every `"nl"` in `backend/`, `frontend/`, `evals/`. No `== "<code>"` branch remains in application code (only `plural_category`'s allow-listed `locale == "fr"`, correct for German).

| Site | Today | Change |
|---|---|---|
| `domain/messages/__init__.CATALOGS` | hand dict + hand import | add `"de": DE`; `test_messages.py` already pins `set(CATALOGS) == set(LOCALES)` |
| `domain/messages/issues.WHERE_WORDS` | `dict[Locale, …]` | add `de`; `test_issue_messages` pins `set == LOCALES` |
| `domain/subject.py` | `("fr","en","nl")` repeated for four subjects | one module constant `OFFERED = ("fr", "en", "nl")`, read by the four; becomes four codes in the last phase (one edit) |
| `issues.issue_text` | passes a `CourseLanguage` as a `Locale` | unchanged: holds because `de` is both; `test_language.py` pins « every course language is a locale » |
| `scripts/probe._LEAK` | hand dict `{"en": …, "nl": …}` (a `de` course: `KeyError` at runtime) | `by_language` (fails at import) |
| `scripts/probe.FOREIGN_LEAK`, `LEAK_FLAGS` | flag text names « néerlandais » | flag text from a `LANGUAGE_NAME` `by_language` row |
| `evals/harness/config.LANGUAGES`, `worker.py` `choices` | hand tuple (the harness never imports the backend) | add `"de"`; a new evals test **reads** `backend/app/domain/language.py` (AST, no import) and asserts the tuple equals the `Literal` |
| `evals/harness/judge.LANGUAGE_NAMES` | hand dict (`KeyError` for `de`) | add `de`; same guard test checks its keys |
| `evals/README.md`, `models.example.toml` | `fr\|en\|nl`, stale `fr \| en` | updated |
| frontend `LOCALES`, `COURSE_LANGUAGES`, `AUTONYM`, `INTL_TAG`, `TEXT`, `LEARNER_SENTENCES`, `MARKER_EXAMPLES`, `NOTATION`, sweep `FOREIGN` | typed `Record`s / `as const` lists | TypeScript forces the `de` row once the list gains it |

**Probe tables.** `scripts/probe.py` holds about 23 `probe_tables(...)` with `nl` rows; `probe_tables` tolerates a missing language (exits « no probe set ») until the German fixtures exist (phase of §8.2), then `test_probe_flags_en.py`'s `PROBE_LANGUAGES == list(COURSE_LANGUAGES)` requires them. The Dutch-specific blocks (`OUT_NL` and the other output paths, `*_PROBES_NL`, chapter references, `_CODE_NL`/`NOTATION_CHECK`, `_FRENCH_WORDS_NL`/`_ENGLISH_WORDS_NL`/`has_foreign`, flowchart/figure/plot rows, `DRAWING_SETS_BY_LANGUAGE`, the révision table) each gain a `de` twin; `has_foreign` takes the course language and checks the three other languages' word lists.

**Tests.** Pinned lists move in the last phase (`test_language`, `test_locale`, `test_subjects`, `test_courses_endpoint`, `test_dutch_course`, `course-language.test.tsx`, `i18n-format.test.ts`, `notation-views.test.tsx`). Counts that assume three (`== 3`, `3 * len`, `other_templates == ["en","nl"]`: `test_scripts_language`, `test_authoring_agent_nl`, `test_revision_rendering`, `test_prompt_library_languages`) are rewritten as `len(COURSE_LANGUAGES)` / derived lists, once, in phase 0. Literal parametrisations (`test_probe_revision`, `test_probe_flags_en`, `test_revision_input_wall`, evals `test_config`) are parametrised over `COURSE_LANGUAGES`. Tests parametrised over the lists but holding per-language rows inside (`test_course_language_turn`, `test_curriculum_render_skipped`, `test_subject_prompts`, `test_revision_endpoint`, `conftest.py`'s lesson rows) gain `de` rows with the German fixtures. Dutch-only suites (backend `test_*_nl`, `test_dutch_course`; frontend `dutch-*-sweep`, `dutch-course-language`, `plural-messages-nl`) get German twins (`test_*_de`, `test_german_course`, `german-*-sweep`, …) where their content is language-specific; nothing is copied where a parametrisation does.

## 5. Frontend

### 5.1 Interface language

`lib/locale.ts` (`LOCALES`, `AUTONYM.de = "Deutsch"`), `i18n-format.ts` (`INTL_TAG.de = "de-DE"`), `lib/error-page.ts` (`TEXT.de`, App. A). `messages/de.json`: the 726 keys of `fr.json`, same variables and plural forms (`one`/`other`); `npm run i18n:check` and Paraglide enforce parity. `accept_language_cases.json` (both copies) gain `de` rows (§8.1).

### 5.2 Notation

```ts
// charts/format.ts — NRW Gymnasium notation. An explicit object, not a spread of FRENCH: a later change to
// the Belgian notation must not move the German board. Where the NRW form is the French one, the French
// formatter function is named on purpose.
export const GERMAN: Notation = {
  number: formatNumber,                                   // fr-BE "min2": 1000, 10 000, decimal comma
  value: formatValue,                                     // 12,5 %
  pair: (x, y) => `(${formatNumber(x)} | ${formatNumber(y)})`,
  bound: formatBound,
  interval: formatInterval,                               // [2 ; 5[, ]−∞ ; 2]
  classLabel,
  measureName: { effectif: "Häufigkeit", frequence: "Relative Häufigkeit", pourcentage: "Prozent" },
  boxStats: ["Minimum", "unteres Quartil", "Median", "oberes Quartil", "Maximum"],
  separator: " ; ",
};
export const NOTATION: Record<CourseLanguage, Notation> = { fr: FRENCH, en: ENGLISH, nl: DUTCH, de: GERMAN };
```

`fr-BE` with `useGrouping: "min2"` writes a narrow no-break space (`10 000`), which is the NRW form; `de-DE` would write `10.000` and is therefore **not** used for the board (it is the interface's `INTL_TAG`, for sizes and counts only). The box-plot labels are longer than the others: checked at 400 px (R4.5.3); if they overflow, the layout wraps them, the words do not change. Wire identifiers do not change.

### 5.3 Learner sentences, markers, source hint

`LEARNER_SENTENCES.de` (every key of the English row, App. A). A test pins that each sentence the German `modes/*.de.md` cites equals the one the interface sends. `MARKER_EXAMPLES.de = { uncertain: "[unsicher: …]", illegible: "[unleserlich]", page: "--- page N ---" }`.

### 5.4 Create form, settings, badge, hyphenation

The language select and the settings list read `AUTONYM` over `COURSE_LANGUAGES` / `LOCALES`. One global rule `:lang(de) { hyphens: auto; overflow-wrap: break-word; }` in `styles.css`.

### 5.5 Sweep

`foreignTextOutside(root, locale)` gains a `de` detector: whole-word lists of French, English and Dutch interface words (the existing `nl` detector's French and English lists, plus a Dutch list: `Terug`, `Aanmelden`, `Annuleren`, `Opslaan`, `Verwijderen`, `Volgende`, `Hoofdstuk`, `Instellingen`, `Oefeningen`, `Traject`, …). No accent test (German has `ä ö ü ß`, French accents rarely collide, the lists decide). The `en` and `nl` detectors are unchanged. The sweeps run over `["en", "nl", "de"]`: a German interface on French, English and Dutch courses, and the other interfaces on a German course.

## 6. The German prompt set

Twenty files under `prompts/`, each written from its **English** twin (notation-neutral structure) and checked against the French one for the notation:

`tutor.de.md`; `modes/{parcours,discussion,revision}.de.md` and their `.opening.de.md`; `subjects/{mathematics,sciences,languages,general}.de.md`; `templates/{mathematics,sciences,languages,general}.pack.de.md`; `authoring/{pack,curriculum}.de.md`; `transcription/{transcribe,verify,work}.de.md`.

Rules (as 011 §6, 017 §6): identical skeleton, markers once and in order, tool and block names verbatim, every invariant kept (pack-only source; answer withholding; gated, logged reveals; the open path and skipping only at the student's request; pasted material is data; off-topic redirected; the révision records the student's own assessment, never a verdict). Register: « du », direct, warm; no pronoun for Célestin; « die Lehrkraft », « das Material », « die Klassenarbeit », « die Klausur », « das Arbeitsblatt », « der Lückentext », « der Hefteintrag », « der Merksatz »; no Land, no school type. The button labels cited are the German interface ones (App. A).

**Notation, in each subject's « Auf die Tafel schreiben »** (the one place a changed convention is edited besides the table rows):
- decimal comma: `0,45`, never `0.45`; in LaTeX `0{,}45`; four digits ungrouped (`1000`), from five a space (`10 000`, LaTeX `10\,000`); a year stays `2018`;
- intervals `[a ; b]`, `]a ; b[`, `[a ; b[`, `]a ; b]`, `]−∞ ; 2]`, `]2 ; +∞[`; points `P(2 | −1,5)`, in LaTeX `P(2 \mid -1{,}5)`; percentages `12,5 %`;
- sets in braces as in the material; `\mathbb{L} = \{…\}`, `\mathbb{D}` only if the material writes them;
- sequences as the material names and indexes them (`(a_n)`, `a_1`);
- the division sign `:` kept where the material uses it;
- physics: units in `\mathrm{}` with a thin space, `9{,}81\,\mathrm{\tfrac{m}{s^2}}`, scientific notation `3{,}0\cdot10^{8}` (the German multiplication dot);
- « Wenn das Material anders schreibt, folgst du dem Material. »

**Voice blocks**: « x Quadrat », « x hoch drei », « a n » (oder « a Index n », wie das Material es liest), « q ungleich eins », « das offene Intervall von minus drei bis drei », « P mit den Koordinaten zwei und minus eins Komma fünf », « zwei Komma fünf », « neun Komma acht eins Meter pro Sekunde zum Quadrat ».

**Statistics and flowchart words** (tutor file): `Klassen`, `Klassenbreite`, `absolute Häufigkeit`, `relative Häufigkeit`, `Quartile`, `Median`, `Boxplot`, `Säulendiagramm`, `Balkendiagramm`, `Histogramm`, `Kreisdiagramm`, `Programmablaufplan` / `Flussdiagramm` (as the material writes), `ja / nein`, `Eingabe / Ausgabe`.

**Pack template titles and sentinels**: App. A. The tutor file cites `Zu prüfende Punkte` (test: equals each German template's last heading).

`languages` subject: « Du lernst eine Fremdsprache (oft Englisch, Französisch oder Latein) auf Deutsch »: Célestin speaks German and works in the studied language.

## 7. Error handling

| Case | Behaviour |
|---|---|
| `language: "de"` before the last phase | `422 invalid_language` (not offered), message in the interface language |
| A `by_language` table without `de` | fails at import, never at runtime |
| A German prompt/template file missing or broken | startup stops naming it; `/api/health` lists it |
| A catalog key missing in `de` | `i18n:check` / `test_messages` fail; at runtime the French text with a logged `i18n_fallback` (010) |
| Pack in the wrong language of the four | `pack.wrong_language` first (any pair involving `de`); student reads it in the interface language, the repair loop in the course's |
| Material in another language than the course's | not detected; the student's to correct |
| `(2 \| 3)` on an open exercise's drawing | refused (`exercise_text`, figures' label rule) in a German course, as `(2 ; 3)` is in French |

## 8. Testing strategy

### 8.1 Offline

- **Existing pins untouched**: `system_text_sha*.txt` (fr, en, nl), `tests/fixtures/render/*` (fr, `_en`, `_nl`), `board_declarations.json`, `error_messages_fr.json`, `status_messages_fr.json`, `markers_fr.json`, the golden SSE transcripts, the French, English and Dutch rule tests.
- **Structural fixes first** (§4.3, §4.9): the « unsupported code » tests moved from `de` to `es` (and `xx` in `test_by_language_tables`), with the shared `accept_language_cases.json` row changed in both copies; `MEMBERS` with the three existing rows; `gives_away` cases for fr/en/nl unchanged; `_bare` with `\mid`; `probe._LEAK` as a table; the evals guard test; the count-assuming tests derived from `COURSE_LANGUAGES`. The whole suite passes unchanged in behaviour before any `de` row.
- **Tests that list the languages**: a test about every language is parametrised over `COURSE_LANGUAGES`/`LOCALES`; a test that pins the list (`test_language`, `test_locale`, `test_subjects`, `test_courses_endpoint`, `create-course-form`, `course-language`) moves to four languages only in the last phase, with `SUBJECTS`.
- **New or extended**: `by_language` coverage; catalog parity over four catalogs and `set(CATALOGS) == set(LOCALES)`; `Accept-Language` (`de`, `de-DE`, `de-AT`, `de-CH`, `de-DE;q=0.8,fr;q=0.9` → fr, `fr,de;q=0.8` → fr, `de;q=0` → fr, `es,de;q=0.5` → de), both copies; prompt-file tests for `de` (markers, skeleton parity, cited heading, no French/English/Dutch prose: three stop-word lists, tool names and `Célestin` excepted); `PromptLibrary` over four languages; `system_text_sha_de.txt`, `_de_discussion`, `_de_revision`; German render goldens (`*_de.txt`, read by the user, then pinned); `moment()` in German; `MARKERS`/`validate_batch`/`handwritten_numbers`/`apply_uncertain` for `de`, including `[unsicher: P(2 | 3) oder P(2 | 8)]`; `chapter_title` (`Kapitel 3:`, `Kap. 2 –`, `Lektion 4)`, `Thema IV.`, no false positive on `Teilchen`); `index_pack` for every pair with `de`; `issue_text(·,"de")`, `render_where("de")`; `NUMBER["de"]` (`12.500`, `1.500,5`, `1,5`, `0.125`, `10000`); rule tables (`PACK_WORDS`, `HOLE_WORDS` sentences; `INTERVAL`, `COORDS` incl. `P(2|3)`; `gives_away("S(2 | 3)", "de")` true, `gives_away("S(2 | 3)", "fr")` unchanged); `notation_cases.json` both sides; the wall test over four languages; the voice config (`"language": "de"`); `test_language_is_passed` and `test_no_language_branches` passing.
- **Frontend**: `GERMAN` formatter rows; learner sentences + cited-sentence parity; `AUTONYM`/`INTL_TAG`/error page; `lang="de"` on course text; the create form lists four autonyms; the sweeps over `["en", "nl", "de"]`.

### 8.2 Fixtures

`tests/fixtures/`: `packs/{maths_valid_de,sciences_valid_de}.md`, `curricula/valid_de.yaml`, `material/{maths_quadratisch_de,maths_statistik_de,physik_gleichfoermig_de,injection_de}.txt`, chapter directories `{folgen_de,statistik_de,koordinatengeometrie_de,ungleichungen_de,gleichfoermige_bewegung_de}/{pack.md,curriculum.yaml}` and the révision fixture's German twin, written to the German templates in NRW notation. Test fixtures only, never offered to students. Offline phases need `maths_valid_de`, `valid_de`, `folgen_de` and one material text; the rest come with the probes phase.

### 8.3 Real-model checks (run by a person, recorded in `tasks.md`)

`smoke --language de` (cache OK per mode), `probe --language de` (guardrails, révision, then `--charts --flowcharts --figures --plots`), `voice_smoke`/`voice_probe --language de`, `authoring_eval`/`document_eval --language de` (one real NRW worksheet). Reported per course language: answer-leak rate (< 1 %), formulas outside the pack (0), leakage (0). The first run decides `TOOL_TEXT["de"]` and checks `CHARS_PER_TOKEN`. The user reads the transcripts.

## 9. Performance considerations

A few dozen more compiled patterns at import; prompt files cached by mtime; one more cached prefix per (subject, mode) for German courses only. Paraglide compiles four catalogs into one bundle: the added weight (about the size of `nl`) is measured from the build output and reported in the tasks.

## 10. Security considerations

`language` from a body goes through `require_language`; file names come from `file_name(base, language)` with a `Literal`. Pasted material is data in German (the German prompts carry the rule; a German injection probe runs). The `|` structural fix closes a leak path for German courses before they exist. Nothing new is logged about a student. `de` in `Accept-Language` selects a catalog, never a path.

## 11. Monitoring and observability

Existing lines carry `language` (`course_created`, `authoring_started`); `i18n_fallback`/`i18n_missing` signal an untranslated key; `/api/health` lists a broken German file. No new log line.

## 12. Documentation to update with the implementation

`documentation/i18n.md` (four interface languages, `Accept-Language` for `de`, `WHERE_WORDS`, the `de` sweep), `course-language.md` (four languages; the per-language table list completed with `REPRISE`, `REVISION`, `NUMBER`, `_PHOTO_LABEL`, result `_WORDS`, `MEMBERS`; the German notation section; « Adding things → A language » corrected with the `MEMBERS` lesson), `README.md`, root `CLAUDE.md` (the spec 010/011 bullets, the notation invariant), `backend/CLAUDE.md` (language lists), `specs/product.md` (lines of requirements §2), `specs/index.md`.

## 13. Differences from the requirements

| Requirement | Design |
|---|---|
| R4.1 `[unsicher: a \| b]` | `[unsicher: a oder b]`: the bar is the German point's separator; no code reads inside the mark. |
| R7.2 « its own notation, not a reference to `FRENCH` » | An explicit `GERMAN` object; it names the French formatter functions where the NRW form is identical (number, value, bound, interval, class labels), so it does not inherit later French changes by spread. |
| R6.4 shared case tables | Only `notation_cases.json` holds language data; the other three are language-free and stay untouched. |
| R5.3 | `CHARS_PER_TOKEN["de"] = 3.4`, an estimate to verify. |
| R3/R5 word tables | The appendix fixes the words that carry notation, identity or interface labels; the other rows are translated field by field from English with the glossary and read by the user (READ tasks). |

## 14. Open points for the user

1. The review: catalogs (`de.json`, `de.py`), 20 prompt files, render goldens, probe transcripts. The spec status depends on it.
2. One real worksheet or textbook page from the school (any subject) for `document_eval --language de`: the only test of German transcription on real material.

## Appendix A — German words

**Interface glossary** (catalogs and the labels the prompts cite; one word per concept everywhere): Mes cours = *Meine Kurse*; cours = *Kurs*; chapitre = *Kapitel*; parcours = *Lernpfad*; section = *Abschnitt*; discussion = *Gespräch*; révision = *Wiederholung*; bilan = *Rückblick*; séance = *Sitzung*; cahier = *Heft*; Paramètres = *Einstellungen*; Passer = *Überspringen*; Étape suivante = *Nächster Schritt*; Section suivante = *Nächster Abschnitt*; exercice = *Aufgabe*; matériel = *Material*; tableau = *Tafel*; administrateur = *Admin*.

**Model-facing glossary** (`AGENT_WORDS`, `WORDS`, `path`, tools): document = *Dokument*; material = *Material*; page = *Seite*; text layer = *Textebene*; chapter = *Kapitel*; path = *Lernpfad*; section = *Abschnitt*; exercise = *Aufgabe*; to repair = *überarbeiten*; points to check = *zu prüfende Punkte*; student = *die oder der Lernende* (in prose « deine Schülerin oder dein Schüler » is avoided: « die Lernenden », or address by « du » where the text speaks to the student); teacher = *Lehrkraft*; skip = *überspringen*; skipped = *übersprungen*. The French tag names (`<materiel>`, `<chapitre>`, `<lignes>`, `<couche_texte>`) stay.

**`curriculum_render`**: `days` Montag, Dienstag, Mittwoch, Donnerstag, Freitag, Samstag, Sonntag; `months` Januar, Februar, März, April, Mai, Juni, Juli, August, September, Oktober, November, Dezember; `parts` vormittags, nachmittags, abends; `moment` `{weekday}, {day}. {month}, {hour}:{minute:02d} Uhr ({part})`. `REVISION.outcomes`: `solid` « sitzt », `shaky` « wackelt », `todo` « nochmal üben ».

**`MARKERS["de"]`**: `handwritten` `[handschriftlich`; `uncertain` `[unsicher`; `illegible` `[unleserlich]`; `empty_page` `[leere Seite]`; `nothing` `[nichts lesbar]`; `missing` `fehlende Markierung für Seite `; `unexpected` `unerwartete Seite `; `disordered` `Seitenmarkierungen doppelt oder in falscher Reihenfolge`; `empty_without_marker` `leere Seite ohne „[leere Seite]“`.

**`_KEYWORD_DE`** (case-insensitive, as `_KEYWORD_NL`): `kapitel|kap\.?|lektion|lerneinheit|einheit|thema|teil|modul|abschnitt|sequenz|woche|stunde`, a number on its own with a closing mark (`4)`, `IV.`).

**Pack templates** (maths): `1. Ziel des Kapitels`, `2. Vorwissen`, `3. Schreibweisen und Konventionen`, `4. Begriffe in didaktischer Reihenfolge`, `5. Fachwortschatz`, `6. Typische Aufgaben`, `7. Zu prüfende Punkte`. § 3 sciences `Schreibweisen, Größen und Einheiten`; languages `Untersuchte Sprache und Konventionen`; general `Orientierungspunkte und Konventionen`. Sentinels: `Keine.`, `Nichts im Material.`, `im Material nicht korrigiert`.

**`PACK_WORDS["de"]`** (case-insensitive; final shapes fixed by the sentence tests): `exp` the French row's `\exp` / `e^` alternatives `|\bexponentialfunktion(?:en)?\b|\be-funktion(?:en)?\b`; `ln` `\bln\b|\bnatürliche[nr]?\s+logarithmus\b|\blogarithmus\s+zur\s+basis\s+\$?\s*(?:\\mathrm\{e\}|\{e\}|e)(?!\w)`; `log` `\blg\b|\blog(?![A-Za-z])|\bzehnerlogarithmus\b|\bdekadische[nr]?\s+logarithmus\b|\blogarithmus\s+zur\s+basis\s+\$?\s*10\b`; `cbrt` `\bkubikwurzel\b|\bdritte\s+wurzel\b|\\sqrt\s*\[\s*3\s*\]|∛`; `sin` `\bsin\b|\bsinus`; `cos` `\bcos\b|\bkosinus|\bcosinus`; `tan` `\btan\b|\btangens\b` (*Tangente* is the line: not a match).

**`HOLE_WORDS["de"]`** (on `_plain_words` text): head `(?:kasten|feld|schritt|knoten|text|block|frage|antwort)(?: nr\.?)?(?: \d+)?`; gap `(?:auszufüllen|zu ergänzen|ergänze|ergänzen|zu (?:finden|bestimmen|berechnen|schreiben)|noch zu (?:bestimmen|finden)|fehlt|fehlende?[rs]?|lücke|leer|versteckt|unbekannt|tbd)`; word list `head(?: gap)?|gap(?: head)?|[lc]?dots`.

**`WHERE_WORDS["de"]`**: words `{"titre": "Titel", "chapitre": "Kapitel", "parcours": "Lernpfad"}`; patterns `^exercice (\S+)$` → `Aufgabe \1`, `^section n°(\d+)$` → `Abschnitt Nr. \1`.

**`LEARNER_SENTENCES.de`**: `review` `Ich möchte den Abschnitt „{title}“ wiederholen.`; `start` `Fangen wir mit dem Abschnitt „{title}“ an?`; `resume` `Machen wir mit dem Abschnitt „{title}“ weiter?`; `skip` `Ich überspringe den Abschnitt „{title}“.`; `nextStep` `Nächster Schritt.`; `nextSection` `Nächster Abschnitt.`; `answer` `Meine Antwort auf die Frage: „{text}“.`; `work` `Hier ist meine Arbeit, gelesen von meinem Foto:\n{text}`; `assess` solid `Ich würde sagen, das sitzt.`, shaky `Ich würde sagen, das wackelt noch.`, todo `Ich würde sagen, das muss ich nochmal üben.`; `voiceToolFailed` `Werkzeug nicht verfügbar. Sag es der Schülerin oder dem Schüler und mach ohne weiter.`

**`work_reading._PHOTO_LABEL["de"]`**: `Hier ist das Foto der Arbeit der Schülerin oder des Schülers.`

**Error page `TEXT.de`**: title `Diese Seite wurde nicht geladen`; body `Bei uns ist etwas schiefgelaufen. Du kannst die Seite neu laden oder zur Startseite zurückgehen.`; retry `Erneut versuchen`; home `Zur Startseite`.

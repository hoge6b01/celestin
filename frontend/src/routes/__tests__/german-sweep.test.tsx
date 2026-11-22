// @vitest-environment jsdom
/**
 * The German sweep (spec 021 R7.6): every screen of the application, with the interface in German
 * and the data a German account really receives (the server writes German too), must hold no
 * French, English or Dutch outside a region that carries a `lang` of its own. The course is still a
 * Dutch one (German courses come later in the spec): its text is marked `lang="nl"`; anything else
 * in another language is a string nobody translated.
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LoginForm, RegisterForm, SetupForm } from "@/components/celestin/auth-forms";
import { foreignTextOutside } from "@/test/english-sweep";
import { withLocale } from "@/test/locale";
import { mockApi, mountRoutes, type Handler } from "@/test/route-harness";
import { Route as ChapterFile } from "../_auth/courses/$courseId/chapters/$chapterId/index";
import { Route as ContentFile } from "../_auth/courses/$courseId/chapters/$chapterId/content";
import { Route as NotebookFile } from "../_auth/courses/$courseId/chapters/$chapterId/notebook";
import { Route as CourseFile } from "../_auth/courses/$courseId/index";
import { Route as CoursesFile } from "../_auth/courses/index";
import { Route as RevisionFile } from "../_auth/courses/$courseId/revision";
import { Route as SettingsFile } from "../_auth/settings";
import { stubLayoutApis } from "@/test/jsdom-stubs";

vi.mock("@/components/celestin/math", () => ({
  Math: ({ tex }: { tex: string }) => <span>{tex}</span>,
}));

const LIMITS = {
  chapter_text_min_chars: 10,
  chapter_text_max_chars: 500,
  pack_max_chars: 60000,
  document_max_bytes: 26214400,
  document_max_pages: 50,
  document_min_pixels: 800,
  document_types: ["application/pdf", "image/jpeg", "image/png", "image/webp"],
};
const SUBJECTS = {
  subjects: [{ id: "sciences", label: "Naturwissenschaften", languages: ["fr"] }],
  limits: LIMITS,
};

const summary = {
  id: "c1",
  name: "Fysica 4e jaar",
  subject: "sciences",
  subject_label: "Naturwissenschaften",
  language: "nl",
  chapters_total: 3,
  chapters_done: 1,
  last_chapter: { id: "h1", title: "Eenparige beweging" },
  generating: 1,
};

const row = (over: Record<string, unknown> = {}) => ({
  id: "h1",
  position: 1,
  title: "Eenparige beweging",
  ready: true,
  section_count: 9,
  done_count: 2,
  state: "in_progress",
  last: true,
  authoring_state: "idle",
  authoring_message: null,
  authoring_stage: null,
  pages_done: 0,
  page_count: 0,
  authoring_received_chars: 0,
  authoring_quiet_s: null,
  ...over,
});

const DETAIL = {
  ...summary,
  chapters: [
    // One section skipped (spec 019): the row counts it apart.
    row({ skipped_count: 1 }),
    row({
      id: "h2",
      position: 2,
      title: null,
      ready: false,
      state: "not_started",
      last: false,
      section_count: 0,
      authoring_state: "generating",
      authoring_stage: "pack",
      authoring_received_chars: 12400,
      authoring_quiet_s: 50,
    }),
    row({
      id: "h3",
      position: 3,
      title: null,
      ready: false,
      state: "not_started",
      last: false,
      section_count: 0,
      authoring_state: "failed",
      authoring_stage: "transcription",
      authoring_message:
        "Das Lesen der Seiten hat zu lange gedauert. Lade das Dokument noch einmal hoch, oder weniger Seiten.",
    }),
  ],
};

// The pack and the path are the course's: Dutch here, and marked `lang="nl"` where they show.
const CONTENT = {
  id: "h1",
  course_id: "c1",
  subject: "sciences",
  position: 1,
  version: 2,
  ready: true,
  title: "De eenparige rechtlijnige beweging",
  pack: "# De ERB\n\n## 1. Doel van het hoofdstuk\n\nEen ERB beschrijven.\n",
  curriculum: {
    title: "De eenparige rechtlijnige beweging",
    sections: [
      {
        id: "snelheid",
        index: 1,
        kind: "teach",
        title: "De gemiddelde snelheid",
        goal: "De snelheid definiëren.",
        done_when: "Klaar",
        pack: ["§4.1"],
        beats: ["De definitie aanhalen."],
        exercises: [],
        count: null,
      },
      {
        id: "berekeningen",
        index: 2,
        kind: "practise",
        title: "Berekeningen",
        goal: "v berekenen.",
        done_when: "Klaar",
        pack: [],
        beats: [],
        exercises: ["6.1.1", "6.1.2"],
        count: 2,
      },
    ],
  },
  source_text: "--- page 1 ---\n\nDe tekst uit het document.\n",
  source_kind: "document",
  language: "nl",
  page_count: 2,
  authoring_received_chars: 0,
  authoring_quiet_s: null,
  authoring_state: "idle",
  authoring_message: null,
  has_progress: true,
};

const api =
  (extra?: Handler): Handler =>
  (method, path, body) => {
    const custom = extra?.(method, path, body);
    if (custom) return custom;
    if (path.endsWith("/api/subjects")) return { body: SUBJECTS };
    if (method === "GET" && path.endsWith("/api/courses/c1")) return { body: DETAIL };
    if (method === "GET" && path.endsWith("/api/courses")) return { body: { courses: [summary] } };
    if (method === "GET" && path.endsWith("/chapters/h1/content")) return { body: CONTENT };
    return undefined;
  };

const ROUTES = [
  { path: "/courses/", file: CoursesFile },
  { path: "/courses/$courseId/", file: CourseFile },
  { path: "/courses/$courseId/chapters/$chapterId/", file: ChapterFile },
  { path: "/courses/$courseId/chapters/$chapterId/content", file: ContentFile },
  { path: "/courses/$courseId/chapters/$chapterId/notebook", file: NotebookFile },
  { path: "/courses/$courseId/revision", file: RevisionFile },
  { path: "/settings", file: SettingsFile },
];

/** Open `initial` as a German account. */
const open = (initial: string, handler?: Handler) => {
  mockApi(api(handler), { locale: "de", name: "Lea" });
  return mountRoutes(ROUTES, initial);
};

const clean = () => expect(foreignTextOutside("de")).toEqual([]);

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("the German sweep: signed out", () => {
  it("sign-in and registration, with their validation messages", () =>
    withLocale("de", () => {
      render(<LoginForm onSuccess={() => undefined} />);
      fireEvent.click(screen.getByRole("button", { name: "Anmelden" }));
      return screen.findByText("Gib deine E-Mail-Adresse ein.").then(() => {
        clean();
        cleanup();
        render(<RegisterForm onSuccess={() => undefined} />);
        fireEvent.click(screen.getByRole("button", { name: "Konto erstellen" }));
        return screen.findByText("Gib deinen Vornamen ein.").then(() => {
          clean();
          cleanup();
          render(<SetupForm onSuccess={() => undefined} />);
          fireEvent.click(screen.getByRole("button", { name: "Admin anlegen" }));
          return screen.findByText("Gib deinen Vornamen ein.").then(clean);
        });
      });
    }));
});

describe("the German sweep: courses", () => {
  it("« Meine Kurse », empty, with the create form and its errors", () =>
    withLocale("de", async () => {
      open("/courses", (method, path) =>
        method === "GET" && path.endsWith("/api/courses") ? { body: { courses: [] } } : undefined,
      );
      await screen.findByText(/Du hast noch keine Kurse/);
      clean();
      fireEvent.click(screen.getByRole("button", { name: "Neuer Kurs" }));
      fireEvent.click(await screen.findByRole("button", { name: "Kurs anlegen" }));
      await screen.findByText("Gib deinem Kurs einen Namen.");
      clean();
    }));

  it("« Meine Kurse », with a course card", () =>
    withLocale("de", async () => {
      open("/courses");
      await screen.findByRole("article", { name: "Fysica 4e jaar" });
      clean();
    }));

  it("a course: ready, preparing and failed chapters, rename and the document picker", () =>
    withLocale("de", async () => {
      open("/courses/c1");
      await screen.findByRole("heading", { name: "Fysica 4e jaar" });
      expect(screen.getAllByText(/2 von 9 fertig · 1 übersprungen/).length).toBeGreaterThan(0);
      clean();
      fireEvent.keyDown(screen.getByRole("button", { name: "Kursaktionen" }), {
        key: "Enter",
      });
      await screen.findByRole("menuitem", { name: "Umbenennen" });
      clean();
      fireEvent.click(screen.getByRole("menuitem", { name: "Umbenennen" }));
      fireEvent.change(screen.getByLabelText("Kursname"), { target: { value: "" } });
      fireEvent.click(screen.getByRole("button", { name: "Speichern" }));
      await screen.findByText("Der Name muss zwischen 1 und 80 Zeichen lang sein.");
      clean();
      fireEvent.click(screen.getByRole("button", { name: "Abbrechen" }));
      fireEvent.click(screen.getByRole("button", { name: "Kapitel hinzufügen" }));
      await screen.findByLabelText("Das PDF oder die Fotos des Materials");
      clean();
    }));

  it("a chapter in preparation, and a chapter that is not found", () =>
    withLocale("de", async () => {
      open("/courses/c1/chapters/h2", (method, path) =>
        path.includes("/chapters/h2") && method === "GET"
          ? {
              status: 409,
              body: { code: "chapter_not_ready", message: "Dieses Kapitel ist noch nicht fertig." },
            }
          : undefined,
      );
      await screen.findByText("Dieses Kapitel wird gerade vorbereitet");
      await screen.findByText(/Läuft noch, der Dienst ist gerade langsam\./);
      clean();
      cleanup();
      open("/courses/c1/chapters/zz", (method, path) =>
        path.includes("/chapters/zz") && method === "GET"
          ? { status: 404, body: { code: "not_found", message: "Diese Seite gibt es nicht." } }
          : undefined,
      );
      await screen.findByText(
        "Diesen Kurs oder dieses Kapitel gibt es nicht, oder es gehört nicht dir.",
      );
      clean();
    }));
});

describe("the German sweep: the content page", () => {
  const tab = async (name: string) => {
    const el = await screen.findByRole("tab", { name });
    fireEvent.mouseDown(el);
    fireEvent.click(el);
  };

  it("the pack, the path and the text, read-only and in their editors", () =>
    withLocale("de", async () => {
      open("/courses/c1/chapters/h1/content");
      await screen.findByRole("tab", { name: "Inhalt" });
      clean();
      fireEvent.click(screen.getByRole("button", { name: "Inhalt bearbeiten" }));
      clean();
      fireEvent.click(screen.getByRole("button", { name: "Inhalt speichern" }));
      await screen.findByRole("alertdialog");
      clean();
      cleanup();

      open("/courses/c1/chapters/h1/content");
      await tab("Lernpfad");
      await screen.findByText("1 · Lektion");
      clean();
      fireEvent.click(screen.getByRole("button", { name: "Lernpfad bearbeiten" }));
      await screen.findByLabelText("Titel des Lernpfads");
      clean();
      cleanup();

      open("/courses/c1/chapters/h1/content");
      await tab("Aus dem Dokument gelesener Text");
      await screen.findByRole("button", { name: "Text bearbeiten" });
      clean();
      fireEvent.click(screen.getByRole("button", { name: "Text bearbeiten" }));
      await screen.findByText(/Korrigier, was Célestin falsch gelesen hat/);
      clean();
    }));

  it("a German account's refused edit lists German reasons", () =>
    withLocale("de", async () => {
      open("/courses/c1/chapters/h1/content", (method) =>
        method === "PUT"
          ? {
              status: 422,
              body: {
                code: "content_invalid",
                message: "Der Inhalt ist ungültig. Korrigier die angezeigten Punkte.",
                issues: [
                  {
                    where: "§ 5",
                    message: "Abschnitt „## 5. Woordenschat“ fehlt oder hat den falschen Titel",
                  },
                ],
              },
            }
          : undefined,
      );
      fireEvent.click(await screen.findByRole("button", { name: "Inhalt bearbeiten" }));
      fireEvent.click(screen.getByRole("button", { name: "Inhalt speichern" }));
      const dialog = await screen.findByRole("alertdialog");
      fireEvent.click(within(dialog).getByRole("button", { name: "Speichern" }));
      await screen.findByRole("alert");
      clean();
    }));
});

describe("the German sweep: settings and the user menu", () => {
  it("the settings screen lists the four languages and is clean", () =>
    withLocale("de", async () => {
      open("/settings");
      await screen.findByRole("heading", { name: "Einstellungen" });
      expect(screen.getByRole("radio", { name: "Deutsch" })).toBeTruthy();
      expect(screen.getByRole("radio", { name: "Nederlands" })).toBeTruthy();
      expect(screen.getByRole("radio", { name: "Français" })).toBeTruthy();
      clean();
    }));

  it("the open user menu", () =>
    withLocale("de", async () => {
      open("/courses");
      await screen.findByRole("button", { name: "Lea" });
      fireEvent.keyDown(screen.getByRole("button", { name: "Lea" }), { key: "Enter" });
      await screen.findByRole("menuitem", { name: "Einstellungen" });
      clean();
    }));
});

import { within } from "@testing-library/react";

// --- the cahier (spec 018) ------------------------------------------------------------------

const NOTEBOOK_CHAPTER = {
  id: "h1",
  title: "Le mouvement rectiligne uniforme",
  position: 1,
  course_id: "c1",
  course_name: "Physics Year 4",
  language: "fr",
  subject: "sciences",
  sections: [
    { id: "s1", index: 1, kind: "teach", title: "Vitesse moyenne", goal: "Définir la vitesse." },
    { id: "s2", index: 2, kind: "practise", title: "Calculer une durée", goal: "g2" },
  ],
  progress: { done: ["s1"], active: "s2", skipped: [] },
};

const NOTEBOOK = {
  sections: [
    {
      section_id: "s1",
      items: [
        {
          kind: "card",
          card: { kind: "title", eyebrow: "Section 1", title: "Vitesse", objective: "o" },
        },
        { kind: "tutor", text: "Voici la définition de la vitesse moyenne." },
        {
          kind: "card",
          card: {
            kind: "check_question",
            question: "Quelle est l'unité de la vitesse ?",
            options: [
              { id: "a", text: "Le mètre par seconde" },
              { id: "b", text: "La seconde" },
            ],
            correct_option_id: "a",
            feedback: "Exact : une distance divisée par une durée.",
          },
        },
        { kind: "learner", text: "Le mètre par seconde, je pense." },
      ],
    },
  ],
};

const notebookApi: Handler = (method, path) => {
  if (method === "GET" && path.endsWith("/chapters/h1/notebook")) return { body: NOTEBOOK };
  if (method === "GET" && path.endsWith("/api/courses/c1/chapters/h1"))
    return { body: NOTEBOOK_CHAPTER };
  return undefined;
};

describe("the German sweep: the cahier", () => {
  it("its sections, the exchange, a revealed answer and the empty state", () =>
    withLocale("de", async () => {
      open("/courses/c1/chapters/h1/notebook", notebookApi);
      await screen.findByRole("heading", { name: "Vitesse moyenne" });
      clean();
      fireEvent.click(screen.getByRole("switch", { name: "Unterhaltung anzeigen" }));
      await screen.findByText("Le mètre par seconde, je pense.");
      fireEvent.click(screen.getByRole("button", { name: /La seconde/ }));
      await screen.findByText(/une distance divisée/);
      clean();
      cleanup();
      open("/courses/c1/chapters/h1/notebook", (method, path) =>
        method === "GET" && path.endsWith("/chapters/h1/notebook")
          ? { body: { sections: [] } }
          : notebookApi(method, path, undefined),
      );
      await screen.findByText(/Dein Heft ist noch leer/);
      clean();
    }));
});

// --- révision (spec 020) ------------------------------------------------------------------------

const REVISION_CHAPTERS = [
  {
    id: "h1",
    position: 1,
    title: "De rijen",
    ready: true,
    section_count: 2,
    done_count: 1,
    skipped_count: 1,
    sections: [
      { id: "s1", index: 1, kind: "teach", title: "Een rij definiëren", state: "done" },
      { id: "s2", index: 2, kind: "practise", title: "Berekenen", state: "skipped" },
    ],
  },
  {
    id: "h2",
    position: 2,
    title: null,
    ready: false,
    section_count: 0,
    done_count: 0,
    skipped_count: 0,
    sections: [],
  },
];

const LIVE_REVISION = {
  id: "r1",
  chapter_ids: ["h1"],
  entry_count: 4,
  created_at: "",
  entries: [
    { kind: "learner", text: "Ja." },
    {
      kind: "tool",
      name: "record_result",
      arguments: { chapter: 1, section_id: "s1", outcome: "shaky" },
      chapter_id: "h1",
      section_id: "s1",
      outcome: "shaky",
      // The backend's form: the section's label (a Dutch course) after the interface's words.
      marker: "notiert: wackelt · 1. Een rij definiëren",
    },
    { kind: "tutor", text: "Vergelijk met je antwoord: gekend, wankel of te herhalen?" },
  ],
};

const revisionApi =
  (live: typeof LIVE_REVISION | null): Handler =>
  (method, path) => {
    if (method === "GET" && path.endsWith("/api/courses/c1/revision"))
      return {
        body: {
          revision: live,
          chapters: REVISION_CHAPTERS,
          results: [
            { chapter_id: "h1", section_id: "s1", outcome: "shaky", at: "2026-11-10T10:00:00Z" },
          ],
        },
      };
    if (method === "POST" && path.endsWith("/api/courses/c1/revision"))
      return {
        status: 422,
        body: {
          code: "revision_too_large",
          message:
            "Diese Kapitel enthalten zu viel Stoff für eine einzige Wiederholung. Wähl weniger aus.",
        },
      };
    return undefined;
  };

describe("the German sweep: the révision", () => {
  it("the chooser and a refusal", () =>
    withLocale("de", async () => {
      stubLayoutApis({ desktop: true });
      open("/courses/c1/revision", revisionApi(null));
      await screen.findByRole("heading", { name: "Was möchtest du wiederholen?" });
      clean();
      fireEvent.click(screen.getByRole("button", { name: "Wiederholung starten" }));
      await screen.findByRole("alert");
      clean();
    }));

  it("a live révision, its « Bilan » and the confirmation to start a new one", () =>
    withLocale("de", async () => {
      stubLayoutApis({ desktop: true });
      open("/courses/c1/revision", revisionApi(LIVE_REVISION));
      await screen.findByText(/Vergelijk me/);
      clean();
      fireEvent.click(screen.getByRole("button", { name: "Rückblick" }));
      await screen.findByRole("dialog", { name: "Rückblick auf die Wiederholung" });
      clean();
      cleanup();
      open("/courses/c1/revision", revisionApi(LIVE_REVISION));
      await screen.findByText(/Vergelijk me/);
      fireEvent.click(screen.getByRole("button", { name: "Neue Wiederholung" }));
      await screen.findByRole("alertdialog");
      clean();
    }));
});

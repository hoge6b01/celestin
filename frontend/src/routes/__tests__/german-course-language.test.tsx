// @vitest-environment jsdom
/**
 * Spec 021 R2.6, R7.6: a German course under each interface language, and a Dutch course under a German
 * interface. The course text says its own language with `lang` (never the interface's), whatever the buttons
 * around it say; and under a German interface no French, English or Dutch interface word is left anywhere.
 */
import { cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { stubLayoutApis } from "@/test/jsdom-stubs";

beforeEach(() => stubLayoutApis({ desktop: true }));

vi.mock("@/components/celestin/use-voice-session", () => ({
  useVoiceSession: () => ({
    phase: "off",
    muted: false,
    capAt: null,
    supported: false,
    start: async () => {},
    stop: () => {},
    toggleMute: () => {},
    sendText: () => {},
  }),
}));

vi.mock("@/components/celestin/discussion-panel", () => ({
  DiscussionPanel: () => <div data-testid="discussion">discussion</div>,
}));

vi.mock("@/lib/tutor/client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("@/lib/tutor/client")>();
  return {
    ...mod,
    streamTurn: vi.fn(async function* () {
      yield { event: "turn.start", turn_id: "t1" };
      yield { event: "text.delta", block_id: 0, text: "Hallo, wir machen mit den Folgen weiter." };
      yield {
        event: "board.set",
        card: {
          kind: "check_question",
          question: "Warum $q \\neq 1$?",
          options: [
            { id: "a", text: "Division durch null" },
            { id: "b", text: "Aus Gewohnheit" },
          ],
          correct_option_id: "a",
          feedback: "Richtig.",
        },
        // What a German account's server sends: the marker and the error in German.
        marker: "Frage gestellt",
      };
      yield { event: "step.ready", marker: "nächster Schritt angeboten" };
      yield {
        event: "error",
        code: "overloaded",
        message: "Célestin ist gerade sehr beschäftigt.",
      };
      yield { event: "turn.end", reason: "end", usage: {} };
    }),
  };
});

import { foreignTextOutside } from "@/test/english-sweep";
import { withLocale } from "@/test/locale";
import { mockApi, mountRoutes } from "@/test/route-harness";
import { Route as ChapterFile } from "../_auth/courses/$courseId/chapters/$chapterId/index";
import type { CourseLanguage } from "@/lib/course-language";
import type { Locale } from "@/lib/locale";

const chapter = (language: CourseLanguage) => ({
  id: "folgen",
  title: language === "de" ? "Folgen" : "Rijen",
  position: 1,
  course_id: "maths",
  course_name: language === "de" ? "Mathematik Klasse 10" : "Wiskunde 5e jaar",
  language,
  subject: "mathematics",
  sections: [
    { id: "s1", index: 1, kind: "teach", title: "Folgen", goal: "a_n lesen." },
    { id: "s2", index: 2, kind: "practise", title: "Ein Glied berechnen", goal: "g2" },
    { id: "s3", index: 3, kind: "synthesis", title: "Zusammenfassung", goal: "g3" },
  ],
  progress: { done: ["s1"], active: "s2", skipped: [] },
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

function mountLesson(locale: Locale, language: CourseLanguage) {
  mockApi(
    (_method, path) => {
      if (path.endsWith("/api/health")) return { body: { voice: false } };
      if (path.endsWith("/api/courses/maths/chapters/folgen")) return { body: chapter(language) };
      return undefined;
    },
    { locale, name: "Lea" },
  );
  mountRoutes(
    [{ path: "/courses/$courseId/chapters/$chapterId/", file: ChapterFile }],
    "/courses/maths/chapters/folgen",
  );
}

/** The `lang` of every region inside the page: the interface's own is on `<html>`. */
const regionLanguages = () =>
  new Set([...document.body.querySelectorAll("[lang]")].map((el) => el.getAttribute("lang")));

describe("a German course", () => {
  it("under a French interface: the course text is marked German, the chrome stays French", () =>
    withLocale("fr", async () => {
      mountLesson("fr", "de");
      await screen.findByText(/Hallo, wir machen mit den Folgen weiter\./);
      expect(regionLanguages()).toEqual(new Set(["de"]));
      const badge = screen.getByTestId("course-language");
      expect([badge.textContent, badge.getAttribute("lang")]).toEqual(["Deutsch", "de"]);
      expect(screen.getByRole("button", { name: "Voir le parcours du chapitre" })).toBeTruthy();
    }));

  it("under a Dutch interface: the course text is marked German, the chrome stays Dutch", () =>
    withLocale("nl", async () => {
      mountLesson("nl", "de");
      await screen.findByText(/Hallo, wir machen mit den Folgen weiter\./);
      expect(regionLanguages()).toEqual(new Set(["de"]));
      expect(
        screen.getByRole("button", { name: "Het traject van het hoofdstuk bekijken" }),
      ).toBeTruthy();
    }));

  it("under a German interface: no French, English or Dutch word is left, in the chrome or in the course", () =>
    withLocale("de", async () => {
      mountLesson("de", "de");
      await screen.findByText(/Hallo, wir machen mit den Folgen weiter\./);
      await screen.findByText(/Célestin ist gerade sehr beschäftigt\./);
      expect(foreignTextOutside("de")).toEqual([]);
      fireEvent.click(screen.getByRole("button", { name: "Lernpfad des Kapitels ansehen" }));
      await screen.findByRole("dialog");
      expect(foreignTextOutside("de")).toEqual([]);
    }));
});

describe("another course under a German interface", () => {
  it("a Dutch course is marked Dutch and its chrome is German", () =>
    withLocale("de", async () => {
      mountLesson("de", "nl");
      await screen.findByText(/Hallo, wir machen mit den Folgen weiter\./);
      expect(regionLanguages()).toEqual(new Set(["nl"]));
      const badge = screen.getByTestId("course-language");
      expect([badge.textContent, badge.getAttribute("lang")]).toEqual(["Nederlands", "nl"]);
      expect(screen.getByRole("button", { name: "Lernpfad des Kapitels ansehen" })).toBeTruthy();
      expect(foreignTextOutside("de")).toEqual([]); // the Dutch text is marked, so it is not a leak
    }));
});

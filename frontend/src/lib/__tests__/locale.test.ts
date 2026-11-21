import { describe, expect, it } from "vitest";
import cases from "./accept_language_cases.json";
import { AUTONYM, LOCALES, isLocale, matchLocale, parseAcceptLanguage } from "../locale";

describe("parseAcceptLanguage", () => {
  it.each(cases)("$header → $expected", ({ header, expected }) => {
    expect(parseAcceptLanguage(header)).toBe(expected);
  });

  it("treats an undefined header as French", () => {
    expect(parseAcceptLanguage(undefined)).toBe("fr");
  });
});

describe("matchLocale", () => {
  it("takes the first supported language of the browser's list", () => {
    expect(matchLocale(["es-ES", "en-GB", "fr-BE"])).toBe("en");
    expect(matchLocale(["fr-BE", "en"])).toBe("fr");
  });

  it("falls back to French", () => {
    expect(matchLocale([])).toBe("fr");
    expect(matchLocale(["es-ES"])).toBe("fr");
  });

  it("reads Flemish and Dutch browsers as Dutch (spec 017)", () => {
    expect(matchLocale(["nl-BE", "fr-BE"])).toBe("nl");
    expect(matchLocale(["nl-NL"])).toBe("nl");
    expect(matchLocale(["fr-BE", "nl-BE"])).toBe("fr");
  });

  it("reads German, Austrian and Swiss browsers as German (spec 021)", () => {
    expect(matchLocale(["de-DE", "en-GB"])).toBe("de");
    expect(matchLocale(["de-AT"])).toBe("de");
    expect(matchLocale(["de-CH", "fr-CH"])).toBe("de");
    expect(matchLocale(["en-GB", "de-DE"])).toBe("en");
  });
});

describe("the supported list", () => {
  it("recognises exactly its members", () => {
    expect(LOCALES.every(isLocale)).toBe(true);
    expect(isLocale("es")).toBe(false);
    expect(isLocale(undefined)).toBe(false);
  });

  it("names each language in its own words", () => {
    expect(Object.keys(AUTONYM).sort()).toEqual([...LOCALES].sort());
    expect(AUTONYM.de).toBe("Deutsch");
  });
});

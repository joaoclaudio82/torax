import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import test from "node:test";

import {
  findStudy,
  mergeNihStudies,
  studies,
  studyFromNihEntry,
} from "../data.js";

test("o acervo base possui IDs únicos e referências Wikimedia", () => {
  assert.ok(studies.length >= 8);
  assert.equal(new Set(studies.map(({ id }) => id)).size, studies.length);
  assert.equal(studies.some((study) => study.id.startsWith("nih-")), false);
});

test("cada estudo base possui metadados e imagem acessível", () => {
  for (const study of studies) {
    assert.match(study.image, /^assets\//);
    assert.ok(existsSync(study.image), `imagem ausente: ${study.image}`);
    assert.match(study.source, /^https:\/\/commons\.wikimedia\.org\//);
    assert.ok(study.license);
    assert.ok(study.observations.length >= 3);
    assert.ok(study.learningTags.length >= 1);
  }
});

test("mergeNihStudies anexa casos do manifesto sem duplicar", () => {
  const merged = mergeNihStudies(studies, [
    {
      id: "nih-demo-1",
      title: "NIH demo",
      subtitle: "Effusion · PA",
      path: "assets/nih-demo/00000011_000.png",
      labels: ["Effusion"],
      view: "PA",
    },
  ]);
  assert.ok(merged.some((study) => study.id === "nih-demo-1"));
  assert.ok(merged.filter((study) => study.id === "pa").length === 1);
  const built = studyFromNihEntry({
    id: "nih-x",
    title: "X",
    subtitle: "Y",
    path: "assets/nih-demo/x.png",
    labels: ["Pneumonia"],
    view: "AP",
  });
  assert.ok(built.learningTags.includes("NIH"));
  assert.ok(built.learningTags.includes("Pneumonia"));
});

test("findStudy retorna o estudo solicitado", () => {
  assert.equal(findStudy("lateral").title, "Radiografia lateral");
});

test("findStudy usa o primeiro estudo como fallback", () => {
  assert.equal(findStudy("inexistente"), studies[0]);
});

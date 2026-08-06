import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import test from "node:test";

import { findStudy, studies } from "../data.js";

test("o acervo possui IDs únicos e pelo menos as referências base", () => {
  assert.ok(studies.length >= 8);
  assert.equal(new Set(studies.map(({ id }) => id)).size, studies.length);
  assert.ok(studies.some((study) => study.id.startsWith("nih-")));
});

test("cada estudo possui metadados e imagem acessível quando aplicável", () => {
  for (const study of studies) {
    assert.match(study.image, /^assets\//);
    const isNihDemo = study.image.startsWith("assets/nih-demo/");
    if (!isNihDemo) {
      assert.ok(existsSync(study.image), `imagem ausente: ${study.image}`);
      assert.match(study.source, /^https:\/\/commons\.wikimedia\.org\//);
    } else {
      assert.match(study.source, /nihcc\.app\.box\.com/);
      assert.match(study.badge, /NIH/i);
      assert.ok(study.learningTags.includes("NIH"));
    }
    assert.ok(study.license);
    assert.ok(study.observations.length >= 3);
    assert.ok(study.learningTags.length >= 1);
    assert.ok(study.learningTags.every((tag) => typeof tag === "string"));
  }
});

test("findStudy retorna o estudo solicitado", () => {
  assert.equal(findStudy("lateral").title, "Radiografia lateral");
  assert.equal(findStudy("nih-cardiomegaly").id, "nih-cardiomegaly");
});

test("findStudy usa o primeiro estudo como fallback", () => {
  assert.equal(findStudy("inexistente"), studies[0]);
});

import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import test from "node:test";

import { findStudy, studies } from "../data.js";

test("o acervo contém oito estudos com IDs únicos", () => {
  assert.equal(studies.length, 8);
  assert.equal(new Set(studies.map(({ id }) => id)).size, studies.length);
});

test("cada estudo possui imagem, fonte e licença", () => {
  for (const study of studies) {
    assert.match(study.image, /^assets\//);
    assert.ok(existsSync(study.image), `imagem ausente: ${study.image}`);
    assert.match(study.source, /^https:\/\/commons\.wikimedia\.org\//);
    assert.ok(study.license);
    assert.ok(study.observations.length >= 3);
    assert.ok(study.learningTags.length >= 1);
    assert.ok(study.learningTags.every((tag) => typeof tag === "string"));
  }
});

test("findStudy retorna o estudo solicitado", () => {
  assert.equal(findStudy("lateral").title, "Radiografia lateral");
});

test("findStudy usa o primeiro estudo como fallback", () => {
  assert.equal(findStudy("inexistente"), studies[0]);
});

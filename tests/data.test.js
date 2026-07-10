import assert from "node:assert/strict";
import test from "node:test";

import { findStudy, studies } from "../data.js";

test("o acervo contém três estudos com IDs únicos", () => {
  assert.equal(studies.length, 3);
  assert.equal(new Set(studies.map(({ id }) => id)).size, studies.length);
});

test("cada estudo possui imagem, fonte e licença", () => {
  for (const study of studies) {
    assert.match(study.image, /^assets\//);
    assert.match(study.source, /^https:\/\/commons\.wikimedia\.org\//);
    assert.ok(study.license);
    assert.ok(study.observations.length >= 3);
  }
});

test("findStudy retorna o estudo solicitado", () => {
  assert.equal(findStudy("lateral").title, "Radiografia lateral");
});

test("findStudy usa o primeiro estudo como fallback", () => {
  assert.equal(findStudy("inexistente"), studies[0]);
});

import assert from "node:assert/strict";
import test from "node:test";

import { createImageFilter, DEFAULT_VIEW, normalizeView } from "../viewer.js";

test("a visualização padrão não altera brilho, contraste ou polaridade", () => {
  assert.equal(
    createImageFilter(DEFAULT_VIEW),
    "brightness(100%) contrast(100%) invert(0)",
  );
});

test("os ajustes são limitados a intervalos seguros para a interface", () => {
  assert.deepEqual(
    normalizeView({ brightness: 500, contrast: 20, inverted: true }),
    { brightness: 150, contrast: 50, inverted: true },
  );
});

test("o filtro representa os ajustes selecionados", () => {
  assert.equal(
    createImageFilter({ brightness: 85, contrast: 140, inverted: true }),
    "brightness(85%) contrast(140%) invert(1)",
  );
});

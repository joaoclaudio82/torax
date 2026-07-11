export const DEFAULT_VIEW = Object.freeze({
  brightness: 100,
  contrast: 100,
  inverted: false,
});

export function normalizeView(view = {}) {
  return {
    brightness: Math.min(150, Math.max(50, Number(view.brightness) || 100)),
    contrast: Math.min(200, Math.max(50, Number(view.contrast) || 100)),
    inverted: Boolean(view.inverted),
  };
}

export function createImageFilter(view) {
  const normalized = normalizeView(view);
  return [
    `brightness(${normalized.brightness}%)`,
    `contrast(${normalized.contrast}%)`,
    `invert(${normalized.inverted ? 1 : 0})`,
  ].join(" ");
}

/** Glossário educacional das classes do modelo (não clínico). */
export const pathologyGlossary = {
  Atelectasis: {
    title: "Atelectasia",
    summary: "Perda de volume pulmonar com opacificação variável.",
  },
  Consolidation: {
    title: "Consolidação",
    summary: "Preenchimento alveolar que obscurece vasos e bronquíolos.",
  },
  Infiltration: {
    title: "Infiltrado",
    summary: "Termo amplo para opacidades intersticiais ou alveolares.",
  },
  Pneumothorax: {
    title: "Pneumotórax",
    summary: "Ar na cavidade pleural com redução da vascularização.",
  },
  Edema: {
    title: "Edema",
    summary: "Acúmulo de líquido no interstício ou alvéolos.",
  },
  Effusion: {
    title: "Derrame pleural",
    summary: "Líquido na cavidade pleural, frequentemente basal.",
  },
  Pneumonia: {
    title: "Pneumonia",
    summary: "Padrão infeccioso com consolidação ou opacidades focais.",
  },
  "Lung Opacity": {
    title: "Opacidade pulmonar",
    summary: "Classe ampla para regiões mais densas que o esperado.",
  },
  Cardiomegaly: {
    title: "Cardiomegalia",
    summary: "Aumento aparente da silhueta cardíaca na projeção.",
  },
  Fibrosis: {
    title: "Fibrose",
    summary: "Espessamento intersticial e padrões reticulares crônicos.",
  },
};

export function glossaryEntry(name) {
  return (
    pathologyGlossary[name] || {
      title: name,
      summary: "Classe do modelo sem glossário dedicado nesta versão.",
    }
  );
}

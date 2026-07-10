export const studies = [
  {
    id: "pa",
    title: "Radiografia PA",
    subtitle: "Incidência posteroanterior",
    image: "assets/chest-pa.jpg",
    alt: "Radiografia posteroanterior de um tórax normal",
    badge: "Vista frontal",
    description:
      "Projeção de rotina para avaliar campos pulmonares, silhueta cardíaca, mediastino e estruturas ósseas.",
    observations: [
      "Campos pulmonares simétricos",
      "Silhueta cardíaca sem aumento aparente",
      "Ângulos costofrênicos livres",
    ],
    source:
      "https://commons.wikimedia.org/wiki/File:Normal_posteroanterior_(PA)_chest_radiograph_(X-ray).jpg",
    license: "CC0 1.0",
  },
  {
    id: "lateral",
    title: "Radiografia lateral",
    subtitle: "Incidência de perfil",
    image: "assets/chest-lateral.jpg",
    alt: "Radiografia lateral de um tórax normal",
    badge: "Vista lateral",
    description:
      "Complementa a incidência PA, ajudando a localizar alterações em profundidade e avaliar o espaço retroesternal.",
    observations: [
      "Coluna torácica em perfil",
      "Espaço retroesternal preservado",
      "Hemidiafragmas identificáveis",
    ],
    source:
      "https://commons.wikimedia.org/wiki/File:Normal_lateral_chest_radiograph_(X-ray).jpg",
    license: "CC0 1.0",
  },
  {
    id: "anatomy",
    title: "Anatomia do tórax",
    subtitle: "Relações anatômicas",
    image: "assets/thorax-anatomy.gif",
    alt: "Ilustração anatômica do coração, pulmões, costelas e esterno",
    badge: "Ilustração",
    description:
      "Referência visual das relações entre pulmões, coração, esterno e arcos costais.",
    observations: [
      "Pulmões ocupam a maior parte da caixa torácica",
      "Coração projeta-se predominantemente à esquerda",
      "Costelas protegem os órgãos intratorácicos",
    ],
    source:
      "https://commons.wikimedia.org/wiki/File:Heart-thorax-gray.gif",
    license: "Domínio público",
  },
];

export function findStudy(id) {
  return studies.find((study) => study.id === id) ?? studies[0];
}

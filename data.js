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
    learningTags: ["Normal"],
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
    learningTags: ["Normal"],
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
    learningTags: ["Anatomia"],
    source:
      "https://commons.wikimedia.org/wiki/File:Heart-thorax-gray.gif",
    license: "Domínio público",
  },
  {
    id: "lobar-pneumonia",
    title: "Pneumonia lobar",
    subtitle: "Lobo médio direito",
    image: "assets/lobar-pneumonia.jpg",
    alt: "Radiografia de tórax com pneumonia lobar no pulmão direito",
    badge: "Achado patológico",
    description:
      "Imagem de referência com consolidação lobar descrita no lobo médio direito.",
    observations: [
      "Opacidade focal no hemitórax direito",
      "Distribuição compatível com padrão lobar",
      "Exemplo para testar as classes Pneumonia e Consolidation",
    ],
    learningTags: ["Pneumonia", "Consolidation"],
    source:
      "https://commons.wikimedia.org/wiki/File:X-ray_of_lobar_pneumonia.jpg",
    license: "CC0 1.0",
  },
  {
    id: "pneumonia-comparison",
    title: "Pneumonia — comparação",
    subtitle: "Normal e pneumonia por febre Q",
    image: "assets/pneumonia-comparison.jpg",
    alt: "Comparação entre radiografia normal e radiografia com pneumonia",
    badge: "Comparativo",
    description:
      "Composição histórica que contrasta uma radiografia normal com um caso de pneumonia associada à febre Q.",
    observations: [
      "Duas imagens reunidas no mesmo arquivo",
      "Diferença de transparência entre os campos pulmonares",
      "Útil para inspeção visual, não para comparação quantitativa",
    ],
    learningTags: ["Pneumonia"],
    source:
      "https://commons.wikimedia.org/wiki/File:Pneumonia_x-ray.jpg",
    license: "Domínio público",
  },
  {
    id: "pneumothorax",
    title: "Pneumotórax",
    subtitle: "Incidência lateral em inspiração",
    image: "assets/pneumothorax-lateral.jpg",
    alt: "Radiografia lateral mostrando pneumotórax",
    badge: "Achado patológico",
    description:
      "Incidência lateral com pneumotórax sutil na região apical da cavidade torácica esquerda.",
    observations: [
      "Redução de marcas vasculares na região apical",
      "Achado mais evidente posteriormente na vista lateral",
      "Exemplo para testar a classe Pneumothorax",
    ],
    learningTags: ["Pneumothorax"],
    source:
      "https://commons.wikimedia.org/wiki/File:Lateral_X-ray_of_pneumothorax_in_inspiration.jpg",
    license: "CC0 1.0",
  },
  {
    id: "pleural-effusion",
    title: "Derrame pleural",
    subtitle: "Acúmulo de líquido pleural",
    image: "assets/pleural-effusion.jpg",
    alt: "Radiografia de tórax com derrame pleural à direita",
    badge: "Achado patológico",
    description:
      "Radiografia de referência com líquido disposto na cavidade pleural direita.",
    observations: [
      "Opacidade na base do hemitórax direito",
      "Redução da área pulmonar aerada",
      "Exemplo para testar a classe Effusion",
    ],
    learningTags: ["Effusion"],
    source:
      "https://commons.wikimedia.org/wiki/File:Pleural_effusion.jpg",
    license: "Domínio público — CDC",
  },
  {
    id: "pulmonary-edema",
    title: "Edema pulmonar",
    subtitle: "Radiografia AP portátil",
    image: "assets/pulmonary-edema.jpg",
    alt: "Radiografia de tórax com edema pulmonar agudo",
    badge: "Achado patológico",
    description:
      "Radiografia AP com padrões intersticial e alveolar descritos como edema pulmonar agudo.",
    observations: [
      "Opacidades alveolares de limites pouco definidos",
      "Espessamento intersticial periférico",
      "Exemplo para testar Edema e Lung Opacity",
    ],
    learningTags: ["Edema", "Lung Opacity"],
    source:
      "https://commons.wikimedia.org/wiki/File:AP_portable_CXR_of_a_patient_in_acute_pulmonary_oedema.jpg",
    license: "CC BY-SA 3.0",
  },,
  {
    id: "nih-no-finding-01",
    title: "NIH — Sem achado",
    subtitle: "No Finding · PA",
    image: "assets/nih-demo/00000002_000.png",
    alt: "Radiografia de tórax NIH rotulada como No Finding",
    badge: "NIH demo",
    description:
      "Caso do ChestX-ray14 sem achado minerado por NLP. Útil como referência de controle no teste do modelo.",
    observations: [
      "Rótulo NIH: No Finding",
      "Incidência PA",
      "Rótulos do NIH são text-mined e não substituem laudo",
    ],
    learningTags: ["NIH", "Normal", "No Finding"],
    source: "https://nihcc.app.box.com/v/ChestXray-NIHCC",
    license: "NIH Clinical Center (atribuição obrigatória)",
  },
  {
    id: "nih-no-finding-02",
    title: "NIH — Sem achado (2)",
    subtitle: "No Finding · PA",
    image: "assets/nih-demo/00000005_000.png",
    alt: "Segunda radiografia NIH rotulada como No Finding",
    badge: "NIH demo",
    description:
      "Segundo exemplo sem achado do acervo NIH para comparar a resposta do modelo em casos negativos.",
    observations: [
      "Rótulo NIH: No Finding",
      "Incidência PA",
      "Compare com o outro caso No Finding do pack",
    ],
    learningTags: ["NIH", "Normal", "No Finding"],
    source: "https://nihcc.app.box.com/v/ChestXray-NIHCC",
    license: "NIH Clinical Center (atribuição obrigatória)",
  },
  {
    id: "nih-cardiomegaly",
    title: "NIH — Cardiomegalia",
    subtitle: "Cardiomegaly · PA",
    image: "assets/nih-demo/00000001_000.png",
    alt: "Radiografia NIH com rótulo Cardiomegaly",
    badge: "NIH demo",
    description:
      "Caso com rótulo único de cardiomegalia no ChestX-ray14.",
    observations: [
      "Rótulo NIH: Cardiomegaly",
      "Incidência PA",
      "Bom alvo para a classe Cardiomegaly do modelo",
    ],
    learningTags: ["NIH", "Cardiomegaly"],
    source: "https://nihcc.app.box.com/v/ChestXray-NIHCC",
    license: "NIH Clinical Center (atribuição obrigatória)",
  },
  {
    id: "nih-atelectasis",
    title: "NIH — Atelectasia",
    subtitle: "Atelectasis · PA",
    image: "assets/nih-demo/00000011_006.png",
    alt: "Radiografia NIH com rótulo Atelectasis",
    badge: "NIH demo",
    description: "Caso com rótulo único de atelectasia.",
    observations: [
      "Rótulo NIH: Atelectasis",
      "Incidência PA",
      "Use no modo estudo antes de abrir o resultado do modelo",
    ],
    learningTags: ["NIH", "Atelectasis"],
    source: "https://nihcc.app.box.com/v/ChestXray-NIHCC",
    license: "NIH Clinical Center (atribuição obrigatória)",
  },
  {
    id: "nih-effusion",
    title: "NIH — Derrame pleural",
    subtitle: "Effusion · PA",
    image: "assets/nih-demo/00000011_000.png",
    alt: "Radiografia NIH com rótulo Effusion",
    badge: "NIH demo",
    description: "Caso com rótulo único de derrame pleural.",
    observations: [
      "Rótulo NIH: Effusion",
      "Incidência PA",
      "Compare com o exemplo Wikimedia de derrame",
    ],
    learningTags: ["NIH", "Effusion"],
    source: "https://nihcc.app.box.com/v/ChestXray-NIHCC",
    license: "NIH Clinical Center (atribuição obrigatória)",
  },
  {
    id: "nih-infiltration",
    title: "NIH — Infiltrado",
    subtitle: "Infiltration · PA",
    image: "assets/nih-demo/00000005_006.png",
    alt: "Radiografia NIH com rótulo Infiltration",
    badge: "NIH demo",
    description: "Caso com rótulo único de infiltrado pulmonar.",
    observations: [
      "Rótulo NIH: Infiltration",
      "Incidência PA",
      "Classe ampla e frequentemente ambígua clinicamente",
    ],
    learningTags: ["NIH", "Infiltration"],
    source: "https://nihcc.app.box.com/v/ChestXray-NIHCC",
    license: "NIH Clinical Center (atribuição obrigatória)",
  }
];

export function findStudy(id) {
  return studies.find((study) => study.id === id) ?? studies[0];
}

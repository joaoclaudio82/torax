# Triagem de Tórax por Radiografia — protótipo de pesquisa

Reconstrução do conceito de "detecção de doença pulmonar" da demonstração
YOLOvX, porém formulado de maneira tecnicamente adequada para radiografia de
tórax. Classificação multipatologia + Grad-CAM, com modelo pré-treinado em
bases públicas reais.

> **Aviso.** Ferramenta de pesquisa e ensino. Não é dispositivo médico, não
> possui registro em ANVISA/FDA e não deve orientar diagnóstico ou decisão
> clínica sobre pacientes reais.

## Por que esta versão é diferente da demo original

| Problema na demo YOLOvX | Escolha aqui |
|---|---|
| Detecção com bounding boxes cobrindo o pulmão inteiro | Classificação multirrótulo; a pneumonia é um padrão de opacidade difuso, não um objeto com contorno |
| Localização grosseira por caixa | Grad-CAM (mapa de calor contínuo) na última camada convolucional |
| Modelo e base de treino não declarados | DenseNet-121 do `torchxrayvision`, treinado em NIH, PadChest, CheXpert, MIMIC-CXR, Kaggle e OpenI |
| Confiança exibida sem contexto | Probabilidade mostrada junto ao limiar de operação calibrado (`op_threshold`) |
| Captura de tela de radiografia | Suporte a DICOM real, com tratamento de rescale e MONOCHROME1 |

## Arquitetura

```
torax/
├── main.py            API FastAPI: /analyze, /health e frontend
├── xray_model.py      carregamento do modelo, inferência e Grad-CAM
├── imaging.py         leitura de PNG/JPG/DICOM e pré-processamento
├── overlay.py         colormap tipo jet e composição da sobreposição
├── index.html         atlas e interface de análise
├── app.js             interação do atlas e envio para a API
├── assets/            imagens abertas usadas na demonstração
├── smoke_test.py      teste de fumaça de ponta a ponta
├── requirements.txt
└── run.sh
```

Fluxo de uma requisição:

1. Upload da imagem para `POST /analyze`.
2. `imaging.load_image` roteia por extensão (DICOM ou raster) e devolve a
   matriz 2D em tons de cinza.
3. `imaging.preprocess` normaliza para a escala do torchxrayvision, faz o
   center-crop e redimensiona para 224x224.
4. `model.predict` roda a inferência multirrótulo (18 patologias).
5. `model.top_target` escolhe a patologia do grupo pneumônico com maior
   probabilidade e `model.gradcam` gera o mapa de calor para essa classe.
6. A resposta traz o ranking completo, os limiares de operação e as duas
   imagens (original e sobreposição) em base64.

## Como executar

Requer Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# Linux/macOS: .venv/bin/python -m pip install -r requirements.txt
npm start
```

Abra `http://localhost:8000`. Na primeira análise, os pesos do modelo
(~30 MB) são baixados automaticamente para `~/.torchxrayvision`.

Teste rápido sem interface:

```bash
npm test
```

## Grupo pneumônico

O modelo prevê 18 patologias. A interface destaca as diretamente ligadas ao
quadro pneumônico: `Pneumonia`, `Consolidation`, `Infiltration` e
`Lung Opacity`. O mapa de calor é ancorado na de maior probabilidade entre
elas.

## Limitações honestas

- Os limiares de operação vêm do treino em bases estrangeiras; a calibração
  não foi verificada em população brasileira.
- Não há segmentação anatômica nem controle de qualidade de posicionamento
  (AP/PA, rotação, exposição).
- O Grad-CAM indica onde o modelo "olhou", o que não equivale a delimitação
  clínica da lesão.
- Sem validação prospectiva, sensibilidade/especificidade próprias ou
  aprovação regulatória.

## Caminhos de extensão

- Fine-tuning em base brasileira (por exemplo, dados do próprio serviço) com
  recalibração de limiares por curva de Youden.
- Substituir o Grad-CAM por Grad-CAM++ ou por segmentação (nnU-Net) quando
  houver máscaras.
- Empacotar o modelo com ONNX Runtime ou TorchScript para inferência local em
  dispositivo, aproximando-se da proposta de edge da demo original.
- Endpoint de laudo estruturado alinhado a um agente interpretável, no espírito
  do BRICS-PRIMA.

# Análise de Radiografias de Tórax

Protótipo educacional para classificação multirrótulo de radiografias de tórax
e visualização das regiões que influenciam as previsões do modelo.

> O projeto demonstra técnicas de visão computacional e não deve ser utilizado
> para diagnóstico ou tomada de decisão clínica.

## Estrutura

```text
torax/
├── main.py                 API FastAPI e entrega do frontend
├── xray_model.py           inferência DenseNet-121 e geração do Grad-CAM
├── imaging.py              leitura e pré-processamento das radiografias
├── overlay.py              composição do mapa de calor sobre a imagem
├── index.html              estrutura da interface web
├── styles.css              apresentação visual e responsividade
├── app.js                  interação da interface e integração com a API
├── data.js                 metadados do atlas visual
├── assets/
│   ├── chest-*.jpg         incidências de referência
│   ├── *pneumonia*.jpg     exemplos de pneumonia
│   ├── pneumothorax-*.jpg  exemplo de pneumotórax
│   ├── pleural-*.jpg       exemplo de derrame pleural
│   ├── pulmonary-*.jpg     exemplo de edema pulmonar
│   └── thorax-anatomy.gif  referência anatômica
├── tests/
│   └── data.test.js        testes dos dados do atlas
└── smoke_test.py           teste ponta a ponta da API e do modelo
```

### Backend

O `main.py` expõe os endpoints:

- `GET /health`: carrega o modelo e informa seu estado.
- `POST /analyze`: recebe uma imagem, executa o pipeline e retorna as previsões,
  a radiografia processada e o mapa de atenção.
- `GET /`: entrega a interface web.

O processamento é dividido em módulos:

1. `imaging.py` converte a entrada em uma matriz bidimensional.
2. `xray_model.py` executa a classificação e produz o Grad-CAM.
3. `overlay.py` combina a radiografia com o mapa de calor.
4. `main.py` organiza o resultado e o devolve em JSON.

### Frontend

A interface utiliza HTML, CSS e JavaScript sem framework. Ela contém:

- um atlas com incidências PA, lateral e referência anatômica;
- upload de arquivos PNG, JPG e DICOM;
- envio da radiografia para a API;
- comparação entre a imagem processada e o Grad-CAM;
- ranking das probabilidades e indicação dos limiares de operação.

## Técnicas utilizadas

### Classificação multirrótulo

Uma radiografia pode apresentar mais de um padrão simultaneamente. Por isso, o
projeto utiliza classificação multirrótulo em vez de escolher uma única classe
ou desenhar caixas delimitadoras.

O modelo calcula probabilidades para 18 padrões radiológicos, incluindo
`Pneumonia`, `Consolidation`, `Infiltration`, `Lung Opacity`, `Pneumothorax`,
`Effusion` e `Fibrosis`.

### DenseNet-121

A inferência utiliza a DenseNet-121 disponibilizada pelo
`torchxrayvision`, pré-treinada em bases públicas de radiografias. Suas conexões
densas favorecem o reaproveitamento de características visuais entre camadas,
como texturas, opacidades e alterações estruturais.

### Pré-processamento

As imagens passam pelas seguintes etapas:

1. leitura de PNG, JPG ou DICOM;
2. conversão para tons de cinza;
3. aplicação de `RescaleSlope` e `RescaleIntercept` em arquivos DICOM;
4. inversão de imagens com interpretação `MONOCHROME1`;
5. normalização para a escala esperada pelo modelo;
6. recorte central;
7. redimensionamento para `224 × 224`;
8. conversão para tensor no formato `[1, 1, 224, 224]`.

### Grad-CAM

O Grad-CAM utiliza os gradientes da classe analisada sobre a última etapa
convolucional da rede. Esses gradientes ponderam os mapas de características e
produzem uma representação espacial das regiões que mais influenciaram a
previsão.

O resultado é normalizado, convertido em um mapa de cores e sobreposto à
radiografia original. O mapa mostra a atenção do modelo, não a delimitação
clínica de uma lesão.

### Limiares de operação

Cada probabilidade pode ser comparada ao `op_threshold` fornecido pelo modelo.
Esse valor oferece contexto para a saída e evita interpretar toda probabilidade
como um resultado binário automático.

### Pipeline

```text
Upload
  → leitura e normalização
  → recorte e redimensionamento
  → DenseNet-121
  → probabilidades multirrótulo
  → seleção do alvo
  → Grad-CAM
  → sobreposição do mapa de calor
  → resposta da API
  → visualização no navegador
```

### Testes

Os testes JavaScript verificam a consistência dos estudos do atlas. O teste de
fumaça em Python gera uma radiografia sintética, chama a API e valida o formato
das previsões e das imagens produzidas pelo pipeline.

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
├── comparison.py           cálculo dos deltas entre duas análises
├── metrics.py              métricas binárias educacionais (AUROC, F1…)
├── radiograph_quality.py   heurísticas de QC radiográfico
├── uncertainty.py          estabilidade via TTA leve
├── analysis_cache.py       cache em memória por hash do arquivo
├── jobs.py                 fila assíncrona de análises
├── rate_limit.py           limitador por origem
├── index.html              estrutura da interface web
├── styles.css              apresentação visual e responsividade
├── app.js                  interação da interface e integração com a API
├── data.js                 metadados do atlas visual
├── glossary.js             glossário educacional das classes
├── viewer.js               regras dos controles radiológicos
├── history.js              histórico privado e relatório educacional
├── Dockerfile              imagem de execução sem privilégios
├── docker-compose.yml      serviço e cache persistente do modelo
├── scripts/                execução Python multiplataforma
├── .github/workflows/      validação automática e build do container
├── assets/
│   ├── chest-*.jpg         incidências de referência
│   ├── *pneumonia*.jpg     exemplos de pneumonia
│   ├── pneumothorax-*.jpg  exemplo de pneumotórax
│   ├── pleural-*.jpg       exemplo de derrame pleural
│   ├── pulmonary-*.jpg     exemplo de edema pulmonar
│   └── thorax-anatomy.gif  referência anatômica
├── tests/
│   ├── data.test.js        consistência dos dados do atlas
│   ├── viewer.test.js      controles de visualização
│   └── history.test.js     histórico e exportação
├── test_*.py               testes unitários da API e processamento
└── smoke_test.py           teste ponta a ponta da API e do modelo
```

### Backend

O `main.py` expõe os endpoints:

- `GET /health`: carrega o modelo e informa seu estado.
- `GET /api/info`: versão da API e capacidades disponíveis.
- `POST /analyze`: recebe uma imagem, executa o pipeline e retorna as previsões,
  a qualidade de entrada, a radiografia processada e o mapa de atenção.
- `POST /analyze/async` e `GET /jobs/{id}`: análise assíncrona com progresso.
- `POST /compare`: processa duas imagens e ordena as maiores diferenças entre
  as probabilidades produzidas pelo modelo.
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
- escolha da classe usada para gerar o Grad-CAM;
- brilho, contraste e inversão no visualizador;
- comparação A/B entre referências;
- modo de estudo e checklist ABCDE;
- histórico limitado ao navegador e exportação JSON;
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

### Avaliação heurística da entrada

Antes da inferência, o sistema calcula resolução, proporção, contraste, faixa
dinâmica e percentuais de pixels próximos ao preto ou branco. Esses indicadores
geram alertas educacionais, sem bloquear imagens atípicas que ainda possam ser
úteis para experimentação.

### Grad-CAM

O Grad-CAM utiliza os gradientes da classe analisada sobre a última etapa
convolucional da rede. Esses gradientes ponderam os mapas de características e
produzem uma representação espacial das regiões que mais influenciaram a
previsão.

O resultado é normalizado, convertido em um mapa de cores e sobreposto à
radiografia original. O mapa mostra a atenção do modelo, não a delimitação
clínica de uma lesão.

O alvo do mapa pode ser alterado entre as classes previstas. O sistema também
resume a ativação média, o percentil 90 e o centro visual de atenção para ajudar
a comparar explicações.

### Limiares de operação

Cada probabilidade pode ser comparada ao `op_threshold` fornecido pelo modelo.
Esse valor oferece contexto para a saída e evita interpretar toda probabilidade
como um resultado binário automático.

### Contexto de decisão

Cada classe recebe a distância até seu limiar e uma ambiguidade matemática
baseada na entropia binária. Classes próximas do limiar são apresentadas como
limítrofes. Essas medidas contextualizam a saída numérica, mas não representam
confiança clínica ou probabilidade diagnóstica.

### DICOM e windowing

O leitor aplica `RescaleSlope`, `RescaleIntercept`, `WindowCenter` e
`WindowWidth` quando disponíveis, além de tratar `MONOCHROME1`. Apenas
metadados técnicos permitidos são devolvidos; identificadores do paciente nunca
entram na resposta da API.

### Comparação A/B

Duas imagens passam pelo mesmo pré-processamento e pela mesma DenseNet-121. A
diferença em pontos percentuais é calculada para cada classe e ordenada por
magnitude. Essa comparação descreve a resposta do modelo, não evolução clínica.

### Persistência privada

O backend não armazena imagens ou resultados. O histórico usa `localStorage`,
mantém no máximo dez registros com miniaturas reduzidas e permite exportar um
JSON educacional sem incluir a imagem original.

### QC radiográfico e estabilidade

Além da qualidade de entrada, o sistema estima exposição, assimetria
(rotação aparente) e um hint educacional de projeção. Opcionalmente, um TTA
leve mede a estabilidade das probabilidades sob flip e ruído.

### Cache, jobs e limite de taxa

Resultados recentes são reutilizados por hash do arquivo. A análise pode
correr em job assíncrono com estágios de progresso. Requisições `POST /analyze*`
podem ser limitadas por origem para demos locais.

### Segurança e observabilidade

A API valida extensão, MIME e assinatura binária, limita uploads, restringe
CORS e adiciona CSP, identificador de requisição e cabeçalhos contra sniffing e
iframes. Tempos de pré-processamento, inferência, Grad-CAM e requisição são
medidos separadamente.

### Infraestrutura

O container executa como usuário sem privilégios e mantém o cache dos pesos em
volume separado. O GitHub Actions compila o Python, executa a suíte rápida em
Linux e verifica a construção da imagem Docker.

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

Os testes JavaScript cobrem atlas, visualizador, histórico, CSV e relatórios.
Os testes Python cobrem métricas, QC radiográfico, cache, rate limit, qualidade,
comparação, estatísticas Grad-CAM, erros da API e o pipeline completo com
radiografia sintética.

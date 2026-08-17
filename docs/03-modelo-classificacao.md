# 03 — Modelo de classificação multirrótulo

A etapa central de inteligência artificial utiliza uma **DenseNet-121** disponibilizada pelo `torchxrayvision`, pré-treinada em bases públicas de radiografias.

## O que foi desenvolvido

1. Carregamento do modelo e dos pesos necessários.
2. Integração do modelo ao backend FastAPI.
3. Inferência sobre tensores de radiografia pré-processados.
4. Classificação multirrótulo, permitindo que uma mesma radiografia apresente simultaneamente mais de um padrão.
5. Retorno de probabilidades para 18 padrões radiológicos.
6. Inclusão de classes como `Pneumonia`, `Consolidation`, `Infiltration`, `Lung Opacity`, `Pneumothorax`, `Effusion` e `Fibrosis`.
7. Associação das probabilidades aos limiares operacionais (`op_threshold`) fornecidos pelo modelo.
8. Ordenação dos resultados para facilitar a interpretação visual no frontend.

A escolha por classificação multirrótulo é importante porque radiografias podem apresentar múltiplos achados ao mesmo tempo. Dessa forma, o sistema não força uma única classe como resposta.

Os valores produzidos pelo modelo devem ser entendidos como saídas matemáticas do classificador e não como probabilidades diagnósticas clínicas.
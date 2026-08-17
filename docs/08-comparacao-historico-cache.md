# 08 — Comparação A/B, histórico, cache e processamento assíncrono

Além da análise individual, o projeto recebeu recursos para comparação, reutilização de resultados e acompanhamento de processamento.

## Comparação A/B

Duas imagens podem ser submetidas ao mesmo pipeline. Para cada classe, o sistema calcula a diferença entre as probabilidades e ordena os maiores deltas em pontos percentuais.

Esse recurso permite comparar a resposta do modelo a duas radiografias, sem interpretar a diferença como evolução clínica.

## Histórico local

O navegador mantém um histórico privado com `localStorage`:

- limite de até dez registros;
- miniaturas reduzidas;
- armazenamento local no navegador;
- exportação de relatório educacional em JSON;
- ausência de persistência da imagem original no backend.

## Cache

Resultados recentes podem ser reutilizados através de um cache em memória indexado pelo hash do arquivo, evitando inferências repetidas quando a mesma entrada é reenviada.

## Jobs assíncronos

A análise também pode ser iniciada em segundo plano pela API, com identificador de job e estágios de progresso consultáveis pelo cliente. Isso separa o envio da imagem da espera síncrona pelo processamento completo.
# 10 — Testes, CI e mini-acervo NIH ChestX-ray14

A etapa final de evolução do protótipo consolidou testes automatizados, integração contínua e um conjunto educacional opcional de radiografias reais.

## Testes automatizados

A suíte JavaScript cobre componentes do frontend, incluindo:

- consistência dos dados do atlas;
- controles do visualizador;
- histórico local;
- exportação e relatórios.

A suíte Python cobre diferentes partes do backend e do pipeline:

- métricas binárias educacionais;
- controle de qualidade radiográfica;
- cache;
- rate limit;
- validação de qualidade da entrada;
- comparação entre análises;
- estatísticas do Grad-CAM;
- tratamento de erros da API;
- pipeline completo com radiografia sintética.

Também existe um `smoke_test.py` para validar o fluxo ponta a ponta.

## Integração contínua

O GitHub Actions foi configurado para:

1. validar a compilação do código Python;
2. executar a suíte rápida de testes em Linux;
3. verificar a construção da imagem Docker.

## NIH ChestX-ray14

Foi adicionado suporte a um mini-acervo educacional com aproximadamente 15 radiografias do NIH ChestX-ray14.

O conjunto não é versionado diretamente no repositório. Um script específico realiza o download local das imagens selecionadas. O atlas permite filtrar esses estudos pela tag `NIH`.

Os rótulos associados ao ChestX-ray14 foram originalmente minerados de texto e não devem ser tratados como laudos clínicos. O uso do conjunto requer atribuição ao NIH Clinical Center e referência ao trabalho de Wang et al. (CVPR 2017).

Com essa etapa, o projeto passou a ter não apenas inferência e interface, mas também mecanismos de validação, reprodutibilidade e demonstração com dados públicos.
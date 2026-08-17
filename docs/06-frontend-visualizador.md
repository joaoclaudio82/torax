# 06 — Frontend e visualizador educacional

O frontend foi desenvolvido com **HTML, CSS e JavaScript sem framework**, mantendo a aplicação leve e diretamente integrada à API.

## Recursos desenvolvidos

1. Interface para upload de radiografias PNG, JPG e DICOM.
2. Integração com o endpoint de análise.
3. Exibição da radiografia processada.
4. Exibição do Grad-CAM e comparação visual com a imagem original.
5. Seleção da classe usada como alvo da explicabilidade.
6. Ranking das probabilidades produzidas pelo modelo.
7. Indicação visual dos limiares de operação.
8. Controles de brilho, contraste e inversão.
9. Atlas com incidências PA, lateral e referências anatômicas.
10. Comparação A/B entre referências.
11. Modo de estudo com checklist ABCDE.
12. Glossário educacional para auxiliar a interpretação das classes.
13. Busca e filtros no catálogo visual.
14. Integração opcional com o mini-acervo NIH ChestX-ray14.

A interface foi construída para permitir que o usuário percorra o fluxo completo — seleção da imagem, inferência, interpretação da saída e análise visual — sem precisar interagir diretamente com código Python.
# 01 — Visão geral do projeto Tórax

O projeto **Tórax** é um protótipo educacional para análise de radiografias de tórax com técnicas de visão computacional e aprendizado profundo.

O objetivo principal foi construir uma aplicação completa capaz de:

- receber radiografias em PNG, JPG e DICOM;
- pré-processar as imagens para o formato esperado pela rede neural;
- executar classificação multirrótulo;
- apresentar probabilidades para diferentes achados radiológicos;
- gerar mapas de atenção com Grad-CAM;
- permitir análise visual diretamente no navegador;
- oferecer recursos de comparação, qualidade da imagem, histórico, exportação e execução assíncrona;
- executar de forma reproduzível por Docker;
- manter testes automatizados e validação por GitHub Actions.

A aplicação foi estruturada em três grandes camadas:

1. **Backend em Python/FastAPI**, responsável pela API e pelo pipeline de inferência.
2. **Modelo de IA baseado em DenseNet-121**, utilizando pesos pré-treinados para radiografias de tórax.
3. **Frontend em HTML, CSS e JavaScript**, responsável pela experiência de visualização e estudo.

O sistema possui finalidade exclusivamente educacional e experimental. As saídas não devem ser interpretadas como diagnóstico clínico.
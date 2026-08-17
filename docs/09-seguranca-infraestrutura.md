# 09 — Segurança, infraestrutura e execução

O projeto foi preparado para execução reproduzível e para reduzir riscos comuns de uma API de upload de imagens.

## Segurança implementada

- validação de extensão do arquivo;
- validação de MIME type;
- verificação da assinatura binária;
- limite de tamanho de upload;
- restrição de CORS;
- Content Security Policy (CSP);
- cabeçalhos contra MIME sniffing;
- proteção contra carregamento em iframe;
- identificador de requisição;
- rate limit por origem para endpoints de análise;
- minimização de metadados DICOM retornados.

## Infraestrutura

A aplicação foi empacotada com Docker. O container executa como usuário sem privilégios e mantém o cache dos pesos do modelo em volume separado.

O arquivo `docker-compose.yml` simplifica a inicialização local do serviço e o reaproveitamento do cache do modelo.

Essa estrutura torna o ambiente mais previsível entre máquinas de desenvolvimento, testes e demonstração.
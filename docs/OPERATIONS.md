# Operação do serviço

Este documento descreve a execução do protótipo educacional de análise de radiografias de tórax. O serviço não é um dispositivo médico e não deve ser utilizado para diagnóstico ou decisão clínica.

## Health checks

- `GET /health/live`: confirma que o processo HTTP está vivo sem carregar pesos do modelo.
- `GET /health/ready`: confirma que a DenseNet pode ser carregada e responde `503` quando o serviço ainda não está pronto.
- `GET /health`: permanece como endpoint de compatibilidade e resumo operacional.

Em orquestradores, use `/health/live` como liveness probe e `/health/ready` como readiness probe.

## Configuração

Copie `.env.example` para o mecanismo de configuração do ambiente. Não versione tokens administrativos. Os parâmetros de upload, rate limit, cache e jobs possuem limites defensivos; valores inválidos retornam aos defaults seguros.

## Uploads

Os uploads devem ser lidos em blocos e interrompidos quando ultrapassarem `THORAX_MAX_UPLOAD_MB`. Isso reduz alocação de memória para requisições excessivas. Extensão, MIME e assinatura binária continuam sendo validados antes do processamento.

## Métricas

`GET /metrics` expõe contadores agregados de processo quando `THORAX_METRICS_ENABLED=1`. As métricas não incluem nome de arquivo, pixels, DICOM tags identificadoras, IP bruto ou conteúdo da requisição.

Indicadores recomendados:

- total de requisições e distribuição por status;
- latência média acumulada;
- ocorrências de rate limit;
- rejeições de upload;
- estatísticas de cache e jobs.

## Logs

O identificador `X-Request-ID` é normalizado antes de ser reutilizado em headers e logs. Evite registrar nomes de pacientes, identificadores DICOM, imagens, payloads de inferência ou tokens.

## Reverse proxy

Ative `THORAX_TRUST_PROXY=1` somente quando o serviço estiver atrás de proxy controlado que sobrescreva `X-Forwarded-For`. Caso contrário, mantenha desativado para evitar spoofing da origem usada pelo rate limit.

## Cache e jobs

Cache e fila são deliberadamente em memória e adequados apenas ao protótipo. Em execução multi-worker, cada processo terá estado próprio. Para produção experimental distribuída, migre esses componentes para um backend externo antes de depender de consistência global.

## Incidentes

Em caso de comportamento anômalo:

1. retire o serviço do balanceador usando a readiness probe;
2. preserve logs sem dados sensíveis;
3. registre versão do código e pesos do modelo;
4. limpe o cache pelo endpoint administrativo somente com token configurado;
5. reproduza o problema com dados de demonstração não identificáveis.

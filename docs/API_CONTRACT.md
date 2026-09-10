# Contrato da API

A API é destinada a pesquisa e ensino. Nenhuma resposta deve ser interpretada como diagnóstico, laudo ou recomendação clínica.

## Endpoints operacionais

### `GET /health/live`

Resposta `200` quando o processo está executando. Não carrega o modelo.

### `GET /health/ready`

Resposta `200` quando o modelo pode ser carregado. Resposta `503` quando a dependência de inferência não está pronta.

### `GET /metrics`

Retorna contadores agregados quando a telemetria está habilitada. Inclui média e percentis p50/p95 de latência calculados sobre uma amostra limitada em memória. Pode responder `404` quando desabilitada por configuração.

### `GET /api/model`

Retorna arquitetura, pesos, classes disponíveis, shape de entrada, finalidade educacional, semântica dos escores e limitações conhecidas.

### `GET /api/config`

Retorna somente a configuração operacional segura para observabilidade; segredos administrativos não são expostos.

## Análise

`POST /analyze` e `POST /analyze/async` aceitam PNG, JPEG e DICOM. O tamanho máximo é definido por `THORAX_MAX_UPLOAD_MB`.

A resposta inclui:

- escores multirrótulo e limiares de operação quando disponíveis;
- contexto matemático de margem e ambiguidade;
- indicadores técnicos de qualidade da entrada e QC radiográfico;
- Grad-CAM e estatísticas do mapa de atenção;
- tempos de processamento;
- aviso explícito de uso educacional.

Por compatibilidade, o campo numérico de cada predição continua denominado `prob`. Ele deve ser interpretado como **escore do modelo normalizado em relação ao ponto de operação**, e não como probabilidade diagnóstica calibrada. O endpoint `GET /api/model` explicita essa semântica e recomenda o termo `model_score` para consumidores novos.

O módulo `quality_policy.py` fornece uma política agregadora testada para evoluções futuras da UI/API, mas não altera silenciosamente o contrato atual de `/analyze`.

## Erros relevantes

- `400`: upload vazio ou requisição incompleta;
- `413`: arquivo ou corpo HTTP acima do limite configurado;
- `415`: extensão, MIME ou assinatura não suportados;
- `422`: imagem inválida para o pipeline ou patologia-alvo desconhecida;
- `429`: limite de requisições excedido;
- `503`: modelo indisponível no readiness check ou fila assíncrona sem capacidade.

## Privacidade

O backend não deve persistir imagens recebidas. Respostas DICOM expõem apenas metadados técnicos permitidos. Métricas operacionais não devem registrar nomes de arquivo, pixels, identificadores de paciente ou conteúdo de predição por requisição.

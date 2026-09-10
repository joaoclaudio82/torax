# Melhorias de robustez — setembro de 2026

Esta rodada consolida três objetivos: manter o CI alinhado à configuração centralizada, tornar a semântica dos escores do modelo explícita e melhorar a observabilidade sem registrar dados clínicos.

## Alterações

- testes da API agora usam `config.settings` em vez de constantes removidas do `main.py`;
- o teste do token administrativo passa a substituir a configuração completa de forma segura;
- o model card declara explicitamente que `prob` é um campo legado que representa um escore normalizado do modelo, não uma probabilidade diagnóstica calibrada;
- o model card inclui versão do contrato, semântica do Grad-CAM e necessidade de validação externa;
- métricas de runtime passam a expor p50 e p95 de latência com amostragem limitada em memória;
- documentação do contrato da API foi atualizada para refletir essas garantias.

Nenhuma alteração foi feita nos pesos, no forward da DenseNet-121, no pré-processamento, no Grad-CAM ou nos pontos operacionais.

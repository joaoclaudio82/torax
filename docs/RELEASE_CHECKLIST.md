# Checklist de release

## Código e testes

- [ ] Instalação limpa de `requirements.txt` concluída.
- [ ] `python -m pip check` sem conflitos.
- [ ] `python -m compileall -q .` concluído.
- [ ] Suíte rápida Python/Node aprovada.
- [ ] Smoke test aprovado com os pesos esperados.
- [ ] Build Docker concluído.

## API

- [ ] `/health/live` responde sem carregar o modelo.
- [ ] `/health/ready` retorna `200` após o modelo estar disponível.
- [ ] `/api/model` descreve os pesos e limitações corretos.
- [ ] Upload acima do limite retorna `413` sem leitura integral do arquivo.
- [ ] Formato inválido retorna `415`.
- [ ] Rate limit retorna `429` e `Retry-After`.

## Privacidade e segurança

- [ ] Nenhum segredo foi versionado.
- [ ] `THORAX_TRUST_PROXY` está coerente com a infraestrutura.
- [ ] CORS contém somente as origens necessárias.
- [ ] Logs e métricas não contêm PHI nem conteúdo de imagem.
- [ ] Metadados DICOM continuam restritos à allowlist técnica.

## Modelo

- [ ] Identificador dos pesos registrado.
- [ ] Número de patologias conferido.
- [ ] Pré-processamento 224×224 conferido.
- [ ] Disclaimer educacional presente na UI e na API.
- [ ] Mudanças de dependências de ML revisadas para regressões de inferência.

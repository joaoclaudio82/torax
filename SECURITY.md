# Política de segurança

## Escopo

Este repositório contém um protótipo educacional de visão computacional para radiografias de tórax. Ele não é um dispositivo médico e não deve receber dados identificáveis de pacientes em ambientes não aprovados.

## Relato de vulnerabilidades

Ao identificar uma vulnerabilidade, evite publicar segredos, dados pessoais, imagens clínicas identificáveis ou detalhes de exploração em issues públicas. Prefira um canal privado do mantenedor quando disponível.

## Controles implementados

- validação de extensão, MIME e assinatura binária;
- limite configurável de upload com leitura interrompida ao excedê-lo;
- CORS restrito por configuração;
- rate limit em endpoints de processamento;
- CSP, `X-Content-Type-Options`, `X-Frame-Options` e política de permissões;
- token administrativo fora do código;
- normalização de `X-Request-ID`;
- metadados DICOM retornados por allowlist técnica, sem identificadores do paciente;
- métricas agregadas sem conteúdo de imagem ou payload clínico.

## Segredos

Nunca versione `THORAX_ADMIN_TOKEN`, credenciais de nuvem, tokens de proxy ou chaves de serviços externos. Use variáveis de ambiente ou secret stores.

## Dependências

A CI deve instalar as dependências a partir de `requirements.txt`, executar `pip check`, testes rápidos e smoke test. Atualizações de dependências de ML devem ser avaliadas também quanto a mudanças de pesos, pré-processamento e compatibilidade do modelo.

## Limitações conhecidas

Cache, rate limit, métricas e jobs são locais ao processo. Em execução com múltiplos workers, esses estados não são globais. O projeto não promete isolamento multiusuário, auditoria clínica, rastreabilidade regulatória ou disponibilidade hospitalar.

# 02 — Pipeline de leitura e pré-processamento

O pipeline de imagem foi desenvolvido para padronizar diferentes formatos de radiografia antes da inferência.

## Etapas implementadas

1. Recebimento do arquivo pela API.
2. Validação de extensão, MIME type, assinatura binária e tamanho do upload.
3. Leitura de PNG e JPG como imagem em tons de cinza.
4. Leitura de DICOM com aplicação de parâmetros técnicos disponíveis no arquivo.
5. Aplicação de `RescaleSlope` e `RescaleIntercept` quando presentes.
6. Tratamento de imagens `MONOCHROME1`, realizando inversão quando necessário.
7. Aplicação de windowing DICOM com `WindowCenter` e `WindowWidth`, quando disponíveis.
8. Conversão para matriz bidimensional.
9. Normalização da intensidade dos pixels.
10. Recorte central da radiografia.
11. Redimensionamento para `224 x 224` pixels.
12. Conversão para tensor no formato esperado pelo modelo: `[1, 1, 224, 224]`.

O módulo `imaging.py` concentra essa responsabilidade e desacopla o tratamento de imagem da lógica da API e da inferência.

Também foi adotado o princípio de minimizar exposição de dados sensíveis em arquivos DICOM: apenas metadados técnicos permitidos são devolvidos pela aplicação, sem incluir identificadores pessoais do paciente.
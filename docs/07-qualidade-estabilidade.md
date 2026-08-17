# 07 — Qualidade radiográfica, limiares e estabilidade

Foram desenvolvidos mecanismos auxiliares para contextualizar a saída do modelo e avaliar tecnicamente a imagem de entrada.

## Qualidade da imagem

Antes da inferência, o sistema calcula indicadores como:

- resolução;
- proporção da imagem;
- contraste;
- faixa dinâmica;
- percentual de pixels muito próximos do preto;
- percentual de pixels muito próximos do branco.

Esses indicadores alimentam alertas educacionais e não bloqueiam automaticamente imagens atípicas.

## QC radiográfico

O projeto também estima heurísticas relacionadas a:

- exposição;
- assimetria, usada como sinal aproximado de rotação;
- projeção radiográfica como informação educacional auxiliar.

## Contexto dos resultados

Cada classe é comparada ao seu `op_threshold`. O sistema calcula ainda:

1. distância entre a probabilidade e o limiar;
2. ambiguidade matemática baseada em entropia binária;
3. identificação de classes próximas do limiar como resultados limítrofes.

## Estabilidade por TTA

Opcionalmente, a aplicação executa uma forma leve de **Test-Time Augmentation (TTA)** usando pequenas perturbações, como flip e ruído, para observar o quanto as probabilidades mudam.

Essa análise representa estabilidade numérica da saída do modelo e não confiança clínica.
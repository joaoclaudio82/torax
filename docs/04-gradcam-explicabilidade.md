# 04 — Grad-CAM e explicabilidade visual

Foi implementado um mecanismo de explicabilidade baseado em **Grad-CAM** para mostrar quais regiões da radiografia mais influenciaram a saída do modelo.

## Fluxo desenvolvido

1. Seleção de uma classe de interesse entre as classes previstas.
2. Cálculo dos gradientes dessa classe em relação à última etapa convolucional da DenseNet-121.
3. Uso dos gradientes como pesos dos mapas de características.
4. Geração do mapa de ativação espacial.
5. Normalização do mapa de calor.
6. Conversão do mapa para uma representação visual adequada à interface.
7. Sobreposição do Grad-CAM à radiografia original.
8. Exibição lado a lado entre imagem processada e mapa de atenção.
9. Possibilidade de alterar dinamicamente a classe usada como alvo do Grad-CAM.
10. Cálculo de estatísticas auxiliares, incluindo ativação média, percentil 90 e centro visual da atenção.

O Grad-CAM indica regiões relevantes para a decisão matemática da rede neural. Ele não representa segmentação de lesão nem delimitação clínica de uma patologia.
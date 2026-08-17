# 05 — API e organização do backend

O backend foi estruturado com **FastAPI** para expor o pipeline de processamento e inferência por meio de endpoints HTTP.

## Endpoints implementados

- `GET /health`: verifica o estado da aplicação e o carregamento do modelo.
- `GET /api/info`: apresenta versão e capacidades disponíveis.
- `POST /analyze`: recebe uma imagem, executa o pipeline completo e devolve previsões, dados de qualidade, imagem processada e Grad-CAM.
- `POST /analyze/async`: inicia uma análise assíncrona.
- `GET /jobs/{id}`: acompanha o progresso e o resultado de um job.
- `POST /compare`: processa duas imagens e retorna as maiores diferenças entre as probabilidades produzidas pelo modelo.
- `GET /`: entrega a interface web.

## Organização interna

O backend foi dividido em módulos especializados para reduzir acoplamento:

- `imaging.py`: leitura e pré-processamento;
- `xray_model.py`: inferência e Grad-CAM;
- `overlay.py`: composição do mapa de calor;
- `comparison.py`: comparação entre análises;
- `analysis_cache.py`: cache por hash;
- `jobs.py`: execução assíncrona;
- `rate_limit.py`: limitação de requisições;
- `radiograph_quality.py`: avaliação heurística da radiografia;
- `uncertainty.py`: estimativa de estabilidade via TTA.

Também foram adicionadas medições separadas de tempo de pré-processamento, inferência, Grad-CAM e tempo total da requisição para melhorar observabilidade.
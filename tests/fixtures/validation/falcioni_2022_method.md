# Referencia metodologica — Falcioni et al. (2022)

**Artigo:** "Classification and Prediction by Pigment Content in Lettuce (Lactuca sativa L.) Varieties Using Machine Learning and ATR-FTIR Spectroscopy".
**DOI:** 10.3390/plants11243413
**URL:** https://doi.org/10.3390/plants11243413

## Uso neste projeto

Este artigo serve como **referencia metodologica apenas** para comparar:
- Regressao por minimos quadrados parciais (PLSR);
- Analise multivariada;
- Metricas preditivas (MAE, RMSE, R2, viés, residuos).

## Restricoes (inegociaveis)

- Nao copiar as metricas publicadas como se fossem previsoes do nosso projeto.
- O conjunto de alface (Lactuca sativa) nao valida automaticamente o modelo de repolho roxo (Brassica oleracea).
- Matrizes diferentes (alface vs repolho roxo), metodo diferente (ATR-FTIR vs espectrofotometria UV-Vis / colorimetria) e espectroscopia diferente impedem transferencia direta de metricas.
- Qualquer comparacao entre Random Forest, PLSR e referencia simples so e valida onde a quantidade e estrutura dos dados do nosso projeto permitirem comparacao valida.
- Com poucas series temporais independentes, emitir `ML_NOT_VALIDATED`; nao declarar "melhor modelo", nao usar split aleatorio por linha, nao declarar previsoes confiaveis.

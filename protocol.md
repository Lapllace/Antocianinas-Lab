# Protocolo v2 — conservação de extrato líquido de repolho roxo para indicador de pH

**Versão de trabalho para discussão com a orientação e adequação aos procedimentos operacionais do laboratório (SOPs).** O produto principal do estudo é o extrato líquido; a liofilização não é necessária na etapa principal.

## 1. Pergunta e contribuição pretendida

**Pergunta:** como a acidificação inicial e a temperatura de armazenamento afetam, em lotes independentes, a retenção de antocianinas e a capacidade do extrato líquido de distinguir soluções de pH conhecido por espectrofotometria e smartphone?

A literatura já demonstra a relação pH-cor usando LED RGB e smartphone e já estudou estabilidade físico-química, colorimétrica e microbiológica de extratos líquidos de repolho roxo. Portanto, não se deve apresentar a estabilidade líquida, por si só, como novidade inédita. A contribuição possível é avaliar a reprodutibilidade entre três lotes independentes, comparar extrato no pH nativo e acidificado, prolongar o acompanhamento até 28 dias e testar se as métricas de smartphone permanecem úteis ao longo do armazenamento. A lacuna e a originalidade precisam ser confirmadas com uma revisão bibliográfica atualizada antes de submeter um artigo.

## 2. Desenho reduzido recomendado

- **Lotes independentes:** 3 extrações realizadas separadamente, identificadas B01, B02 e B03. Esses lotes, e não várias leituras da mesma amostra, são as réplicas experimentais independentes.
- **Formulações:** F_NATIVE, extrato no pH nativo; F_PH3, alíquota do mesmo lote ajustada a pH 3,0 ± 0,1. Escolher um único acidificante de concentração conhecida e usá-lo em todos os lotes; registrar volume adicionado e pH final. O resultado será específico desse acidificante.
- **Armazenamento:** C4_DARK, 4 ± 1 °C no escuro; C25_DARK, 25 ± 2 °C no escuro. Manter luz protegida nas duas condições para isolar, nesta fase, o fator temperatura. A literatura já aponta efeito importante da luz; um estudo de luz pode ser uma segunda fase.
- **Tempos:** dias 0, 3, 7, 10, 14 e 28. Os primeiros tempos são densos porque um estudo publicado em 2026 estimou meia-vida de cerca de 9,5 dias para o extrato aquoso sob as condições daquele estudo.
- **Frascos/unidades físicas:** 60 alíquotas de armazenamento (3 lotes × 2 formulações × 2 condições × 5 tempos depois do dia 0) + 6 alíquotas basais (3 lotes × 2 formulações) = **66 unidades no total**. O dia 0 é medido uma vez para cada lote/formulação, antes de distribuir as alíquotas entre as condições. Essa medição basal compartilhada não exige um frasco físico separado para cada condição.
- **Volume:** usar inicialmente cerca de 10–15 mL por frasco, após confirmar em um piloto que o volume comporta espectrofotometria, colorimetria e eventuais análises complementares. O total aproximado fica entre 660 e 990 mL, além das perdas de filtração e do material reservado para caracterização inicial.
- **Oxigênio/espaço de cabeça:** não será um fator experimental separado. Padronizar o modelo de frasco, tampa, volume de enchimento e espaço de cabeça e não concluir sobre o efeito independente do oxigênio.

**Alternativa ainda menor:** se a orientação decidir que acidificação não é uma pergunta experimental e já escolher uma única formulação com base na literatura e num piloto, o desenho passa a 3 lotes × 2 condições × 5 tempos posteriores + 3 basais = **33 unidades**. Essa opção reduz custo, mas não permite estimar o efeito da acidificação em paralelo.

## 3. Extração e preparo

A proporção inicial de 1:10 (massa:volume) é uma condição operacional proposta, não uma condição universalmente ótima. Sugestão para o piloto: 50 g de repolho roxo e 500 mL de água destilada/deionizada por lote. Padronizar fornecedor, condição do vegetal, tamanho dos fragmentos, tempo de homogeneização, temperatura, tempo de contato, filtração e volume recuperado.

1. Lavar o repolho, retirar partes deterioradas, secar superficialmente e registrar lote de compra, data e massa fresca.
2. Homogeneizar a massa vegetal com água destilada/deionizada em proporção 1:10 (m/v), evitando aquecimento significativo.
3. Como condição inicial de piloto, manter 30 minutos a 4 °C, protegido da luz, sob agitação suave padronizada.
4. Filtrar pelo mesmo procedimento em todos os lotes; registrar volume recuperado, pH, temperatura e aparência.
5. Dividir cada lote em duas partes. Preservar uma no pH nativo e ajustar a outra a pH 3,0 ± 0,1 com solução diluída padronizada do acidificante selecionado. Registrar pH e volume adicionados.
6. Antes de alocar amostras, retirar e analisar a alíquota basal de cada formulação. Identificar claramente essas observações com `day=0` e `storage_condition=BASELINE` nos CSVs. A versão v2 do código aceita esse dia 0 compartilhado.
7. Distribuir volumes iguais em frascos individuais codificados. Cada frasco armazenado é aberto apenas uma vez, no seu tempo de análise.

Não usar hipoclorito/água sanitária para alcalinizar amostras usadas na calibração pH-cor: o hipoclorito é oxidante e pode degradar pigmentos, confundindo o efeito do pH com oxidação. Para a resposta indicadora, usar soluções-tampão de pH conhecido e medir o pH final da mistura com o extrato.

## 4. Condições de armazenamento

- `C4_DARK`: 4 ± 1 °C, no escuro.
- `C25_DARK`: 25 ± 2 °C, no escuro.

Usar frascos, tampas e volumes de enchimento equivalentes. Registrar temperatura real em cada condição. Randomizar a posição das amostras quando apropriado. Não adicionar conservantes nesta primeira fase: isso confundiria a pergunta sobre acidificação/temperatura. Conservantes só devem ser testados em um estudo separado, depois de definir objetivo e segurança.

## 5. Medições

### 5.1 Em todos os tempos (0, 3, 7, 10, 14 e 28 dias)

- pH do extrato, temperatura da leitura, turbidez/precipitado e observações físicas.
- Antocianinas monoméricas pelo método diferencial de pH, se o laboratório tiver o procedimento validado e reagentes necessários.
- RGB por smartphone numa configuração fixa e resposta indicadora para um conjunto sentinela de pHs (por exemplo, pH 3, 7 e 10).

### 5.2 Curva completa de resposta ao pH

Nos dias 0, 14 e 28, testar uma série de tampões, por exemplo pH 2–10, com proporção extrato:tampão, volume, tempo de equilíbrio e temperatura padronizados. Medir o pH final depois de misturar tampão e extrato. Fazer varreduras UV–Vis de 400–700 nm nos mesmos pontos-chave, conforme volume disponível. Os valores escolhidos são um plano experimental; ajustar em piloto e fixar antes da coleta principal.

### 5.3 Método diferencial de pH

Seguir o SOP validado pelo laboratório (por exemplo, método de Lee et al./AOAC 2005.02). Em termos gerais, preparar alíquotas apropriadas em tampão pH 1,0 e tampão pH 4,5; medir absorbância a 520 e 700 nm, com brancos e fator de diluição registrados.

\[
A = (A_{520}-A_{700})_{pH\,1,0}-(A_{520}-A_{700})_{pH\,4,5}
\]

\[
C\;(\mathrm{mg\ C3G/L}) = \frac{A\times 449,2\times DF\times 1000}{26.900\times l}
\]

Aqui `DF` é o fator de diluição e `l` o caminho óptico em cm. Reportar a concentração como equivalentes de cianidina-3-glicosídeo (C3G), não como identificação individual de todas as antocianinas. Confirmar massa molar, coeficiente de extinção, caminho óptico e fórmula no procedimento analítico adotado antes de reportar resultados.

Calcular retenção química: `retention_pct = 100 × C_t / C_0`, usando o dia 0 do mesmo lote e formulação como referência. A retenção química não substitui a avaliação da função indicadora.

### 5.4 Smartphone

Usar o mesmo smartphone, suporte, recipiente/cubeta, posição, distância, fundo e iluminação. Desativar flash, filtros e HDR e bloquear exposição, foco e balanço de branco quando disponível. Guardar imagens originais sem edição; incluir referência de branco/cinza e extrair a mediana RGB de uma região de interesse sem reflexos. Converter RGB em HSV no código. Se houver colorímetro ou procedimento calibrado para CIELAB, registrar L*, a*, b* e calcular diferença de cor, deixando claro qual fórmula foi usada.

A iluminação verde merece ser testada como hipótese baseada no artigo da UFN, mas não deve ser presumida como sempre superior. A geometria, a câmera e o tipo de LED diferem entre estudos; por isso, dados externos de RGB/HSV não devem ser combinados automaticamente com os nossos como se viessem do mesmo instrumento.

## 6. Avaliação microbiológica: opcional ou necessária?

Para um estudo limitado à **estabilidade físico-química e colorimétrica de um reagente de laboratório**, a avaliação microbiológica pode ser uma segunda etapa, desde que o artigo declare que não avaliou segurança nem validade microbiológica. A avaliação ganha importância se o trabalho pretender afirmar prazo de validade geral do líquido, armazená-lo por semanas em condições não assépticas ou aplicá-lo em alimentos/embalagens.

Como alternativa de baixo custo, discutir com o laboratório de microbiologia uma triagem nos dias 0 e 28, em amostras das duas formulações e condições. O plano pode usar amostra retirada assepticamente do frasco correspondente antes das análises físico-químicas, se o responsável pelo método considerar adequado; caso o SOP exija unidades separadas, acrescentar essas unidades à contagem. Não presumir segurança microbiológica a partir da cor ou do pH.

## 7. Estatística e critério de vida útil

- Tratar `batch_id` como lote experimental independente e leituras repetidas do mesmo frasco como repetições técnicas.
- Estimar efeitos de formulação, armazenamento, tempo e suas interações; usar lote como bloco/efeito aleatório se os dados e o modelo permitirem.
- Inspecionar dados brutos, resíduos, incerteza analítica e valores influentes.
- Testar `C_t = C_0 e^{-kt}` apenas como modelo cinético inicial; a meia-vida `ln(2)/k` é parâmetro químico, não prazo de validade funcional.
- Pré-definir o que significa “continuar funcionando”: retenção de antocianinas, erro aceitável na estimativa de pH a partir da cor e/ou separação de categorias de pH. Não adotar 80% de retenção como padrão universal sem justificar o critério.
- Para aprendizagem de máquina, começar com modelos simples e validar deixando lotes inteiros fora do treino. Não dividir aleatoriamente linhas do mesmo lote entre treino e teste.

## 8. Reutilização de dados publicados

Há dois tipos de informação que devem permanecer separados:

1. **Dados de literatura:** valores de tabelas, suplementos, repositórios ou figuras de artigos. Registrar DOI, citação, página/tabela/figura, origem do dado (`raw`, `supplement`, `table`, `digitized_figure`, `abstract`), unidade, método e incerteza. Valores digitalizados de gráficos são aproximações e devem ser identificados como tal.
2. **Dados próprios:** medições deste laboratório, imutáveis no diretório de dados brutos. O código não combina registros bibliográficos e experimentais automaticamente.

O artigo da UFN de 2026 relata 189 observações de pH/cor, mas a página consultada não apresentou um CSV bruto separado. A licença CC BY 4.0 permite reutilização adequada do conteúdo publicado com atribuição. Solicitar aos autores, se possível, a planilha linha a linha e metadados da montagem. Para o artigo de estabilidade publicado em setembro de 2026, a declaração de disponibilidade informa que os dados podem ser solicitados ao autor correspondente.

Não treinar um modelo universal juntando diretamente medições de smartphones, LEDs, protocolos de extração e escalas de cor diferentes. Use os estudos para selecionar fatores, hipóteses e referências; use os dados brutos externos como banco separado, e valide no seu próprio aparelho e nos lotes próprios.

## 9. Referências principais

- Filho, M. B. et al. (2026). *Análise experimental da relação entre pH e cor do extrato de repolho roxo sob LED RGB utilizando aprendizagem de máquina*. Disciplinarum Scientia | Naturais e Tecnológicas, 27(2), 27–44. https://doi.org/10.37779/nt.v27i2.5632
- Huțuțui, L.-M.; Amariei, S.; Gâtlan, A.-M. (2026). *Evaluation of the Biochemical, Colorimetric, and Microbiological Stability of Red Cabbage Anthocyanin Extracts for Application as Natural Indicators*. Molecules, 31(18), 3339. https://doi.org/10.3390/molecules31183339
- Lee, J.; Durst, R. W.; Wrolstad, R. E. (2005). *Determination of Total Monomeric Anthocyanin Pigment Content ... by the pH Differential Method: Collaborative Study*. Journal of AOAC International, 88(5), 1269–1278.

---

## Extensão computacional: painel visual, simulação e futura aprendizagem de máquina

### Painel visual experimental

Após `python anthocyanin_lab.py analyze --dir .`, abra `data/processed/results_dashboard.html` no navegador. O arquivo agrega as tabelas resumo e incorpora os gráficos existentes como imagens. As fontes continuam sendo os CSVs experimentais em `data/raw/`. O relatório não cria valores ausentes e as saídas cinéticas/colorimétricas são exploratórias.

### Simulador de cenários

Use `python anthocyanin_lab.py simulate --dir . --demo` apenas para testar o software com parâmetros artificiais. Para um cenário customizado, edite `data/config/simulation_parameters.json`, informe a meia-vida de referência e a energia de ativação adequadas e execute `python anthocyanin_lab.py simulate --dir .`.

O modelo assume degradação de primeira ordem, com taxa de referência derivada da meia-vida e ajuste de temperatura pela equação de Arrhenius. Os multiplicadores de pH, luz, oxigênio e embalagem são entradas hipotéticas. Não são automaticamente inferidos de artigos nem dos dados experimentais. Por padrão, a configuração inicial deixa os parâmetros cinéticos sem preencher para evitar que números arbitrários pareçam científicos.

Arquivos de simulação são salvos em `data/simulation/`, separados dos resultados reais em `data/processed/`. A curva simulada serve para formular e priorizar hipóteses; não serve, sem calibração e validação, para declarar estabilidade, segurança microbiológica ou validade.

### Uso de ML (exploratório)

`data/templates/ml_observation_template.csv` define campos possíveis. Preencha `data/raw/ml_observations.csv` apenas com medições reais e marque `data_origin` como `EXPERIMENTAL`. O comando `python anthocyanin_lab.py ml --dir . --target retention_pct` exclui automaticamente origens `SIMULATION_ONLY` e `LITERATURE`.

O modelo inicial compara Random Forest com um baseline de média e usa validação cruzada agrupada por `independent_batch` (ou `batch_id` quando o primeiro estiver vazio). Essa separação tenta evitar que tempos diferentes do mesmo lote apareçam simultaneamente em treino e teste. O limite de 3 grupos é apenas mínimo técnico e não torna o conjunto suficiente para conclusões científicas. São recomendados mais lotes independentes e validação prospectiva. Não use o modelo para definir prazo de validade, segurança ou recomendar a melhor formulação sem confirmação experimental. Não misture resultados simulados com observações de laboratório como se fossem a mesma origem.

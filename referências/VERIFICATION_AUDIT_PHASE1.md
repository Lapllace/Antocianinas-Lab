# Antocianinas Lab — Auditoria de fontes e dados (Fase 1)

**Data da auditoria:** 17 de outubro de 2026  
**Escopo:** Huțuțui et al. (2026), Muhamad et al. (2022) e Lin et al. (2023).  
**Natureza:** auditoria bibliográfica e de rastreabilidade baseada nos registros editoriais, texto integral/indexado de fontes primárias e metadados consultáveis.  
**Limite de execução:** este arquivo foi criado fora do clone local do projeto; nenhum CSV, manifesto ou código do repositório foi modificado. Copie-o para `data/literature/VERIFICATION_AUDIT_PHASE1.md` após revisão.

## 1. Resumo executivo

| Conjunto | O que foi confirmado | Situação da auditoria | Principal pendência |
|---|---|---|---|
| Huțuțui et al. (2026) | Os valores textuais de TAC para seis condições P2, P4, P8, P9, P13 e P14 nos dias 1, 5 e 10; unidades e condições correspondentes. | **Confirmação primária parcial** | O artigo menciona medições em seis dias (1, 2, 3, 4, 5 e 10), enquanto as séries históricas atuais contêm somente três pontos. Resolver divergências metodológicas e a checagem de P2 antes de considerar o conjunto cinético definitivamente validado. |
| Muhamad et al. (2022) | As 21 médias de TAC (três embalagens × sete meses), desvios-padrão, unidades e protocolo da bebida. | **Valores da tabela confirmados; independência do conjunto limitada** | Existe uma publicação de 2023 dos mesmos autores com a mesma tabela numérica, sem evidência de que seja experimento independente. Não contar como segunda replicação. O DOI impresso no PDF difere do DOI exibido atualmente na página editorial. |
| Lin et al. (2023) | A referência publicada, a concentração dos polifenóis testados (0,4%), e o par publicado para ácido gálico `k = 0,0466 d⁻¹`, `t½ = 14,87 d`. | **Confirmação parcial ao nível do resumo editorial** | Acesso ao texto completo/tabelas não foi possível nesta consulta. Ainda faltam localização exata do dado no artigo, série concentração-tempo, condições detalhadas e equação/ajuste cinético. |

**Não houve alteração do status de nenhum registro do repositório.** Este relatório distingue confirmação do que está explicitamente publicado, confirmação parcial e itens que permanecem pendentes. Recomenda-se manter os status de importação existentes até a auditoria ser aplicada por uma alteração rastreável e revisada.

---

## 2. Huțuțui, Amariei & Gâtlan (2026)

### 2.1 Referência e fonte primária

Huțuțui, L.-M.; Amariei, S.; Gâtlan, A.-M. “Evaluation of the Biochemical, Colorimetric, and Microbiological Stability of Red Cabbage Anthocyanin Extracts for Application as Natural Indicators.” *Molecules* **31**(18), 3339 (2026). DOI: [10.3390/molecules31183339](https://doi.org/10.3390/molecules31183339). Publicado em 20 de setembro de 2026.

Fonte primária: [página do artigo na MDPI](https://www.mdpi.com/1420-3049/31/18/3339). A extração completa direta da página apresentou limitação de acesso durante esta consulta, mas o resultado textual indexado pelo próprio domínio editorial expõe os trechos citados abaixo. Os valores enumerados em 2.3 são explicitamente transcritos na narrativa do artigo, não estimados visualmente de figura nesta auditoria.

### 2.2 Condições e método relevante para a comparabilidade

O estudo compara extratos de repolho roxo em água e em etanol a 50% (v/v). A preparação descrita inclui razão sólido:solvente 1:10 (m/v), acidificação a pH 3 com HCl 0,1 N, maceração por 24 h a 25 °C no escuro, centrifugação e filtração. Foram comparadas combinações de solvente, luz/escuro, condição aeróbia/anaeróbia e temperatura de 4 ± 0,5 °C ou 25 ± 0,5 °C.

A **Tabela 5** associa as codificações das amostras às condições de armazenamento. Condições relevantes:

| Série | Solvente | Temperatura | Luz | Oxigênio |
|---|---|---:|---|---|
| P2 | Etanol 50% | 4 ± 0,5 °C | Escuro | Aeróbia |
| P4 | Etanol 50% | 4 ± 0,5 °C | Escuro | Anaeróbia |
| P8 | Etanol 50% | 25 ± 0,5 °C | Escuro | Anaeróbia |
| P9 | Água | 4 ± 0,5 °C | Luz | Aeróbia |
| P13 | Água | 25 ± 0,5 °C | Luz | Aeróbia |
| P14 | Água | 25 ± 0,5 °C | Escuro | Aeróbia |

A TAC é expressa no artigo como **mg de equivalentes de cianidina-3-glicosídeo (CGE) por 100 g de massa fresca (FW)**. O artigo informa resultados como média ± desvio-padrão, `n = 3`. Porém, a seção de métodos descreve **um lote de extração por solvente** distribuído em frascos de armazenamento. Logo, `n = 3` não deve ser interpretado automaticamente como três extrações biologicamente independentes: as réplicas reportadas não demonstram, por si só, a reprodutibilidade entre lotes independentes.

### 2.3 Valores textuais encontrados na publicação

Valores de TAC explicitamente reportados na narrativa da publicação:

| Série | Dia 1 | Dia 5 | Dia 10 | `kTAC` publicado (d⁻¹) | `t½` publicado (d) |
|---|---:|---:|---:|---:|---:|
| P2 | 115,470 | 107,321 | 104,161 | 0,0112 | 60,5 |
| P4 | 116,859 | 110,353 | 107,653 | 0,009 | 76,0 |
| P8 | 116,462 | 97,179 | 91,940 | 0,026 | 26,4 |
| P9 | 72,678 | 59,587 | 49,249 | 0,043 | 16,0 |
| P13 | 74,273 | 44,663 | 38,482 | 0,073 | 9,5 |
| P14 | 74,798 | 58,212 | 49,402 | 0,046 | 15,0 |

**Unidade para todas as três colunas de TAC:** mg CGE/100 g FW. Os valores de `kTAC` e `t½` são transcritos com o arredondamento apresentado no texto do artigo. As fontes editoriais descrevem os valores de P2 e P4 na análise por condição de oxigenação; P4/P9 em comparação de temperatura; P8/P13/P14 na análise a 25 °C/efeito da temperatura.

**Localização da evidência na fonte:** Tabela 5 para a definição de P2/P4/P8/P9/P13/P14; subseções de resultados sobre efeito do oxigênio e efeito da temperatura, incluindo a seção **2.4.4, “The Effect of Temperature on Anthocyanin Content and Antioxidant Activity (DPPH)”**, e **Figura 9**. Os valores dos seis pontos selecionados estão escritos na narrativa junto aos respectivos resultados; não são valores calculados por este relatório.

### 2.4 Discrepâncias e limitações identificadas

1. **Série temporal possivelmente incompleta.** A seção de métodos declara que as análises de TAC foram realizadas nos dias 1, 2, 3, 4, 5 e 10. O histórico atual do projeto registra apenas os dias 1, 5 e 10 para essas seis séries. Antes de usar essas séries como representação completa dos dados do artigo, precisamos verificar se os valores dos dias 2, 3 e 4 são recuperáveis das tabelas, figuras ou dados suplementares. Não estimá-los a olho nem inventá-los.
2. **Inconsistência de comprimento de onda.** A descrição do método lista medições a 510 nm e 700 nm, mas a equação da diferença de absorbância aparece como `(A520 − A700)pH 1.0 − (A520 − A700)pH 4.5`. O comprimento de onda efetivamente usado precisa ser confirmado no PDF/editor e registrado no método do projeto; não corrigir silenciosamente para 510 ou 520 nm.
3. **Checagem aritmética de P2.** Se for aplicada a relação convencional de primeira ordem `t½ = ln(2)/k`, `k = 0,0112 d⁻¹` implica `t½ ≈ 61,9 d`, e não 60,5 d. Os números impressos no artigo não coincidem à precisão apresentada. Deve-se consultar tabela, cálculo original ou autores; manter ambos os valores reportados, com a discrepância documentada, até resolução.
4. **Possível lapso editorial na descrição da Figura 9.** A narrativa chama P4/P9 de “at room temperature (Figure 9a)” em um trecho, mas a legenda da Figura 9 define o painel (a) como TAC a 4 °C. Não usar esse trecho isoladamente para atribuir temperatura; a Tabela 5 e a legenda devem ter prioridade na interpretação, com a contradição anotada.
5. **Dependência da formulação.** Estes dados são de extratos acidificados a pH 3, com solvente de extração e condições específicas. Eles não são, sem validação, curvas universais de estabilidade para toda formulação líquida de repolho roxo.
6. **Unidade incompatível com a bebida de Muhamad.** `mg CGE/100 g FW` não é a mesma unidade que `mg C3G/L` de uma bebida pronta. Não juntar diretamente concentrações dos dois estudos em uma única curva. Constantes cinéticas também não devem ser agrupadas sem considerar diferença de matriz, método, tratamento e definição temporal.

### 2.5 Situação recomendada

- **Valores dos dias 1, 5 e 10:** confirmados na narrativa do artigo primário para as seis séries citadas.
- **Metadados das condições das seis séries:** confirmados pela Tabela 5.
- **Série cinética completa:** parcialmente verificada, porque o artigo relata mais dias de análise do que constam no conjunto histórico atual.
- **Constante/meia-vida de P2:** manter como reportadas e sinalizar discrepância interna; não substituir a meia-vida publicada pela calculada sem uma decisão documentada.
- **Ação posterior necessária:** localizar a fonte dos demais tempos, registrar localizador específico para cada valor e resolver os dois pontos metodológicos/editoriais.

---

## 3. Muhamad, Hussin & Arifin (2022)

### 3.1 Referência e fontes

Muhamad, N. F. H.; Hussin, F.; Arifin, N. “Effect of Packaging Materials and Storage on Physicochemical Properties and Anthocyanin Contents of Red Cabbage-Roselle Blended Drink.” *Malaysian Journal of Science, Health & Technology* **8**(1), 1–8 (2022). Página editorial: [mjosht.usim.edu.my/article/view/239](https://mjosht.usim.edu.my/index.php/mjosht/article/view/239). DOI atualmente apresentado na página editorial: [10.33102/mjosht.v8i1.239](https://doi.org/10.33102/mjosht.v8i1.239).

Foi possível conferir o texto integral disponibilizado como conteúdo do autor no [ResearchGate](https://www.researchgate.net/publication/358109008_Effect_of_Packaging_Materials_and_Storage_on_Physicochemical_Properties_and_Anthocyanin_Contents_of_Red_Cabbage-Roselle_Blended_Drink), além da página oficial do periódico.

### 3.2 Método, matriz e condições

O objeto é uma **bebida mista de repolho roxo e roselle (Hibiscus sabdariffa)**, não um extrato líquido de repolho roxo puro. A formulação publica 70% de uma mistura de extratos de repolho roxo:roselle na proporção 40:10, além de água (23,40%), mel (1,00%), sacarose (5,00%), goma arábica (0,50%), ácido cítrico (0,10%) e benzoato de sódio (0,03%). A bebida foi pasteurizada a 70,01 °C por 284,07 s, envasada a quente acima de 65 °C em embalagens de 250 mL e armazenada no escuro a 29 ± 2 °C. Foram comparadas garrafa de vidro, lata e garrafa de polipropileno (PP), com avaliações mensais até seis meses.

A TAC foi determinada pelo método diferencial de pH, com tampões pH 1,0 e 4,5; absorbâncias a 520 e 700 nm; resultados expressos como equivalentes de cianidina-3-glicosídeo. A tabela apresenta média ± desvio-padrão; o estudo declara análise em triplicata.

### 3.3 Tabela 8: valores confirmados

Valores de TAC da bebida, em **mg equivalentes de cianidina-3-glicosídeo/L (mg cyd-3-glu/L)**, apresentados como média ± SD:

| Mês | Vidro | Lata | PP |
|---:|---:|---:|---:|
| 0 | 263,40 ± 1,67 | 262,66 ± 0,87 | 262,17 ± 1,04 |
| 1 | 132,10 ± 3,60 | 113,20 ± 3,96 | 96,88 ± 0,71 |
| 2 | 87,75 ± 16,60 | 94,54 ± 23,17 | 88,21 ± 18,55 |
| 3 | 74,38 ± 2,21 | 71,80 ± 7,35 | 40,42 ± 0,49 |
| 4 | 55,60 ± 0,87 | 49,27 ± 1,93 | 21,09 ± 1,31 |
| 5 | 48,29 ± 0,96 | 39,85 ± 0,85 | 14,38 ± 0,17 |
| 6 | 34,36 ± 1,83 | 30,50 ± 0,17 | 10,44 ± 1,42 |

**Localização:** **Tabela 8**, “Total Anthocyanins Content (mg cyd-3-glu/L) of Red Cabbage-Roselle Blended drinks in Different Packaging Materials”, do artigo de 2022. O texto integral acessível mostra as 21 médias, os desvios-padrão, os meses e as três embalagens. Se o dataset local atualmente retém apenas médias, recomenda-se acrescentar SD, unidade, mês, tipo de embalagem e localizador da tabela por meio de uma alteração de dados revisada; manter os dados brutos originais intocados.

### 3.4 Publicação relacionada de 2023 e risco de dupla contagem

Foi localizada uma publicação posterior, com autores correspondentes e o título “Effect of packaging materials and storage time on anthocyanins stability of red cabbage-roselle mixed drink”, *Food Research* **6** (Supplementary 2), 182–190 (2023), DOI [10.26656/fr.2017.6(S2).030](https://doi.org/10.26656/fr.2017.6(S2).030). Sua **Tabela 2** contém a mesma série de sete meses × três embalagens: as 21 médias e todos os desvios-padrão coincidem com os da Tabela 8 do artigo de 2022.

A coincidência exata de valores, a composição autoral e o desenho experimental coincidente são fortes indícios de sobreposição do conjunto de dados. Esta auditoria não conclui sobre a relação editorial entre os trabalhos além do que a evidência mostra, mas recomenda **não importar as duas tabelas como observações experimentais independentes**. Se ambas as referências forem mantidas na bibliografia, ambas devem apontar para o mesmo grupo de dados subjacente/relacionado, com aviso explícito de sobreposição.

Há também uma discrepância bibliográfica: a página editorial atual de 2022 apresenta DOI `10.33102/mjosht.v8i1.239`, enquanto a cópia integral do artigo exibe no cabeçalho `10.33102/2022239`. Usar a página oficial do periódico como identificador canônico provisório e conservar a discrepância como nota bibliográfica até confirmar o histórico do DOI; não apagar o dado impresso no PDF.

### 3.5 Situação recomendada

- **Tabela numérica de 2022:** confirmada no texto integral da publicação primária.
- **Unidades, desvio-padrão e meses:** confirmados.
- **Independência em relação à publicação de 2023:** não estabelecida; tratar os dados como sobrepostos, não como replicação independente.
- **Aplicação no Antocianinas Lab:** referência útil para a influência de embalagem em bebida formulada; não usar como curva diretamente equivalente ao extrato líquido puro.

---

## 4. Lin et al. (2023)

### 4.1 Referência e fonte

Lin, M.; Sun, C.; Gao, Q.; Zhang, Z.; Liang, Y.; Wang, S. “Effect of five polyphenols on the stability of purple cabbage anthocyanins in simulated beverage systems containing L-ascorbic acid.” *Food Packaging and Shelf Life* **37** (June 2023), 101065. DOI: [10.1016/j.fpsl.2023.101065](https://doi.org/10.1016/j.fpsl.2023.101065). Página editorial: [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S221428942300042X). Também localizei um preprint no [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4351866).

### 4.2 Informações confirmadas no resumo editorial

O estudo investiga sistemas de bebida simulada contendo ácido L-ascórbico e cinco compostos usados como copigmentos a **0,4%**: catequina, epigalocatequina galato (EGCG), vanilina, ácido gálico e ácido rosmarínico. O resumo editorial informa que, na condição com ácido gálico, a constante cinética mínima reportada foi `k = 0,0466 d⁻¹` e a meia-vida foi `t½ = 14,87 d`; o resumo também reporta melhora na absorbância e redução da variação total de cor.

**Checagem aritmética:** `ln(2) / 0,0466 d⁻¹ ≈ 14,87 d`. Portanto, a constante e a meia-vida publicadas são mutuamente consistentes ao arredondamento apresentado. Essa verificação matemática não comprova, por si só, como os autores ajustaram o modelo aos dados.

### 4.3 Limite de verificação e uso recomendado

A página editorial e o resumo estavam acessíveis; o download direto do texto completo/tabelas falhou nesta consulta. Portanto, ainda não foram confirmados nesta auditoria: número/localização exatos da tabela que contém o `k`; série completa concentração-tempo; composição e concentração inicial exatas do sistema simulado; pH, regime térmico e todos os detalhes do ajuste; equação cinética e resíduos/ajuste usados para obter `k`.

O valor `k = 0,0466 d⁻¹` pode ser mantido no inventário bibliográfico **como parâmetro explicitamente reportado pelo resumo do artigo**, com a origem registrada como “resumo editorial”; não deve ser tratado como série bruta nem usado para reconstruir concentrações sem os dados e condições completos. Como o estudo envolve bebida simulada com ácido ascórbico e copigmento, não transferir sua constante diretamente para o extrato puro. O texto completo é necessário antes de preencher parâmetros adicionais ou efetuar comparação mais rigorosa entre modelos cinéticos.

### 4.4 Situação recomendada

- **Referência, DOI e parâmetro `k`/`t½` do resumo:** confirmados parcialmente na fonte editorial.
- **Consistência matemática do par `k`/`t½`:** confirmada por recálculo simples.
- **Dados brutos, tabela, método cinético e condições completas:** pendentes de texto integral.
- **Status no inventário:** parcial; não inventar séries concentração-tempo nem atribuir precisão maior que a apresentada.

---

## 5. Regras para não degradar a rastreabilidade do projeto

1. Preservar as linhas brutas existentes; correções devem ser novos commits/alterações documentadas, nunca sobrescrita silenciosa.
2. Para cada valor, guardar DOI/URL, publicação/versão, tabela ou figura, página/seção, unidade, condição experimental e classificação **publicado diretamente**, **calculado a partir do publicado** ou **estimado/digitalizado**.
3. Manter separados os dados de cada matriz. Não misturar `mg CGE/100 g FW` com `mg C3G/L` sem transformação fundamentada e metadados de densidade/massa/volume apropriados.
4. Não tratar desvios-padrão como réplica independente de extração quando o artigo só informa um lote por solvente.
5. Não contar a publicação de 2022 e a de 2023 de Muhamad et al. como duas replicações independentes enquanto a sobreposição de dados não for resolvida.
6. Manter a série de Huțuțui como temporalmente incompleta até localizar os dias 2, 3 e 4 ou justificar documentalmente por que se utilizaram somente dias 1, 5 e 10.
7. Para Lin et al., usar a constante publicada apenas como parâmetro de literatura identificado; não gerar pontos artificiais de concentração ao longo do tempo.
8. Nenhum limiar universal de “fim de vida útil” deve ser derivado destas três fontes sem definição funcional, validação experimental e análise de comparabilidade.

---

## 6. Próximas ações de auditoria

1. Obter a versão integral e, se houver, dados suplementares de Huțuțui et al.; recuperar os dias 2, 3 e 4, verificar o comprimento de onda correto e resolver a diferença P2 entre `k` e `t½`.
2. Marcar internamente as publicações de Muhamad 2022 e 2023 como **fontes com dados sobrepostos**, manter ambas na bibliografia e garantir que as séries numéricas sejam contadas uma só vez na modelagem.
3. Obter o texto integral de Lin et al.; registrar a tabela exata do parâmetro cinético e verificar a equação e condições experimentais antes de incorporá-lo a comparações quantitativas.
4. Após revisão no repositório, atualizar os metadados/manifestos existentes com as localizações de evidência e estados de verificação granulares; não alterar código de ajuste cinético nesta rodada.

## 7. Fontes consultadas

1. Huțuțui, L.-M. et al. (2026). *Molecules* 31(18), 3339. [DOI](https://doi.org/10.3390/molecules31183339) · [Texto do artigo](https://www.mdpi.com/1420-3049/31/18/3339).
2. Muhamad, N. F. H. et al. (2022). *Malaysian Journal of Science, Health & Technology* 8(1), 1–8. [Página do periódico/DOI atual](https://mjosht.usim.edu.my/index.php/mjosht/article/view/239) · [Cópia de texto integral do autor](https://www.researchgate.net/publication/358109008_Effect_of_Packaging_Materials_and_Storage_on_Physicochemical_Properties_and_Anthocyanin_Contents_of_Red_Cabbage-Roselle_Blended_Drink).
3. Muhamad, N. F. H. et al. (2023). *Food Research* 6(Suppl. 2), 182–190. [DOI](https://doi.org/10.26656/fr.2017.6(S2).030) · [PDF](https://myfoodresearch.com/uploads/8/4/8/5/84855864/_23__fr-nfts-030_muhamad.pdf).
4. Lin, M. et al. (2023). *Food Packaging and Shelf Life* 37, 101065. [DOI](https://doi.org/10.1016/j.fpsl.2023.101065) · [Página do artigo](https://www.sciencedirect.com/science/article/abs/pii/S221428942300042X) · [Preprint SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4351866).

**Fim da auditoria parcial — Fase 1.** Esta auditoria conclui a conferência disponível para os três conjuntos prioritários, mas não declara a revisão bibliográfica global como concluída. Os itens identificados como pendentes exigem nova obtenção de fonte primária/dados suplementares e revisão no repositório.

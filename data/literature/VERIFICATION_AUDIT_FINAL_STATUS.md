# Auditoria Final de Rastreabilidade Bibliográfica — Antocianinas Lab

**Data da geração:** 20 de outubro de 2026  
**Escopo:** todos os registros de literatura em `data/literature/`  
**Natureza:** documentação de rastreabilidade. Nenhum CSV de literatura, valor científico ou função de produção foi alterado.

## 1. Resumo executivo

| Conjunto | Registros harmônicos | Status de verificação | Localização exata por valor |
|---|---:|---|---|
| STUDY_A — Huțuțui et al. (2026) | 18 | VERIFICATION_PENDING | Não confirmada (PDF HTTP 403) |
| STUDY_B — Muhamad et al. (2022) | 21 | VERIFICATION_PENDING (valores confirmados por texto integral em 20/10/2026; promoção pendente de revisão explícita) | Confirmada — Tabela 8, p. 6 impressa (ver §7.2) |
| STUDY_C — Lin et al. (2023) | 8 (evidências) | VERIFICATION_PENDING | Não confirmada (texto integral 403) |
| STUDY_D — Pan et al. (2020) | 0 (não harmônico) | Não aplicado | Resumo editorial confirmado, não harmônico |
| STUDY_E — Patras (2019) | 3 (evidências) | VERIFICATION_PENDING | Qualitativo, texto integral 403 |
| STUDY_F — Muhamad et al. (2023) | 0 | Bibliográfico apenas | Sobreposição com STUDY_B documentada |
| **Total** | **50** | **50 pendentes** (21 com valores já confirmados integralmente) | **21 de 50 confirmadas por texto integral (STUDY_B)** |

**Nenhuma observação foi promovida para `VERIFIED`.** Conforme exigido pelo protocolo do projeto, uma referência só pode ser marcada `VERIFIED` quando houver localização exata (tabela/página/linha) no texto integral, o que não está acessível para nenhuma das fontes principais.

## 2. Distinção de níveis de confirmação

Conforme o AGENTS.md e o protocolo v2, distinguimos três níveis:

| Nível | Significado | Aplicável neste projeto |
|---|---|---|
| **Confirmação bibliográfica** | DOI, autores, título, ano, periódico, URL verificados no registro editorial | Sim — todos os 6 estudos |
| **Confirmação por resumo editorial** | Valores numéricos extraídos do resumo/abstract ou narrativa indexada | Parcial — Pan (2020) resumo completo; Huțuțui, Muhamad 2022, Lin 2023, Patras 2019 apenas resumo parcial |
| **Confirmação por texto integral** | Localização exata (tabela, figura, página, seção, equação) no artigo completo | **Não** — HTTP 403 ou falha de fetch para todas as fontes exceto Pan (2020), cujos dados ainda não foram harmônicos no projeto |
## 3. Detalhe por estudo

### STUDY_A — Huțuțui, Amariei & Gâtlan (2026)

- **Referência completa:** *Molecules* 31(18), 3339 (2026). DOI: 10.3390/molecules31183339. Publicado 20/09/2026.
- **URL:** https://doi.org/10.3390/molecules31183339 · https://www.mdpi.com/1420-3049/31/18/3339
- **Valor editorial confirmado:** TAC para 6 condições (P2, P4, P8, P9, P13, P14) nos dias 1, 5 e 10; unidade mg CGE/100 g FW; condições da Tabela 5 (solvente água/etanol 50%, pH 3,0, 4 °C ou 25 °C, escuro/luz, aeróbico/anaeróbico).
- **Localização exata:** NÃO confirmada. PDF bloqueado (HTTP 403). Não foi possível localizar tabela/linha específica para cada um dos 18 valores.
- **Classificação dos valores:** `reported` (valores publicados informados pelo usuário).
- **Limitações de comparabilidade:** matriz extrato aquoso/etanólico, não necessariamente comparável ao extrato deste projeto; um lote por solvente; pontos longitudinais do mesmo lote não são lotes independentes; DP e réplicas não informados.
- **Status:** `VERIFICATION_PENDING`.

### STUDY_B — Muhamad, Hussin & Arifin (2022)

- **Referência completa:** *Malaysian Journal of Science, Health & Technology* 8(1), 1–8 (2022). DOI: 10.33102/mjosht.v8i1.239.
- **URL:** https://mjosht.usim.edu.my/index.php/mjosht/article/view/239
- **Valor editorial confirmado:** 21 médias de TAC (3 embalagens × 7 meses), Tabela 8, armazenamento a 29 ± 2 °C no escuro, unidade mg equivalentes de cianidina-3-glicosídeo/L.
- **Localização exata:** CONFIRMADA em 20/10/2026 — Tabela 8, página impressa 6 (PDF obtido via espelho Semantic Scholar; ver §7.2 e `STUDY_B_COMPARISON_REPORT.md`). Os 21 valores médios coincidem integralmente com o CSV; a fonte também publica desvios-padrão ainda não registrados no projeto.
- **Classificação dos valores:** `reported`.
- **Limitações de comparabilidade:** bebida mista repolho roxo + rosela, pasteurizada, envasada a quente — não representa extrato puro de repolho roxo. A fonte informa desvios-padrão (registrados como pendência; CSVs não alterados). O DOI impresso no PDF (10.33102/2022239) difere do DOI registrado no projeto (10.33102/mjosht.v8i1.239); ambos apontam para o mesmo artigo — divergência documentada, sem alteração de dados.
- **Sobreposição com STUDY_F (Muhamad 2023):** tabela numérica coincidente; não tratar como replicação independente.
- **Status:** `VERIFICATION_PENDING` (valores confirmados por texto integral; promoção para `VERIFIED` depende de revisão explícita).

### STUDY_C — Lin et al. (2023)

- **Referência completa:** *Food Packaging and Shelf Life* 37, 101065 (2023). DOI: 10.1016/j.fpsl.2023.101065.
- **URL:** https://doi.org/10.1016/j.fpsl.2023.101065
- **Valor editorial confirmado:** ácido gálico 0,4%, k = 0,0466 dia⁻¹, t½ = 14,87 dias (par publicado no resumo editorial).
- **Localização exata:** NÃO confirmada. Texto integral bloqueado (HTTP 403).
- **Classificação dos valores:** `reported`.
- **Limitações de comparabilidade:** bebida simulada com ácido L-ascórbico; não transferir ao extrato aquoso sem calibração; não é série temporal para digitalizar.
- **Status:** `VERIFICATION_PENDING`.

### STUDY_D — Pan et al. (2020/2021)

- **Referência completa:** *Stability and Degradation Kinetics of Anthocyanins from Red Cabbage*. DOI: 10.13386/j.issn1002-0306.2020050071.
- **URL:** https://www.spgykj.com/en/article/doi/10.13386/j.issn1002-0306.2020050071
- **Valor confirmado (resumo editorial + PDF acessível):** retenção 92,92% ± 0,69% (pH 2,0, 5 h); retenção 70,50% ± 0,52% (40 °C, escuro, 5 h); t½ 67,28 h (50 °C, pH 2,0); Ea máxima 39,16 kJ/mol; cinética primeira ordem.
- **Localização exata no texto integral:** não localizada no escopo desta auditoria (PDF acessível, mas localização por tabela/página não registrada).
- **Status no projeto:** 0 registros harmônicos em `literature_measurements.csv`. Não está incluído como STUDY_D harmônico.
- **Classificação:** `reported` (resumo). Não promovido para `VERIFIED` porque não há localização exata registrada no projeto e os dados não foram harmônicos.
- **Status:** não aplicado (não harmônico).

### STUDY_E — Patras (2019)

- **Referência completa:** *Food Chemistry*. DOI: 10.1016/j.foodchem.2018.09.100.
- **Valor:** qualitativo — avaliação de cor e antocianinas monoméricas, 6,31, 4 °C, escuro, aeróbico, 20 semanas.
- **Localização exata:** NÃO confirmada (HTTP 403).
- **Classificação:** evidência qualitativa, não quantitativa para cinética.
- **Status:** `VERIFICATION_PENDING`.

### STUDY_F — Muhamad, Hussin & Arifin (2023)

- **Referência completa:** *Food Research* 6(Suppl. 2), 182–190. DOI: 10.26656/fr.2017.6(S2).030.
- **URL:** https://myfoodresearch.com/uploads/8/4/8/5/84855864/_23__fr-nfts-030_muhamad.pdf
- **Status:** bibliográfico apenas; sobreposição com STUDY_B documentada (mesma tabela numérica). Não tratar como segunda replicação independente.
- **Status:** bibliográfico apenas, não há registros harmônicos.

### Giusti & Wrolstad (2001) — base metodológica do TAC

- **Referência:** método diferencial de pH para antocianinas monoméricas. DOI: 10.1002/0471142913.faf0102s00.
- **Uso no projeto:** justificativa para as equações implementadas em `anthocyanin_lab.py` (`calculate_tac`):
  - `A = (A520 − A700)pH1,0 − (A520 − A700)pH4,5`
  - `C = A × MW × DF × 1000 / (ε × l)`
- **Constantes usadas no código:** MW_C3G = 449,2 g/mol; ε_C3G = 26900 L mol⁻¹ cm⁻¹; saída em mg/L.
- **Status:** referência metodológica citada no `protocol.md`; não há registro próprio de literatura para este DOI nos CSVs do projeto (não é um dado de medição, é um método).


## 4. Regras de rastreabilidade respeitadas (sem alterações)

1. **Nenhum valor de literatura foi alterado.** Todos os 50 registros permanecem com `verification_status = VERIFICATION_PENDING`.
2. **Nenhum `reported_or_calculated` foi mudado.** Todos os valores de medição permanecem como `reported`.
3. **Nenhuma linha `SIMULATION_ONLY` ou `LITERATURE` foi tratada como `EXPERIMENTAL`.**
4. **Não houve conversão implícita de unidades** (horas vs dias, mg CGE/100 g FW vs mg C3G/L).
5. **Não foram criados pontos artificiais de concentração-tempo** a partir de resumos publicados.
6. **ESTUDO_B e ESTUDO_F não foram contados como replicações independentes.**

## 5. Arquivos consultados (não modificados)

- `data/literature/literature_studies.csv`
- `data/literature/literature_measurements.csv`
- `data/literature/literature_verification_status.csv`
- `data/literature/VERIFICATION_AUDIT_PHASE1.md`
- `data/literature/VERIFICATION_AUDIT_PHASE3.md`
- `data/literature/VERIFICATION_AUDIT_PHASE3_REVISED.md`
- `tests/fixtures/validation/pan_2021.json`
- `tests/fixtures/validation/lin_2023_gallic_acid.json`
- `tests/fixtures/validation/hututui_2026_audit.csv`
- `tests/fixtures/validation/muhamad_2022_audit.csv`
- `tests/fixtures/validation/falcioni_2022_method.md`
- `AGENTS.md`, `protocol.md`, `README.md`

## 6. Conclusão

A rastreabilidade bibliográfica está **documentada, mas não concluída quanto à confirmação por texto integral**. Todos os 50 registros harmônicos de literatura permanecem `VERIFICATION_PENDING` porque o acesso ao texto integral está bloqueado (HTTP 403 / falha de fetch) e não há localização exata por valor (tabela/página/linha) registrada no projeto. Isso é intencional e está em conformidade com o AGENTS.md: não promover status por inferência.

**Próximo passo recomendado:** obter acesso alternativo aos PDFs (biblioteca institucional, contato com autores, pré-print) para completar a localização exata por valor e, somente então, avaliar a promoção para `VERIFIED` ou `REJECTED` por alteração rastreável e revisada.

**Atualização (20/10/2026):** o texto integral de STUDY_B foi recuperado por espelho alternativo e os 21 valores foram confirmados contra a Tabela 8 (ver §7.2). O status formal segue `VERIFICATION_PENDING` até revisão explícita.

## 7. Tentativas de acesso nesta fase (auditoria direcionada)

Data das tentativas: 20 de outubro de 2026. Todas as quatro fontes primárias foram consultadas pelas URLs oficiais indicadas no planejamento. Nenhum texto integral foi acessível.

| Fonte | DOI | URL consultada | Resultado | Tipo de evidência recuperada |
|---|---|---|---|---|
| Huțuțui et al. (2026) | 10.3390/molecules31183339 | https://www.mdpi.com/1420-3049/31/18/3339 | HTTP 403 Forbidden | Nenhum (acesso negado) |
| Muhamad et al. (2022) | 10.33102/mjosht.v8i1.239 | https://mjosht.usim.edu.my/index.php/mjosht/article/view/239 | Falha de fetch (servidor) | Nenhum (acesso negado) |
| Lin et al. (2023) | 10.1016/j.fpsl.2023.101065 | https://www.sciencedirect.com/science/article/abs/pii/S221428942300042X | HTTP 403 Forbidden | Nenhum (acesso negado) |
| Pan et al. (2020/2021) | 10.13386/j.issn1002-0306.2020050071 | https://www.spgykj.com/en/article/doi/10.13386/j.issn1002-0306.2020050071 | Timeout após 30s | Nenhum (acesso negado) |

### 7.1 Tentativa adicional — fonte alternativa para STUDY_B (auditoria focal)

Data da tentativa: 20 de outubro de 2026. Foi tentada a versão integral via ResearchGate, além de nova tentativa na página oficial do MJOSHT.

| Fonte | URL consultada | Resultado | Tipo de evidência recuperada |
|---|---|---|---|
| ResearchGate (versão integral) | https://www.researchgate.net/publication/380009067_Effect_of_Packaging_Materials_and_Storage_on_Physicochemical_Properties_and_Anthocyanin_Contents_of_Red_Cabbage-Roselle_Blended_Drink | HTTP 403 Forbidden | Nenhum (acesso negado) |
| MJOSHT (página oficial, nova tentativa) | https://mjosht.usim.edu.my/index.php/mjosht/article/view/239 | Falha de fetch (servidor inacessível) | Nenhum (acesso negado) |

**Conclusão da auditoria focal de STUDY_B (atualizada em 20/10/2026):** a Tabela 8, página impressa 6, foi recuperada via espelho do Semantic Scholar e confirma os 21 valores do projeto (ver §7.2).

### 7.2 Resolução — STUDY_B confirmado por texto integral (20 de outubro de 2026)

| Item | Detalhe |
|---|---|
| URL efetivamente consultada | https://pdfs.semanticscholar.org/9158/d0c936907258920f3e0f28326aa0bff70dd6.pdf |
| Arquivo salvo | `data/literature/sources/muhamad_2022.pdf` |
| SHA-256 do PDF | `4a8e00d602cde92c38ae0734f2330dcb0837aebcc8e9cbc49148461fcc362a23` |
| Tamanho / páginas | 327.405 bytes; 8 páginas (PDF-1.7) |
| Identidade | Título, autores (Muhamad, Hussin, Arifin) e MJoSHT 8(1) 2022 confirmados na página 1 |
| Localização dos dados | Tabela 8, página impressa 6 |
| Método declarado | pH diferencial (Giusti & Wrolstad); equivalentes de cianidina-3-glicosídeo; MW 449,2 g/mol |
| Verificação | Triplice: visual (página 6), visual ampliada (300 DPI) e camada de texto (PyMuPDF) |

Resultado: 21 de 21 médias de STUDY_B coincidem exatamente com a Tabela 8. A fonte publica desvios-padrão para os 21 valores, ausentes no CSV do projeto (pendência documentada; CSVs não alterados). O DOI impresso no PDF (10.33102/2022239) difere do registrado no projeto (10.33102/mjosht.v8i1.239); ambos apontam para o mesmo artigo.

**Conclusão desta fase:** nenhum dos 50 registros harmônicos pôde ser conferido registro por registro no texto integral. O acesso ao corpo integral está bloqueado para todas as fontes principais. Nenhum registro foi promovido para `VERIFIED`. Todos permanecem `VERIFICATION_PENDING`.


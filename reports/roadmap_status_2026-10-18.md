# Status do roadmap de integração científica — Fases 1 a 8

**Data:** 2026-10-18
**Branch:** `feature/scientific-skills-integration` (sem commit nesta etapa; revisão pendente)
**Escopo:** consolidação do trabalho de integração das fases 1–8, distinguindo **concluído**, **parcial**, **pendências** e **bloqueios**. Nenhum dado experimental, bibliográfico ou simulado foi criado, alterado ou migrado, exceto as alterações autorizadas listadas na seção "Alterações desta rodada".

---

## Quadro-resumo

| Fase | Tema | Status |
|---|---|---|
| 1 | Auditoria de fontes da literatura | **Concluído** (com pendências de fonte primária herdadas) |
| 2 | Harmonização da base de literatura | **Concluído** (Etapa 1); lacunas registradas, nenhuma silenciosa |
| 3 | Integração entre literatura e cinética | **Integrada** (visões verified/pending/rejected/combined; ver ressalvas e pendências de fonte) |
| 4 | Decisões laboratoriais pendentes | **Pendência** — nenhuma decisão é do código |
| 5 | Pipeline cor–pH | **Parcial** — utilitário RGB→CIELAB adicionado; não integrado ao pipeline |
| 6 | Simulações moleculares (GROMACS/ORCA/PyMOL) | **Pendência** — nenhum artefato de simulação molecular existe |
| 7 | Validação de ML | **Bloqueio** — `ML_NOT_VALIDATED` preservado por falta de dados |
| 8 | Rastreabilidade de publicação | **Bloqueio** — `source_location` genérico exige texto integral |

---

## Fase 1 — Auditoria de fontes: **concluído**

**Entregue:**
- `data/literature/VERIFICATION_AUDIT_PHASE1.md` e cópia em `referências/` idênticas (SHA-256 conferido); auditoria cobrindo Huțuțui et al. (2026), Muhamad et al. (2022) e Lin et al. (2023).
- Reconciliação com `reports/validation/discrepancy_reconciliation.md` registrada no apêndice "Reconciliação com a auditoria da Fase 1 (2026-10-18)": direção do alinhamento dos fixtures corroborada pela narrativa do artigo; relação `STUDY_B → STUDY_F` implementada com o vocabulário exigido ("possível sobreposição, sujeita a confirmação documental").
- Fixtures `tests/fixtures/validation/hututui_2026_audit.csv` e `muhamad_2022_audit.csv` sem divergências vs CSVs de origem.

**Pendências herdadas (não bloqueiam esta fase):** dias 2–4 da série de Huțuțui ausentes; inconsistência 510/520 nm; discrepância `k`/`t½` de P2; DOI impresso vs editorial de Muhamad 2022; texto integral de Lin et al. Nenhuma foi silenciosamente resolvida — todas estão registradas na reconciliação.

---

## Fase 2 — Harmonização: **concluído** (Etapa 1)

**Entregue (correções de bugs desta rodada):**
- `tools/harmonize_literature.py`:
  - `build_overlapping_relations()` corrigido: a relação agora é `STUDY_B ↔ STUDY_F` (Muhamad 2022 ↔ Muhamad 2023), e não mais a relação errada `STUDY_B ↔ STUDY_C`.
  - `detect_exact_duplicates()` reescrito: compara **todos os campos científicos** excluindo apenas identificadores de execução → 0 duplicatas falsas (antes havia falsos positivos).
  - `build_report()` com quebras de linha reais (`"\n"`); relatório markdown legível.
  - `execution_id` determinístico via `_compute_execution_id()`; `generated_on_utc` removido (`""`) — duas execuções produzem saída idêntica.
  - `STUDY_F` incluído em `COMPARISON_GROUPS` e no loop de estudos; seção 6 do relatório com os dois DOIs.
- `data/literature/literature_studies.csv`: linha `STUDY_F` reconstruída para 16 campos (única alteração em CSV bruto, autorizada e documentada: +1 linha).
- Saídas em `data/literature/processed/harmonized/` regeneradas: **54 observações, 0 duplicatas exatas, relação `STUDY_B → STUDY_F`, markdown correto**.

**Validação:** 6 testes de regressão novos em `tests/test_literature_harmonization.py` (total 16) + `tests/test_analysis.py` com 6 estudos e asserções `STUDY_F`; suíte completa **90 passed, 16 subtests passed**.

**Lacunas registradas (o que ainda falta para *concluir a harmonização científica*, não para a Etapa 1):**
1. `source_location` segue genérico nas 39 medições (ver Fase 8).
2. Nenhuma conversão de unidade foi feita (`normalization_*` vazios por decisão): `mg CGE/100 g FW` (STUDY_A) e `mg C3G/L` (STUDY_B) permanecem em matrizes separadas — correto, mas impede comparações cruzadas quantitativas.
3. Relação `STUDY_B → STUDY_F` aguarda confirmação documental da relação editorial antes de qualquer agregação de séries.
4. A base harmonizada ainda **não é consumida por nenhum módulo de análise** (ver Fase 3).

---

## Fase 3 — Integração literatura ↔ cinética: **integrada** (com ressalvas)

**Entregue nesta rodada (2026-10-18, segunda execução):** `analyze_literature()` agora lê a
**base harmonizada derivada** via `load_harmonized_catalog()` (bijeção linha a linha
`STUDY|L{n}`/`STUDY|E{n}` contra os CSVs brutos; bloqueio anti-promoção de `VERIFIED` sem
localização primária específica). As funções de modelo (`validate/fit/compare/estimate_*`,
retenção, plots, HTML) foram **preservadas sem alteração de contrato**. Três visões científicas
+ combinada explícita, usando só o vocabulário existente (`VERIFIED`/`VERIFICATION_PENDING`/
`REJECTED`): `verified` (padrão, sem fallback para pendentes), `pending` (exploratória),
`rejected` (registros preservados com motivo, excluídos de ajuste por padrão), `combined`
(exploratória, `VERIFIED+PENDING`, nunca inclui `REJECTED`). CLI: `--view
{verified,pending,rejected,combined}` (padrão `verified`); `--include-pending` mantido como
alias legado de `combined`. Só `QUANTITATIVE_MEASUREMENT` entra nos ajustes
(`adapt_measurements_for_analysis()` rejeita parâmetros publicados e narrativas com erro, sem
inventar série temporal a partir de `k`/meia-vida); parâmetros publicados (`reported`) e ajustes
do projeto (`calculated_from_published_series`) em tabelas distintas; narrativas qualitativas
fora dos insumos numéricos; `analysis_view` + `verification_status` propagados a retenção,
ajustes, comparação, incertezas e intervalos. Saídas por visão em
`data/literature/processed/views/<verified|pending_exploratory|rejected|combined_exploratory>/`
(catálogo da visão, 3 tabelas por classe, 5 CSVs de análise, `inclusion_exclusion_summary.csv`,
HTML, PNGs); arquivos legados em `processed/` refletem **somente a visão executada**, com título
carimbado (`Analise de literatura [verified]` etc.). Sem conversão implícita de unidades ou
escalas (campos `normalization_*` vazios, verificado em teste); agrupamentos existentes separam
matriz/unidade/escala; o resumo registra `CROSS_STUDY_POOLING_BLOCKED` (curva única entre estudos
bloqueada). Visão `verified` vazia válida no estado atual (0 séries): CSVs só com cabeçalho
(kinetics com as 28 colunas de `LITERATURE_FIT_COLUMNS`), HTML com "Nenhuma série elegível nesta
visão" + contagem de pendentes excluídos, `UserWarning`, nenhum PNG de visão anterior
reaproveitado como resultado verificado.

**Ressalvas (não são validação científica):** as 54 observações seguem `VERIFICATION_PENDING`,
logo a visão `verified` está propositalmente vazia — promoção exige localização primária por
valor + conferência manual no original (Fase 8). `pending`/`combined` são exploratórias
(`UserWarning` + carimbo no HTML e no diretório `*_exploratory`), não benchmarks. Testes de
software verdes **não** validam cinética, unidades ou conclusões — só o comportamento do código.

**Validação:** 9 testes novos em `tests/test_literature_views_integration.py` (fixture isolada
`module`-scoped em tempdir; harmonizador executado 1×; ≤4 execuções de `analyze_literature`);
suíte completa **99 passed + 16 subtests** (2026-10-18); `git diff --check` sem erros de
whitespace; SHA-256 dos 4 CSVs brutos idênticos ao baseline pré-Fase-3 (ver apêndice).

**O que existe e está correto (não refazer):**
- `anthocyanin_lab.py`: `analyze_literature()`, `fit_literature_kinetics()`, comparação de modelos e incerteza paramétrica; `validate_literature_data()` valida o CSV bruto.
- Saídas em `data/literature/processed/` e cobertura de testes existentes.

**Lacuna de integração identificada (não corrigida nesta rodada):**
- `analyze_literature()` lê **`literature_measurements.csv` bruto** (via `validate_literature_data`), **não** a base harmonizada `data/literature/processed/harmonized/harmonized_measurements.csv`. A Fase 2 produz uma base que nenhum módulo de análise consome — a harmonização é, por enquanto, um artefato de auditoria e não um insumo do pipeline.
- **Por que não foi corrigida agora:** trocar a fonte de leitura de `analyze_literature()` altera o comportamento de um módulo já testado e muda saídas científicas (quais observações entram nos ajustes); exige decisão explícita sobre quais campos da base harmonizada devem alimentar a cinética (ex.: filtrar por `data_origin`/grupo de comparabilidade) e revisão. Consistente com AGENTS.md §9, a alteração é registrada como pendência e não executada sem revisão.
- **Ação recomendada:** adicionar uma opção de fonte (padrão: bruto, para não quebrar saídas existentes) ou migrar explicitamente, com teste que fixe qual base é lida e um teste de regressão das saídas.

---

## Fase 4 — Decisões laboratoriais pendentes: **pendência (fora do alcance do código)**

Nenhum experimento foi executado ou declarado. Decisões que `protocol.md` explicitamente delega ao laboratório/orientação e que o código não pode tomar:

1. **Acidificante único** de concentração conhecida para `F_PH3` (o protocolo exige um só, registrado com volume e pH final 3,0 ± 0,1).
2. **Volume de enchimento e piloto** de frascos (10–15 mL é estimativa; confirmar em piloto).
3. **Critério de "continuar funcionando"** (pergunta central da Fase 4): a métrica de retenção de pH por cor, erro máximo aceitável e método diferencial de pH devem ser pré-definidos antes de qualquer experimento.
4. **Triagem microbiológica** nos dias 0 e 28: definir com o laboratório; o código não verifica segurança microbiológica (limitação documentada).
5. **Revisão bibliográfica atualizada** para confirmar lacuna/originalidade antes de submissão (também pré-requisito da Fase 8).

---

## Fase 5 — Pipeline cor–pH: **parcial**

**O que existe (não refazer):** RGB→HSV e ΔE CIE76 calculado **a partir de L\*/a\*/b\* medidos** (`add_hsv_and_delta_e`); a UI declara explicitamente que L\*, a\*, b\* **não** são derivados de RGB.

**Avanço nesta rodada:** `srgb_to_cielab(r, g, b)` adicionada a `anthocyanin_lab.py` — conversão padrão sRGB (gamma) → XYZ (primárias D65) → CIELAB, com retorno `(nan, nan, nan)` para entrada inválida. Coberta por teste com valores de referência CIE (branco, preto, vermelho puro; tolerâncias explícitas).

**Lacuna restante:** o utilitário **não está integrado ao pipeline** — `add_hsv_and_delta_e` continua sem derivar L\*a\*b\* de RGB, e `delta_e_cie76_vs_day0` continua vindo apenas de medição. A integração (se desejada) exige: (a) marcação de origem `DERIVED_FROM_RGB` nas linhas derivadas, (b) validação contra leitura espectrofotômetro no mesmo frasco, (c) decisão sobre iluminação/fundo do smartphone. Até lá, não afirmar que o pipeline calcula CIELAB — apenas que o utilitário existe.

---

## Fase 6 — Simulações moleculares (GROMACS/ORCA/PyMOL): **pendência**

- **Nenhum artefato existe:** varredura do repositório não encontrou arquivos de GROMACS (`.gro`, `.top`, `.itp`, `.tpr`), de ORCA (`.inp`, `.out`) ou scripts PyMOL associados, nem código de simulação molecular. O único diretório de simulação é `data/simulation/`, que contém **simulação cinética de degradação** (primeira ordem/Arrhenius) — não é simulação molecular e não deve ser confundida com ela.
- **Nada foi inventado:** não há resultados, estruturas, energias ou trajetórias declaradas em nenhum arquivo do projeto.
- **O que falta para concluir:** definir perguntas e sistemas (espécies protonadas da antocianina nos pHs do protocolo), protocolo de minimização/equilibração, force field, solvente, temperatura e critérios de análise; só então executar com software instalado. Enquanto não houver execução real, qualquer valor seria speculação e é omitido por decisão. Nenhum código de simulação molecular foi criado nesta rodada (diferente da Fase 5, onde o utilitário de conversão foi implementado e testado).

---

## Fase 7 — Validação de ML: **bloqueio preservado**

- `reports/validation/ml_validation_status.json` permanece com `"status": "ML_NOT_VALIDATED"` (reverificado em 2026-10-18; arquivo inalterado nesta rodada).
- Restrições intactas: não declarar melhor modelo, não usar split aleatório por linha, não declarar previsões confiáveis; separação experimental/literatura/simulação verificada (`GroupKFold`, sem vazamento por lote).
- **Bloqueio:** poucas séries temporais independentes. Nenhuma mudança de código é necessária nem permitida; a mudança exige **novos lotes experimentais independentes** e validação prospectiva. `data/raw/ml_observations.csv` não foi tocado.

---

## Fase 8 — Rastreabilidade de publicação: **bloqueio de fonte primária**

- Os **39 valores** de `source_location` em `literature_measurements.csv` seguem com texto genérico ("Localização exata no artigo pendente de conferência") — confirmado por varredura em 2026-10-18.
- A auditoria da Fase 1 forneceu localizações *de estudo* (Tabela 5, seções 2.4.4, Figura 9, Tabela 8), mas **localização por valor** (tabela/figura/linha de cada medição) exige texto integral/dados suplementares: Huțuțui (editor, HTTP 403) e Lin et al. (resumo apenas) não estavam acessíveis; Muhamad 2022 sim (ResearchGate), com Tabela 8 confirmada.
- Todas as observações seguem `VERIFICATION_PENDING`. `VERIFIED` exige DOI + localização primária + evidência de conferência; promover sem localização violaria a proposta de status de `discrepancy_reconciliation.md`.
- **Bloqueio:** acesso ao texto integral de Huțuțui et al. (2026) e Lin et al. (2023), e suplementos de Huțuțui. É pendência de **acesso a fonte**, não de código; nada no repositório a resolve.

---

## Alterações desta rodada (todas revisáveis; nenhum commit feito)

| Arquivo | Mudança | Testes |
|---|---|---|
| `tools/harmonize_literature.py` | Correções de bug (relação B↔F, duplicatas, markdown, determinismo) | 16/16 harmonization |
| `data/literature/literature_studies.csv` | +1 linha (`STUDY_F`, 16 campos) | `test_analysis` 6 estudos |
| `tests/test_literature_harmonization.py` | +6 testes de regressão (arquivo novo, untracked) | 16/16 |
| `tests/test_analysis.py` | Atualização para 6 estudos; +1 teste `srgb_to_cielab` | suíte completa |
| `anthocyanin_lab.py` | +`srgb_to_cielab()` (utilitário puro; pipeline não alterado) | teste de referência CIE |
| `reports/validation/discrepancy_reconciliation.md` | Apêndice de reconciliação Fase 1 | — |
| `data/literature/processed/harmonized/` | Saídas regeneradas (untracked) | — |

**Verificações finais (2026-10-18):**
- `python -m pytest tests/ -q` → **90 passed, 16 subtests passed**.
- `git diff --check` → sem erros de whitespace.
- `git diff --exit-code` sobre `literature_{measurements,evidence,verification_status}.csv` → **inalterados vs HEAD**; `literature_studies.csv` contém apenas a linha `STUDY_F` (+1).
- SHA-256 dos quatro CSVs brutos registrado no apêndice da reconciliação (`discrepancy_reconciliation.md`).
- `git status --short`: apenas as alterações da tabela acima (4 modificados + 2 untracked). Nenhum commit, push ou merge realizado.

**Limites deste relatório:** nenhum item foi marcado como concluído sem evidência verificável (saída de teste, diff ou leitura direta de arquivo). Pendências de acesso a fonte e decisões laboratoriais não podem ser resolvidas por alteração de código.

---

## Apêndice — Execução Fase 3 (2026-10-18, segunda rodada)

Resultados **efetivamente observados** nesta rodada. Testes de software aprovados **não**
constituem evidência científica validada: validam apenas o comportamento do código.

### A. Testes e comandos executados

| Comando | Saída real observada |
|---|---|
| `python -m pytest tests/test_literature_harmonization.py -q -p no:cacheprovider` | `16 passed` |
| `python -m pytest tests/test_literature_views_integration.py -q -p no:cacheprovider` | `9 passed` (+ 2 `UserWarning` esperados: ajuste/comparação exploratória com 39 pendentes) |
| `python -m pytest tests/ -q -p no:cacheprovider` | **`99 passed, 2 warnings, 16 subtests passed in 57.58s`** (nenhuma falha) |
| `git diff --check` (arquivos da fase) | saída vazia (exit 0); só avisos LF→CRLF do Git, sem erro de whitespace |
| `python anthocyanin_lab.py literature --dir . [--view …]` (4 visões, fumaça) | `verified`: 0 ajustes + aviso de 54 excluídos; `pending`/`combined`: 9 ajustes + aviso exploratório; `rejected`: 0 ajustes |

Se houvesse falha, a causa seria investigada antes de qualquer alteração de código ou teste;
não houve falhas nesta rodada.

### B. Hashes SHA-256 dos 4 CSVs protegidos (verificação 2)

Baseline registrado **imediatamente antes** das alterações da Fase 3 (estado local atual,
**incluindo `STUDY_F`**, 6 estudos) e comparado novamente ao final. Nenhum hash foi inventado:
todos capturados via `Get-FileHash -Algorithm SHA256` antes e depois.

| Arquivo (linhas) | SHA-256 (prefixo…sufixo; completo no log de execução) | Comparação final |
|---|---|---|
| `literature_measurements.csv` (39) | `159CE435…2ED351` | **idêntico** |
| `literature_evidence.csv` (15) | `F4728FB9…C0ED1DE4` | **idêntico** |
| `literature_verification_status.csv` (39) | `831B1FFE…387559E` | **idêntico** |
| `literature_studies.csv` (6, com `STUDY_F`) | `DE52A87C…098E19` | **idêntico** |

Referência: estado local pré-Fase-3 desta branch (não um HEAD antigo sem `STUDY_F`). Nenhum dado
bruto alterado; nenhum status promovido (catálogo segue 54× `VERIFICATION_PENDING`).

### C. Contagens em 3 níveis (verificação 3)

- **Origem (brutos):** 39 linhas em `literature_measurements.csv` + 15 linhas em
  `literature_evidence.csv` = 54 registros-fonte; manifesto com 39 chaves; 6 estudos (com
  `STUDY_F`, só bibliográfico, sem observações).
- **Harmonizada (`evidence_class`):** 43 `QUANTITATIVE_MEASUREMENT` + 8
  `PUBLISHED_KINETIC_PARAMETER` + 3 `QUALITATIVE_NARRATIVE` = **54 registros**. A diferença
  39 ≠ 43 é explicada: 4 quantitativas vêm de `literature_evidence.csv` (STUDY_C|E9–E10,
  STUDY_D|E12–E13, com `value` numérico transcrito); nenhuma fusão de conceitos.
- **`verification_status`:** 0 `VERIFIED` / 54 `VERIFICATION_PENDING` / 0 `REJECTED`.

### D. Elegibilidade por visão (observado via `split/adapt/mask/summary`)

| Visão | Incluídas (classe) | Elegíveis p/ ajuste | Ajustes | Excluídas e motivos |
|---|---|---|---|---|
| `verified` (padrão) | 0 | 0 | 0 (CSV só cabeçalho, 28 cols) | 54 por `EXCLUDED_BY_STATUS` |
| `pending` | 54 (43+8+3) | **39 linhas** (as 39 `\|L`) | **9** (P2/P4/P8/P9/P13/P14 + GLASS/METAL_CAN/POLYPROPYLENE) | 11 `EXCLUDED_NOT_QUANTITATIVE`; 4 `EXCLUDED_NO_TIME_SERIES` (C|E9–E10 sem tempo; D|E12–E13 com 1 tempo) |
| `rejected` | 0 | 0 | 0 (+ `EXCLUDED_REJECTED_POLICY`) | 54 por status; política impede ajuste |
| `combined` | 54 (0 verified + 54 pending) | 39 | 9 | idem `pending`; `REJECTED` nunca entra |

### E. Bloqueios, fontes pendentes, sobreposições

- `CROSS_STUDY_POOLING_BLOCKED`: curva única entre estudos bloqueada — unidades
  (`mg CGE/100 g FW` × `mg/L` × `%`), escalas (`dia` × `month` × `h` × `weeks`) e matrizes
  distintas; ajustes só intra-grupo (`SERIES_GROUP_KEYS`). `normalization_*` vazio em teste.
- Fontes pendentes: 39 `source_location` genéricos + 15 evidências com localização de estudo,
  não por valor (Fase 8). Divergências abertas herdadas (fora do escopo de código): dias 2–4
  Huțuțui, 510/520 nm, `k`/`t½` P2, DOI impresso 2022, texto integral Lin, suplementos.
- Sobreposição B↔F: "possível sobreposição, sujeita a confirmação documental"; `STUDY_F` sem
  observações, sem dupla contagem.

### F. Arquivos e estado final do Git (sem commit/push/merge)

- Modificados nesta branch: `anthocyanin_lab.py` (4 funções + `analyze_literature(root,
  include_pending, view)` + CLI `--view`), `tests/test_literature_views_integration.py` (novo,
  9 testes), `reports/roadmap_status_2026-10-18.md` (este apêndice); pré-existentes:
  `tools/harmonize_literature.py`, `tests/test_analysis.py`,
  `data/literature/literature_studies.csv` (linha `STUDY_F`),
  `reports/validation/discrepancy_reconciliation.md`,
  `tests/test_literature_harmonization.py` (untracked).
- Untracked gerados: `data/literature/processed/harmonized/` (base regenerada),
  `data/literature/processed/views/*/` (fumaça manual; não commitados). Legados
  `processed/literature_*` restaurados ao HEAD após a fumaça (sem modificação no status final).

### G. Carimbo de visão nas saídas (verificação 4, tempdir isolado)

- Padrão `verified` → legado `<h1>Analise de literatura [verified] …</h1>`, notice "Visao
  VERIFICADA (analysis_view='verified'): apenas registros VERIFIED; sem fallback para pendentes.
  Catalogo: 54 observacoes; incluidas nesta visao: 0; … Nenhuma serie elegivel nesta visao;
  saidas vazias validas.", kinetics 0 linhas/28 cols, `UserWarning` + print dos 54 excluídos.
- `view="pending"` → `<h1>… [pending] …</h1>`, "EXPLORATORIA" no notice, kinetics 9 linhas,
  `UserWarning` exploratório.
- Exploratório **não** aparece como verificado; `verified` vazia informa a exclusão.

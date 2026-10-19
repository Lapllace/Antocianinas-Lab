# Antocianinas Lab — Fase 2: auditoria de harmonização dos dados

**Data:** 17 de outubro de 2026  
**Status:** iniciada — auditoria estrutural e regras de comparabilidade  
**Escopo desta revisão:** estrutura dos arquivos CSV acessíveis na referência remota `feature/scientific-skills-integration`.  
**Limitação essencial:** esta referência remota pode estar atrás do diretório de trabalho local, que contém mudanças mais recentes não publicadas. Este documento não substitui uma verificação dos arquivos atuais no computador do projeto e não autoriza sobrescrever nenhuma alteração local.

## 1. Objetivo da Fase 2

Criar uma base que preserve os dados de origem e permita comparações válidas entre estudos, sem tratar formulações, unidades, métodos ou tipos de evidência diferentes como equivalentes.

A regra central é: **harmonizar os metadados e a organização não significa converter ou fundir automaticamente os valores científicos.** Dados brutos permanecem imutáveis; qualquer versão normalizada deve ser um derivado rastreável.

## 2. Inventário estrutural observado

| Arquivo consultado na referência remota | Registros de dados | Observação |
|---|---:|---|
| `data/literature/literature_measurements.csv` | 39 | 18 registros de STUDY_A e 21 de STUDY_B. |
| `data/literature/literature_studies.csv` | 5 estudos | STUDY_A a STUDY_E. |
| `data/literature/literature_evidence.csv` | 15 evidências | Mistura resumos cinéticos, resultados quantitativos e evidência qualitativa. |

A referência remota consultada não continha os arquivos de comparação/incerteza citados no histórico local mais recente nem `literature_verification_status.csv` no caminho procurado. Isso pode ser resultado de diferença entre a branch remota e o diretório local; **não criar substitutos nem remover arquivos locais com base nessa ausência**.

## 3. Achados que precisam ser tratados

### 3.1 Séries medidas

- **STUDY_A — Huțuțui et al. (2026):** 6 tratamentos × 3 tempos observados = 18 linhas. Os tempos disponíveis são dias 1, 5 e 10. A auditoria da Fase 1 registra que o artigo descreve medições também nos dias 2, 3 e 4. Esses pontos ausentes não devem ser interpolados, digitalizados de forma aproximada ou inventados para completar a série.
- **STUDY_B — Muhamad et al. (2022):** 3 embalagens × 7 tempos = 21 linhas, meses 0 a 6. A matriz é uma bebida mista de repolho roxo e rosela, não o extrato puro do projeto.
- **STUDY_C — Lin et al. (2023):** consta no catálogo/evidências, mas não possui série tempo–concentração em `literature_measurements.csv`. Isso é correto enquanto só houver resumo cinético verificável; não criar pontos sintéticos a partir de `k` e meia-vida.
- **STUDY_D — Pan et al.:** existe evidência de retenção percentual em horas e uma meia-vida reportada em horas, mas ela não deve ser misturada diretamente às séries de concentração de A/B.
- **STUDY_E — Patras (2019):** a informação armazenada é essencialmente qualitativa. Não converter descrições de mudança de cor em valores numéricos sem dados publicados rastreáveis.

### 3.2 Localizadores de fontes

Nas linhas de medições acessíveis, `source_location` contém texto genérico indicando que a localização exata ainda está pendente. Assim, os 39 registros não possuem localização específica e auditável por célula/linha da fonte (por exemplo, tabela, figura, página, suplemento). O DOI sozinho identifica a publicação, mas não permite reconstituir rapidamente qual evidência sustenta cada valor.

A classificação `reported_or_calculated=reported` não comprova por si só que o valor foi conferido no original: as notas de diversas linhas afirmam que o valor foi informado/transcrito pelo usuário. A proveniência e o estado de verificação precisam ser campos separados.

### 3.3 Campos ausentes e informação sobre replicatas

No `literature_measurements.csv` da referência consultada:

- `standard_deviation` está vazio nas 39 linhas;
- `replicate_count` está vazio nas 39 linhas;
- os campos `additive` e `additive_concentration_pct` estão vazios nas 39 linhas;
- vários campos são vazios para STUDY_B, incluindo solvente, pH e condição de oxigênio.

Nem todo campo vazio é necessariamente um erro: alguns parâmetros podem não ser aplicáveis ou podem não ter sido reportados no artigo. Portanto, não preencher com valores padrão nem inferir, por exemplo, pH neutro, condição aeróbia ou ausência de aditivo sem suporte documental. Usar estados explícitos para diferenciar `not_reported`, `not_applicable`, `pending_extraction` e um valor efetivamente conhecido.

A auditoria da Fase 1 informa que o artigo de STUDY_A apresenta média ± desvio-padrão e `n=3`, mas também descreve um lote de extração por solvente. O `n` publicado não pode ser assumido como três lotes independentes. Para STUDY_B, os valores de desvio-padrão existentes no artigo precisam ser recuperados com a referência específica; não inferir a partir de outras publicações sobrepostas.

### 3.4 Unidades e matriz

As 39 linhas incluem duas unidades de concentração diferentes:

- `mg CGE/100 g FW` para STUDY_A;
- equivalentes de cianidina-3-glicosídeo por litro para STUDY_B.

Essas unidades descrevem denominadores e matrizes diferentes. **Não converter, juntar ou ajustar uma única curva usando ambas** sem uma transformação justificável a partir de informação experimental adicional. A normalização de unidades deve preservar sempre o texto original e registrar fórmula, fatores e origem de qualquer conversão.

Os tempos também usam escalas diferentes (`dia` e `mês`). Não converter meses em dias assumindo automaticamente que cada mês tem 30 dias. Manter o valor/unidade original ou obter as datas reais de armazenamento e explicitar a regra da conversão.

### 3.5 Proveniência bibliográfica e duplicação potencial

A Fase 1 identificou que o artigo de Muhamad et al. (2022) e uma publicação de 2023 dos mesmos autores apresentam uma tabela numérica igual ou sobreposta. A referência de 2023 deve permanecer na bibliografia, mas seus números não podem ser adicionados como um segundo conjunto independente até que a independência seja demonstrada. Criar uma relação `overlap/related_dataset` no catálogo, sem apagar a publicação.

Também é necessário conferir o ano/citação de STUDY_D na fonte original; os arquivos históricos têm referências ao mesmo DOI com ano diferente. Não alterar o ano bibliográfico com base apenas em uma discrepância entre registros locais.

### 3.6 Integridade textual

No conteúdo da referência remota consultada aparecem interrogações no lugar de caracteres acentuados em textos como a descrição da matriz de STUDY_C e algumas notas. A origem desses caracteres precisa ser verificada. Corrigir textos a partir da referência bibliográfica ou do conteúdo original preservando um registro da correção; não realizar substituição global de `?`, pois esses caracteres podem também aparecer legitimamente em texto.

## 4. Grupos de comparabilidade recomendados

| Grupo | Evidências | Uso permitido neste momento | Não fazer |
|---|---|---|---|
| A — extratos acidificados de repolho roxo | STUDY_A, separando P2/P4/P8/P9/P13/P14 | Análise por tratamento, com série incompleta explicitada e confirmação da fonte. | Não tratar tratamentos diferentes como réplicas nem completar tempos ausentes. |
| B — bebida mista e embalagem | STUDY_B, vidro/lata/polipropileno | Comparar as embalagens dentro do estudo, após recuperar desvio-padrão, replicatas e localizadores. | Não usar como curva diretamente equivalente ao extrato puro de STUDY_A. |
| C — parâmetro cinético reportado em resumo | STUDY_C / Lin et al. | Referência contextual de `k`, preservando as condições conhecidas e o status parcial. | Não reconstruir série concentração–tempo sem dados brutos e condições completas. |
| D — retenção percentual/estabilidade em horas | STUDY_D / Pan et al. | Evidências separadas por pH, temperatura, tempo e endpoint reportados. | Não misturar retenção (%) em horas com concentração em dias sem modelo e transformação explicitados. |
| E — resultados qualitativos de cor/ingredientes | STUDY_E / Patras | Contexto qualitativo e hipótese experimental. | Não gerar valores de concentração ou classificar estabilização química apenas por diferença de cor. |

## 5. Esquema de dados harmonizados — proposta

Não substituir os arquivos atuais por um esquema novo de uma só vez. Criar, depois de inspecionar o diretório local e os consumidores de dados, uma saída derivada e versionada, mantendo intactos os CSVs de origem.

Campos mínimos recomendados para cada observação harmonizada:

- `observation_id` estável e único;
- `study_id`, `treatment_id` e, quando existir, `source_record_id`;
- `doi`, `source_url`, `source_version` e `source_locator` (tabela/figura/página/suplemento);
- `provenance_class` — por exemplo `ARTICLE_TABLE`, `ARTICLE_TEXT`, `SUPPLEMENTARY_DATA`, `DIGITIZED_FIGURE`, `CALCULATED_FROM_SOURCE`, `USER_TRANSCRIBED_PENDING_VERIFICATION`, `LAB_MEASUREMENT` ou `SIMULATION`;
- `verification_status` independente da proveniência: `PENDING`, `PARTIAL`, `VERIFIED` ou `BLOCKED`, acompanhado de `verification_note`;
- `matrix_type`, `species`, `extraction_method`, `solvent_composition`, `pH`, `additive`, concentração do aditivo e condições de armazenamento;
- `time_value_original`, `time_unit_original`, e campos normalizados só quando a conversão for definida e justificada;
- `measurement_name`, `value_original`, `unit_original`, `standard_deviation`, `replicate_count` e `replicate_type` (`technical`, `independent_sample`, `independent_extraction`, `unknown` ou `not_reported`);
- `normalization_formula`, `normalized_value` e `normalized_unit`, somente quando realmente calculados, com método/unidades de entrada;
- `comparability_group`, `exclusion_reason` e notas.

Quando o artigo não fornecer uma informação, preservar ausência e seu motivo — não converter ausência em zero ou assumir um valor por conveniência.

## 6. Ordem de implementação recomendada na cópia local

1. Reconciliar este relatório com o diretório local atual. Registrar branch, commit, arquivos modificados e status antes de começar; preservar alterações locais não comitadas.
2. Inventariar os campos e consumidores atuais dos CSVs; não remover nem renomear campos utilizados pelo código.
3. Manter os arquivos brutos intactos. Criar um script determinístico de harmonização ou arquivo derivado separado, sem rede e sem alterar os dados originais.
4. Normalizar apenas vocabulários e metadados seguros (por exemplo, unidades de tempo reconhecidas, nomes de condições e classes de proveniência), mantendo sempre os valores originais.
5. Adicionar estados explícitos de ausência/pendência e grupos de comparabilidade; nunca inferir condição experimental a partir de campo vazio.
6. Adicionar validadores de integridade: chave estável, campos obrigatórios condicionais, unidades, tempos numéricos, IDs de estudo existentes, origem/localizador e duplicatas exatas sem excluir automaticamente linhas.
7. Gerar um relatório de diferenças entre entrada e saída, com contagens, alterações por campo e todos os valores que não puderam ser normalizados.
8. Rodar somente testes focados de harmonização/validação e `git diff --check`. Não regenerar ou mudar modelos cinéticos, intervalos de incerteza, resultados de ML ou simulações nesta fase.

## 7. Critérios de conclusão da Fase 2

A Fase 2 só pode ser considerada concluída quando:

- cada observação mantém ligação direta à sua fonte e linha/registro original;
- unidades, escalas de tempo e matrizes diferentes permanecem distinguíveis;
- a diferença entre valor publicado, cálculo derivado e transcrição não verificada é explícita;
- ausências e motivos são representados sem imputações silenciosas;
- publicações com dados potencialmente sobrepostos estão relacionadas sem duplicar as observações na modelagem;
- a harmonização pode ser reproduzida a partir dos arquivos de entrada e gera um relatório de auditoria;
- os dados pendentes de Fase 1 continuam pendentes, sem atualizações automáticas para `VERIFIED`.

## 8. Próxima ação imediata para o agente local

Usar este relatório como especificação de trabalho, mas antes de escrever arquivos comparar os caminhos e conteúdos com o checkout local atual — que pode conter versões mais recentes. Implementar primeiro o gerador de relatório/harmonização derivada em escopo mínimo. Não editar os CSVs brutos nem fazer alterações nos modelos.

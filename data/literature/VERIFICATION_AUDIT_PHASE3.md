# Antocianinas Lab — Auditoria de fontes e dados (Fase 3)

**Data da auditoria:** 18 de outubro de 2026  
**Escopo:** Atualização do status de verificação baseada em tentativas de acesso atuais e verificação consolidada da Fase 1.  
**Natureza:** Auditoria de rastreabilidade e registro de bloqueios de acesso. Nenhum dado bruto foi modificado.

## 1. Resumo executivo

| Conjunto | Status Fase 1 | Status Acesso Atual | Situação Fase 3 | Ação Recomendada |
|---|---|---|---|---|
| Huțuțui et al. (2026) | Parcial (valores textuais confirmados) | PDF bloqueado (HTTP 403) | Valores mantidos como reportados; localização por valor pendente | Aguardar acesso ao PDF completo ou suplementos |
| Muhamad et al. (2022) | Tabela 8 confirmada (texto integral) | Acesso bloqueado (HTTP 403) | Valores da Tabela 8 mantidos; SD pode ser adicionado | Adicionar SD da Tabela 8; localização por valor pendente |
| Muhamad et al. (2023) | Identificada como sobreposição | PDF 404 (arquivo não encontrado) | Sobreposição documentada; sem novos dados | Confirmar relação editorial; não duplicar observações |
| Lin et al. (2023) | Parcial (resumo editorial) | Acesso bloqueado (HTTP 403) | Parâmetros do resumo mantidos; série temporal pendente | Aguardar texto completo |

**Registro de verificação atualizado:** 54 observações permanecem como `VERIFICATION_PENDING`. Nenhuma promoção automática para `VERIFIED` - isso exige acesso ao texto integral e localização específica por valor (tabela/figura/linha).

---

## 2. Huțuțui, Amariei & Gâtlan (2026) — STUDY_A

### 2.1 Status de acesso atual (2026-10-18)

- **DOI:** 10.3390/molecules31183339 — resolve corretamente
- **Página editorial MDPI:** acessível (metadados bibliográficos)
- **PDF do artigo:** HTTP 403 (acesso negado)
- **Suplementos:** não testados (acesso ao PDF bloqueado)

### 2.2 O que foi confirmado na Fase 1

A auditoria da Fase 1 (baseada em acesso disponível em 2026-10-17) confirmou:

- Valores textuais de TAC para seis condições (P2, P4, P8, P9, P13, P14) nos dias 1, 5 e 10
- Condições experimentais da Tabela 5 (solvente, temperatura, luz, oxigênio)
- Unidade: mg CGE/100 g FW
- Localização por estudo: Tabela 5, seção 2.4.4, Figura 9
- Parâmetros cinéticos publicados (k e t½) para cada tratamento

### 2.3 Lacunas pendentes (bloqueio de acesso)

- **Dias 2, 3 e 4:** O artigo menciona medições nestes dias, mas os valores não foram recuperados na Fase 1. Acesso ao PDF é necessário para verificar se estes valores estão em tabelas/figuras ou suplementos.
- **Localização por valor:** Cada um dos 18 valores de TAC (6 tratamentos × 3 tempos) precisa de localização específica (qual tabela, linha, figura ou suplemento). Atualmente temos apenas localização por estudo.
- **Discrepância P2 (k vs t½):** k=0.0112 d⁻¹ implica t½≈61.9 d, mas o artigo reporta 60.5 d. Consultar tabela ou método original para resolução.
- **Comprimento de onda:** 510 nm vs 520 nm no método diferencial de pH. Confirmar no PDF.

### 2.4 Status recomendado

**Manter `VERIFICATION_PENDING` para todas as 18 observações.**

Justificativa: Embora os valores numéricos tenham sido confirmados da narrativa editorial, a rastreabilidade completa exige localização por valor específico e acesso ao PDF para resolver as discrepâncias metodológicas. Não promover sem PDF completo.

---

## 3. Muhamad, Hussin & Arifin (2022) — STUDY_B

### 3.1 Status de acesso atual (2026-10-18)

- **DOI:** 10.33102/mjosht.v8i1.239 — resolve corretamente
- **Página editorial do periódico:** falha na tentativa de fetch
- **ResearchGate (texto integral):** HTTP 403 (acesso negado)
- **DOI alternativo impresso no PDF:** 10.33102/2022239 (registrado na Fase 1)

### 3.2 O que foi confirmado na Fase 1

A auditoria da Fase 1 confirmou a **Tabela 8** do artigo de 2022, com todos os 21 valores:

| Mês | Vidro (±SD) | Lata (±SD) | PP (±SD) |
|---|---|---|---|
| 0 | 263.40 ± 1.67 | 262.66 ± 0.87 | 262.17 ± 1.04 |
| 1 | 132.10 ± 3.60 | 113.20 ± 3.96 | 96.88 ± 0.71 |
| 2 | 87.75 ± 16.60 | 94.54 ± 23.17 | 88.21 ± 18.55 |
| 3 | 74.38 ± 2.21 | 71.80 ± 7.35 | 40.42 ± 0.49 |
| 4 | 55.60 ± 0.87 | 49.27 ± 1.93 | 21.09 ± 1.31 |
| 5 | 48.29 ± 0.96 | 39.85 ± 0.85 | 14.38 ± 0.17 |
| 6 | 34.36 ± 1.83 | 30.50 ± 0.17 | 10.44 ± 1.42 |

**Unidade:** mg equivalentes de cianidina-3-glicosídeo/L  
**Localização por estudo:** Tabela 8  
**Condições:** bebida mista repolho roxo + roselle, armazenamento a 29 ± 2 °C, escuro

### 3.3 Ação necessária: adicionar desvios-padrão

O CSV atual (`literature_measurements.csv`) contém apenas as médias (21 linhas). Os desvios-padrão acima, confirmados na Fase 1, devem ser adicionados.

**Recomendação:** Criar um commit separado para adicionar os campos `standard_deviation` e `replicate_count` às 21 linhas de STUDY_B, com `source_location` atualizado para "Tabela 8" e note explicando que SD foi adicionado com base na auditoria da Fase 1.

### 3.4 Sobreposição com Muhamad et al. (2023) — STUDY_F

A publicação de 2023 (DOI 10.26656/fr.2017.6(S2).030) contém a **mesma Tabela 2** com os mesmos 21 valores e desvios-padrão. Esta sobreposição já está registrada em:
- `data/literature/processed/harmonized/relations_overlapping_publications.csv`
- `data/literature/literature_studies.csv` (linha STUDY_F)

**Status da relação:** "possível sobreposição, sujeita a confirmação documental"

**Bloqueio atual:** O PDF de 2023 retorna HTTP 404 (arquivo não encontrado no servidor myfoodresearch.com). Impossível confirmar a relação editorial ou obter informações adicionais.

**Ação recomendada:** Não contar as duas publicações como experimentos independentes. Manter STUDY_F como registro bibliográfico sem observações harmônicas até que a relação seja esclarecida.

### 3.5 Status recomendado

**Manter `VERIFICATION_PENDING` para todas as 21 observações.**

Justificativa: Valores confirmados da Tabela 8, mas localização por valor específica (qual linha da tabela para cada combinação mês×embalagem) não está registrada. Acesso ao PDF seria necessário para rastreabilidade granular.

---

## 4. Lin et al. (2023) — STUDY_C

### 4.1 Status de acesso atual (2026-10-18)

- **DOI:** 10.1016/j.fpsl.2023.101065 — resolve corretamente
- **ScienceDirect:** HTTP 403 (acesso negado)
- **Preprint SSRN:** não testado nesta rodada

### 4.2 O que foi confirmado na Fase 1

A auditoria da Fase 1 confirmou do **resumo editorial**:

- k = 0.0466 d⁻¹ (para ácido gálico a 0.4%)
- t½ = 14.87 d
- Consistência matemática: ln(2)/0.0466 ≈ 14.87
- Contexto: sistema de bebida simulada com ácido L-ascórbico

### 4.3 Lacunas pendentes

- **Texto completo:** Não acessível (bloqueio ScienceDirect)
- **Tabela específica:** Localização exata do parâmetro cinético não confirmada
- **Série temporal:** Não há série concentração-tempo no inventário (apenas resumo cinético)
- **Condições detalhadas:** pH, regime térmico, composição completa do sistema simulado não confirmados

### 4.4 Status recomendado

**Manter `VERIFICATION_PENDING` para as evidências de STUDY_C.**

Justificativa: Parâmetros confirmados apenas do resumo. Rastreabilidade completa exige texto completo e localização específica da tabela/figura. Não é uma série temporal de medições (evidência classificada como `PUBLISHED_KINETIC_PARAMETER` na base harmonizada).

---

## 5. Pan et al. (2020) — STUDY_D

### 5.1 Status

Este estudo foi incluído no inventário (`literature_evidence.csv`) com evidências de retenção percentual em horas e meia-vida reportada em horas. Não foi priorizado na Fase 1, e não houve tentativa de acesso nesta rodada.

**Classificação na base harmonizada:** Grupo D (retenção em horas; não misturar com séries em dias)

**Recomendação:** Priorizar verificação após Huțuțui, Muhamad e Lin, pois as evidências são qualitativamente diferentes (retenção % em horas vs concentração em dias/meses).

---

## 6. Patras (2019) — STUDY_E

### 6.1 Status

Este estudo contém evidências qualitativas sobre efeitos de ingredientes na cor de extrato hidroetanólico. Não há série temporal de concentração.

**Classificação na base harmonizada:** Grupo E (dados qualitativos; sem valores quantitativos)

**Recomendação:** Manter como contexto qualitativo. Não tentar converter descrições de cor em valores numéricos sem dados quantitativos do artigo.

---

## 7. Resumo de bloqueios de acesso

| Fonte | Bloqueio | Tipo | Impacto |
|---|---|---|---|
| Huțuțui (2026) MDPI PDF | HTTP 403 | Acesso negado | Impede localização por valor e resolução de discrepâncias |
| Muhamad (2022) ResearchGate | HTTP 403 | Acesso negado | Impede nova verificação; valores já confirmados na Fase 1 |
| Muhamad (2022) MJOSHT | Falha fetch | Possível servidor indisponível | Mesmo que ResearchGate |
| Muhamad (2023) PDF | HTTP 404 | Arquivo não encontrado | Impede confirmação da relação editorial |
| Lin (2023) ScienceDirect | HTTP 403 | Acesso negado | Impede texto completo e localização da tabela |

**Conclusão:** Todos os bloqueios são de acesso a fonte primária, não problemas de código. Não há ação de software que resolva estes bloqueios.

---

## 8. Atualizações recomendadas sem modificar dados brutos

### 8.1 Adicionar desvios-padrão de Muhamad (2022)

Proposta de alteração (commit separado, após revisão):

1. Atualizar `literature_measurements.csv` para as 21 linhas de STUDY_B:
   - Preencher `standard_deviation` com os valores da Tabela 8
   - Preencher `replicate_count` com 3 (informado no artigo)
   - Atualizar `source_location` para "Tabela 8, Total Anthocyanins Content (mg cyd-3-glu/L)"
   - Adicionar note: "Desvio-padrão adicionado com base na auditoria Fase 1 (2026-10-17)"

2. Atualizar `literature_verification_status.csv`:
   - Para as 21 linhas de STUDY_B, atualizar `verified_source_location` para "Tabela 8"
   - Atualizar `verification_notes` para incluir referência à auditoria Fase 1
   - Manter `verification_status` como `VERIFICATION_PENDING` (localização por valor específica ainda pendente)

### 8.2 Documentar sobreposição B↔F

A relação `STUDY_B ↔ STUDY_F` já está registrada em:
- `data/literature/processed/harmonized/relations_overlapping_publications.csv`
- `data/literature/literature_studies.csv`

Nenhuma ação adicional necessária até que o PDF de 2023 seja acessível ou a relação editorial seja confirmada por outra via.

### 8.3 Criar registro de tentativas de acesso

Adicionar uma nota em `data/literature/VERIFICATION_AUDIT_PHASE3.md` (este arquivo) documentando as tentativas de acesso de 2026-10-18 e os bloqueios encontrados.

---

## 9. Contagem final de registros

| Estudo | Observações | Status Fase 3 | Motivo de pendência |
|---|---:|---|---|
| STUDY_A (Huțuțui) | 18 | VERIFICATION_PENDING | Acesso ao PDF bloqueado; localização por valor pendente |
| STUDY_B (Muhamad 2022) | 21 | VERIFICATION_PENDING | Acesso ao PDF bloqueado; localização por valor pendente |
| STUDY_C (Lin) | 8 (evidências) | VERIFICATION_PENDING | Acesso ao texto completo bloqueado |
| STUDY_D (Pan) | 2 (evidências) | VERIFICATION_PENDING | Não priorizado; retenção em horas |
| STUDY_E (Patras) | 3 (evidências) | VERIFICATION_PENDING | Dados qualitativos |
| STUDY_F (Muhamad 2023) | 0 | - | Bibliográfico apenas; sobreposição documentada |
| **Total** | **52** | **52 pendentes** | Bloqueios de acesso ou natureza qualitativa |

**Nenhuma observação promovida para VERIFIED nesta fase.**

---

## 10. Próximas ações possíveis (fora do escopo desta auditoria)

1. **Acesso alternativo ao PDF de Huțuțui:** Via biblioteca institucional, contato com autores, ou pré-print em outro repositório.
2. **Acesso alternativo ao PDF de Muhamad 2022:** Via biblioteca institucional ou arquivo compartilhado pelos autores.
3. **Confirmar relação editorial B↔F:** Contactar editores do periódico Food Research ou verificar outras bases bibliográficas.
4. **Acesso ao texto completo de Lin 2023:** Via biblioteca institucional ou pré-print alternativo.
5. **Priorizar STUDY_D:** Verificar a fonte primária de Pan et al. (2020) para documentar retenção em horas.

---

## 11. Limitações desta auditoria

- Nenhum dado bruto foi modificado.
- Nenhum status foi promovido automaticamente.
- Os bloqueios de acesso são externos ao repositório e não podem ser resolvidos por alteração de código.
- Os valores confirmados na Fase 1 são mantidos como reportados; não foram recalculados ou substituídos.
- A adição de desvios-padrão de Muhamad 2022 requer um commit separado após revisão.

---

**Data de geração:** 2026-10-18  
**Metodologia:** Tentativas de acesso via webfetch + consolidação da auditoria Fase 1  
**Próxima revisão:** Quando acesso a fontes primárias estiver disponível.

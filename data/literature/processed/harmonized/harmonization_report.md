# Relatorio de Auditoria - Fase 2, Etapa 1: Harmonia de Dados

**Data:** 17 de outubro de 2026
**Execucao:** F2E1-fb880f2bcdbe583a
**Status:** iniciada - derivada gerada; originais inalterados.

## 1. Resumo executivo

| Metrica | Valor |
|---|---|
| Linhas originais (literature_measurements.csv) | 39 |
| Linhas geradas na base harmonica | 54 |
| Duplicatas exatas detectadas | 0 |
| Dados simulados incluidos | nao |
| Classe: medicoes quantitativas | 43 |
| Classe: parametros cineticos publicados | 8 |
| Classe: evidencias qualitativas/narrativas | 3 |

## 2. Preservacao de originais

Cada observacao mantém value_original, unit_original, time_value_original, time_unit_original copiados textualmente de literature_measurements.csv. Nenhuma conversao de unidades, escala temporal ou inferencia de valores ausentes foi realizada.

Os campos normalization_formula, normalized_value, normalized_unit estao vazios por decisao de fase: nenhuma transformacao foi aplicada nesta etapa.

## 3. Lacunas registradas

| Campo | Quantidade | Motivo registrado |
|---|---|---|
| source_locator | 0 | Localizacao pendente de conferencia; somente DOI disponivel. |
| standard_deviation | 31 | Nao informado na fonte; ausencia preservada, nao substituida por zero. |
| replicate_type | 33 | Nao informado; classe not_reported para nao confundir com replica independente. |
| pH | 26 | Nao reportado; nenhuma inferencia de pH. |
| additive_concentration_pct | 49 | Nao reportado; ausencia registrada. |

## 4. Duplicatas
Nenhuma dupla exata encontrada nos registros de mensuracao.

## 5. Unidades e escalas mantidas

As duas matrizes de unidade sao mantidas separadas:
- mg CGE/100 g FW - STUDY_A (extrato)
- mg equivalentes de cianidina-3-glicosideo/L - STUDY_B (bebida mista)

Tempos preservados em dia (STUDY_A) e mes (STUDY_B); conversao nao e feita.

## 6. Publicacoes potencialmente sobrepostas

Relacao STUDY_B (Muhamad et al. 2022, DOI 10.33102/mjosht.v8i1.239) com STUDY_F (Muhamad et al. 2023, DOI 10.26656/fr.2017.6(S2).030) registrada em relations_overlapping_publications.csv como possivel sobreposicao de dados, sujeita a confirmacao documental. STUDY_C (Lin et al. 2023) NAO e publicacao sobreposta a STUDY_B. As observacoes originais nao sao duplicadas; ambas permanecem na bibliografia.

## 7. Listas de grupos de comparabilidade

| Grupo | Estudos | Observacao |
|---|---|---|
| A | STUDY_A |  |
| B | STUDY_B |  |
| C | STUDY_C | Sem serie temporal; apenas resumo cinetico |
| D | STUDY_D | Retencao em horas; nao misturar com series em dias |
| E | STUDY_E | Dados qualitativos; sem valores quantitativos |
| None | STUDY_F | Sem observacoes harmonizadas nesta etapa; publicacao relacionada a STUDY_B (possivel sobreposicao de dados, sujeita a confirmacao documental) |

## 8. Arquivos gerados

- data/literature/processed/harmonized/harmonized_measurements.csv
- data/literature/processed/harmonized/relations_overlapping_publications.csv
- data/literature/processed/harmonized/harmonization_report.csv
- data/literature/processed/harmonized/harmonization_report.md

## 9. Limites e pendencias

- Estado VERIFICATION_PENDING mantido (nao autoatualiza a VERIFIED).
- Localidade de cada celula ainda nao confirmada na fonte original.
- Unidades mg CGE/100 g FW vs mg equivalentes de cianidina-3-glicosideo/L sao distintas e nao sao convertidas.
- Suplemento de enriquecimento aplicado: 21 registros de literature_measurements_supplement_phase3.csv
  (desvios-padrao, replicatas e localizadores adicionados na Fase 3)

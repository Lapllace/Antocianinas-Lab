# Relatório de Comparação — STUDY_B (Muhamad et al., 2022)

**Data da geração:** 20 de outubro de 2026 (atualizado no mesmo dia após recuperação do texto integral)  
**Escopo:** os 21 registros de `study_id = STUDY_B` em `data/literature/literature_measurements.csv`  
**Fonte-alvo:** Tabela 8, página impressa 6 do texto integral  
**Natureza:** documentação de rastreabilidade. **Nenhum CSV de literatura, valor científico ou função de produção foi alterado.**

---

## 1. Resumo executivo

| Métrica | Contagem |
|---|---:|
| Registros comparados | 21 |
| **Coincidem com a fonte** | **21** |
| Divergem da fonte | 0 |
| Sem confirmação | 0 |

**Os 21 valores médios de STUDY_B coincidem exatamente com a Tabela 8 do texto integral.** O status formal permanece `VERIFICATION_PENDING` — a promoção para `VERIFIED` depende de revisão explícita das evidências.

## 2. Fonte efetivamente consultada e tentativas anteriores

| # | Fonte | URL consultada | Resultado |
|---|---|---|---|
| 1 | ResearchGate (versão integral) | `https://www.researchgate.net/publication/380009067_Effect_of_Packaging_Materials_and_Storage_on_Physicochemical_Properties_and_Anthocyanin_Contents_of_Red_Cabbage-Roselle_Blended_Drink` | HTTP 403 Forbidden |
| 2 | MJOSHT (página oficial do periódico) | `https://mjosht.usim.edu.my/index.php/mjosht/article/view/239` | Falha de fetch |
| 3 | OAREP USIM (repositório institucional) | `https://oarep.usim.edu.my/entities/publication/f1831795-184a-4f8d-bc19-4a307a23f6a5` e endpoint de bitstream | Falha de conexão |
| 4 | MJOSHT OJS (galley view/download) | `https://mjosht.usim.edu.my/index.php/mjosht/article/download/239/143/1413` | Falha de conexão |
| **5** | **Espelho Semantic Scholar (PDF)** | `https://pdfs.semanticscholar.org/9158/d0c936907258920f3e0f28326aa0bff70dd6.pdf` | **HTTP 200 — PDF obtido** |

**Arquivo de fonte:** `data/literature/sources/muhamad_2022.pdf` — 327.405 bytes, PDF-1.7, 8 páginas.  
**SHA-256 do PDF:** `4a8e00d602cde92c38ae0734f2330dcb0837aebcc8e9cbc49148461fcc362a23`.

**Identidade confirmada (página 1):** título, autores (Nur Farah Hani Muhamad; Faridah Hussin; Norlelawati Arifin), MJoSHT Vol. 8 No. 1 (2022); recebido 23/08/2021; publicado 01/02/2022.

**Localização exata dos dados:** Tabela 8 — "Total Anthocyanins Content (mg cyd-3-glu/ L) of Red Cabbage-Roselle Blended drinks in Different Packaging Materials" — **página impressa 6**.

**Método declarado no artigo (p. 3):** pH diferencial (Giusti & Wrolstad [23]); valores expressos em equivalentes de cianidina-3-glicosídeo; MW = 449,2 g/mol.

**Verificação triplice da Tabela 8:** (a) leitura visual da página 6 renderizada; (b) leitura visual de recorte ampliado da tabela a 300 DPI; (c) extração da camada de texto com PyMuPDF. As três vias convergem para os mesmos valores.

## 3. Tabela de comparação registro a registro

**Localização comum a todas as linhas:** PDF `data/literature/sources/muhamad_2022.pdf` (SHA-256 `4a8e00d6…`), obtido de `https://pdfs.semanticscholar.org/9158/d0c936907258920f3e0f28326aa0bff70dd6.pdf`; MJoSHT 8(1) 2022, **Tabela 8, página impressa 6** — coluna = embalagem, linha = mês de armazenamento.

| # | Registro no projeto | Embalagem | Mês | Valor original (projeto) | Valor de referência (Tabela 8) | DP na fonte | Localização (T8 = Tabela 8, p. 6) | Comparação | Pendência |
|---:|---|---|---:|---:|---:|---:|---|---|---|
| 1 | STUDY_B / GLASS / mês 0 | Vidro | 0 | 263,40 | 263,40 | 1,67 | T8 · Glass bottle · mês 0 | Coincide | Registrar DP 1,67 |
| 2 | STUDY_B / GLASS / mês 1 | Vidro | 1 | 132,10 | 132,10 | 3,60 | T8 · Glass bottle · mês 1 | Coincide | Registrar DP 3,60 |
| 3 | STUDY_B / GLASS / mês 2 | Vidro | 2 | 87,75 | 87,75 | 16,60 | T8 · Glass bottle · mês 2 | Coincide | Registrar DP 16,60 |
| 4 | STUDY_B / GLASS / mês 3 | Vidro | 3 | 74,38 | 74,38 | 2,21 | T8 · Glass bottle · mês 3 | Coincide | Registrar DP 2,21 |
| 5 | STUDY_B / GLASS / mês 4 | Vidro | 4 | 55,60 | 55,60 | 0,87 | T8 · Glass bottle · mês 4 | Coincide | Registrar DP 0,87 |
| 6 | STUDY_B / GLASS / mês 5 | Vidro | 5 | 48,29 | 48,29 | 0,96 | T8 · Glass bottle · mês 5 | Coincide | Registrar DP 0,96 |
| 7 | STUDY_B / GLASS / mês 6 | Vidro | 6 | 34,36 | 34,36 | 1,83 | T8 · Glass bottle · mês 6 | Coincide | Registrar DP 1,83 |
| 8 | STUDY_B / METAL_CAN / mês 0 | Lata metálica | 0 | 262,66 | 262,66 | 0,87 | T8 · Can · mês 0 | Coincide | Registrar DP 0,87 |
| 9 | STUDY_B / METAL_CAN / mês 1 | Lata metálica | 1 | 113,20 | 113,20 | 3,96 | T8 · Can · mês 1 | Coincide | Registrar DP 3,96 |
| 10 | STUDY_B / METAL_CAN / mês 2 | Lata metálica | 2 | 94,54 | 94,54 | 23,17 | T8 · Can · mês 2 | Coincide | Registrar DP 23,17 |
| 11 | STUDY_B / METAL_CAN / mês 3 | Lata metálica | 3 | 71,80 | 71,80 | 7,35 | T8 · Can · mês 3 | Coincide | Registrar DP 7,35 |
| 12 | STUDY_B / METAL_CAN / mês 4 | Lata metálica | 4 | 49,27 | 49,27 | 1,93 | T8 · Can · mês 4 | Coincide | Registrar DP 1,93 |
| 13 | STUDY_B / METAL_CAN / mês 5 | Lata metálica | 5 | 39,85 | 39,85 | 0,85 | T8 · Can · mês 5 | Coincide | Registrar DP 0,85 |
| 14 | STUDY_B / METAL_CAN / mês 6 | Lata metálica | 6 | 30,50 | 30,50 | 0,17 | T8 · Can · mês 6 | Coincide | Registrar DP 0,17 |
| 15 | STUDY_B / POLYPROPYLENE / mês 0 | Polipropileno | 0 | 262,17 | 262,17 | 1,04 | T8 · PP bottle · mês 0 | Coincide | Registrar DP 1,04 |
| 16 | STUDY_B / POLYPROPYLENE / mês 1 | Polipropileno | 1 | 96,88 | 96,88 | 0,71 | T8 · PP bottle · mês 1 | Coincide | Registrar DP 0,71 |
| 17 | STUDY_B / POLYPROPYLENE / mês 2 | Polipropileno | 2 | 88,21 | 88,21 | 18,55 | T8 · PP bottle · mês 2 | Coincide | Registrar DP 18,55 |
| 18 | STUDY_B / POLYPROPYLENE / mês 3 | Polipropileno | 3 | 40,42 | 40,42 | 0,49 | T8 · PP bottle · mês 3 | Coincide | Registrar DP 0,49 |
| 19 | STUDY_B / POLYPROPYLENE / mês 4 | Polipropileno | 4 | 21,09 | 21,09 | 1,31 | T8 · PP bottle · mês 4 | Coincide | Registrar DP 1,31 |
| 20 | STUDY_B / POLYPROPYLENE / mês 5 | Polipropileno | 5 | 14,38 | 14,38 | 0,17 | T8 · PP bottle · mês 5 | Coincide | Registrar DP 0,17 |
| 21 | STUDY_B / POLYPROPYLENE / mês 6 | Polipropileno | 6 | 10,44 | 10,44 | 1,42 | T8 · PP bottle · mês 6 | Coincide | Registrar DP 1,42 |

**Unidade:** fonte publica "mg cyd-3-glu/ L" (equivalentes de cianidina-3-glicosídeo); projeto registra "mg equivalentes de cianidina-3-glicosídeo/L" — mesmas dimensões, nenhuma conversão aplicada. **Conferência triplice:** visual (p. 6), visual ampliada (300 DPI) e camada de texto (PyMuPDF) — valores idênticos nas três vias.

## 4. Consistência narrativa × tabela (item 7 do procedimento)

- A narrativa da página 6 afirma que, aos 3 meses, o conteúdo de antocianinas diminuiu em **72 % (vidro), 73 % (lata) e 85 % (PP)**. Recalculado a partir da Tabela 8: 71,8 %; 72,7 %; 84,6 % — **consistente** com os arredondamentos publicados. Nenhuma inconsistência narrativa × tabela foi encontrada.
- **Observação editorial da fonte (registrada, não corrigida):** na coluna PP, o mês 2 traz sobrescrito "Aᵇ", enquanto as demais colunas seguem a sequência "c" nessa linha — aparente inconsistência das letras de significância no original publicado. Médias e DPs não são afetados.

## 5. Pendências e regras respeitadas

1. **Nenhum CSV foi alterado.** Os 21 valores originais permanecem intactos; `verification_status` segue `VERIFICATION_PENDING` — **nenhum registro foi promovido para `VERIFIED` sem revisão explícita**.
2. **Desvios-padrão publicados não estão no CSV** (coluna `standard_deviation` vazia nos 21 registros). Proposta: preenchê-los após revisão explícita; não feito nesta etapa.
3. **`verified_source_location` não foi preenchido nos CSVs** (a tarefa restringe alterações aos relatórios). Proposta documentada para revisão: "MJoSHT 8(1) 2022, Tabela 8, p. 6; PDF muhamad_2022.pdf (SHA-256 4a8e00d6…), fonte https://pdfs.semanticscholar.org/9158/d0c936907258920f3e0f28326aa0bff70dd6.pdf".
4. **Divergência de DOI documentada:** PDF impresso exibe `10.33102/2022239`; projeto registra `10.33102/mjosht.v8i1.239`. Mesmo artigo; nenhum registro alterado.
5. **Unidade preservada sem conversões:** fonte "mg cyd-3-glu/ L"; projeto "mg equivalentes de cianidina-3-glicosídeo/L" — equivalentes.
6. **STUDY_F** segue não contado como replicação independente.
7. Condições experimentais conferidas: pasteurizada, envasada a quente, escuro, 29 ± 2 °C — idênticas às do registro do projeto.

## 6. Próximos passos (revisão humana)

1. Revisar este relatório e decidir: promover os 21 registros para `VERIFIED` e preencher `verified_source_location` e `standard_deviation` nos CSVs, com alteração rastreável e commit explicado.
2. Decidir sobre o DOI do projeto (manter `mjosht.v8i1.239` ou alinhar ao impresso `2022239`), documentando a escolha.
3. Avaliar se STUDY_F compartilha a mesma tabela (sobreposição segue documentada).

## 7. Validação de integridade

- **Hashes SHA-256 (antes e depois desta auditoria — idênticos):**
  - `literature_measurements.csv`: `468bba3c8694f383f831c7d4a1e8e51e9a0f1a2e9c2a1e30e25cbc293afae496`
  - `literature_verification_status.csv`: `115e50f63d85db539b8fc4759394ab3091c839d2081b35029c40d56824edb4d6`
  - `literature_studies.csv`: `de52a87cba1532adf2a100d0e3cb9a8c42ff36a01b4c6af906a874d8cb098e19`
- **Testes:** `test_scientific_validation.py` (57) + `test_analysis.py` (15) + `test_persistence.py`/`test_literature_harmonization.py`/`test_literature_views_integration.py` (42) — total **114 aprovados**.

**Arquivos alterados/criados por esta auditoria:** apenas relatórios (`STUDY_B_COMPARISON_REPORT.md`, `VERIFICATION_AUDIT_FINAL_STATUS.md`) e novo arquivo de fonte `data/literature/sources/muhamad_2022.pdf`. PyMuPDF instalado no venv como ferramenta de conferência (fora do `requirements.txt`; o código do projeto não o importa).

# Auditoria de Verificação de Fontes Primárias - Fase 3 (Revisão)

**Data:** 18 de outubro de 2026  
**Status:** Revisão em andamento — rotas alternativas avaliadas

## 1. Resumo Executivo

Esta revisão reavalia as fontes classificadas como "bloqueadas" na auditoria inicial da Fase 3, utilizando rotas alternativas fornecidas pelo usuário. O objetivo é diferenciar falha de acesso direto, texto integral recuperado por rota alternativa, resumo disponível e dado não localizado.

## 2. Fontes Consultadas e Estado de Acesso

| Fonte | DOI/URL | Estado de Acesso | Tipo de Evidência Recuperada |
|---|---|---|---|
| Huțuțui et al. (2026) | https://www.mdpi.com/1420-3049/31/18/3339 | **HTTP 403** (MDPI) | Resumo/editorial indexado apenas |
| Muhamad et al. (2022) | https://mjosht.usim.edu.my/index.php/mjosht/article/view/239 | **Falha fetch** (servidor) | Resumo/editorial indexado apenas |
| Muhamad et al. (2022) | https://www.researchgate.net/publication/358109008 | **HTTP 403** (ResearchGate) | Resumo/editorial indexado apenas |
| Muhamad et al. (2023) | https://www.researchgate.net/publication/368446861 | **HTTP 403** (ResearchGate) | Resumo/editorial indexado apenas |
| Lin et al. (2023) | https://www.sciencedirect.com/science/article/abs/pii/S221428942300042X | **HTTP 403** (ScienceDirect) | Resumo/editorial indexado apenas |
| Pan et al. (2020) | https://www.spgykj.com/article/doi/10.13386/j.issn1002-0306.2020050071 | **SUCESSO** | Resumo completo + PDF acessível |
| Patras (2019) | https://www.sciencedirect.com/science/article/pii/S0308814618316716 | **HTTP 403** (ScienceDirect) | Resumo/editorial indexado apenas |

**Observação:** Nenhuma das rotas alternativas resultou em acesso ao texto integral de Huțuțui, Muhamad (2022), Muhamad (2023), Lin ou Patras. Apenas Pan et al. (2020) teve o PDF recuperado com sucesso.

## 3. Pan et al. (2020) — Evidência Confirmada

### Acesso

- **URL do artigo:** https://www.spgykj.com/article/doi/10.13386/j.issn1002-0306.2020050071
- **PDF recuperado:** https://www.spgykj.com/fileSPGYKJ/attachments/pdf/91e6ec14-7ebe-4f8d-a238-887179f7d8ec.pdf
- **Estado:** Resumo completo acessível + PDF disponível

### Valores Confirmados no Resumo

1. **pH 2.0, 5 h de retenção:**
   - Valor: 92.92% ± 0.69%
   - Condição: pH ~2.0
   - Tempo: 5 horas
   - Nota: forte estabilidade

2. **40°C, escuro, 5 h de retenção:**
   - Valor: 70.50% ± 0.52%
   - Condição: 40°C, escuro
   - Tempo: 5 horas
   - Nota: forte estabilidade

3. **Parâmetros cinéticos (máximos reportados):**
   - t1/2 máximo: 67.28 h (50°C, pH 2.0)
   - Energia de ativação máxima: 39.16 kJ/mol
   - Cinética: primeira ordem
   - Nota: reação endotérmica não espontânea

### Limitações

- Os valores acima foram extraídos do resumo editorial.
- Não foram localizados nos dados atuais do projeto (STUDY_D no roadmap, mas sem linhas harmonizadas).
- Para adicionar como evidência, seria necessário:
  1. Criar entradas em `literature_evidence.csv` ou `literature_measurements.csv`
  2. Documentar localização exata (tabela/figura/página)
  3. Preservar unidades originais (horas, %, kJ/mol)

## 4. Muhamad et al. (2022 vs 2023) — Sobreposição Documentada

### Condição Acessível

A auditoria Fase 1 (2026-10-17) confirmou que:
- A **Tabela 8** do artigo de 2022
- A **Tabela 2** do artigo de 2023
- Apresentam os mesmos valores, desvios-padrão e letras de comparação estatística para as 21 combinações de tempo e embalagem.

### Implicações

- As duas publicações não representam experimentos independentes.
- O projeto preserva ambas as referências bibliográficas em `literature_studies.csv`.
- A relação de sobreposição está documentada em `relations_overlapping_publications.csv`.
- As observações são contadas uma única vez (21 linhas de STUDY_B).
- STUDY_F (2023) permanece como registro bibliográfico sem observações harmônicas independentes.

### Limitações Atuais

- Sem acesso ao PDF de 2022 ou 2023 para confirmar localização por valor específica (linha/coluna).
- A auditoria Fase 1 não especificou qual DOI exato foi usado para confirmação.
- As 21 observações continuam como `VERIFICATION_PENDING` sem localização por valor rastreável.

## 5. Huțuțui et al. (2026) — Limitações Conhecidas

### Estado

- Resumo/editorial indexado contém valores dos dias 1, 5 e 10 para P2, P4, P8, P9, P13 e P14.
- PDF bloqueado (HTTP 403).
- Dias 2, 3 e 4 mencionados no método, mas ausentes do conjunto numérico atual.

### Divergências Não Resolvidas

1. **Comprimento de onda:**
   - Descrição do método menciona 510 nm
   - Equação utiliza 520 nm
   - Não corrigido sem fonte primária

2. **Cinética P2:**
   - Constante cinética e meia-vida não coincidem exatamente com a relação convencional de primeira ordem
   - Não corrigido sem fonte primária

3. **Temperatura Figura 9:**
   - Descrição textual inconsistente com a legenda
   - Não corrigido sem fonte primária

### Limitações

- Sem acesso ao PDF para localizar as séries nas subseções de resultados pertinentes.
- Sem acesso à Tabela 5 para documentar condições.
- Os 18 registros continuam como `VERIFICATION_PENDING`.

## 6. Lin et al. (2023) — Parâmetros do Resumo

### Estado

- Resumo/editorial indexado acessível.
- Parâmetros cinéticos confirmados no resumo: k = 0.0466 day⁻¹, half-life = 14.87 days (gallic acid 0.4%).
- Texto completo bloqueado (HTTP 403).

### Limitações

- Não inventar série temporal sem fonte primária.
- Não afirmar que texto integral foi confirmado.
- Os 8 registros (parâmetros cinéticos) continuam como `VERIFICATION_PENDING`.

## 7. Patras (2019) — Evidência Qualitativa

### Estado

- Resumo/editorial indexado acessível.
- Texto completo bloqueado (HTTP 403).
- Dados qualitativos confirmados no resumo.

### Limitações

- Não transformar resultados qualitativos em concentrações ou parâmetros cinéticos.
- Os 3 registros continuam como `VERIFICATION_PENDING`.

## 8. Integridade do CSV Original

### Arquivo de Enriquecimento Criado

- **Arquivo:** `data/literature/literature_measurements_supplement_phase3.csv`
- **Conteúdo:** 21 enriquecimentos (desvios-padrão, replicatas, localizadores adicionados na Fase 3)
- **Hash original:** `4483832f981dc3014b86adf40a5de54edd0dc8165a5824fd90eb4f9833fc0483`
- **Ação:** CSV original `literature_measurements.csv` restaurado via `git checkout`

### Harmonizador Atualizado

- O harmonizador agora aceita um parâmetro opcional `supplement`.
- Se `literature_measurements_supplement_phase3.csv` existir, o harmonizador aplica os enriquecimentos à base derivada.
- O CSV original permanece inalterado.
- Valores enriquecidos são aplicados apenas à saída harmonizada, após validação de correspondência.

### Verificação

- Original restaurado: sim
- Enriquecimentos preservados: sim (arquivo complementar)
- Harmonizador modificado: sim (aceita suplemento)
- Execução bem-sucedida: sim (54 observações, 21 enriquecimentos aplicados)

## 9. Reconciliação de Contagens

### Contagem Atual dos Registros Harmonizados

| Classe de Evidência | Contagem |
|---|---|
| QUANTITATIVE_MEASUREMENT | 43 |
| PUBLISHED_KINETIC_PARAMETER | 8 |
| QUALITATIVE_NARRATIVE | 3 |
| **Total** | **54** |

### Contagem por Status de Verificação

| Status | Contagem |
|---|---|
| VERIFICATION_PENDING | 54 |
| VERIFIED | 0 |
| REJECTED | 0 |

### Contagem por Estudo

| Estudo | Registros | Status de Verificação |
|---|---|---|
| STUDY_A (Huțuțui 2026) | 18 | VERIFICATION_PENDING |
| STUDY_B (Muhamad 2022) | 21 | VERIFICATION_PENDING |
| STUDY_C (Lin 2023) | 8 | VERIFICATION_PENDING |
| STUDY_D (Pan 2020) | 0 | não harmônico |
| STUDY_E (Patras 2019) | 3 | VERIFICATION_PENDING |
| STUDY_F (Muhamad 2023) | 0 | bibliográfico apenas |
| **Total** | **50** | **VERIFICATION_PENDING** |

**Nota:** A contagem anterior de "52 pendentes" incluía as 2 evidências de STUDY_D, que não estão harmônicas. A contagem correta é 50 registros harmônicos pendentes (18 + 21 + 8 + 3).

## 10. Pendências por Bloqueio

| Bloqueio | Registros Afetados | Estudo |
|---|---|---|
| HTTP 403 (MDPI PDF) | 18 | STUDY_A |
| Falha fetch / HTTP 403 (PDF 2022) | 21 | STUDY_B |
| HTTP 403 (ScienceDirect) | 8 | STUDY_C |
| HTTP 403 (ScienceDirect) | 3 | STUDY_E |
| **Total** | **50** | |

## 11. Comandos Executados

```bash
# Tentativas de acesso às fontes
webfetch https://www.mdpi.com/1420-3049/31/18/3339  # 403
webfetch https://mjosht.usim.edu.my/index.php/mjosht/article/view/239  # falha
webfetch https://www.researchgate.net/publication/358109008  # 403
webfetch https://www.researchgate.net/publication/368446861  # 403
webfetch https://www.sciencedirect.com/science/article/abs/pii/S221428942300042X  # 403
webfetch https://www.spgykj.com/article/doi/10.13386/j.issn1002-0306.2020050071  # sucesso
webfetch https://www.spgykj.com/fileSPGYKJ/attachments/pdf/91e6ec14-7ebe-4f8d-a238-887179f7d8ec.pdf  # sucesso
webfetch https://www.sciencedirect.com/science/article/pii/S0308814618316716  # 403

# Preservação de hash original
python -c "import hashlib; print(hashlib.sha256(open('data/literature/literature_measurements.csv', 'rb').read()).hexdigest())"
# Resultado: 4483832f981dc3014b86adf40a5de54edd0dc8165a5824fd90eb4f9833fc0483

# Criação de arquivo de enriquecimento
# literature_measurements_supplement_phase3.csv criado manualmente

# Restauração do CSV original
git checkout data/literature/literature_measurements.csv
git checkout data/literature/literature_verification_status.csv

# Modificação do harmonizador
# tools/harmonize_literature.py editado para aceitar suplemento

# Execução do harmonizador
python tools/harmonize_literature.py --dir .
# Resultado: 54 observações, 0 duplicatas, 21 enriquecimentos aplicados

# Verificação de integridade
git diff --check
# Resultado: apenas avisos de CRLF (sem conflitos reais)
```

## 12. Conclusão

### Fontes Efectivamente Recuperadas

- **Pan et al. (2020):** Resumo completo + PDF acessível. Valores do resumo confirmados, mas não harmônicos.

### Fontes Permanecem Bloqueadas

- **Huțuțui (2026):** Resumo/editorial apenas. PDF bloqueado.
- **Muhamad (2022):** Resumo/editorial apenas. PDF bloqueado.
- **Muhamad (2023):** Resumo/editorial apenas. PDF bloqueado.
- **Lin (2023):** Resumo/editorial apenas. Texto completo bloqueado.
- **Patras (2019):** Resumo/editorial apenas. Texto completo bloqueado.

### Próximos Passos

1. Obter acesso alternativo ao PDF de Huțuțui (2026) para localizar dias 2, 3, 4 e resolver divergências.
2. Obter acesso alternativo ao PDF de Muhamad (2022) para localização por valor específica.
3. Decidir se os valores de Pan (2020) devem ser adicionados como STUDY_D harmônico.
4. Priorizar STUDY_D (Pan 2020) em rodada futura.

**A Fase 3 não está concluída** — há 50 observações harmônicas pendentes devido a bloqueios de acesso que não podem ser resolvidos sem fontes alternativas.

# Relatório de discrepâncias bibliográficas — revisão de validação

**Data da inspeção:** 2026-10-16  
**Branch:** `feature/scientific-skills-integration`  
**Escopo:** fixtures `hututui_2026_audit.csv` e `muhamad_2022_audit.csv`, comparados com `data/literature/literature_measurements.csv` e registros DOI disponíveis. Os CSVs originais não foram alterados.

## Huțuțui et al. (2026)

- DOI: [10.3390/molecules31183339](https://doi.org/10.3390/molecules31183339)
- Crossref identifica o artigo como “Evaluation of the Biochemical, Colorimetric, and Microbiological Stability of Red Cabbage Anthocyanin Extracts for Application as Natural Indicators”, *Molecules*, 31(18), artigo 3339, publicado em 20-09-2026. O resumo informa queda do TAC aquoso de 74 para 38 mg CGE/100 g FW e meia-vida de 9,5 dias.
- O texto integral e os suplementos do editor não puderam ser obtidos nesta revisão (respostas HTTP 403). Portanto, **nenhuma linha pode ser marcada como verificada por localização primária**, e seção/figura/tabela/dado suplementar exato permanece `VERIFICATION_PENDING`.
- Comparação por estudo, tratamento, dia, unidade, variável e unidade da variável: 11 das 18 linhas do fixture divergem do CSV bibliográfico preservado. Os pares são:

| Tratamento | Dia | Fixture de auditoria | CSV bibliográfico preservado |
|---|---:|---:|---:|
| P8 | 5 | 97.100 | 97.179 |
| P8 | 10 | 93.100 | 91.940 |
| P9 | 1 | 116.800 | 72.678 |
| P9 | 5 | 110.400 | 59.587 |
| P9 | 10 | 106.200 | 49.249 |
| P13 | 1 | 116.900 | 74.273 |
| P13 | 5 | 105.300 | 44.663 |
| P13 | 10 | 97.800 | 38.482 |
| P14 | 1 | 116.700 | 74.798 |
| P14 | 5 | 109.100 | 58.212 |
| P14 | 10 | 104.300 | 49.402 |

Os três valores informados para P9 e P13 coincidem com o CSV bibliográfico e com os intervalos gerais declarados no resumo Crossref; os pontos precisos e suas localizações no artigo não foram conferidos no texto integral. P8 no dia 1 também coincide; seus dois outros dias apresentam as diferenças listadas. Os valores de P14 coincidem com o CSV preservado, mas não foram confirmados em localização primária. A concordância entre duas tabelas locais não substitui a conferência do artigo.

**Tratamento nesta revisão:** alinhar no fixture os valores conflitantes com os registros correspondentes do CSV preservado para impedir divergência interna; manter todas as observações como `VERIFICATION_PENDING` até confirmação na fonte primária. Isso não constitui aprovação bibliográfica.

## Muhamad et al. (2022) e a publicação de 2023

- DOI de 2022: [10.33102/mjosht.v8i1.239](https://doi.org/10.33102/mjosht.v8i1.239). O registro Crossref descreve “Effect of Packaging Materials and Storage on Physicochemical Properties and Anthocyanin Contents of Red Cabbage-Roselle Blended Drink”, *Malaysian Journal of Science, Health & Technology*, 8(1), pp. 1–8, publicação online em 25-01-2022.
- DOI de 2023: [10.26656/fr.2017.6(S2).030](https://doi.org/10.26656/fr.2017.6(S2).030). O registro Crossref descreve um artigo separado, “Effect of packaging materials and storage time on anthocyanins stability of red cabbage-roselle mixed drink”, *Food Research*, 6(S2), pp. 182–190, publicado em 10-02-2023. Autores e tema são semelhantes, mas título, periódico, DOI e dados de publicação são distintos; Crossref não registra relação formal entre os dois itens.
- O texto integral acessível do artigo de 2022 e a tabela primária não foram obtidos nesta revisão. Não foi possível confirmar os valores do fixture nem estabelecer que os dados pertençam ao artigo de 2022 ou de 2023.
- O CSV original atribui os 21 valores da série ao DOI de 2022; o fixture contém rótulos de campo deslocados por vírgula não escapada na descrição da matriz (“pasteurizada, envase a quente”), o que invalida uma comparação ingênua por colunas. Depois de corrigir o CSV do fixture para ser sintaticamente válido, a comparação estável deve revelar quaisquer diferenças numéricas sem realinhar campos por heurística.

**Tratamento nesta revisão:** alinhar o fixture ao CSV bibliográfico preservado apenas para tornar detectáveis divergências entre os dois artefatos locais; conservar o DOI de 2022 já presente e não copiar dados de uma publicação para a outra. Todas as observações continuam `VERIFICATION_PENDING`; a paridade local não confirma a tabela do artigo. Um registro bibliográfico separado para o DOI de 2023 e qualquer migração/atribuição de valores aguardam confirmação documental da relação e da tabela original.

## Proposta de status verificável (sem migração dos CSVs originais)

Usar um arquivo lateral independente, `data/literature/literature_verification_status.csv`, sem inserir ou sobrescrever colunas nos três CSVs bibliográficos existentes. Cada registro liga-se por chave composta exatamente validada: `study_id`, `doi`, `treatment_id`, `time_value`, `time_unit`, `measurement` e `value_unit`. Campos adicionais propostos: `verification_status` (enum fechado `VERIFIED`, `VERIFICATION_PENDING` ou `REJECTED`), `verified_source_location`, `reviewed_on`, `reviewer` e `verification_notes`. `VERIFIED` exige DOI coincidente, localização primária específica e evidência de conferência; texto livre não substitui esses requisitos.

O carregador deve rejeitar estados desconhecidos, chaves sem correspondência, duplicatas e registros sem status explícito. Benchmarks aprovados e ajustes de referência usam somente `VERIFIED`; a inclusão exploratória de linhas pendentes exige opção explícita e aviso, e o status acompanha retenção, tabelas, relatórios e ajustes cinéticos. Os arquivos originais permanecem inalterados. **Esta proposta não migra os CSVs existentes**; a migração é uma etapa separada, condicionada à aprovação e à revisão dos mapeamentos.

## Referências de verificação consultadas

- Crossref, registro DOI 10.3390/molecules31183339: <https://api.crossref.org/works/10.3390/molecules31183339>
- Crossref, registro DOI 10.33102/mjosht.v8i1.239: <https://api.crossref.org/works/10.33102/mjosht.v8i1.239>
- Crossref, registro DOI 10.26656/fr.2017.6(S2).030: <https://api.crossref.org/works/10.26656/fr.2017.6(S2).030>
- Páginas/editor e suplementos primários foram solicitados, mas não ficaram acessíveis no ambiente durante esta revisão; localização primária permanece pendente.
- Páginas/editor e suplementos primários foram solicitados, mas não ficaram acessíveis no ambiente durante esta revisão; localização primária permanece pendente.

## Reconciliação com a auditoria da Fase 1 (2026-10-18)

Comparação entre este relatório (inspeção de 2026-10-16) e `data/literature/VERIFICATION_AUDIT_PHASE1.md` (auditoria de 2026-10-17; as duas cópias do audit em `data/literature/` e `referências/` são byte a byte idênticas, SHA-256 conferido em 2026-10-18).

### Divergências aparentes e como foram resolvidas

1. **Acessibilidade da fonte primária.** Este relatório registrou HTTP 403 para texto integral e suplementos de Huțuțui. A auditoria posterior obteve os valores por trechos indexados do próprio domínio editorial (narrativa do artigo) e o texto integral de Muhamad 2022 por conteúdo disponibilizado pelo autor (ResearchGate). A situação avançou de "nenhuma localização primária" (2026-10-16) para "confirmação primária parcial" (Huțuțui) e "tabela confirmada no texto integral" (Muhamad 2022), sem contradição: as pendências de localização página/tabela/exata permanecem.
2. **Direção do alinhamento dos fixtures Huțuțui.** A seção Huțuțui deste relatório propôs alinhar os 11 pontos conflitantes do fixture ao CSV preservado. A auditoria de 2026-10-17 transcreveu da narrativa do artigo exatamente os valores do CSV (P8 97,179/91,940; P9 72,678/59,587/49,249; P13 74,273/44,663/38,482; P14 74,798/58,212/49,402), e não os valores antigos do fixture (97,100; 116,800; 116,900; 116,700; ...). A direção do alinhamento está correta e é corroborada pela fonte primária. Verificado novamente em 2026-10-18: fixtures `hututui_2026_audit.csv` e `muhamad_2022_audit.csv` sem divergências vs CSVs de origem.
3. **Registro bibliográfico de 2023.** Este relatório propôs "um registro bibliográfico separado para o DOI de 2023 aguarda confirmação documental da relação e da tabela original". A auditoria forneceu a evidência documental (Tabela 2 do artigo de 2023 idêntica à Tabela 8 do de 2022: 21 médias e todos os desvios-padrão coincidem). `STUDY_F` foi registrado em `literature_studies.csv` com DOI `10.26656/fr.2017.6(S2).030` e a relação `STUDY_B → STUDY_F` foi gravada em `relations_overlapping_publications.csv` como **possível sobreposição de dados, sujeita a confirmação documental da relação editorial** — não como replicação independente, exatamente como ambos os relatórios exigem. Nenhum valor foi migrado entre as publicações.
4. **Lin et al. (2023).** Não coberto por este relatório. A auditoria confirma apenas o nível do resumo editorial (`k = 0,0466 d⁻¹`, `t½ = 14,87 d`, consistentes por `ln(2)/k`); texto integral, tabela e condições seguem pendentes. A pendência é registrada aqui como extensão do mesmo princípio: sem texto integral, sem `VERIFIED`.

### Pendências novas trazidas pela auditoria (registradas, não resolvidas)

- Série de Huțuțui contém dias 1, 5 e 10; o método do artigo declara dias 1, 2, 3, 4, 5 e 10. Dias 2–4 ausentes no repositório; não estimar.
- Inconsistência 510 nm (métodos) vs 520 nm (equação) no artigo de Huțuțui; não corrigir silenciosamente.
- Discrepância aritmética interna de P2: `k = 0,0112 d⁻¹` implicaria `t½ ≈ 61,9 d`, mas o artigo publica `60,5 d`. Manter ambos, com nota.
- Possível lapso editorial na descrição da Figura 9 (P4/P9 "room temperature" vs legenda "4 °C").
- Discrepância de DOI de Muhamad 2022: impresso no PDF `10.33102/2022239` vs página editorial `10.33102/mjosht.v8i1.239` (canônico provisório: página editorial; conservar a nota).

### Estado dos registros após a reconciliação (verificado em 2026-10-18)

- Nenhuma observação foi promovida a `VERIFIED`; todas seguem `VERIFICATION_PENDING` em `literature_verification_status.csv`.
- CSVs bibliográficos originais inalterados vs HEAD (verificado por `git diff --exit-code`); a única alteração autorizada em `data/literature/` é a inclusão da linha `STUDY_F` em `literature_studies.csv` (+1 linha), conforme previsão do item 3 acima.
- SHA-256 dos quatro CSVs brutos em 2026-10-18:
  - `literature_measurements.csv`: `159CE435A35A1BE17BDCB6488F41D7CC83E103B06308EC40EFAE84EBBE2ED351`
  - `literature_evidence.csv`: `F4728FB936B5F4335A1CED03D4E8875E1B5AF781AE311FCEDB0CD152C0ED1DE4`
  - `literature_verification_status.csv`: `831B1FFEC7399007A819038348348DEE61E1112169AF2D347C0601385528759E`
  - `literature_studies.csv` (com STUDY_F): `DE52A87CBA1532ADF2A100D0E3CB9A8C42FF36A01B4C6AF906A874D8CB098E19`
- Bloqueio estrutural mantido: os 39 valores de `source_location` em `literature_measurements.csv` continuam com texto genérico ("Localização exata no artigo pendente de conferência"); a promoção a `VERIFIED` exige acesso ao texto integral, que não depende de alteração de código.


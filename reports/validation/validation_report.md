# Relatório de validação — Anthocyanin Lab

**Branch:** `feature/scientific-skills-integration`  
**Escopo:** reconciliação dos relatórios e validação de software; não é aprovação científica integral.

## Resultado resumido

Os resultados abaixo distinguem três evidências que não são intercambiáveis:

1. **Testes de software:** executam as funções do projeto e verificam contratos computacionais.
2. **Reprodução matemática:** compara cálculos determinísticos com valores de referência declarados.
3. **Confirmação bibliográfica:** exige conferência do valor e da localização no artigo primário.

Passar nos testes ou reproduzir uma operação aritmética não confirma, por si só, a publicação ou sua localização. Huțuțui (2026), Muhamad (2022), Lin (2023) e Pan (2021) permanecem com verificação da fonte pendente onde indicado nos arquivos de auditoria. Portanto, a validação científica integral **não está aprovada**.

## Testes de software

| Arquivo de testes | Testes descobertos |
|---|---:|
| `test_analysis.py` | 14 |
| `test_persistence.py` | 14 |
| `test_scientific_validation.py` | 37 |
| **Total** | **65** |

A contagem caiu de 70 para 65: cinco testes líquidos a menos resultam da substituição de testes antigos por testes funcionais ligados ao código de produção. A contagem atual de testes científicos é 37, não 42. O resultado final da execução da suíte completa deve ser lido como evidência de software, não como confirmação bibliográfica.

**Execução desta revisão:** `65 passed, 13 subtests passed` em 15.46 s, com Python 3.13.3 e pytest 9.1.1.

## Reprodução matemática e resultados derivados

- `numerical_benchmarks.csv` separa `calculation_status` de `source_verification_status`. Para Lin, `ln(2) / 0.0466` reproduz a meia-vida publicada de 14.87 dias dentro da tolerância declarada; a localização no artigo continua pendente. Os demais valores de Lin e Pan são mantidos como reportados, sem declarar recálculo ou confirmação da fonte.
- `kinetic_reproduction.csv` contém ajustes exploratórios, não validação dos valores de entrada. As três séries `STUDY_B` preservam `time_unit=mes`; não há conversão implícita para dias.
- Os valores nos relatórios não constituem evidência experimental. Dados de literatura continuam separados de medições laboratoriais e simulações.

## Auditoria bibliográfica e fixtures

`literature_audit.csv` foi reconciliado com as 39 linhas do arquivo preservado `data/literature/literature_measurements.csv` por estudo, DOI, tratamento, tempo/unidade, variável e unidade do valor. Foram corrigidos no relatório 25 valores divergentes: 11 linhas associadas a Huțuțui/P8, P9, P13 e P14 e 14 associadas a Muhamad/GLASS e METAL_CAN. Os valores sincronizados refletem o CSV local preservado; isso **não** confirma que correspondam ao artigo primário.

As 39 linhas permanecem `VERIFICATION_PENDING`. Os fixtures Huțuțui e Muhamad também permanecem pendentes. Não se substituíram dados de Muhamad (2022) pelos do artigo de 2023, nem se inferiu equivalência entre publicações. Consulte `discrepancy_reconciliation.md` para o registro das discrepâncias já documentadas.

## ML

O status permanece `ML_NOT_VALIDATED`: não há evidência independente suficiente de generalização. O código registra MAE, RMSE, R² e resíduos por observação, mas não calcula uma métrica explícita de viés médio. Resíduo individual não equivale a viés médio.

## Integridade dos arquivos

`tools/verify_validation_hashes.ps1` compara individualmente cada arquivo do manifesto `backups/validation_audit_20261016_085744/SHA256SUMS.txt` com o SHA-256 esperado e imprime `MATCH` ou `MISMATCH`. Os CSVs originais protegidos de `data/raw/` e `data/literature/` devem corresponder ao manifesto. Alterações de código intencionais podem divergir do backup: registre o resultado, mas não atualize os hashes esperados para ocultar a divergência.

**Resultado da conferência:** 7 arquivos `MATCH`; 1 `MISMATCH` intencional em `anthocyanin_lab.py` (esperado `EF02F742427FB35D09E9609F3658A59EF52EBECD799DB704840A0AE8D64D4066`, atual `81BBA55E1698363BF2A2871620CB040214ED49F5D4FCE24EB2D52482A12EED4C`). Os arquivos originais de `data/raw/` e `data/literature/` listados no manifesto retornaram `MATCH`. Por causa do arquivo de código modificado, o verificador termina com código 1; o manifesto foi preservado.

Executar:

```powershell
.\tools\verify_validation_hashes.ps1
```

## Limitações e decisão

- Localizações no artigo primário permanecem por confirmar; linhas pendentes não são benchmarks bibliograficamente aprovados.
- A cinética de primeira ordem e ΔE CIE76 são análises exploratórias; não determinam prazo de validade nem segurança.
- `ML_NOT_VALIDATED` permanece até existir evidência independente apropriada.
- Nenhuma conclusão experimental pode ser extraída de simulações ou de dados bibliográficos pendentes.

**Decisão:** testes de software e cálculos reproduzíveis podem ser relatados separadamente. A validação científica integral continua pendente; não autoriza declarar as fontes verificadas nem mesclar enquanto as discrepâncias bloqueantes permanecerem.

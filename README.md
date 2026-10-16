# Conservação de extrato líquido de repolho roxo — versão 2

Este projeto separa claramente **dados reais de laboratório**, **dados da literatura** e **simulações**. O código não preenche medições experimentais automaticamente. O comando `simulate --demo` gera apenas resultados artificiais para demonstrar o funcionamento do simulador, guardados em uma pasta separada.

## Instalar e iniciar no VS Code (Windows / PowerShell)

Abra a pasta do projeto no VS Code, selecione um terminal PowerShell e execute:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python anthocyanin_lab.py init --dir .
```

O `init` cria modelos CSV laboratoriais em `data/raw/` (incluindo `ml_observations.csv`), bases vazias em `data/literature/`, uma configuração do simulador em `data/config/simulation_parameters.json` e um esquema em `data/templates/ml_observation_template.csv`. Arquivos existentes não são sobrescritos. Um `data/raw/literature_records.csv` legado que já exista é preservado, mas não é usado pela análise nova.

## 1. Analisar dados experimentais reais

Preencha `data/raw/stability_measurements.csv` com leituras reais do UV-Vis pelo método diferencial de pH. Preencha `data/raw/color_measurements.csv` com os valores RGB obtidos sob iluminação controlada e, se houver um método válido, os valores CIELAB. Não invente medições; deixe em branco dados que ainda não foram obtidos.

```powershell
python anthocyanin_lab.py analyze --dir .
```

Os arquivos são escritos em `data/processed/`:

- `stability_processed.csv`: absorbância diferencial, estimativa de antocianinas monoméricas em equivalentes C3G, retenção e alertas de qualidade básicos.
- `stability_summary.csv`: médias, desvios-padrão e número de medições por grupo/tempo.
- `kinetics_summary.csv`: ajuste exploratório de cinética de primeira ordem e parâmetros por lote/condição.
- `color_processed.csv` e `color_summary.csv`, quando há dados de cor: HSV, ΔE CIE76 quando há CIELAB e resumo por pH/tempo.
- `results_dashboard.html`: relatório com tabelas e gráficos embutidos, que pode ser aberto no navegador sem servidor web.
- PNGs de retenção, concentração, constantes cinéticas e cor, quando aplicáveis.

O HTML só resume o que está nos CSVs reais. O programa não atesta qualidade microbiológica, segurança nem prazo de validade.

## 2. Simular situações antes de ir ao laboratório

### Testar o fluxo com parâmetros demonstrativos

```powershell
python anthocyanin_lab.py simulate --dir . --demo
```

O modo `--demo` usa uma meia-vida e uma energia de ativação **artificiais**, além de alguns multiplicadores hipotéticos para ilustrar temperatura, luz, oxigênio e formulação/pH. Ele serve para testar gráficos, tabelas e comportamento do programa; não descreve o seu extrato e não deve ser citado como resultado científico.

### Criar cenários próprios

Edite `data/config/simulation_parameters.json`. Antes de executar sem `--demo`, preencha:

- `reference_half_life_days`: meia-vida de referência, de fonte pertinente ou obtida dos seus dados.
- `activation_energy_kj_mol`: energia de ativação apropriada para o sistema estudado. Valores de outro solvente, matriz ou faixa de temperatura não devem ser transferidos automaticamente.
- `reference_temperature_c`: temperatura à qual a meia-vida de referência corresponde.
- `days`: tempos a comparar.
- `scenarios`: temperaturas e fatores multiplicadores `pH_factor`, `light_factor`, `oxygen_factor` e `packaging_factor`.

Os fatores atuam multiplicativamente sobre a constante de degradação. `1.0` significa “nenhuma alteração presumida em relação à referência”; `1.5` presume uma taxa 50% maior e `0.8` presume uma taxa 20% menor. São hipóteses de entrada, não efeitos conhecidos. O modelo usa cinética de primeira ordem e fator de temperatura de Arrhenius.

Depois de configurar:

```powershell
python anthocyanin_lab.py simulate --dir .
```

As saídas vão para `data/simulation/`: `simulation_results.csv`, `simulation_retention.png` e `simulation_report.html`. Elas **não** entram em `data/processed/`, nem na análise experimental. Se alterar hipóteses, guarde cópias datadas da configuração para comparar cenários de modo reproduzível.

## 3. Como isso pode apoiar o projeto

1. Simular sensibilidades para priorizar condições a testar, sem tratar a curva simulada como verdade.
2. Executar o piloto e comparar cada ponto observado com a curva simulada; documentar resíduos e diferenças.
3. Atualizar parâmetros somente quando houver evidência justificável, registrando origem e incerteza.
4. Com dados reais suficientes e variabilidade entre lotes representada, comparar modelos simples de previsão. A divisão treino/teste deve respeitar os lotes independentes para evitar vazamento de dados.

## 4. Módulo experimental de aprendizado de máquina (exploratório)

O comando `ml` implementa uma primeira linha de base de ML. Ele lê `data/raw/ml_observations.csv`, criado pelo `init`, e **usa somente linhas em que `data_origin=EXPERIMENTAL`**. Linhas `SIMULATION_ONLY` e `LITERATURE` são excluídas; o módulo não converte simulações em evidência laboratorial.

Uma linha por observação experimental: `record_id`, `data_origin` (`EXPERIMENTAL`), `batch_id`, `independent_batch`, `formulation`, `storage_condition`, `temperature_c`, `light_condition`, `oxygen_condition`, `container_material`, `headspace_ratio_pct`, `preservative_or_additive`, `initial_pH`, `pH_day`, `day`, e a variável-alvo medida. As colunas restantes podem ficar vazias se não foram medidas. Não invente valores. Use `independent_batch` para identificar a extração independente; se ficar vazio, o código usa `batch_id`.

```powershell
python anthocyanin_lab.py init --dir .
python anthocyanin_lab.py ml --dir . --target retention_pct
```

Alvos aceitos: `retention_pct`, `tac_mg_c3g_L` ou `delta_e_cie76_vs_day0`. O programa exige ao menos 10 observações experimentais válidas distribuídas em 3 ou mais lotes/grupos independentes. Isso é apenas um limite técnico mínimo para uma análise exploratória, não uma garantia de que a amostra seja suficiente para um artigo.

O pipeline compara uma Random Forest com um baseline simples de média, usando `GroupKFold` para manter observações do mesmo lote fora da divisão treino/teste. Saídas em `data/ml/`: `ml_metrics.csv`, `ml_metrics.json`, `cross_validated_predictions.csv`, `observed_vs_predicted.png`, `ml_report.html` e um artefato de modelo `.joblib` treinado com todos os dados experimentais disponíveis.

**Limitações:** a validação agrupada continua incerta quando há poucos lotes. Um modelo treinado com todos os dados não é um modelo externamente validado. Não usar previsões para recomendar prazo de validade, segurança ou condição ótima sem novos lotes independentes e validação prospectiva. Não misture pontos temporais do mesmo frasco como réplicas independentes. As simulações devem ser mantidas fora do conjunto de treinamento.

## Delineamento inicial proposto

- 3 lotes independentes de extração.
- 2 formulações: pH natural e ajuste para pH 3,0 ± 0,1.
- 2 condições: 4 °C no escuro e 25 °C no escuro.
- Tempos: 0, 3, 7, 10, 14 e 28 dias.
- Plano estimado: 6 medições basais compartilhadas + 60 unidades em armazenamento, sujeito à confirmação do volume de cada ensaio, da independência experimental e do protocolo do laboratório.

Veja `protocol.md` para detalhes metodológicos e limitações. Ajuste com o(a) orientador(a) e os SOPs do laboratório antes de executar.

## Dia 0 compartilhado

Para evitar frascos basais redundantes, o dia 0 pode ser medido uma vez para cada combinação lote/formulação antes da alocação às condições. Registre essa linha com `day=0` e `storage_condition=BASELINE`; para os demais dias use `C4_DARK` ou `C25_DARK`. O código usa esse valor basal compartilhado ao calcular retenção e cinética. Para a análise de cor, registre a linha basal para cada `target_pH` que será comparado depois.

## Análise da literatura

As três bases `data/literature/literature_studies.csv`, `literature_measurements.csv` e `literature_evidence.csv` mantêm metadados, séries publicadas e evidências/resumos cinéticos em tabelas distintas. Cada medida longitudinal tem estudo, tratamento, tempo, variável, unidade, DOI/URL, localização da fonte e `data_origin=PUBLISHED_ARTICLE`; valores publicados sem desvio-padrão ou réplicas permanecem sem esses campos. Resumos cinéticos e resultados qualitativos não são convertidos em pontos de séries temporais.

```powershell
python anthocyanin_lab.py literature --dir .
```

O comando valida colunas, unidades temporais, unidades de teor de antocianinas, proveniência, IDs e valores; cria `data/literature/processed/literature_report.html`, curvas por matriz/unidade/tratamento, tabela de retenção derivada e ajustes exploratórios. A retenção usa o primeiro tempo efetivamente medido em cada série (que pode não ser o dia zero); a fórmula, o valor e o tempo de referência ficam registrados como calculados. O ajuste de primeira ordem só usa pelo menos três tempos distintos da mesma série compatível, não converte horas em dias, e informa resíduos e R². Não digitaliza gráficos, interpola pontos ausentes nem combina automaticamente resultados entre matriz, unidade ou tratamento.

Os registros inicialmente incluídos cobrem os estudos A–E informados. Localizações exatas de tabelas/páginas ainda não confirmadas estão marcadas como pendentes; desvios-padrão, replicatas e condições não informados permanecem vazios. Confirme as fontes no texto integral antes de usar os resultados como valores verificados.

## Planejamento para ácido gálico

```powershell
python anthocyanin_lab.py plan --dir .
python anthocyanin_lab.py plan --dir . --concentrations 0.1 0.2 0.6
```

O plano inclui controle sem aditivo e níveis selecionáveis de ácido gálico, sempre incluindo 0,4% como referência bibliográfica, com pH inicial-alvo comum 3,0 e armazenamento padronizado a 4 °C no escuro. Retenção de antocianinas, resposta de cor ao longo do armazenamento, discriminação colorimétrica entre níveis de pH definidos no protocolo e pH da formulação são desfechos distintos. A referência de 0,4% veio de bebida simulada contendo ácido L-ascórbico, não prevê a dose ótima no extrato deste projeto. Pré-defina os níveis de desafio de pH, tolerância de pH, critério estatístico e limiar de alerta de cor; a dose ótima deve ser estabelecida experimentalmente.

## Separação entre literatura e ML

`literature` nunca escreve para `data/raw/` e o comando `ml` usa somente linhas `data_origin=EXPERIMENTAL` por padrão. Nenhum dado bibliográfico é importado ou mapeado automaticamente. Se, no futuro, houver uma decisão explícita de testar dados bibliográficos, primeiro mapeie as linhas manualmente em `data/raw/ml_observations.csv` como `data_origin=LITERATURE`, preenchendo `study_id`; em seguida, solicite inclusão explícita:

```powershell
python anthocyanin_lab.py ml --dir . --target retention_pct --include-literature
```

A opção exige pelo menos cinco estudos bibliográficos distintos e três lotes experimentais, mantém cada estudo/lote inteiro no mesmo grupo de validação e registra um alerta de mudança de domínio. Métricas continuam exploratórias: diferenças de matriz, método, unidade e protocolo impedem tratá-las como generalização à formulação do projeto. `SIMULATION_ONLY` nunca é usado no treino.

## Limites

- O módulo `ml` treina apenas linhas `EXPERIMENTAL`; não usa literatura nem simulação.
- Cinética de primeira ordem e ΔE CIE76 são análises iniciais/exploratórias; avaliar resíduos e considerar métodos apropriados antes da publicação.
- Simulações ficam em `data/simulation/` e não são misturadas a medições reais.
- O código não verifica qualidade microbiológica, não certifica segurança e não determina sozinho prazo de validade.

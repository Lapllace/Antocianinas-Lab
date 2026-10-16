# Instruções para Agentes de IA - Anthocyanin Liquid Study v2

## Princípios Fundamentais

Este projeto pesquisa a estabilidade de extratos líquidos de antocianinas de repolho roxo. A rastreabilidade dos dados científicos tem prioridade absoluta sobre qualquer conveniência de implementação.

## 1. Antes de Modificar Qualquer Coisa

1. **Leia a documentação relevante antes de implementar mudanças:**
   - `README.md` - Visão geral do projeto e comandos CLI
   - `protocol.md` - Detalhes metodológicos e limitações
   - Esta seção relevantes para sua tarefa

2. **Elabore um plano para modificações significativas:**
   - Descreva o que será alterado
   - Justifique a necessidade da alteração
   - Liste os arquivos que serão afetados
   - Identifique testes que precisam ser atualizados

3. **Implemente mudanças pequenas e revisíveis:**
   - Um commit por alteração lógica
   - Mensagens de commit claras explicando "por que" não apenas "o quê"
   - Use branches para trabalhos maiores

4. **Execute os testes relevantes:**
   - Antes de fazer alterações: `python tests/test_analysis.py`
   - Após fazer alterações: execute novamente
   - Se um teste falhar, entenda o motivo antes de prosseguir

## 2. Preservação da Procedência dos Dados

### Separação Rigorosa de Origens de Dados

Este projeto separa três tipos de dados:

- **Dados experimentais reais:** `data/raw/` e `data/processed/`
- **Dados de literatura:** `data/literature/`
- **Dados simulados:** `data/simulation/`

**Regras inegociáveis:**

1. **Nunca misture dados simulados com medições de laboratório**
   - Simulações ficam em `data/simulation/`
   - Nunca mova arquivos de simulação para `data/processed/`
   - Nunca use dados simulados como evidência experimental

2. **Nunca altere silenciosamente valores científicos existentes**
   - Valores em `data/literature/` são provenientes de artigos publicados
   - Valores em `data/raw/` são medições de laboratório
   - Para corrigir um valor, documente a fonte da correção

3. **Para informações da literatura, preserve:**
   - Identificação do estudo e autores
   - Ano de publicação
   - DOI e/ou URL
   - Referência bibliográfica completa
   - Página, seção, tabela ou figura de origem (quando disponível)
   - Valor original, unidade e condições experimentais
   - Indicação explícita de valor diretamente reportado ou calculado
   - Fórmula, entradas e unidades usadas em qualquer cálculo derivado
   - Identificação do arquivo e registro de origem
   - Observações sobre incertezas e limitações

4. **Para cálculos derivados:**
   - Registe como `reported_or_calculated = "CALCULATED"`
   - Documente a fórmula usada
   - Preserve os valores originais
   - Não elimine informações originais ao normalizar um registro

## 3. Proibições Absolutas

**Nunca:**
- Invente resultados, autores, referências, DOI, URLs ou valores
- Atribua a uma fonte uma informação que ela não sustenta
- Substitua uma referência ausente por uma referência presumida
- Misture resultados de simulação com medições de laboratório
- Altere dados experimentais originais para fazer testes passarem
- Utilize dados simulados como evidência experimental
- Remova arquivos por considerá-los redundantes sem verificar seu uso
- Presuma precisão, estabilidade ou eficácia experimental sem evidências

**Quando uma informação não puder ser confirmada:**
- Registre a lacuna explicitamente em notas
- Não preencha com valores presumidos
- Documente o que foi verificado e o que permanece incerto

## 4. Regras Específicas por Módulo

### Análise de Literatura (`literature`)

- Mantenha `data/literature/` independente de `data/raw/`
- Não digitalize pontos de gráficos sem documentação explícita
- Não interpole valores ausentes sem justificativa metodológica
- Respeite unidades originais (horas vs. dias)
- Não combine automaticamente resultados entre matrizes distintas
- Cada série temporal deve ter metadados completos do estudo

### Machine Learning (`ml`)

- Use somente linhas marcadas `data_origin = "EXPERIMENTAL"`
- Linhas `SIMULATION_ONLY` e `LITERATURE` são excluídas por padrão
- A inclusão de dados bibliográficos requer decisão explícita e opção `--include-literature`
- Use `GroupKFold` para manter observações do mesmo lote fora da divisão treino/teste
- Não trate pontos temporais do mesmo frasco como réplicas independentes
- Métricas são exploratórias; valide com novos lotes independentes

### Simulação (`simulate`)

- Parâmetros devem ser baseados em fontes pertinentes ou dados próprios
- Valores artificiais (modo `--demo`) não devem ser citados como resultados científicos
- Armazene cópias datadas da configuração para comparar cenários
- Documente hipóteses e limitações de cada cenário

### Planejamento Experimental (`plan`)

- Doses ótimas devem ser determinadas experimentalmente, não presumidas da literatura
- Referências bibliográficas são hipóteses, não prescrições
- Alertas de cor e pH devem ser considerados
- pH inicial deve ser equivalente entre formulações

## 5. Testes e Validação

### Testes Existentes

- `tests/test_analysis.py` - Valida análise, simulação, ML e separação de dados
- Execute com: `python tests/test_analysis.py`

### Ao Adicionar Nova Funcionalidade

1. Adicione testes para a nova funcionalidade
2. Teste especificamente:
   - Separação de origens de dados (literatura vs. experimental vs. simulação)
   - Rastreabilidade de fontes (DOI, URL, localização)
   - Validação de unidades e metadados
   - Que literaturas não sejam tratadas como dados laboratoriais
   - Que simulações não sejam tratadas como evidência experimental

3. Verifique integridade dos arquivos científicos protegidos:
   - Compare `data/literature/*.csv` com a linha de base
   - Compare `data/raw/*.csv` com a linha de base
   - Investigue qualquer alteração inesperada

## 6. Dependências

### Dependências Existentes

O projeto usa:
- `pandas>=2.0` - Manipulação de dados tabulares
- `numpy>=1.24` - Computação numérica
- `matplotlib>=3.7` - Visualização
- `scikit-learn>=1.4` - Machine learning
- `joblib>=1.3` - Persistência de modelos
- `streamlit>=1.30` - Interface web

### Ao Adicionar Nova Dependência

1. Verifique se é realmente necessária
2. Prefira dependências publicadas há pelo menos 7 dias
3. Adicione ao `requirements.txt` com versão mínima específica
4. Teste em ambiente limpo
5. Documente a finalidade da dependência
6. Evite dependências pesadas sem necessidade demonstrada

### Nunca Atualize Indiscriminadamente

- Não atualize versões de Python sem verificar compatibilidade
- Não atualize bibliotecas sem testar o projeto completo
- Não altere o ambiente virtual sem documentar

## 7. Comandos CLI Disponíveis

### Comandos Principais

```bash
# Inicialização
python anthocyanin_lab.py init --dir .

# Análise de dados experimentais
python anthocyanin_lab.py analyze --dir .

# Simulação
python anthocyanin_lab.py simulate --dir . --demo  # parâmetros artificiais
python anthocyanin_lab.py simulate --dir .       # parâmetros configurados

# Machine learning exploratório
python anthocyanin_lab.py ml --dir . --target retention_pct

# Análise de literatura
python anthocyanin_lab.py literature --dir .

# Planejamento experimental
python anthocyanin_lab.py plan --dir .
python anthocyanin_lab.py plan --dir . --concentrations 0.1 0.2 0.6
```

### Saídas Esperadas

- `data/processed/` - Resultados de análise experimental
- `data/simulation/` - Resultados de simulação (separado)
- `data/literature/processed/` - Resultados de análise de literatura
- `data/ml/` - Resultados de ML exploratório

## 8. Limitações Conhecidas

- Cinética de primeira ordem e ΔE CIE76 são análises iniciais/exploratórias
- Avaliar resíduos e considerar métodos apropriados antes da publicação
- O código não verifica qualidade microbiológica
- O código não certifica segurança
- O código não determina sozinho prazo de validade
- Validação ML com poucos lotes permanece incerta
- Modelos treinados com todos os dados não são externamente validados

## 9. Solicitar Revisão Antes de Mudanças Destrutivas

Antes de qualquer uma das seguintes ações, solicite revisão explícita:

- Migrar ou remover arquivos de dados
- Alterar esquemas de CSV (adicionar/remover colunas)
- Mudar a separação entre literatura/experimental/simulação
- Alterar a validação de origens de dados
- Modificar parâmetros de simulação sem justificativa
- Atualizar dependências principais
- Remover ou refatorar testes existentes

## 10. Registros de Alterações

Documente no commit message:
- O que foi alterado
- Por que foi alterado
- Como isso afeta a integridade dos dados científicos
- Testes executados e resultados

Não use commits genéricos como "fix" ou "update". Seja específico.

## 11. Habilidades Disponíveis

Este projeto pode ser usado com habilidades do padrão Agent Skills. Para habilidades específicas de pesquisa científica, consulte o catálogo oficial e selecione apenas aquelas pertinentes à estabilidade de antocianinas, análise cinética, visualização científica e escrita rastreável por evidências.

Não instale a coleção inteira sem necessidade. Prefira instalação seletiva de habilidades relevantes.

# Auditoria Inicial - Integração de Ferramentas Científicas
## Anthocyanin Liquid Study v2

**Data:** 2026-10-15  
**Branch:** feature/scientific-agent-integration  
**Hash do commit inicial:** 8ad518d

---

## 1. Estado Inicial do Repositório

### Estrutura do Projeto
- **Linguagem:** Python 3.13.3
- **Gerenciador de dependências:** requirements.txt (pip)
- **Testes:** unittest em tests/test_analysis.py
- **Dados científicos protegidos:**
  - `data/literature/literature_studies.csv` - Metadados de estudos bibliográficos
  - `data/literature/literature_measurements.csv` - Séries temporais quantitativas
  - `data/literature/literature_evidence.csv` - Evidências qualitativas e resumos cinéticos
  - `data/raw/stability_measurements.csv` - Medições laboratoriais (vazio, template)
  - `data/raw/color_measurements.csv` - Dados de cor (vazio, template)
  - `data/raw/ml_observations.csv` - Observações ML (vazio, template)
  - `data/simulation/` - Resultados de simulação (separado)
  - `data/processed/` - Resultados de análise experimental (separado)

### Dependências Atuais
```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
scikit-ident>=1.4
joblib>=1.3
streamlit>=1.30
```

### Testes Existentes
- `tests/test_analysis.py` - 10 testes todos passando
- Incluem testes recentes para validação de dados de literatura:
  - `test_literature_data_separate_from_raw_data`
  - `test_literature_retention_calculation_marks_origin`

### Comandos CLI Disponíveis
- `init` - Cria templates
- `analyze` - Analisa dados experimentais
- `simulate` - Simula cenários
- `ml` - Treina modelo ML exploratório
- `literature` - Analisa dados de literatura (NOVO)
- `plan` - Gera plano experimental (NOVO)

### Problemas Preexistentes Resolvidos
1. **Git sem commits:** Foi criado commit inicial na branch master
2. **Arquivos não relacionados:** Arquivos de outro projeto (mlbb-tactical-bot) foram removidos do staging com `git rm -rf --cached`
3. **Branch de trabalho:** Criada branch `feature/scientific-agent-integration` para este trabalho

### Backup de Dados
- `data_backup/` - Backup anterior preservado
- `data_backup_20261013_153326/` - Backup adicional preservado

---

## 2. Avaliação das Ferramentas

### A. Scientific Agent Skills (K-Dense-AI)
**Status:** Em avaliação

**Repositório:** https://github.com/K-Dense-AI/scientific-agent-skills  
**Licença:** MIT  
**Estrelas:** 50.6k  
**Forks:** 4.5k  
**Habilidades:** 177 habilidades científicas

**Compatibilidade:**
- Segue o padrão Agent Skills
- Funciona com Cursor, Claude Code, Codex, Pi, Antigravity
- Pode ser instalado como plugin via `plugin.json`

**Habilidades potencialmente relevantes:**
- Revisão bibliográfica e síntese de literatura
- Análise estatística e exploração de dados
- Visualização científica
- Escrita científica rastreável por evidências
- Análise de séries temporais

**Decisão pendente:** Avaliar catálogo completo para selecionar habilidades específicas relevantes

### B. Superpowers (obra)
**Status:** Em avaliação

**Repositório:** https://github.com/obra/superpowers  
**Licença:** MIT  
**Estrelas:** 299.9k  
**Forks:** 26.8k

**Método de instalação documentado:**
```bash
agy plugin install https://github.com/obra/superpowers
```

**Compatibilidade:**
- Suporta Devin CLI nativamente
- Framework de metodologia de desenvolvimento
- Skills compositáveis

**Foco principal:** Desenvolvimento de software, não especificamente científico

**Decisão pendente:** Verificar se comando `agy` está disponível no ambiente atual

### C. Everything Claude Code / ECC (affaan-m)
**Status:** Em avaliação

**Repositório:** https://github.com/affaan-m/ECC  
**Licença:** MIT  
**Renomeado de: everything-claude-code → ECC

**Instalação para Claude Code:**
```bash
npx ecc-universal@2.2.3 setup
```

**Foco principal:** Otimização de performance de harness de agentes, não especificamente científico

**Decisão pendente:** Avaliar se há benefício complementar em relação ao Superpowers

---

## 3. Próximos Passos

1. Verificar disponibilidade do comando `agy` no ambiente atual
2. Consultar catálogo de habilidades do Scientific Agent Skills
3. Selecionar habilidades científicas relevantes para o projeto
4. Avaliar necessidade de Superpowers vs. habilidades científicas específicas
5. Criar AGENTS.md com instruções para o projeto
6. Implementar integração selecionada de forma aditiva e reversível
7. Executar testes e verificar integridade dos dados científicos

---

## 4. Restrições Científicas Inegociáveis

**Procedência dos dados:**
- ✓ Dados de literatura: separados em `data/literature/`
- ✓ Dados experimentais: separados em `data/raw/`
- ✓ Dados simulados: separados em `data/simulation/`
- ✓ Apenas dados `EXPERIMENTAL` são usados no treino ML

**Rastreabilidade exigida:**
- DOI, URL, citação completa
- Localização da fonte (tabela/figura/seção)
- Valor original, unidade, condições experimentais
- Indicação explícita de reportado vs. calculado
- Fórmula de cálculo quando aplicável

**Proibições:**
- Não inventar resultados, autores, referências, DOI, URLs ou valores
- Não misturar simulação com medições de laboratório
- Não alterar dados experimentais originais
- Não remover informações originais ao normalizar registros

---

## 5. Critérios de Sucesso

Ao final da integração:
- [ ] Projeto continua funcional (testes passam)
- [ ] Dados científicos permanecem íntegros
- [ ] Agentes têm instruções verificáveis
- [ ] Integração é aditiva e reversível
- [ ] Dependências adicionadas são documentadas
- [ ] Não há conflito com workflow existente

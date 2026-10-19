# Plano de Commit - Integração de Habilidades Científicas

**Branch:** `feature/scientific-skills-integration`  
**Data:** 2026-10-16  
**Status:** Pronto para revisão (sem commit realizado)

---

## Arquivos Modificados

### 1. `.agents/skills/README.md`

**Justificativa:**
- Documentação atualizada das habilidades importadas
- Correção de trailing whitespace (linhas 15-16 e 30-31)
- Passou em `git diff --check` após correção
- Necessário para manter documentação consistente com o estado real do workspace

**Tipo de alteração:** Formatação e documentação

---

## Arquivos Não Rastreados (Novos)

### Grupo 1: Habilidades Científicas Importadas (4 pastas)

**Arquivos:**
- `.agents/skills/citation-management/`
- `.agents/skills/literature-review/`
- `.agents/skills/experimental-design/`
- `.agents/skills/statistical-analysis/`

**Justificativa:**
- Importadas do repositório K-Dense-AI/scientific-agent-skills
- Revisão upstream: `a1043ef544e3a100c28e70a736b6cf32554d0677`
- Licença: MIT (cópias do LICENSE.md incluídas em cada diretório)
- Complementam as habilidades locais específicas do projeto
- Frontmatter YAML validado
- Dependências científicas não foram instaladas no `.venv` do projeto
- README skills documenta que stacks científicos devem usar ambientes separados

**Tipo de alteração:** Importação de habilidades oficiais

---

### Grupo 2: Habilidades de Desenvolvimento Importadas (3 pastas)

**Arquivos:**
- `.agents/skills/test-driven-development/`
- `.agents/skills/systematic-debugging/`
- `.agents/skills/verification-before-completion/`

**Justificativa:**
- Importadas do repositório obra/superpowers
- Revisão upstream: `bb92a77741419a4ab5f06e711a283343f1ada0c3` (v7.0.0)
- Licença: MIT (cópias do LICENSE incluídas em cada diretório)
- Skills de workspace, não plugin instalado
- README skills documenta que não é instalação oficial do Superpowers
- Skill `writing-plans` não foi importado por conflito com instruções do projeto

**Tipo de alteração:** Importação de habilidades de desenvolvimento

---

### Grupo 3: Documentação de Auditoria (2 arquivos)

**Arquivos:**
- `AUDITORIA_COMPARATIVA.md`
- `RELATORIO_INTEGRACAO_COPILOT.md` (atualizado)

**Justificativa:**
- `AUDITORIA_COMPARATIVA.md`: Documenta que apenas um projeto existe fisicamente ("Antocianinas Lab")
- `RELATORIO_INTEGRACAO_COPILOT.md`: Documenta integração de habilidades, validação de frontmatter, integridade de dados científicos
- Ambos arquivos registram hashes SHA-256 dos dados de literatura para comprovar integridade
- Documentam que os 3 arquivos CSV de literatura permaneceram inalterados desde o commit inicial
- Essencial para rastreabilidade e transparência da integração

**Tipo de alteração:** Documentação de processo

---

## Arquivos NÃO Incluídos no Commit

### Habilidades Específicas do Projeto (3 pastas)

**Arquivos:**
- `.agents/skills/literature-traceability/`
- `.agents/skills/scientific-data-integrity/`
- `.agents/skills/experimental-planning/`

**Justificativa para NÃO incluir:**
- Já estavam presentes no commit inicial `919573a`
- Já são rastreados pelo Git
- Não foram modificadas durante esta integração
- Fazem parte do baseline do projeto

---

## Dados Científicos

### Status: NENHUMA ALTERAÇÃO

**Arquivos verificados:**
- `data/literature/literature_studies.csv` - SHA-256 idêntico ao commit inicial
- `data/literature/literature_measurements.csv` - SHA-256 idêntico ao commit inicial
- `data/literature/literature_evidence.csv` - SHA-256 idêntico ao commit inicial
- `data/raw/*.csv` - Não modificados
- `data/simulation/*` - Não modificados
- `data/processed/*` - Não modificados

**Conclusão:** Dados científicos preservados integralmente.

---

## Estado dos Testes

**Comando:** `.venv\Scripts\python.exe -m pytest -q tests`  
**Resultado:** **28 passed in 56.06s**  
**Status:** ✓ Todos os testes passando

---

## Resumo do Commit Proposto

### Arquivos para `git add`:

1. `.agents/skills/README.md` (modificado)
2. `.agents/skills/citation-management/` (novo)
3. `.agents/skills/literature-review/` (novo)
4. `.agents/skills/experimental-design/` (novo)
5. `.agents/skills/statistical-analysis/` (novo)
6. `.agents/skills/test-driven-development/` (novo)
7. `.agents/skills/systematic-debugging/` (novo)
8. `.agents/skills/verification-before-completion/` (novo)
9. `AUDITORIA_COMPARATIVA.md` (novo)
10. `RELATORIO_INTEGRACAO_COPILOT.md` (novo)

### Mensagem de commit sugerida:

```
Import scientific and development skills to workspace

- Import 4 scientific skills from K-Dense-AI/scientific-agent-skills
  (revision a1043ef544e3a100c28e70a736b6cf32554d0677, MIT license)
- Import 3 development skills from obra/superpowers
  (revision bb92a77741419a4ab5f06e711a283343f1ada0c3, MIT license)
- Preserve 3 project-specific skills (literature-traceability,
  scientific-data-integrity, experimental-planning)
- Add audit documentation (AUDITORIA_COMPARATIVA.md,
  RELATORIO_INTEGRACAO_COPILOT.md)
- Fix trailing whitespace in .agents/skills/README.md
- Verify scientific data integrity with SHA-256 hashes
- All 28 tests passing

No scientific data was modified. Literature CSVs remain unchanged
since initial commit 919573a. No dependencies added to project .venv.
```

---

## Ações Restantes Antes do Commit

1. ✓ Branch de trabalho criada (`feature/scientific-skills-integration`)
2. ✓ Testes executados e passando
3. ✓ Formatação verificada (`git diff --check` passa)
4. ✓ Dados científicos verificados (SHA-256)
5. ✓ Documentação de auditoria criada
6. ⏸️ Aguardando aprovação do usuário para commit

---

## Limitações e Considerações

1. **Ativação em Copilot Chat:** Skills estão localizadas corretamente para descoberta pelo VS Code, mas não foi possível demonstrar ativação em uma sessão real do Copilot Chat neste ambiente (Cursor, não VS Code com GitHub Copilot).

2. **Dependências científicas:** As habilidades importadas têm dependências científicas (Pingouin, SciPy, PyMC, etc.) que não foram instaladas no `.venv` do projeto. README skills documenta que ambientes separados devem ser usados para essas stacks.

3. **Compatibilidade PowerShell:** A habilidade `systematic-debugging` inclui scripts POSIX. README skills alerta para não executar scripts POSIX do PowerShell sem verificar compatibilidade.

4. **Licenças:** Todas as habilidades importadas são licenciadas sob MIT. Cópias dos arquivos de licença upstream estão incluídas em cada diretório importado.

---

## Recomendação

**Aprovar commit** se:
- A importação das habilidades é desejada
- A documentação de auditoria é aceitável
- A separação entre habilidades específicas do projeto e importadas é clara

**Revisar antes do commit** se:
- Alguma habilidade importada não é necessária
- A abordagem de ambientes separados para dependências científicas deve ser alterada
- Mais documentação é necessária sobre o uso das habilidades

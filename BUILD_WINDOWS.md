# Compilação e Uso no Windows — Anthocianinas Estabilidade Lab

Este guia explica como gerar um executável Windows que inicia a interface
Streamlit com um clique duplo e como trocar o ícone do aplicativo.

## Visão geral

| Arquivo | Função |
|---|---|
| `launcher.py` | Inicia o Streamlit (apenas em `127.0.0.1`) e abre o navegador |
| `tools/build_windows.ps1` | Executa os testes e compila o `.exe` com PyInstaller |
| `tools/make_shortcut.ps1` | Cria um atalho na Área de Trabalho apontando para o `.exe` |
| `tools/make_icon_placeholder.py` | (Opcional) Regenera o ícone placeholder |
| `assets/Antocianinas_Estabilidade_Lab.ico` | Ícone embutido no `.exe` (substituível) |

O executável **não** embute dados, referências bibliográficas nem configurações:
ele apenas orquestra o Streamlit apontando para a pasta original do projeto.
Nenhum CSV, resultado científico ou configuração é alterado ou removido.

## Pré-requisitos

- Windows 10/11
- `Python 3.12` no `.venv` (já existente) com `requirements.txt` instalado
- `PyInstaller` (instale com `requirements-dev.txt`)

```powershell
# Na raiz do projeto
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Compilar

```powershell
# Na raiz do projeto
powershell -ExecutionPolicy Bypass -File .\tools\build_windows.ps1
```

O script:
1. Verifica que o sistema é Windows e a raiz do projeto está correta.
2. Executa `python -m unittest discover -s tests -v` e **aborta** se houver falha.
3. Verifica a interface (`app.py`, `anthocyanin_ui.py`, …), o `.venv` e o ícone.
4. Compila `launcher.py` em `dist\AntocianinasEstabilidadeLab.exe` usando
   `--icon assets\Antocianinas_Estabilidade_Lab.ico`.

Para pular a etapa de testes (apenas para desenvolvimento rápido):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_windows.ps1 -SkipTests
```

## Criar o atalho (duplo-clique)

Após a compilação:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\make_shortcut.ps1
```

Isso cria `Antocianinas Estabilidade Lab.lnk` na Área de Trabalho, apontando
para `dist\AntocianinasEstabilidadeLab.exe` e usando o ícone de
`assets\Antocianinas_Estabilidade_Lab.ico`.

**Duplo-clique no atalho** → o launcher:
1. Verifica interface, dependências e porta disponível.
2. Se o Streamlit já estiver rodando em `127.0.0.1`, apenas abre o navegador.
3. Caso contrário, inicia o servidor em uma janela de console **separada e
   visível** (somente em `127.0.0.1`, sem exposição à rede).
4. Quando o servidor estiver pronto, abre o navegador padrão.
5. Os erros são registrados em `data\logs\launcher_*.log` (nunca apaga dados).

## Trocar o ícone

O ícone atual é um **placeholder** gerado por script (gradiente roxo com
"pigmentos"). Para usar o seu próprio ícone:

1. Prepare um arquivo `.ico` com pelo menos os tamanhos 256×256, 48×48, 32×32
   e 16×16.
2. Substitua `assets\Antocianinas_Estabilidade_Lab.ico` pelo seu arquivo
   (mantenha o mesmo nome e caminho).
3. Recompile:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_windows.ps1 -SkipTests
```

4. Recrie o atalho (para atualizar o ícone do `.lnk`):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\make_shortcut.ps1
```

Para regenerar o placeholder original:

```powershell
.venv\Scripts\python.exe tools\make_icon_placeholder.py
```

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| `Faltam arquivos de interface` | `.exe` movido para outra pasta sem o projeto | Mantenha o `.exe`/atalho apontando para a pasta do projeto |
| `Dependência(ões) ausente(s)` | `.venv` incompleto | `.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| Porta 8501 ocupada | Outro Streamlit/software na porta | O launcher tenta 8550–8554 automaticamente |
| Ícone não aparece no atalho | Atalho criado antes de trocar o ícone | Reexecute `make_shortcut.ps1` após recompilar |
| Servidor não inicia | Erro no Streamlit | Verifique `data\logs\launcher_*.log` e a janela de console do servidor |

## Notas de implementação

- `launcher.py` usa `--server.address 127.0.0.1` (não expõe à rede).
- O servidor roda via `CREATE_NEW_CONSOLE` (janela visível e encerrável).
- O `.exe` usa `--console` para exibir mensagens e aguardar `Enter`.
- `anthocyanin_lab.py` permanece **intocado**; a compilação apenas o referencia.


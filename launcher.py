"""Iniciador do aplicativo Antocianinas Estabilidade Lab.

Deixa duplo-clicar na Área de Trabalho e inicia:

    Streamlit (somente 127.0.0.1) -> navegador

Comportamentos principais:
* Localiza a raiz do projeto, mesmo se o executável estiver em ``dist/``.
* Verifica a interface e as dependências antes de tentar iniciar.
* Evita subir duas instâncias desnecessárias (reutiliza uma já rodando).
* Mantém o servidor em processo separado/visível; fecha-o ao fechar a janela.
* Registra erros em ``data/logs/launcher_*.log`` (nunca apaga dados).
"""

from __future__ import annotations

import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

import requests  # type: ignore  # type: ignore[import-untyped]

# --------------------------------------------------------------------------- #
# Caminhos e contratos de interface
# --------------------------------------------------------------------------- #
APP_PY = "app.py"
UI_MODULE = "anthocyanin_ui.py"
LAB_MODULE = "anthocyanin_lab.py"
DATA_RAW = "data/raw"
CONFIG_FILE = "data/config/simulation_parameters.json"
ML_CSV = "data/raw/ml_observations.csv"

# Solicita de filas para iniciar o servidor (evita conflitos se outra instância
# já estiver rodando na porta padrão).
STREAMLIT_PORT_ATTEMPTS = (8501, 8550, 8551, 8552, 8553, 8554)

# Caminho do log; sempre relativo à raiz do projeto (nunca apaga dados).
LOG_DIR_NAME = "data/logs"


def resolve_project_root() -> Path:
    """Determina a raiz do projeto de forma robusta.

    Caso 1: o ``launcher.py`` foi empacotado por PyInstaller -> ``sys._MEIPASS``
    não é a raiz; a raiz é o diretório do executável (ou o super-diretório,
    se o executável estiver em dist/).
    Caso 2: executado de uma árvore de projeto normal -> a raiz é o diretório
    do ``launcher.py``.
    """
    candidate = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()

    # Executável PyInstaller provável.
    if getattr(sys, "frozen", False):
        root = candidate.parent
        for _ in range(4):
            if (root / APP_PY).exists() and (root / UI_MODULE).exists():
                break
            root = root.parent
        if not (root / APP_PY).exists():
            root = candidate.parent  # fallback: dist/ ou pasta com o exe
        return root

    # Execução *in place* (não empacotado).
    root = candidate.parent
    if (root / APP_PY).exists() and (root / UI_MODULE).exists():
        return root

    # Corrida de ``python tools/build_windows.ps1`` ou de ``dist/``.
    for _ in range(4):
        parent = root.parent
        if (parent / APP_PY).exists() and (parent / UI_MODULE).exists():
            return parent
        root = parent
    return candidate.parent


def interface_files(root: Path) -> list[tuple[str, Path]]:
    """Retorna (rótulo, caminho) para os artefatos de interface que devem existir."""
    return [
        ("Interface principal", root / APP_PY),
        ("Módulo de interface", root / UI_MODULE),
        ("Módulo científico", root / LAB_MODULE),
        ("Dados experimentais", root / DATA_RAW),
        ("Configuração do simulador", root / CONFIG_FILE),
        ("Dados experimentais", root / ML_CSV),
    ]


def check_dependencies() -> list[str]:
    """Verifica se os pacotes de *execução* exigem com importlib (sem lado effects)."""
    # (nome do pacote no pip, nome do módulo para importar)
    required = [
        ("streamlit", "streamlit"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("scikit-learn", "sklearn"),
        ("joblib", "joblib"),
    ]
    missing = []

    # No executável congelado (PyInstaller) os pacotes NÃO são embutidos; a
    # verificação deve usar o python do .venv do projeto, que os possui.
    if getattr(sys, "frozen", False):
        root = resolve_project_root()
        python = root / ".venv" / "Scripts" / "python.exe"
        if not python.exists():
            return [f".venv\\Scripts\\python.exe (não encontrado em {root})"]
        import subprocess

        try:
            subprocess.run(
                [str(python), "-c", "import streamlit, pandas, numpy, sklearn, joblib"],
                check=True,
                capture_output=True,
                timeout=30,
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or b"").decode("utf-8", "replace").strip()
            missing.append(f"dependências no .venv ({detail})")
        except Exception as exc:  # noqa: BLE001
            missing.append(f"dependências ({type(exc).__name__}: {exc})")
        return missing

    # Execução in place: verifica importando diretamente no interpretador atual.
    for package, module in required:
        try:
            __import__(module)
        except Exception as exc:  # noqa: BLE001
            missing.append(f"{package} ({type(exc).__name__}: {exc})")
    return missing


def resolve_log_path(root: Path) -> Path:
    log_dir = root / LOG_DIR_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"launcher_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log_message(log_path: Path, level: str, message: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}"
    print(line)
    try:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as exc:  # noqa: BLE001
        print(f"[AVISO] Não foi possível escrever o log {log_path}: {exc}")


def is_streamlit_running(host: str, port: int, timeout: float = 1.0) -> bool:
    """Verifica se um servidor Streamlit já responde na porta indicada."""
    url = f"http://{host}:{port}/apis/id"
    try:
        with requests.get(url, timeout=timeout) as response:
            return response.status_code == 200
    except Exception:  # noqa: BLE001
        return False


def find_free_port(host: str, preferred: int | None = None) -> int:
    ports = STREAMLIT_PORT_ATTEMPTS if preferred is None else [preferred]
    for port in ports:
        if not is_streamlit_running(host, port):
            return port
    raise RuntimeError(
        f"Nenhuma porta disponível para o Streamlit em {host}. "
        "Verifique se outro software está usando a rede."
    )


def open_browser(url: str) -> None:
    try:
        webbrowser.open(url, new=1)
    except Exception as exc:  # noqa: BLE001
        log_message(LOG, "AVISO", f"Não foi possível abrir o navegador automaticamente: {exc}")


def start_server(root: Path, host: str, port: int, log_path: Path) -> tuple[subprocess.Popen, str]:
    """Inicia o Streamlit em uma janela de console separada e visível."""
    import subprocess

    if getattr(sys, "frozen", False):
        python = str(root / ".venv" / "Scripts" / "python.exe")
    else:
        python = sys.executable

    cmd = [
        python,
        "-m",
        "streamlit",
        "run",
        str(root / APP_PY),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        "false",
        "--client.toolbarMode",
        "minimal",
    ]

    log_message(log_path, "INFO", f"Iniciando Streamlit em {host}:{port} (cmd: {' '.join(cmd)})")
    proc = subprocess.Popen(
        cmd,
        creationflags=subprocess.CREATE_NEW_CONSOLE,  # janela visível e independente
        cwd=str(root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def main() -> int:
    global LOG
    root = resolve_project_root()
    log_path = resolve_log_path(root)
    LOG = log_path

    log_message(LOG, "INFO", "=== Iniciando Antocianinas Estabilidade Lab ===")

    # 1) Verificar interface.
    missing_interface = [label for label, path in interface_files(root) if not path.exists()]
    if missing_interface:
        msg = "Faltam arquivos de interface: " + ", ".join(missing_interface)
        log_message(LOG, "ERRO", msg)
        print(f"\n[ERRO] {msg}\n")
        print("Execute a compilação com:\n  powershell -ExecutionPolicy Bypass -File .\\tools\\build_windows.ps1")
        return 2

    # 2) Verificar dependências de execução.
    missing = check_dependencies()
    if missing:
        msg = "Dependência(ões) ausente(s): " + "; ".join(missing)
        log_message(LOG, "ERRO", msg)
        print(f"\n[ERRO] {msg}\n")
        print("Instale com:\n  .venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        return 3

    # 3) Escolher porta disponível.
    try:
        port = find_free_port("127.0.0.1", preferred=8501)
    except RuntimeError as exc:
        log_message(LOG, "ERRO", str(exc))
        print(f"\n[ERRO] {exc}\n")
        return 4

    # 4) Evitar dupla execução.
    if is_streamlit_running("127.0.0.1", port):
        log_message(LOG, "INFO", f"Já existe um Streamlit rodando em 127.0.0.1:{port}. Abrindo o navegador.")
        print(f"\n[Stared] Interface já está ativa em:\n    {APP_URL}:{port}\n")
        open_browser(APP_URL + f":{port}")
        log_message(LOG, "INFO", "Interface já em execução; aguardando encerramento.")
        try:
            input("Pressione Enter para fechar... ")
        except EOFError:
            pass
        return 0

    # 5) Iniciar servidor.
    server_process = start_server(root, "127.0.0.1", port, log_path)
    log_message(LOG, "INFO", f"Processo do Streamlit iniciado (PID={server_process.pid}).")

    try:
        import time
        import urllib.request

        deadline = datetime.now().timestamp() + 35
        ready = False
        while datetime.now().timestamp() < deadline:
            if is_streamlit_running("127.0.0.1", port):
                ready = True
                break
            if server_process.poll() is not None:
                log_message(LOG, "ERRO", "Processo do Streamlit encerrado inesperadamente (código de saída).")
                print("\n[ERRO] O servidor não foi inicializado corretamente.\n")
                log_message(LOG, "ERRO", "Código de saída do processo: " + str(server_process.returncode))
                return 5
            time.sleep(0.4)

        if not ready:
            log_message(LOG, "ERRO", "Tempo esgotado esperando o servidor ficar pronto.")
            print("\n[ERRO] O servidor não respondeu no tempo esperado.\n")
            return 5

        url = f"http://127.0.0.1:{port}"
        log_message(LOG, "INFO", f"Streamlit pronto em {url}.")
        print(f"\n[Ok] A interface está rodando em:\n    {url}\n")
        open_browser(url)
        print("Abra esse endereço no navegador padrão. O servidor roda em uma janela separada.")
        print("Pressione Enter para fechar esta janela (o servidor permanece visível em sua própria janela).\n")

        try:
            input("Pressione Enter para encerrar... ")
        except EOFError:
            pass
        return 0
    finally:
        # Encerra o servidor via handle do próprio processo (não depende de
        # psutil nem de varredura por cmdline; é mais confiável no Windows).
        if server_process.poll() is None:
            log_message(LOG, "INFO", "Encerrando o servidor Streamlit.")
            try:
                server_process.terminate()
                server_process.wait(timeout=10)
            except Exception:  # noqa: BLE001
                try:
                    server_process.kill()
                    server_process.wait(timeout=5)
                except Exception:  # noqa: BLE001
                    pass


if __name__ == "__main__":
    raise SystemExit(main())


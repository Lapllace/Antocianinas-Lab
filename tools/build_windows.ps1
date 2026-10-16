<#
.SYNOPSIS
  Compila o iniciador Windows (AntocianinasEstabilidadeLab.exe) para o
  aplicativo Anthocianinas Estabilidade Lab.

.DESCRIPTION
  1. Verifica que o sistema é Windows e a raiz do projeto está correta.
  2. Executa a suíte de testes unitários e interrompe a compilação se houver
     falhas.
  3. Verifica a existência da interface e do ambiente virtual (.venv).
  4. Compila launcher.py em dist/AntocianinasEstabilidadeLab.exe, incorpo
     os ícone assets/Antocianinas_Estabilidade_Lab.ico.
  5. Mantém os dados, as referências, os módulos científicos e as configurações
     fora do executável.

.UAGE
  powershell -ExecutionPolicy Bypass -File .\tools\build_windows.ps1
#>

param(
    [switch]$SkipTests = $false,
    [switch]$SkipInterfaceCheck = $false
)

$ErrorActionPreference = "Stop"

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir   # tools/ -> raiz do projeto

function Write-Header($text) {
    Write-Host ""
    Write-Host ("=" * 72) -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host ("=" * 72) -ForegroundColor Cyan
}

function Write-Step($text) {
    Write-Host ">>> $text" -ForegroundColor Yellow
}

function Write-OK($text) {
    Write-Host "  [OK] $text" -ForegroundColor Green
}

function Write-Fail($text) {
    Write-Host "  [FALHA] $text" -ForegroundColor Red
}

function Assert-Windows {
    if ([System.Environment]::OSVersion.Platform -ne "Win32NT") {
        Write-Fail "Esta compilação só é suportada no Windows."
        exit 1
    }
    $psv = $PSVersionTable.PSVersion
    if ($psv.Major -lt 5) {
        Write-Fail "PowerShell 5.1 ou superior é necessário."
        exit 1
    }
    Write-OK "Windows detectado (PowerShell $psv)."
}

function Assert-ProjectRoot {
    if (-not (Test-Path (Join-Path $ProjectRoot "app.py"))) {
        Write-Fail "Pasta raiz do projeto não encontrada em: $ProjectRoot"
        Write-Fail "Execute este script a partir da raiz do projeto (onde está tools/)."
        exit 1
    }
    Write-OK "Raiz do projeto : $ProjectRoot"
}

function Run-Tests {
    Write-Step "Executando a suíte de testes existentes + nova..."
    $python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        Write-Fail "Ambiente virtual não encontrado em $ProjectRoot\.venv"
        Write-Fail "Crie-o com: py -m venv .venv ; .venv\Scripts\Activate.ps1 ; pip install -r requirements.txt"
        exit 1
    }
    if (-not $SkipTests) {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $python
        $psi.Arguments = " -m unittest discover -s tests -v"
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $proc = New-Object System.Diagnostics.Process
        $proc.StartInfo = $psi
        $proc.Start() | Out-Null
        $out = $proc.StandardOutput.ReadToEnd()
        $err = $proc.StandardError.ReadToEnd()
        $proc.WaitForExit()

        $out | ForEach-Object { Write-Host $_ }
        if ($err) { $err | ForEach-Object { Write-Host "ERRO: $_" -ForegroundColor Red } }

        if ($proc.ExitCode -ne 0) {
            Write-Fail "A suíte de testes falhou. A compilação foi interrompida."
            exit $proc.ExitCode
        }
        Write-OK "Suíte de testes passou."
    } else {
        Write-OK "Verificação de testes omitida ($SkipTests)."
    }
}

function Check-InterfaceAndEnvironment {
    Write-Step "Verificando interface e ambiente virtual..."

    $files = @(
        "app.py",
        "anthocyanin_ui.py",
        "anthocyanin_persistence.py",
        "anthocyanin_lab.py",
        "requirements.txt",
        "data\raw",
        "data\config\simulation_parameters.json",
        "assets\Antocianinas_Estabilidade_Lab.ico"
    )
    $allOk = $true
    foreach ($f in $files) {
        $full = Join-Path $ProjectRoot $f
        if (-not (Test-Path $full)) {
            Write-Fail "Arquivo ausente: $f"
            $allOk = $false
        }
    }

    $venv = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venv)) {
        Write-Fail ".venv\Scripts\python.exe não encontrado."
        Write-Fail "Crie o ambiente com: py -m venv .venv"
        $allOk = $false
    } else {
        Write-OK ".venv detectado."
    }

    if (-not $allOk) {
        Write-Fail "Verifique os arquivos acima antes de compilar."
        exit 1
    }
}

function Build-Exe {
    Write-Step "Compilando launcher.py -> dist/AntocianinasEstabilidadeLab.exe"

    $python   = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    $icon     = Join-Path $ProjectRoot "assets\Antocianinas_Estabilidade_Lab.ico"
    $launcher = Join-Path $ProjectRoot "launcher.py"
    $destDir  = Join-Path $ProjectRoot "dist"
    $outName  = "AntocianinasEstabilidadeLab.exe"

    if (-not (Test-Path $icon)) {
        Write-Fail "Ícone não encontrado: $icon"
        Write-Fail "Crie-o com: python tools\make_icon_placeholder.py (ou coloque o seu)"
        exit 1
    }

    $cmd = @(
        "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", "AntocianinasEstabilidadeLab",
        "--icon", $icon,
        "--distpath", $destDir,
        "--workpath", (Join-Path $ProjectRoot "build"),
        $launcher
    )

    Write-Host ("  Comando: {0} {1}" -f $python, ($cmd -join " "))
    & $python @cmd

    $exe = Join-Path $destDir $outName
    if (-not (Test-Path $exe)) {
        Write-Fail "Executável não foi gerado em $exe"
        exit 1
    }

    Write-OK "Executável gerado: $exe"
}

Write-Header "Compilacao - Anthocianinas Estabilidade Lab (Windows)"
Write-Header "1/4 - Verificacoes iniciais"
Assert-Windows
Assert-ProjectRoot

Write-Header "2/4 - Executando testes unitarios"
Run-Tests

Write-Header "3/4 - Verificando interface e ambiente virtual"
Check-InterfaceAndEnvironment

Write-Header "4/4 - Compilando executavel"
Build-Exe

Write-Header "Concluido!"
Write-OK "Executavel em: dist\AntocianinasEstabilidadeLab.exe"
Write-OK "Crie um atalho na Area de Trabalho para duplo-clicar (ver BUILD_WINDOWS.md)."


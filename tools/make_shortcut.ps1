<#
.SYNOPSIS
  Cria um atalho na Área de Trabalho apontando para o executável compilado.

.DESCRIPTION
  Gera ``Antocianinas Estabilidade Lab.lnk`` na Área de Trabalho do usuário
  apontando para ``dist\AntocianinasEstabilidadeLab.exe`` e usando o ícone
  ``assets\Antocianinas_Estabilidade_Lab.ico``. O usuário pode então
  duplo-clicar no atalho para iniciar a interface.

  Execute após ``tools\build_windows.ps1``.

.USAGE
  powershell -ExecutionPolicy Bypass -File .\tools\make_shortcut.ps1
#>

param(
    [string]$ExePath = "",
    [string]$ShortcutPath = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DefaultExe  = Join-Path $ProjectRoot "dist\AntocianinasEstabilidadeLab.exe"
$IconFile    = Join-Path $ProjectRoot "assets\Antocianinas_Estabilidade_Lab.ico"
$Desktop     = [Environment]::GetFolderPath("Desktop")
$LnkName     = "Antocianinas Estabilidade Lab.lnk"

if (-not $ExePath)      { $ExePath = $DefaultExe }
if (-not $ShortcutPath) { $ShortcutPath = Join-Path $Desktop $LnkName }

if (-not (Test-Path $ExePath)) {
    Write-Host "[ERRO] Executável não encontrado: $ExePath" -ForegroundColor Red
    Write-Host "Compile primeiro com: powershell -ExecutionPolicy Bypass -File .\tools\build_windows.ps1" -ForegroundColor Yellow
    exit 1
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $ExePath
$shortcut.WorkingDirectory = Split-Path -Parent $ExePath
$shortcut.IconLocation = "$IconFile,0"
$shortcut.Description = "Antocianinas Estabilidade Lab"
$shortcut.Save()

Write-Host "[OK] Atalho criado: $ShortcutPath" -ForegroundColor Green
Write-Host "     Alvo : $ExePath" -ForegroundColor Cyan
Write-Host "     Ícone: $IconFile" -ForegroundColor Cyan
Write-Host "Duplo-clique no atalho para iniciar a interface." -ForegroundColor Yellow

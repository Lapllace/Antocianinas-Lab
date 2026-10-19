param(
    [string]$ManifestPath
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path.TrimEnd('\')
if (-not $ManifestPath) {
    $ManifestPath = Join-Path $repoRoot "backups\validation_audit_20261016_085744\SHA256SUMS.txt"
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Write-Error "Manifesto de hashes não encontrado: $ManifestPath"
    exit 2
}

$rootPrefix = $repoRoot + '\'
$mismatches = 0
foreach ($line in Get-Content -LiteralPath $ManifestPath) {
    if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith('#')) {
        continue
    }
    $parts = [regex]::Split($line.Trim(), '\s{2,}', 2)
    if ($parts.Count -ne 2 -or $parts[0] -notmatch '^[A-Fa-f0-9]{64}$') {
        Write-Output "MISMATCH`t<manifest-line>`t$line"
        $mismatches++
        continue
    }

    $expected = $parts[0].ToUpperInvariant()
    $relativePath = $parts[1].Trim()
    $filePath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $relativePath))
    if (-not $filePath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        Write-Output "MISMATCH`t$relativePath`tpath escapes repository"
        $mismatches++
        continue
    }
    if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
        Write-Output "MISMATCH`t$relativePath`tfile missing"
        $mismatches++
        continue
    }

    $actual = (Get-FileHash -LiteralPath $filePath -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($actual -eq $expected) {
        Write-Output "MATCH`t$relativePath`t$actual"
    }
    else {
        Write-Output "MISMATCH`t$relativePath`texpected=$expected`tactual=$actual"
        $mismatches++
    }
}

if ($mismatches -gt 0) {
    Write-Output "Conferência finalizada: $mismatches divergência(s)."
    exit 1
}
Write-Output "Conferência finalizada: todos os arquivos correspondem ao manifesto."
exit 0

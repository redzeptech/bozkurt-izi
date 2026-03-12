$ErrorActionPreference = "Stop"

# Konsolda Türkçe karakter bozulmasını azaltır
try {
    chcp 65001 | Out-Null
} catch {}

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$CollectorPath = Join-Path $ScriptRoot "collectors\collect_rdp_events.ps1"
$EnginePath    = Join-Path $ScriptRoot "engine\analyze_rdp.py"
$OutputDir     = Join-Path $ScriptRoot "output"
$JsonPath      = Join-Path $OutputDir "rdp_events.json"

Write-Host "[*] Bozkurt İzi çalışıyor..."
Write-Host "[*] ScriptRoot: $ScriptRoot"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host "[*] Collector başlatılıyor..."
powershell -ExecutionPolicy Bypass -File $CollectorPath -OutputPath $JsonPath

if (-not (Test-Path $JsonPath)) {
    throw "Collector çıktısı oluşmadı: $JsonPath"
}

Write-Host "[*] JSON bulundu: $JsonPath"
Write-Host "[*] Python engine başlatılıyor..."

python $EnginePath --input $JsonPath --output-dir $OutputDir

Write-Host "[+] Tamamlandı."
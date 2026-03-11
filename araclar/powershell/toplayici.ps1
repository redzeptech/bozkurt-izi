param(
    [string]$CiktiKlasoru = ".\ciktilar"
)

Write-Host "Bozkurt İzi PowerShell toplayıcı başlatıldı." -ForegroundColor Cyan

if (-not (Test-Path $CiktiKlasoru)) {
    New-Item -ItemType Directory -Path $CiktiKlasoru | Out-Null
}

$zaman = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$dosya = Join-Path $CiktiKlasoru "sistem_bilgisi_$zaman.txt"

@"
Bilgisayar Adı : $env:COMPUTERNAME
Kullanıcı      : $env:USERNAME
Tarih          : $(Get-Date)
İşletim Sistemi:
$((Get-CimInstance Win32_OperatingSystem).Caption)
"@ | Out-File -FilePath $dosya -Encoding UTF8

Write-Host "Sistem bilgisi kaydedildi: $dosya" -ForegroundColor Green
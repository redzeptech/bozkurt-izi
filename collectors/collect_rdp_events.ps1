param(
    [Parameter(Mandatory=$true)]
    [string]$OutputPath,

    [int]$MaxEvents = 5000
)

$ErrorActionPreference = "Stop"

try {
    chcp 65001 | Out-Null
} catch {}

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

Write-Host "[*] Bozkurt İzi - RDP event toplama başlıyor..."
Write-Host "[*] OutputPath: $OutputPath"

$outputDir = Split-Path -Parent $OutputPath
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$eventIds = 4624, 4625

$events = Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    ID      = $eventIds
} -MaxEvents $MaxEvents -ErrorAction SilentlyContinue

$results = @()

foreach ($event in $events) {
    try {
        $xml = [xml]$event.ToXml()

        $dataMap = @{}
        foreach ($d in $xml.Event.EventData.Data) {
            $name = $d.Name
            $value = $d.'#text'
            if ($null -ne $name -and $name -ne "") {
                $dataMap[$name] = $value
            }
        }

        $logonType = $dataMap["LogonType"]
        $ipAddress = $dataMap["IpAddress"]
        $targetUser = $dataMap["TargetUserName"]
        $targetDomain = $dataMap["TargetDomainName"]
        $workstation = $dataMap["WorkstationName"]
        $status = $dataMap["Status"]
        $subStatus = $dataMap["SubStatus"]

        # İlk aşama: RDP odaklı
        if ($logonType -eq "10") {
            $results += [PSCustomObject]@{
                TimeCreated      = $event.TimeCreated.ToString("o")
                EventID          = $event.Id
                RecordId         = $event.RecordId
                Computer         = $event.MachineName
                LogonType        = $logonType
                IpAddress        = $ipAddress
                TargetUserName   = $targetUser
                TargetDomainName = $targetDomain
                WorkstationName  = $workstation
                Status           = $status
                SubStatus        = $subStatus
            }
        }
    }
    catch {
        Write-Warning "Event parse edilemedi. RecordId: $($event.RecordId)"
    }
}

# Boş olsa bile geçerli JSON üret
$json = $results | ConvertTo-Json -Depth 4
if ([string]::IsNullOrWhiteSpace($json)) {
    $json = "[]"
}

Set-Content -Path $OutputPath -Value $json -Encoding UTF8

Write-Host "[+] Toplanan event sayısı: $($results.Count)"
Write-Host "[+] Çıktı dosyası: $OutputPath"

if (Test-Path $OutputPath) {
    $item = Get-Item $OutputPath
    Write-Host "[+] Dosya oluşturuldu. Boyut: $($item.Length) byte"
} else {
    Write-Host "[!] Dosya oluşturulamadı!"
}
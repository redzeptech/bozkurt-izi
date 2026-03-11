param(
    [string]$Cikti = ".\ciktilar\event_timeline.csv",
    [int]$SonGun = 7
)

Write-Host "Bozkurt İzi - Event timeline toplama başlatıldı" -ForegroundColor Cyan

$baslangic = (Get-Date).AddDays(-$SonGun)

$hedefOlaylar = @(
    4624,   # Başarılı oturum açma
    4625,   # Başarısız oturum açma
    4634,   # Oturum kapatma
    4648,   # Açık kimlik bilgisi ile oturum açma girişimi
    4672    # Özel ayrıcalık atandı
)

$events = Get-WinEvent -FilterHashtable @{
    LogName   = 'Security'
    Id        = $hedefOlaylar
    StartTime = $baslangic
} -ErrorAction SilentlyContinue

$sonuc = foreach ($event in $events) {
    $xml = [xml]$event.ToXml()

    $eventData = @{}
    foreach ($d in $xml.Event.EventData.Data) {
        if ($d.Name) {
            $eventData[$d.Name] = $d.'#text'
        }
    }

    [PSCustomObject]@{
        TimeCreated   = $event.TimeCreated
        EventID       = $event.Id
        TargetUser    = $eventData["TargetUserName"]
        TargetDomain  = $eventData["TargetDomainName"]
        LogonType     = $eventData["LogonType"]
        IpAddress     = $eventData["IpAddress"]
        Workstation   = $eventData["WorkstationName"]
        ProcessName   = $eventData["ProcessName"]
        SubjectUser   = $eventData["SubjectUserName"]
        Computer      = $env:COMPUTERNAME
    }
}

if (-not (Test-Path (Split-Path $Cikti -Parent))) {
    New-Item -ItemType Directory -Path (Split-Path $Cikti -Parent) | Out-Null
}

$sonuc |
    Sort-Object TimeCreated |
    Export-Csv $Cikti -NoTypeInformation -Encoding UTF8

Write-Host "Timeline verisi kaydedildi: $Cikti" -ForegroundColor Green
Write-Host "Toplam olay sayısı: $($sonuc.Count)" -ForegroundColor Yellow
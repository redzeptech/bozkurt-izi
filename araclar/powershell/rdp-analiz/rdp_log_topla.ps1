param(
    [string]$Cikti = ".\ciktilar\rdp_loglari.csv"
)

Write-Host "Bozkurt İzi - RDP log toplama başlatıldı" -ForegroundColor Cyan

$events = Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4625
} -ErrorAction SilentlyContinue

$sonuc = foreach ($event in $events) {

    $xml = [xml]$event.ToXml()

    $ip = ($xml.Event.EventData.Data | Where-Object {$_.Name -eq "IpAddress"}).'#text'

    if ($ip -and $ip -ne "-") {

        [PSCustomObject]@{
            TimeCreated = $event.TimeCreated
            IPAddress   = $ip
        }
    }
}

$sonuc | Export-Csv $Cikti -NoTypeInformation -Encoding UTF8

Write-Host "Loglar kaydedildi: $Cikti" -ForegroundColor Green
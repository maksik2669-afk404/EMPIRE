# Downloads the 10 WINTER ARC reels from Higgsfield into a folder on the Desktop. Started by download_reels.bat.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"   # makes Invoke-WebRequest much faster in PowerShell 5.1
$dest = Join-Path ([Environment]::GetFolderPath("Desktop")) "WinterArc_Reels"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$base = "https://d2ol7oe51mr4n9.cloudfront.net/user_3JoppAlhrzv4RWeSyfI2vtpTHg8/"
$ids = @("3c4dd9cd-a68c-4c43-9de5-a7cf4e4879fe", "8ab91c3f-9de8-4514-af54-9ee70990cd6d",
         "cce7a2d7-f918-487c-a5c5-f435d66b6236", "6fd66732-1b4c-41f1-a4b7-7ad929ee24ad",
         "a4557e96-ed29-47f9-96f6-d0d11543c05d", "8ed0f248-f8f4-412d-a112-3057b66d8f64",
         "3f6d8412-ceca-48ad-a529-24851acfa7aa", "18d19a06-e8a0-4736-bb56-82d35125c339",
         "ed807011-6439-4b18-a47c-98d05a97ef6f", "9a73f473-f1e8-4cac-8b45-1dc962176841")
$failed = 0
for ($i = 0; $i -lt $ids.Count; $i++) {
    $name = "winter_arc_reel_{0:D2}.mp4" -f ($i + 1)
    $out = Join-Path $dest $name
    Write-Host "Downloading $name ..."
    try { Invoke-WebRequest -Uri ($base + $ids[$i] + ".mp4") -OutFile $out -UseBasicParsing }
    catch { Write-Host "  failed: $($_.Exception.Message)" -ForegroundColor Yellow; $failed++ }
}
Write-Host ""
Write-Host "Done: $dest ($($ids.Count - $failed) of $($ids.Count) downloaded)" -ForegroundColor Cyan
Start-Process $dest

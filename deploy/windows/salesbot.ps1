# WINTER ARC sales bot on a Windows PC. Started by start_salesbot.bat. ASCII-only on purpose (PowerShell 5.1).
$ErrorActionPreference = "Continue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
$EnvFile = Join-Path $Root ".env.salesbot"

function Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Read-Secret($prompt) {
    $s = Read-Host $prompt -AsSecureString
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { return ([Runtime.InteropServices.Marshal]::PtrToStringBSTR($b)).Trim() }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
function Test-Py($exe, $pre) {
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { return $false }
    $out = & $exe @pre -c "import sys; print(sys.version_info >= (3, 10))" 2>$null
    return ($LASTEXITCODE -eq 0 -and "$out".Trim() -eq "True")
}

if (-not (Test-Path $VenvPy)) {
    Step "Looking for Python 3.10+"
    $py = $null
    if (Test-Py "py" @("-3")) { $py = @("py", "-3") } elseif (Test-Py "python" @()) { $py = @("python") }
    if (-not $py) {
        Warn "Python 3.10+ not found. Installing Python 3.12 with winget..."
        winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
        Warn "Python installed. Close this window and double-click start_salesbot.bat again."
        exit 1
    }
    & $py[0] @($py | Select-Object -Skip 1) -m venv .venv
}
Step "Installing dependencies"
& $VenvPy -m pip install -q --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { Warn "pip install failed - check the internet connection"; exit 1 }

if (-not (Test-Path $EnvFile)) {
    Step "Setup of the SALES bot (a separate bot from @BotFather, not the marketplace one)"
    do {
        $token = Read-Secret "1/5 Sales bot token from @BotFather (input hidden)"
        $ok = $token -match '^[0-9]+:[A-Za-z0-9_-]{30,}$'
        if (-not $ok) { Warn "That does not look like a bot token (123456789:AA...). Try again." }
    } until ($ok)
    do {
        $url = (Read-Host "2/5 Link to the table (the .../copy link from setup() or any Google Sheets link)").Trim()
        $ok = $url -match '^https://docs\.google\.com/'
        if (-not $ok) { Warn "Paste a docs.google.com link." }
    } until ($ok)
    $price = (Read-Host "3/5 Price in Telegram Stars (Enter = 149)").Trim()
    if (-not ($price -match '^[0-9]+$')) { $price = "149" }
    $admin = (Read-Host "4/5 Your Telegram ID for sale alerts and /stats (ask @userinfobot)").Trim()
    $support = (Read-Host "5/5 Support contact for buyers, e.g. @your_username").Trim()
    $video = "https://d2ol7oe51mr4n9.cloudfront.net/user_3JoppAlhrzv4RWeSyfI2vtpTHg8/3c4dd9cd-a68c-4c43-9de5-a7cf4e4879fe.mp4"
    $lines = @("SALES_BOT_TOKEN=$token", "TABLE_URL=$url", "PRICE_STARS=$price", "ADMIN_IDS=$admin",
               "SUPPORT_CONTACT=$support", "WELCOME_VIDEO_URL=$video", "SALES_DB=data/sales.db", "TELEGRAM_PROXY=")
    [IO.File]::WriteAllLines($EnvFile, $lines)  # UTF-8 without BOM
    Warn "Saved to $EnvFile (delete it to enter the settings again)."
}

Step "Starting the sales bot. Keep this window open."
while ($true) {
    & $VenvPy -m salesbot.bot
    Warn "Bot stopped (exit code $LASTEXITCODE). Restarting in 10 seconds - close this window to stop."
    Start-Sleep -Seconds 10
}

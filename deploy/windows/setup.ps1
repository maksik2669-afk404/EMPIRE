# EMPIRE Reply - run the bot on a Windows PC (testing / demo video). Started by start.bat.
# ASCII-only on purpose: Windows PowerShell 5.1 misreads UTF-8 scripts without a BOM.
$ErrorActionPreference = "Continue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12  # PS 5.1 defaults to old TLS
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root
$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
$EnvFile = Join-Path $Root ".env"

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

# ---- 1. Python 3.10+ and a virtual environment
if (-not (Test-Path $VenvPy)) {
    Step "Looking for Python 3.10+"
    $py = $null
    if (Test-Py "py" @("-3")) { $py = @("py", "-3") }
    elseif (Test-Py "python" @()) { $py = @("python") }
    if (-not $py) {
        Warn "Python 3.10+ not found. Installing Python 3.12 with winget..."
        winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
        Warn "Python installed. Close this window and double-click start.bat again."
        exit 1
    }
    Step "Creating a virtual environment"
    $exe = $py[0]
    $pre = @($py | Select-Object -Skip 1)
    & $exe @pre -m venv .venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPy)) { Warn "Could not create .venv"; exit 1 }
}

Step "Installing dependencies (1-2 minutes the first time)"
& $VenvPy -m pip install -q --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { Warn "pip install failed - check the internet connection and run start.bat again"; exit 1 }

# ---- 2. Keys (asked once, stored only on this PC)
if (Test-Path $EnvFile) {
    Step "Using existing .env (delete it to enter the keys again)"
} else {
    Step "Setup: paste your keys here - they stay on this PC"
    do {
        $token = Read-Secret "1/4 Bot token from @BotFather (input hidden)"
        $ok = $token -match '^[0-9]+:[A-Za-z0-9_-]{30,}$'
        if (-not $ok) { Warn "That does not look like a bot token (123456789:AA...). Try again." }
    } until ($ok)

    $proxy = ""
    try {
        $me = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getMe" -TimeoutSec 15
        Write-Host "    Bot found: @$($me.result.username)"
    } catch {
        Warn "api.telegram.org did not answer: wrong token, or Telegram is blocked on this network."
        $proxy = (Read-Host "    Proxy for Telegram (http://user:pass@host:port or socks5://...), Enter to skip").Trim()
    }

    $ykey = Read-Secret "2/4 YandexGPT API key (Enter = demo mode without AI; input hidden)"
    $folder = ""
    $provider = "mock"
    if ($ykey) {
        $folder = (Read-Host "3/4 Yandex Cloud folder ID (starts with b1...)").Trim()
        $provider = "yandex"
        try {
            $body = @{ modelUri = "gpt://$folder/yandexgpt/latest"; completionOptions = @{ maxTokens = "5" };
                       messages = @(@{ role = "user"; text = "ok" }) } | ConvertTo-Json -Depth 5
            Invoke-RestMethod -Method Post -Uri "https://llm.api.cloud.yandex.net/foundationModels/v1/completion" `
                -Headers @{ Authorization = "Api-Key $ykey"; "x-folder-id" = $folder } `
                -ContentType "application/json" -Body $body -TimeoutSec 30 | Out-Null
            Write-Host "    YandexGPT answers OK"
        } catch {
            Warn "YandexGPT check failed: $($_.Exception.Message). Fix the key or folder ID later in .env"
        }
    } else {
        Warn "Demo mode: placeholder replies instead of AI. Add the YandexGPT key to .env later."
    }

    $admin = (Read-Host "4/4 Your Telegram ID for admin commands (ask @userinfobot), Enter to skip").Trim()
    $fernet = "$(& $VenvPy -m app.crypto)".Trim()
    $lines = @("BOT_TOKEN=$token", "FERNET_KEY=$fernet", "LLM_PROVIDER=$provider", "YANDEX_API_KEY=$ykey",
               "YANDEX_FOLDER_ID=$folder", "YANDEX_MODEL=yandexgpt/latest", "ADMIN_IDS=$admin",
               "POLL_INTERVAL_SEC=300", "MAX_ITEMS_PER_POLL=20", "FREE_MONTHLY_LIMIT=100",
               "DB_PATH=data/app.db", "TELEGRAM_PROXY=$proxy")
    [IO.File]::WriteAllLines($EnvFile, $lines)  # UTF-8 without BOM
    Warn "Keys saved to $EnvFile. Back it up: without FERNET_KEY connected shops cannot be decrypted."
}

# ---- 3. Optional autostart at Windows logon
$startup = Join-Path ([Environment]::GetFolderPath("Startup")) "empire-bot.cmd"
if (-not (Test-Path $startup)) {
    $a = Read-Host "Start the bot automatically when you log in to Windows? (y/N)"
    if ($a -match '^[yY]') {
        [IO.File]::WriteAllLines($startup, @("@echo off", "start `"EMPIRE bot`" /min `"$PSScriptRoot\start.bat`""))
        Write-Host "    Autostart on. To turn it off delete: $startup"
    }
}

# ---- 4. Run, restarting after crashes
Step "Starting the bot. Open it in Telegram and send /start."
Warn "Keep this window open and do not let the PC sleep (Settings > System > Power > Sleep: Never)."
while ($true) {
    & $VenvPy -m app.main
    Warn "Bot stopped (exit code $LASTEXITCODE). Restarting in 10 seconds - close this window to stop."
    Start-Sleep -Seconds 10
}

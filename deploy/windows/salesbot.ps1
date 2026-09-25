# Бот продаж WINTER ARC на Windows. Запускается через start_salesbot.bat.
$ErrorActionPreference = "Continue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
# Работает и из папки репозитория (deploy\windows), и из распакованного архива (корень)
$Root = if (Test-Path (Join-Path $PSScriptRoot "salesbot")) { $PSScriptRoot } else { (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path }
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

# ---- 1. Python и зависимости
if (-not (Test-Path $VenvPy)) {
    Step "Ищу Python 3.10+"
    $py = $null
    if (Test-Py "py" @("-3")) { $py = @("py", "-3") } elseif (Test-Py "python" @()) { $py = @("python") }
    if (-not $py) {
        Warn "Python не найден. Ставлю Python 3.12 через winget..."
        winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
        Warn "Python установлен. Закройте окно и снова запустите start_salesbot.bat."
        exit 1
    }
    & $py[0] @($py | Select-Object -Skip 1) -m venv .venv
}
Step "Устанавливаю зависимости (первый раз 1-2 минуты)"
& $VenvPy -m pip install -q --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { Warn "Не удалось установить зависимости - проверьте интернет и запустите снова"; exit 1 }

# ---- 2. Настройки: спрашиваю только то, чего нет в .env.salesbot
$firstRun = -not (Test-Path $EnvFile)
if ($firstRun -and (Test-Path "$EnvFile.example")) { Copy-Item "$EnvFile.example" $EnvFile }
$cfg = [ordered]@{ SALES_BOT_TOKEN = ""; TABLE_URL = ""; PRICE_STARS = "149"; ADMIN_IDS = ""; SUPPORT_CONTACT = "";
                   WELCOME_VIDEO_URL = ""; SALES_DB = "data/sales.db"; TELEGRAM_PROXY = "" }
if (Test-Path $EnvFile) {
    foreach ($line in Get-Content $EnvFile -Encoding UTF8) {
        if ($line -match '^\s*([A-Z_]+)\s*=(.*)$') { $cfg[$Matches[1]] = $Matches[2].Trim() }
    }
}
$changed = $false
while (-not ($cfg.SALES_BOT_TOKEN -match '^[0-9]+:[A-Za-z0-9_-]{30,}$')) {
    Step "ТОКЕН БОТА"
    Write-Host "Откройте @BotFather -> /newbot (или /mybots -> ваш бот -> API Token) и скопируйте токен."
    Write-Host "Вставьте его сюда: Ctrl+V или правый клик мыши, затем Enter. Вместо символов будут звёздочки - так и надо."
    $cfg.SALES_BOT_TOKEN = Read-Secret "Токен"
    $changed = $true
    if (-not ($cfg.SALES_BOT_TOKEN -match '^[0-9]+:[A-Za-z0-9_-]{30,}$')) { Warn "Не похоже на токен (вид: 123456789:AAH...). Ещё раз." }
}
while (-not ($cfg.TABLE_URL -match '^https://docs\.google\.com/')) {
    Step "ССЫЛКА НА ТАБЛИЦУ"
    Write-Host "Ссылка вида https://docs.google.com/spreadsheets/d/.../copy (её печатает setup() в Apps Script)."
    $cfg.TABLE_URL = (Read-Host "Ссылка").Trim()
    $changed = $true
}
if ($firstRun) {
    $p = (Read-Host "Цена в звёздах Telegram (Enter = $($cfg.PRICE_STARS))").Trim()
    if ($p -match '^[0-9]+$') { $cfg.PRICE_STARS = $p }
    $cfg.ADMIN_IDS = (Read-Host "Ваш Telegram ID для уведомлений о продажах (узнать у @userinfobot), Enter - пропустить").Trim()
    $cfg.SUPPORT_CONTACT = (Read-Host "Контакт поддержки для покупателей, например @ваш_ник").Trim()
    $changed = $true
}
if ($changed) {
    $out = @("# Настройки бота продаж WINTER ARC. Токен - в строке SALES_BOT_TOKEN= (без пробелов и кавычек).")
    foreach ($k in $cfg.Keys) { $out += "$k=$($cfg[$k])" }
    [IO.File]::WriteAllLines($EnvFile, $out)  # UTF-8 без BOM
    Warn "Сохранено в $EnvFile - поменять токен или цену можно там же в Блокноте."
}

# ---- 3. Запуск с автоперезапуском
Step "Запускаю бота. Не закрывайте это окно."
while ($true) {
    & $VenvPy -m salesbot.bot
    Warn "Бот остановился (код $LASTEXITCODE). Перезапуск через 10 секунд - закройте окно, чтобы остановить."
    Start-Sleep -Seconds 10
}

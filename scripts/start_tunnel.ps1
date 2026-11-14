# Public demo link for the CRM on this computer: restarts the server with an access code and a daily model budget,
# then opens a Cloudflare quick tunnel (no account; the link changes at every start). Close both windows to stop.
#   powershell -ExecutionPolicy Bypass -File scripts/start_tunnel.ps1 [-AccessCode <code>] [-Budget 3]
param([string]$AccessCode = "", [string]$Budget = "3")
$ErrorActionPreference = "Stop"
$kit = Split-Path -Parent $PSScriptRoot
$cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $cf) { $cf = Join-Path $env:LOCALAPPDATA "cloudflared\cloudflared.exe" }
if (-not (Test-Path $cf)) { throw "cloudflared not found: get cloudflared-windows-amd64.exe from https://github.com/cloudflare/cloudflared/releases" }
# no 0, 1, l or o: the code is read aloud and typed by hand
if (-not $AccessCode) { $AccessCode = -join ((50..57) + (97..107) + (109..110) + (112..122) | Get-Random -Count 10 | ForEach-Object { [char]$_ }) }

# a server without the code must never sit behind the public link: stop whatever listens on 8787 first
Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Process powershell -ArgumentList @('-NoExit', '-NoProfile', '-Command', "Set-Location -LiteralPath '$kit'; `$host.UI.RawUI.WindowTitle = 'Orbita CRM server :8787 (access code on)'; `$env:ORBITA_ACCESS_CODE = '$AccessCode'; `$env:ORBITA_DAILY_BUDGET_USD = '$Budget'; node mockups/server.mjs")

$log = Join-Path $env:LOCALAPPDATA "cloudflared\tunnel.log"
# a tunnel still open from an earlier start keeps its link: only the server restarts (close its window for a new link)
$open = Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" | Where-Object { $_.CommandLine -like '*--url http://127.0.0.1:8787*' }
if (-not $open) {
  Remove-Item $log -ErrorAction SilentlyContinue
  Start-Process powershell -ArgumentList @('-NoExit', '-NoProfile', '-Command', "`$host.UI.RawUI.WindowTitle = 'Orbita public link (Cloudflare tunnel)'; & '$cf' tunnel --no-autoupdate --url http://127.0.0.1:8787 --logfile '$log'")
}

$url = $null
for ($i = 0; $i -lt 60 -and -not $url; $i++) {
  Start-Sleep 1
  if (Test-Path $log) { $m = Select-String -Path $log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' | Select-Object -First 1; if ($m) { $url = $m.Matches[0].Value } }
}
if (-not $url) { throw "No link after 60 s: look at the 'Orbita public link' window." }
"Share this link (opens the CRM in one click): $url/?code=$AccessCode"
"Access code, if someone opens the bare address: $AccessCode"
"It lives while this computer is awake and both windows stay open."

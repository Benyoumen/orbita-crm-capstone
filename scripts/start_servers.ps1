# Starts the two local servers, each in its own window (close a window to stop its server).
#   powershell -ExecutionPolicy Bypass -File scripts/start_servers.ps1
#   Orbita CRM (the page, live agent):  http://localhost:8787
#   Error discovery (trace review):     http://127.0.0.1:8790
$kit = Split-Path -Parent $PSScriptRoot
Start-Process powershell -ArgumentList @('-NoExit', '-NoProfile', '-Command', "Set-Location -LiteralPath '$kit'; `$host.UI.RawUI.WindowTitle = 'Orbita CRM server :8787'; node mockups/server.mjs")
Start-Process powershell -ArgumentList @('-NoExit', '-NoProfile', '-Command', "Set-Location -LiteralPath '$kit'; `$host.UI.RawUI.WindowTitle = 'Error discovery app :8790'; python eval/error_discovery/server.py")

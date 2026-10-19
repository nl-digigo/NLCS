# build.ps1 - Bouw de NLCS Exporter tool tot een losse .exe
#
# Gebruik (vanuit deze map):
#     powershell -ExecutionPolicy Bypass -File .\build.ps1
#
# Resultaat: dist\NLCS-Exporter.exe (dubbelklikbaar, geen console).
# De tool draait de 'publicatie'-SPARQL-queries rechtstreeks (alleen `requests`);
# de .rq-queries worden live uit de door de gebruiker gekozen repo-map gelezen,
# dus niets wordt meegebundeld behalve de code zelf.

$ErrorActionPreference = "Stop"

$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Python niet gevonden op $py. Pas het pad in build.ps1 aan."
}

& $py -m pip install --quiet --upgrade pyinstaller requests pillow
if ($LASTEXITCODE -ne 0) { Write-Error "pip install mislukte." }

Remove-Item -Recurse -Force build, "NLCS-Exporter.spec" -ErrorAction SilentlyContinue
Remove-Item -Force "dist\NLCS-Exporter.exe" -ErrorAction SilentlyContinue

$iconArgs = @()
if (Test-Path "groen.ico") { $iconArgs = @("--icon", "groen.ico") }

& $py -m PyInstaller `
    --onefile `
    --windowed `
    --name "NLCS-Exporter" `
    @iconArgs `
    main.py
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller-build mislukte." }

Remove-Item -Recurse -Force build, "NLCS-Exporter.spec", __pycache__ -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Klaar. De executable staat in:  dist\NLCS-Exporter.exe" -ForegroundColor Green

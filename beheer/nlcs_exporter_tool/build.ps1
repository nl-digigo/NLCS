# build.ps1 - Bouw de NLCS Exporter tool tot een losse .exe
#
# Gebruik (vanuit deze map):
#     powershell -ExecutionPolicy Bypass -File .\build.ps1
#
# Resultaat: dist\NLCS-Exporter.exe (dubbelklikbaar, geen console).
# De tool hergebruikt code\nlcs\nlcs_exporter\nlcs_exporter.py (+ html_exporter.py,
# utils.py) ONGEWIJZIGD; die worden in de .exe meegebundeld. De queries (.rq) en de
# uitvoer lopen via de door de gebruiker gekozen repo-/uitvoermap.

$ErrorActionPreference = "Stop"

$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Python niet gevonden op $py. Pas het pad in build.ps1 aan."
}

& $py -m pip install --quiet --upgrade pyinstaller requests pandas pillow
if ($LASTEXITCODE -ne 0) { Write-Error "pip install mislukte." }

$exdir = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\code\nlcs\nlcs_exporter"))
if (-not (Test-Path $exdir)) { Write-Error "nlcs_exporter-map niet gevonden op $exdir" }

$addData = @()
foreach ($f in @("nlcs_exporter.py", "html_exporter.py", "utils.py")) {
    $p = Join-Path $exdir $f
    if (Test-Path $p) { $addData += @("--add-data", "$p;.") }
}

Remove-Item -Recurse -Force build, "NLCS-Exporter.spec" -ErrorAction SilentlyContinue
Remove-Item -Force "dist\NLCS-Exporter.exe" -ErrorAction SilentlyContinue

$iconArgs = @()
if (Test-Path "groen.ico") { $iconArgs = @("--icon", "groen.ico") }

& $py -m PyInstaller `
    --onefile `
    --windowed `
    --name "NLCS-Exporter" `
    --collect-submodules pandas `
    @addData `
    @iconArgs `
    main.py
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller-build mislukte." }

Remove-Item -Recurse -Force build, "NLCS-Exporter.spec", __pycache__ -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Klaar. De executable staat in:  dist\NLCS-Exporter.exe" -ForegroundColor Green

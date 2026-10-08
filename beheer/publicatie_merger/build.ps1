# build.ps1 - Bouw de NLCS Publicatie-Merger tool tot een losse .exe
#
# Gebruik (vanuit deze map):
#     powershell -ExecutionPolicy Bypass -File .\build.ps1
#
# Resultaat: dist\NLCS-Publicatie-Merger.exe (dubbelklikbaar, geen console).
# De tool hergebruikt code\nlcs\split\merger\publication_merger.py; die kopie
# wordt in de .exe meegebundeld (het origineel wordt niet aangepast).

$ErrorActionPreference = "Stop"

$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Python niet gevonden op $py. Pas het pad in build.ps1 aan."
}

# PyInstaller + runtime-dependencies (rdflib trekt pyparsing e.d. mee)
& $py -m pip install --quiet --upgrade pyinstaller requests rdflib
if ($LASTEXITCODE -ne 0) { Write-Error "pip install mislukte." }

# publication_merger.py meebundelen (relatief t.o.v. deze map: ..\..\code\...)
$merger = Join-Path $PSScriptRoot "..\..\code\nlcs\split\merger\publication_merger.py"
$merger = [System.IO.Path]::GetFullPath($merger)
if (-not (Test-Path $merger)) {
    Write-Error "publication_merger.py niet gevonden op $merger"
}

# Oude build opruimen
Remove-Item -Recurse -Force build, "NLCS-Publicatie-Merger.spec" -ErrorAction SilentlyContinue
Remove-Item -Force "dist\NLCS-Publicatie-Merger.exe" -ErrorAction SilentlyContinue

$iconArgs = @()
if (Test-Path "digigo.ico") { $iconArgs = @("--icon", "digigo.ico") }

# Bouwen: 1 bestand, geen console. rdflib gebruikt plugin-metadata ->
# --collect-all + --copy-metadata zodat (de)serializers in de .exe werken.
& $py -m PyInstaller `
    --onefile `
    --windowed `
    --name "NLCS-Publicatie-Merger" `
    --collect-all rdflib `
    --copy-metadata rdflib `
    --add-data "$merger;." `
    @iconArgs `
    main.py
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller-build mislukte." }

Remove-Item -Recurse -Force build, "NLCS-Publicatie-Merger.spec", __pycache__ -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Klaar. De executable staat in:  dist\NLCS-Publicatie-Merger.exe" -ForegroundColor Green

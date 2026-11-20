# build.ps1 - Bouw de changelog-tool tot TWEE losse .exe's (twee families):
#   dist\NLCS-Changelog.exe      (rode C)  - objecten/symbolen/lijntypes/
#                                             arceringen + Controles + Overzicht
#   dist\Mapping-Changelog.exe   (blauwe C) - classificatie-pagina + BGT-mapping
#                                             (tabelpagina + changelog)
#
# Gebruik (vanuit deze map):
#     powershell -ExecutionPolicy Bypass -File .\build.ps1
#
# config-nlcs.json / config-mapping.json worden naast de .exe aangemaakt.

$ErrorActionPreference = "Stop"

$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Python niet gevonden op $py. Pas het pad in build.ps1 aan."
}

# rdflib: nodig voor de GWSW-URI-check (TTL-parsing) in de Mapping-Changelog.
& $py -m pip install --quiet --upgrade pyinstaller openpyxl pillow rdflib
if ($LASTEXITCODE -ne 0) { Write-Error "pip install mislukte." }

# Prototype-HTML dat gen_classificatie_html.py als sjabloon leest (classificatie-
# pagina). Zonder --add-data vindt de .exe het niet.
$dataArgs = @()
if (Test-Path "classificatie-prototype.html") {
    $dataArgs = @("--add-data", "classificatie-prototype.html;.")
}

# (naam, entrypoint, icoon, rdflib nodig?). Alleen de Mapping-Changelog gebruikt
# de GWSW-URI-check (rdflib); de NLCS-Changelog roept die nooit aan.
$targets = @(
    @{ name = "NLCS-Changelog";    entry = "main_nlcs.py";    icon = "C-red.ico";  rdf = $false },
    @{ name = "Mapping-Changelog"; entry = "main_mapping.py"; icon = "C-blue.ico"; rdf = $true  }
)

foreach ($t in $targets) {
    Remove-Item -Recurse -Force build, "$($t.name).spec" -ErrorAction SilentlyContinue
    Remove-Item -Force "dist\$($t.name).exe" -ErrorAction SilentlyContinue

    $iconArgs = @()
    if (Test-Path $t.icon) { $iconArgs = @("--icon", $t.icon, "--add-data", "$($t.icon);.") }

    $rdfArgs = @()
    if ($t.rdf) { $rdfArgs = @("--collect-all", "rdflib", "--copy-metadata", "rdflib") }

    & $py -m PyInstaller `
        --onefile `
        --windowed `
        --name $t.name `
        --hidden-import openpyxl `
        @iconArgs `
        @dataArgs `
        @rdfArgs `
        $t.entry
    if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller-build van $($t.name) mislukte." }

    Remove-Item -Recurse -Force build, "$($t.name).spec", __pycache__ -ErrorAction SilentlyContinue
    Write-Host "Klaar: dist\$($t.name).exe" -ForegroundColor Green
}

Write-Host ""
Write-Host "Beide changelog-apps gebouwd in dist\." -ForegroundColor Green

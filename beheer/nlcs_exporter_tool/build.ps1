# build.ps1 - Bouw de Exporter tot TWEE losse .exe's (twee families):
#   dist\NLCS-Exporter.exe       (rode E)  - alleen NLCS-publicatie
#   dist\Mapping-Exporter.exe    (blauwe E) - BGT, GWSW, classificatie-RI
#
# Gebruik (vanuit deze map):
#     powershell -ExecutionPolicy Bypass -File .\build.ps1
#
# De .rq-queries worden live uit de door de gebruiker gekozen repo-map gelezen;
# alleen het familie-icoon wordt meegebundeld (voor het venstericoon).

$ErrorActionPreference = "Stop"

$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Python niet gevonden op $py. Pas het pad in build.ps1 aan."
}

& $py -m pip install --quiet --upgrade pyinstaller requests pillow
if ($LASTEXITCODE -ne 0) { Write-Error "pip install mislukte." }

# (naam, entrypoint, icoon)
$targets = @(
    @{ name = "NLCS-Exporter";    entry = "main_nlcs.py";    icon = "E-red.ico"  },
    @{ name = "Mapping-Exporter"; entry = "main_mapping.py"; icon = "E-blue.ico" }
)

foreach ($t in $targets) {
    Remove-Item -Recurse -Force build, "$($t.name).spec" -ErrorAction SilentlyContinue
    Remove-Item -Force "dist\$($t.name).exe" -ErrorAction SilentlyContinue

    $iconArgs = @()
    if (Test-Path $t.icon) { $iconArgs = @("--icon", $t.icon, "--add-data", "$($t.icon);.") }

    & $py -m PyInstaller `
        --onefile `
        --windowed `
        --name $t.name `
        @iconArgs `
        $t.entry
    if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller-build van $($t.name) mislukte." }

    Remove-Item -Recurse -Force build, "$($t.name).spec", __pycache__ -ErrorAction SilentlyContinue
    Write-Host "Klaar: dist\$($t.name).exe" -ForegroundColor Green
}

Write-Host ""
Write-Host "Beide exporters gebouwd in dist\." -ForegroundColor Green

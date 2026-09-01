# build.ps1 - Bouw de NLCS Objectentabellen-changelog tool tot een losse .exe
#
# Gebruik (vanuit deze map):
#     powershell -ExecutionPolicy Bypass -File .\build.ps1
#
# Resultaat: dist\NLCS-Objectchangelog.exe  (dubbelklikbaar, geen console-venster).
# config.json wordt naast de .exe aangemaakt zodra je het programma sluit.

$ErrorActionPreference = "Stop"

# Volledig pad naar de user-scope Python (niet op PATH)
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Python niet gevonden op $py. Pas het pad in build.ps1 aan."
}

# Zorg dat PyInstaller aanwezig is
& $py -m pip install --quiet --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { Write-Error "pip install mislukte." }

# Oude build opruimen (dist\ blijft staan zodat config.json bewaard blijft;
# alleen de oude .exe wordt weggegooid)
Remove-Item -Recurse -Force build, "NLCS-Objectchangelog.spec" -ErrorAction SilentlyContinue
Remove-Item -Force "dist\NLCS-Objectchangelog.exe" -ErrorAction SilentlyContinue

# Icoon (digiGO-badge); optioneel, alleen meenemen als het bestand bestaat
$iconArgs = @()
if (Test-Path "digigo.ico") { $iconArgs = @("--icon", "digigo.ico") }

# Bouwen: alles in 1 bestand, geen console-venster
& $py -m PyInstaller `
    --onefile `
    --windowed `
    --name "NLCS-Objectchangelog" `
    @iconArgs `
    main.py
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller-build mislukte." }

# Tussenbestanden opruimen; alleen dist\ met de .exe blijft over
Remove-Item -Recurse -Force build, "NLCS-Objectchangelog.spec", __pycache__ -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Klaar. De executable staat in:  dist\NLCS-Objectchangelog.exe" -ForegroundColor Green
Write-Host "Tussenmap 'build\' en 'NLCS-Objectchangelog.spec' zijn opgeruimd." -ForegroundColor Green

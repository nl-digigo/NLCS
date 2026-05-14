<#
.SYNOPSIS
    GitHub Issues Release Notes Query Tool (PowerShell versie)

.DESCRIPTION
    Dit script haalt alle gesloten issues op van de nl-digigo/NLCS GitHub repository
    en doorzoekt de comments op release note informatie.

    Output: een HTML-tabel en een CSV-bestand in beheer/changelog/

.NOTES
    Gebruik:
    1. Stel je GitHub token in als environment variable:
       $env:GITHUB_TOKEN = "jouw_token_hier"
    2. Draai het script:
       .\beheer\changelog\github_issues_release_notes.ps1

    PowerShell heeft GEEN extra installaties nodig - Invoke-RestMethod
    is ingebouwd en doet hetzelfde als Python's 'requests' library.
#>

# =============================================================================
# CONFIGURATIE
# =============================================================================

# GitHub repository gegevens
$RepoOwner = "nl-digigo"
$RepoName  = "NLCS"
$BaseUrl   = "https://api.github.com/repos/$RepoOwner/$RepoName"

# Output bestanden (relatief aan dit script)
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputCsv  = Join-Path $ScriptDir "release_notes_issues.csv"
$OutputHtml = Join-Path $ScriptDir "release_notes_issues.html"

# Zoekteksten voor release notes in comments
$ReleaseNoteTag = "[Release note]"
$NoChangeTag    = "[release note: no change from issue]"


# =============================================================================
# STAP 1: GitHub API verbinding opzetten
# =============================================================================

function Get-GitHubToken {
    <#
    .SYNOPSIS
        Leest het GitHub Personal Access Token uit de environment variable GITHUB_TOKEN.
        Stopt het script met een duidelijke foutmelding als het token niet is ingesteld.
    #>
    $token = $env:GITHUB_TOKEN

    if (-not $token) {
        Write-Host "FOUT: Environment variable GITHUB_TOKEN is niet ingesteld." -ForegroundColor Red
        Write-Host ""
        Write-Host "Stel deze in voordat je het script draait:"
        Write-Host '  $env:GITHUB_TOKEN = "jouw_token_hier"'
        exit 1
    }

    return $token
}


function New-GitHubHeaders {
    <#
    .SYNOPSIS
        Maakt de HTTP headers aan die nodig zijn voor de GitHub API.
        Het token zorgt voor authenticatie (5000 requests/uur in plaats van 60).
    .PARAMETER Token
        Het GitHub Personal Access Token
    #>
    param([string]$Token)

    return @{
        "Authorization" = "token $Token"
        "Accept"        = "application/vnd.github.v3+json"
    }
}


function Invoke-GitHubApi {
    <#
    .SYNOPSIS
        Voert een GitHub API-call uit met automatische retry bij fouten.
        Dit is het PowerShell-equivalent van de Python requests Session met retry-logica.
    .PARAMETER Url
        De volledige URL om aan te roepen
    .PARAMETER Headers
        De HTTP headers met authenticatie
    .PARAMETER MaxRetries
        Maximaal aantal pogingen (standaard 5)
    #>
    param(
        [string]$Url,
        [hashtable]$Headers,
        [int]$MaxRetries = 5
    )

    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            # Invoke-RestMethod is het PowerShell-equivalent van requests.get()
            # Het parst automatisch JSON naar PowerShell objecten
            $response = Invoke-RestMethod -Uri $Url -Headers $Headers -Method Get -TimeoutSec 30
            return $response
        }
        catch {
            if ($attempt -eq $MaxRetries) {
                Write-Host "  WAARSCHUWING: API-call mislukt na $MaxRetries pogingen: $Url" -ForegroundColor Yellow
                Write-Host "  Fout: $_" -ForegroundColor Yellow
                return $null
            }

            # Wacht steeds langer voor de volgende poging (exponential backoff)
            # Poging 1: 1s, Poging 2: 2s, Poging 3: 4s, etc.
            $waitSeconds = [Math]::Pow(2, $attempt - 1)
            Write-Host "  Poging $attempt mislukt, opnieuw proberen na ${waitSeconds}s..." -ForegroundColor Yellow
            Start-Sleep -Seconds $waitSeconds
        }
    }
}


# =============================================================================
# STAP 2: Alle gesloten issues ophalen (met paginering)
# =============================================================================

function Get-AllClosedIssues {
    <#
    .SYNOPSIS
        Haalt ALLE gesloten issues op uit de repository.
        De GitHub API geeft maximaal 100 issues per keer terug (per 'pagina').
        We moeten dus meerdere pagina's ophalen totdat er geen resultaten meer zijn.
    .PARAMETER Headers
        De HTTP headers met authenticatie
    #>
    param([hashtable]$Headers)

    $allIssues = @()
    $page = 1

    Write-Host "Issues ophalen van $RepoOwner/$RepoName..."

    while ($true) {
        # Bouw de URL met parameters:
        # - state=closed  -> alleen gesloten issues
        # - per_page=100  -> maximaal 100 per pagina (het maximum van de API)
        # - page=N        -> welke pagina we willen
        $url = "$BaseUrl/issues?state=closed&per_page=100&page=$page"

        $issuesOnPage = Invoke-GitHubApi -Url $url -Headers $Headers

        # Als de pagina leeg is of er geen resultaat is, zijn we klaar
        if (-not $issuesOnPage -or $issuesOnPage.Count -eq 0) {
            break
        }

        # Filter pull requests eruit - de GitHub Issues API geeft ook PRs terug.
        # Een issue is een PR als het een "pull_request" eigenschap heeft.
        $realIssues = $issuesOnPage | Where-Object { -not $_.pull_request }

        $allIssues += $realIssues
        $count = @($realIssues).Count
        Write-Host "  Pagina ${page}: $count issues opgehaald (totaal: $($allIssues.Count))"

        $page++

        # Korte pauze om de API niet te overbelasten
        Start-Sleep -Milliseconds 300
    }

    Write-Host "Totaal: $($allIssues.Count) gesloten issues gevonden.`n"
    return $allIssues
}


# =============================================================================
# STAP 3: Comments ophalen en doorzoeken per issue
# =============================================================================

function Get-CommentsForIssue {
    <#
    .SYNOPSIS
        Haalt alle comments op voor een specifiek issue nummer.
    .PARAMETER IssueNumber
        Het nummer van de issue
    .PARAMETER Headers
        De HTTP headers met authenticatie
    #>
    param(
        [int]$IssueNumber,
        [hashtable]$Headers
    )

    $allComments = @()
    $page = 1

    while ($true) {
        $url = "$BaseUrl/issues/$IssueNumber/comments?per_page=100&page=$page"

        $commentsOnPage = Invoke-GitHubApi -Url $url -Headers $Headers

        if (-not $commentsOnPage -or $commentsOnPage.Count -eq 0) {
            break
        }

        $allComments += $commentsOnPage
        $page++

        # Korte pauze
        Start-Sleep -Milliseconds 200
    }

    return $allComments
}


function Search-CommentsForReleaseNotes {
    <#
    .SYNOPSIS
        Doorzoekt de comments van een issue op release note informatie.
        Zoekt naar:
        1. Een comment die '[Release note]' bevat         -> ReleaseNote
        2. Een comment die '[release note: no change from issue]' bevat -> NoChange
        3. De laatste comment (als fallback)              -> LastComment
    .PARAMETER Comments
        Array met comment objecten van de GitHub API
    #>
    param([array]$Comments)

    $releaseNoteText = ""
    $noChangeText    = ""
    $lastCommentText = ""

    # Doorloop alle comments
    foreach ($comment in $Comments) {
        $body = if ($comment.body) { $comment.body } else { "" }

        # Zoek naar [Release note] (case-insensitive)
        # In PowerShell is -like standaard case-insensitive
        if ($body -match [regex]::Escape($ReleaseNoteTag)) {
            $releaseNoteText = $body.Trim()
        }

        # Zoek naar [release note: no change from issue] (case-insensitive)
        if ($body -match [regex]::Escape($NoChangeTag)) {
            $noChangeText = $body.Trim()
        }
    }

    # De laatste comment (als er comments zijn)
    if ($Comments -and $Comments.Count -gt 0) {
        $lastBody = if ($Comments[-1].body) { $Comments[-1].body } else { "" }
        $lastCommentText = $lastBody.Trim()
    }

    # Fallback logica: de laatste comment wordt alleen gebruikt als BEIDE
    # releaseNoteText EN noChangeText leeg zijn
    if ($releaseNoteText -or $noChangeText) {
        $lastCommentText = ""
    }

    return @{
        ReleaseNote = $releaseNoteText
        NoChange    = $noChangeText
        LastComment = $lastCommentText
    }
}


# =============================================================================
# STAP 4: Data verzamelen voor alle issues
# =============================================================================

function Process-AllIssues {
    <#
    .SYNOPSIS
        Verwerkt alle issues: haalt comments op en bouwt de data-rijen op.
    .PARAMETER Issues
        Array met issue objecten van de GitHub API
    .PARAMETER Headers
        De HTTP headers met authenticatie
    #>
    param(
        [array]$Issues,
        [hashtable]$Headers
    )

    $rows = @()
    $total = $Issues.Count

    for ($i = 0; $i -lt $total; $i++) {
        $issue = $Issues[$i]
        $issueNumber = $issue.number
        $issueUrl    = $issue.html_url

        # Milestone (kan $null zijn als er geen milestone is)
        $milestone = ""
        if ($issue.milestone) {
            $milestone = $issue.milestone.title
        }

        # Labels: gescheiden door ' | ' (pipe)
        $labels = ""
        if ($issue.labels -and $issue.labels.Count -gt 0) {
            $labels = ($issue.labels | ForEach-Object { $_.name }) -join " | "
        }

        # Voortgang tonen
        $index = $i + 1
        Write-Host "  [$index/$total] Issue #$issueNumber verwerken..."

        # Comments ophalen
        $comments = @(Get-CommentsForIssue -IssueNumber $issueNumber -Headers $Headers)

        # Comments doorzoeken op release note patronen
        $releaseNoteResult = Search-CommentsForReleaseNotes -Comments $comments

        # Data-rij toevoegen als een custom object
        $rows += [PSCustomObject]@{
            IssueNumber = $issueNumber
            IssueUrl    = $issueUrl
            Milestone   = $milestone
            Labels      = $labels
            ReleaseNote = $releaseNoteResult.ReleaseNote
            NoChange    = $releaseNoteResult.NoChange
            LastComment = $releaseNoteResult.LastComment
        }
    }

    return $rows
}


# =============================================================================
# STAP 5: Sorteren
# =============================================================================

function Sort-Rows {
    <#
    .SYNOPSIS
        Sorteert de rijen op:
        1. Milestone (alfabetisch, issues ZONDER milestone komen onderaan)
        2. Issue nummer (oplopend)
    .PARAMETER Rows
        Array met data-objecten
    #>
    param([array]$Rows)

    # Sorteer met een custom expressie:
    # - Eerst: heeft het een milestone? (0=ja, 1=nee) -> zonder milestone onderaan
    # - Dan: milestone naam (alfabetisch)
    # - Dan: issue nummer (oplopend)
    $sorted = $Rows | Sort-Object -Property @(
        @{ Expression = { if ($_.Milestone) { 0 } else { 1 } }; Ascending = $true }
        @{ Expression = { $_.Milestone.ToLower() }; Ascending = $true }
        @{ Expression = { $_.IssueNumber }; Ascending = $true }
    )

    return $sorted
}


# =============================================================================
# STAP 6: CSV genereren
# =============================================================================

function Export-CsvFile {
    <#
    .SYNOPSIS
        Genereert een CSV-bestand met puntkomma als scheidingsteken.
        Puntkomma wordt gebruikt zodat het bestand correct opent in Excel.
    .PARAMETER Rows
        Gesorteerde array met data-objecten
    .PARAMETER FilePath
        Pad waar het CSV-bestand wordt opgeslagen
    #>
    param(
        [array]$Rows,
        [string]$FilePath
    )

    # StringBuilder voor efficiënt strings samenvoegen
    $sb = [System.Text.StringBuilder]::new()

    # BOM (Byte Order Mark) wordt automatisch toegevoegd door UTF8 encoding met BOM
    # Header rij
    [void]$sb.AppendLine('"Issue";"Milestone";"Labels";"Release Note";"No Change";"Laatste Comment"')

    # Data rijen
    foreach ($row in $Rows) {
        # Escape dubbele aanhalingstekens in de data (verdubbelen)
        $issue      = "#$($row.IssueNumber)" -replace '"', '""'
        $milestone  = $row.Milestone -replace '"', '""'
        $labels     = $row.Labels -replace '"', '""'
        $relNote    = $row.ReleaseNote -replace '"', '""'
        $noChange   = $row.NoChange -replace '"', '""'
        $lastCom    = $row.LastComment -replace '"', '""'

        [void]$sb.AppendLine("""$issue"";""$milestone"";""$labels"";""$relNote"";""$noChange"";""$lastCom""")
    }

    # Schrijf met UTF-8 BOM (zodat Excel het correct herkent)
    $utf8Bom = [System.Text.Encoding]::UTF8
    [System.IO.File]::WriteAllText($FilePath, $sb.ToString(), $utf8Bom)

    Write-Host "CSV opgeslagen: $FilePath"
}


# =============================================================================
# STAP 7: HTML tabel genereren
# =============================================================================

function ConvertTo-HtmlSafe {
    <#
    .SYNOPSIS
        Vervangt speciale HTML-tekens zodat ze correct worden weergegeven.
        Bijvoorbeeld: < wordt &lt; zodat het niet als HTML-tag wordt gezien.
    .PARAMETER Text
        De tekst om te escapen
    #>
    param([string]$Text)

    return $Text.
        Replace("&", "&amp;").
        Replace("<", "&lt;").
        Replace(">", "&gt;").
        Replace('"', "&quot;").
        Replace("`n", "<br>")
}


function Export-HtmlFile {
    <#
    .SYNOPSIS
        Genereert een HTML-bestand met een gestileerde tabel.
        Issue nummers worden als klikbare links weergegeven.
    .PARAMETER Rows
        Gesorteerde array met data-objecten
    .PARAMETER FilePath
        Pad waar het HTML-bestand wordt opgeslagen
    #>
    param(
        [array]$Rows,
        [string]$FilePath
    )

    $totalCount = $Rows.Count

    # StringBuilder voor efficiënt strings samenvoegen
    $sb = [System.Text.StringBuilder]::new()

    # HTML header met styling
    [void]$sb.Append(@"
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NLCS GitHub Issues - Release Notes</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            margin: 20px;
            background-color: #f6f8fa;
        }
        h1 {
            color: #24292e;
        }
        .info {
            color: #586069;
            margin-bottom: 20px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        th {
            background-color: #24292e;
            color: white;
            padding: 10px 12px;
            text-align: left;
            position: sticky;
            top: 0;
        }
        td {
            padding: 8px 12px;
            border-bottom: 1px solid #e1e4e8;
            vertical-align: top;
            max-width: 400px;
            overflow-wrap: break-word;
        }
        tr:hover {
            background-color: #f1f8ff;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .milestone {
            background-color: #e1e4e8;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.85em;
        }
        .label {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
            background-color: #d1ecf1;
            margin: 1px;
        }
    </style>
</head>
<body>
    <h1>NLCS GitHub Issues - Release Notes</h1>
    <p class="info">Totaal: $totalCount gesloten issues |
    Gesorteerd op milestone, daarna op issue nummer</p>
    <table>
        <thead>
            <tr>
                <th>Issue</th>
                <th>Milestone</th>
                <th>Labels</th>
                <th>Release Note</th>
                <th>No Change</th>
                <th>Laatste Comment</th>
            </tr>
        </thead>
        <tbody>
"@)

    # Tabel rijen
    foreach ($row in $Rows) {
        $issueLink = "<a href=`"$($row.IssueUrl)`" target=`"_blank`">#$($row.IssueNumber)</a>"

        $milestoneHtml = ""
        if ($row.Milestone) {
            $milestoneHtml = "<span class=`"milestone`">$(ConvertTo-HtmlSafe $row.Milestone)</span>"
        }

        # Labels als individuele badges
        $labelsHtml = ""
        if ($row.Labels) {
            $labelList = $row.Labels -split " \| "
            $labelsHtml = ($labelList | ForEach-Object {
                "<span class=`"label`">$(ConvertTo-HtmlSafe $_)</span>"
            }) -join " "
        }

        [void]$sb.AppendLine(@"
            <tr>
                <td>$issueLink</td>
                <td>$milestoneHtml</td>
                <td>$labelsHtml</td>
                <td>$(ConvertTo-HtmlSafe $row.ReleaseNote)</td>
                <td>$(ConvertTo-HtmlSafe $row.NoChange)</td>
                <td>$(ConvertTo-HtmlSafe $row.LastComment)</td>
            </tr>
"@)
    }

    # HTML afsluiten
    [void]$sb.Append(@"
        </tbody>
    </table>
</body>
</html>
"@)

    [System.IO.File]::WriteAllText($FilePath, $sb.ToString(), [System.Text.Encoding]::UTF8)

    Write-Host "HTML opgeslagen: $FilePath"
}


# =============================================================================
# HOOFDPROGRAMMA
# =============================================================================

Write-Host ("=" * 60)
Write-Host "NLCS GitHub Issues - Release Notes Generator (PowerShell)"
Write-Host ("=" * 60)
Write-Host ""

# Stap 1: Token ophalen
$token   = Get-GitHubToken
$headers = New-GitHubHeaders -Token $token

# Stap 2: Alle gesloten issues ophalen
$issues = @(Get-AllClosedIssues -Headers $headers)

if ($issues.Count -eq 0) {
    Write-Host "Geen gesloten issues gevonden. Script stopt."
    exit 0
}

# Stap 3: Comments verwerken per issue
Write-Host "Comments ophalen en doorzoeken..."
$rows = @(Process-AllIssues -Issues $issues -Headers $headers)

# Stap 4: Sorteren
Write-Host "`nResultaten sorteren..."
$sortedRows = @(Sort-Rows -Rows $rows)

# Stap 5: CSV genereren
Write-Host "`nOutput genereren..."
Export-CsvFile -Rows $sortedRows -FilePath $OutputCsv

# Stap 6: HTML genereren
Export-HtmlFile -Rows $sortedRows -FilePath $OutputHtml

Write-Host ""
Write-Host ("=" * 60)
Write-Host "Klaar!"
Write-Host "  CSV:  $OutputCsv"
Write-Host "  HTML: $OutputHtml"
Write-Host ("=" * 60)

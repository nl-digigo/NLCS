$issues = Import-Csv .\docs\changelog\releasenotes\issues_releasenotes.csv
 
$issues |

Select-Object `
number,
title,
state,
milestone,
labels,
release_notes |
ConvertTo-Html `
-Title "NLCS Release Notes" `
-PreContent "<h1>NLCS Release Notes</h1>" |
Set-Content .\releasenotes.html -Encoding UTF8
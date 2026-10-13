<#
.SYNOPSIS
    Create the v2.0.0 GitHub release and its milestone.
.DESCRIPTION
    Written as a file rather than typed inline: the release body contains
    backticks, asterisks and em dashes, all of which PowerShell mangles when a
    here-string is passed through the command line.
#>
$ErrorActionPreference = 'Stop'

$git = 'D:\Git\cmd\git.exe'
$repo = 'quxianp/RAiNBOW_Hello-World'
$root = Split-Path -Parent $PSScriptRoot

$cred = "protocol=https`nhost=github.com`n`n" | & $git credential fill 2>$null
$token = (($cred | Select-String '^password=') -replace '^password=', '').Trim()
if (-not $token) { throw 'no token in credential store' }

$headers = @{
    Authorization        = "Bearer $token"
    Accept               = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
    'User-Agent'         = 'rainbow-release'
}
$api = "https://api.github.com/repos/$repo"

function Post-Json($uri, $obj) {
    $json = $obj | ConvertTo-Json -Depth 6 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    Invoke-RestMethod -Uri $uri -Headers $headers -Method Post -Body $bytes `
        -ContentType 'application/json; charset=utf-8' -TimeoutSec 120
}

# ------------------------------------------------------------------ milestone
$milestones = @(Invoke-RestMethod -Uri "$api/milestones?state=all" -Headers $headers -TimeoutSec 60)
$ms = $milestones | Where-Object { $_.title -like 'v2.0.0*' } | Select-Object -First 1
if (-not $ms) {
    $ms = Post-Json "$api/milestones" @{
        title       = 'v2.0.0 -- the rainbow bar'
        description = '694 core languages, equal byte shares, hue-ordered. 19/19 acceptance checks passing.'
        state       = 'open'
    }
    Write-Host "milestone created: #$($ms.number)"
} else {
    Write-Host "milestone exists: #$($ms.number)"
}

# ------------------------------------------------------------------ release
$releases = @(Invoke-RestMethod -Uri "$api/releases" -Headers $headers -TimeoutSec 60)
$rel = $releases | Where-Object { $_.tag_name -eq 'v2.0.0' } | Select-Object -First 1
if ($rel) {
    Write-Host "release already exists: $($rel.html_url)"
} else {
    $bodyPath = Join-Path $root '.tmp\release_notes.md'
    if (-not (Test-Path $bodyPath)) { throw "missing $bodyPath" }
    $bodyText = [System.IO.File]::ReadAllText($bodyPath, [System.Text.Encoding]::UTF8)

    $rel = Post-Json "$api/releases" @{
        tag_name         = 'v2.0.0'
        target_commitish = 'main'
        name             = 'v2.0.0 -- the rainbow bar'
        body             = $bodyText
        draft            = $false
        prerelease       = $false
    }
    Write-Host "release created: $($rel.tag_name) -> $($rel.html_url)"
}

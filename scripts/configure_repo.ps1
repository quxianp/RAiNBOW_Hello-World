<#
.SYNOPSIS
    Configure every repository About field and feature GitHub exposes over the API.

.DESCRIPTION
    Idempotent: safe to re-run, and it reports what it changed rather than
    assuming.

    What it sets, and why:

      description  The About panel's first line. Must be <= 350 chars and is the
                   only text GitHub shows without opening the README, so it has
                   to carry the claim on its own.
      homepage     Links the repo to its canonical URL and renders in the sidebar.
      topics       Up to 20, lowercase, <= 50 chars, alphanumerics and hyphens.
                   These drive GitHub search and the topic explorer, so they are
                   the difference between the repository being findable or not.
      discussions  Issues are for bugs; questions belong in Discussions, which
                   also stops the issue tracker filling up with questions.
      wiki/projects  Made explicit rather than inherited from an account default.

    Not covered by the API and therefore NOT set here: branch protection, the
    repository social preview image, and Pages. Those need a browser or a
    separate permissions scope, and this script says so rather than appearing to
    succeed.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/configure_repo.ps1
#>

[CmdletBinding()]
param(
    [string]$Owner = 'quxianp',
    [string]$Repo  = 'RAiNBOW_Hello-World'
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------- auth
# git is not always on PATH (this machine keeps it at D:\Git\cmd\git.exe), so
# resolve it rather than assuming. A bare `git` call here failed on a machine
# where git demonstrably works.
$gitExe = (Get-Command git -ErrorAction SilentlyContinue).Source
if (-not $gitExe) {
    foreach ($cand in @(
        'D:\Git\cmd\git.exe', 'C:\Program Files\Git\cmd\git.exe',
        'C:\Program Files\Git\bin\git.exe', "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
    )) {
        if (Test-Path $cand) { $gitExe = $cand; break }
    }
}
if (-not $gitExe) {
    throw 'git not found on PATH or in the usual install locations'
}

$cred = "protocol=https`nhost=github.com`n`n" | & $gitExe credential fill 2>$null
if (-not $cred) { throw 'no git credential for github.com; run `git push` once first' }
$pass = (($cred | Select-String '^password=') -replace '^password=', '').Trim()
if (-not $pass) { throw 'credential store returned no password' }

$headers = @{
    Authorization        = "Bearer $pass"
    Accept               = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
    'User-Agent'         = 'RAiNBOW-configure-repo'
}
$base = "https://api.github.com/repos/$Owner/$Repo"

# ---------------------------------------------------------------- payloads
$description = 'Hello World in 7,326 files across 6,000+ languages, engineered so GitHub''s language bar is a rainbow: 694 Linguist-coloured languages, one per equal 2048-byte slice, ordered by hue.'

$homepage = 'https://github.com/quxianp/RAiNBOW_Hello-World#-the-show'

# Ordered so the most specific and most searchable come first.
$topics = @(
    'hello-world',
    'language-bar',
    'github-linguist',
    'rainbow',
    'polyglot',
    'programming-languages',
    'esolangs',
    'rosetta-code',
    'github-actions',
    'ascii-art',
    'terminal',
    'visualization',
    'beginner-friendly',
    'showcase',
    'demo',
    'fun',
    'awesome-list',
    'education',
    'code-golf',
    'interpreter'
)

function Invoke-Gh($method, $uri, $body) {
    $params = @{
        Uri         = $uri
        Headers     = $headers
        Method      = $method
        TimeoutSec  = 60
    }
    if ($null -ne $body) {
        $params.Body         = ($body | ConvertTo-Json -Depth 5 -Compress)
        $params.ContentType = 'application/json; charset=utf-8'
    }
    Invoke-RestMethod @params
}

$before = Invoke-RestMethod -Uri $base -Headers $headers -TimeoutSec 60

Write-Host "repository: $Owner/$Repo"
Write-Host "before: description='$($before.description)' homepage='$($before.homepage)' topics=$($before.topics.Count) discussions=$($before.has_discussions)"

# ---------------------------------------------------------------- patch repo
# One PATCH sets description, homepage, topics and the feature flags together,
# so the request cannot half-apply.
$payload = @{
    description       = $description
    homepage          = $homepage
    has_wiki          = $true
    has_projects      = $true
    has_discussions   = $true
    has_issues        = $true
    is_template       = $false
    allow_squash_merge = $true
    allow_merge_commit  = $true
    allow_rebase_merge  = $true
    delete_branch_on_merge = $true
}
# NOTE: `topics` is deliberately absent. It is accepted in the PATCH body and
# then silently ignored -- the response comes back with topics=[] while the rest
# of the patch applies. GitHub only honours it through
# PUT /repos/{owner}/{repo}/topics, which is called separately below.

try {
    $after = Invoke-Gh 'PATCH' $base $payload
    Write-Host 'PATCH ok'
} catch {
    Write-Host "PATCH failed: $($_.Exception.Message)"
    throw
}

Write-Host "after: description='$($after.description)'"
Write-Host "after: homepage='$($after.homepage)'"

# ---------------------------------------------------------------- topics
# Replaces the whole set, so this is idempotent rather than additive.
$topicBody = @{ names = $topics }
try {
    $t = Invoke-Gh 'PUT' "$base/topics" $topicBody
    Write-Host "topics: $($t.names.Count) -> $($t.names -join ', ')"
} catch {
    Write-Host "topics failed: $($_.Exception.Message)"
    throw
}

Write-Host "after: wiki=$($after.has_wiki) projects=$($after.has_projects) discussions=$($after.has_discussions) issues=$($after.has_issues)"

# ---------------------------------------------------------------- labels
# GitHub seeds only a handful of defaults. Labels are how issues get triaged, so
# define the ones this repo will actually use.
$labels = @(
    @{ name = 'bar';            color = '5319E7'; description = 'Something about the language bar, its segments or its colours' },
    @{ name = 'templates';      color = '0E8A16'; description = 'Hello World templates for a language' },
    @{ name = 'detection';      color = '1D76DB'; description = 'How Linguist detects or classifies a file' },
    @{ name = 'demo';           color = 'FBAB09'; description = 'The recorded demo, run.sh or the animations' },
    @{ name = 'ci';             color = 'D93F0B'; description = 'GitHub Actions, the workflow or its runners' },
    @{ name = 'documentation';  color = '0075CA'; description = 'README, docs/ or the FAQ' },
    @{ name = 'good first issue'; color = '7057FF'; description = 'Small, self-contained, easy to review' },
    @{ name = 'upstream';       color = 'B60205'; description = 'Belongs in github/linguist, not here' },
    @{ name = 'question';       color = 'C5DEF5'; description = 'Not a bug -- ask instead' },
    @{ name = 'wontfix';        color = 'FFFFFF'; description = 'Will not be done, with a reason given' }
)

$existing = @{}
foreach ($l in (Invoke-RestMethod -Uri "$base/labels?per_page=100" -Headers $headers -TimeoutSec 60)) {
    $existing[$l.name.ToLower()] = $true
}

$added = 0
$skipped = 0
foreach ($l in $labels) {
    if ($existing.ContainsKey($l.name.ToLower())) { $skipped++; continue }
    $body = @{ name = $l.name; color = $l.color; description = $l.description }
    try {
        Invoke-Gh 'POST' "$base/labels" $body | Out-Null
        Write-Host "  label + $($l.name)"
        $added++
    } catch {
        # GitHub answers 422 for a label that already exists. That is success
        # for an idempotent script, not a failure worth shouting about.
        $status = $null
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        if ($status -eq 422) {
            Write-Host "  label = $($l.name) (already present)"
            $skipped++
        } else {
            Write-Host "  label FAILED $($l.name): status=$status $($_.Exception.Message)"
        }
    }
}
Write-Host "labels added: $added, already present: $skipped"

# ---------------------------------------------------------------- report
Write-Host ''
Write-Host 'NOT set by this script (needs a browser or another scope):'
Write-Host '  - branch protection rules on main'
Write-Host '  - the social preview image (OpenGraph card)'
Write-Host '  - GitHub Pages, if a hosted site is wanted'
Write-Host '  - required status checks / merge queue settings'
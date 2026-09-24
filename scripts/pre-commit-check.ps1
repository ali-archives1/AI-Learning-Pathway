[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git'))) {
    Write-Error "Expected Git repository not found at $repoRoot"
    exit 1
}

$stagedFiles = @(& git -C $repoRoot diff --cached --name-only --diff-filter=ACMR)
if ($LASTEXITCODE -ne 0) {
    Write-Error 'Could not inspect staged files.'
    exit 1
}

$blockedPathPattern = '(?i)(^|/)(\.obsidian|private|personal)(/|$)|(^|/)(\.env($|\.)|credentials?[^/]*|secrets?[^/]*|id_rsa[^/]*|id_ed25519[^/]*|[^/]*\.(pem|key|p12|pfx|kdbx|gpg|age))$'
$textFilePattern = '(?i)(^|/)(AGENTS\.md|\.gitignore)$|\.(md|txt|json|ya?ml|toml|ini|cfg|ps1|sh|py|js|ts|tsx|jsx)$'
$secretPatterns = @(
    '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
    '(?i)\b(AKIA|ASIA)[A-Z0-9]{16}\b',
    '(?i)\b(ghp_|github_pat_|glpat-|xox[baprs]-|sk-)[A-Za-z0-9_\-]{16,}\b',
    '(?i)\b(api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*["'']?[A-Za-z0-9_\/+=.\-]{12,}'
)

$problems = [System.Collections.Generic.List[string]]::new()
foreach ($path in $stagedFiles) {
    $normalized = $path.Replace('\', '/')
    if ($normalized -match $blockedPathPattern) {
        $problems.Add("Blocked private or credential path: $path")
        continue
    }
    if ($normalized -notmatch $textFilePattern) { continue }

    $content = (& git -C $repoRoot show --format= ":$path" 2>$null) -join "`n"
    if ($LASTEXITCODE -ne 0) {
        $problems.Add("Could not scan staged file: $path")
        continue
    }
    foreach ($pattern in $secretPatterns) {
        if ($content -match $pattern) {
            $problems.Add("Possible secret in staged file: $path")
            break
        }
    }
}

if ($problems.Count -gt 0) {
    Write-Host 'Commit stopped for safety:' -ForegroundColor Red
    $problems | Sort-Object -Unique | ForEach-Object { Write-Host "- $_" -ForegroundColor Red }
    exit 1
}

Write-Host 'Pre-commit privacy check passed.'
exit 0

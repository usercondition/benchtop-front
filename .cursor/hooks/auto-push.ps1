# Auto-commit and push project changes when an agent turn ends.
# Reads Cursor stop-hook JSON from stdin (ignored) and exits 0 always so hooks stay fail-open.

$ErrorActionPreference = "Continue"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $root

# Drain stdin so the hook runner does not hang
try { [Console]::In.ReadToEnd() | Out-Null } catch {}

if (-not (Test-Path (Join-Path $root ".git"))) {
  exit 0
}

$status = git status --porcelain 2>$null
$ahead = git rev-list --count "@{u}..HEAD" 2>$null
if (-not $ahead) { $ahead = "0" }

if ([string]::IsNullOrWhiteSpace($status) -and $ahead -eq "0") {
  exit 0
}

if (-not [string]::IsNullOrWhiteSpace($status)) {
  git add -A
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
  git commit -m "chore: auto-sync $stamp"
}

$remote = git remote 2>$null
if ($remote -match "origin") {
  git push -u origin HEAD 2>&1 | Out-Null
}

exit 0

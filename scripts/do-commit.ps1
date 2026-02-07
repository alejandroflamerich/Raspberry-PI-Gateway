Param(
  [string]$MessageFile = "COMMIT_MESSAGE.txt"
)
if (-not (Test-Path $MessageFile)){
  Write-Error "Create $MessageFile with the commit message before running this script."
  exit 1
}

# Ensure we're inside a git repository; if not, initialize one.
$inside = $false
try {
  git rev-parse --is-inside-work-tree >$null 2>&1
  if ($LASTEXITCODE -eq 0) { $inside = $true }
} catch {
  $inside = $false
}

if (-not $inside) {
  Write-Host "No git repository found — initializing repository..."
  git init
  git branch -M main
  Write-Host "Initialized empty git repository and set branch to 'main'."
}

git add .

# Detect whether HEAD exists (has previous commits)
$hasHead = $false
try {
  git rev-parse --verify HEAD >$null 2>&1
  if ($LASTEXITCODE -eq 0) { $hasHead = $true }
} catch {}

if ($hasHead) {
  git commit -F $MessageFile | Out-Host
} else {
  $msg = Get-Content $MessageFile -Raw
  git commit -m $msg | Out-Host
}

Write-Host "Commit created. To push to remote, run: git remote add origin <url> ; git push -u origin main"
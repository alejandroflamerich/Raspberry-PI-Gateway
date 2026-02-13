<#
PowerShell helper to prepare and show how to push this workspace to GitHub.
Usage (PowerShell):
  .\scripts\push-to-github.ps1 -RemoteUrl "https://github.com/alejandroflamerich/Raspberry-PI-Gateway.git" -Branch main
Notes:
- This script will initialize git (if needed), add all files and create an initial commit.
- It will set the `origin` remote to the URL you pass but it will NOT embed any token.
- After running the script, run the printed `git push` command and provide credentials (or configure SSH/PAT).
#>
param(
    [string]$RemoteUrl = "https://github.com/alejandroflamerich/Raspberry-PI-Gateway.git",
    [string]$Branch = "main"
)

Write-Host "Preparing repository to push to $RemoteUrl (branch: $Branch)"

# initialize if needed
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..."
    git init
} else {
    Write-Host ".git already exists"
}

Write-Host "Adding files and creating commit..."
git add .
# Create commit if none exists
$hasCommits = git rev-parse --verify HEAD 2>$null
if ($LASTEXITCODE -ne 0) {
    git commit -m "Initial commit from local workspace"
} else {
    Write-Host "Repository already has commits; creating a new commit"
    git commit -m "Update: sync workspace" || Write-Host "No changes to commit"
}

Write-Host "Setting branch name to $Branch"
git branch -M $Branch 2>$null

# set remote
try { git remote remove origin 2>$null } catch {}
git remote add origin $RemoteUrl

Write-Host "Repository prepared. To push, run one of the commands below depending on your auth method:"
Write-Host "1) If using HTTPS and Git will prompt for username/password (or Personal Access Token), run:"
Write-Host "   git push -u origin $Branch"
Write-Host "2) If using a Personal Access Token non-interactively (UNSAFE to store inline), you can run:"
Write-Host "   git push https://<YOUR_TOKEN>@github.com/alejandroflamerich/Raspberry-PI-Gateway.git -u origin $Branch"
Write-Host "   (replace <YOUR_TOKEN> with a token that has repo permission)"
Write-Host "3) If you prefer SSH, set the remote to your SSH URL and then run the push command. Example:"
Write-Host "   git remote set-url origin git@github.com:alejandroflamerich/Raspberry-PI-Gateway.git"
Write-Host "   git push -u origin $Branch"

Write-Host "Done."

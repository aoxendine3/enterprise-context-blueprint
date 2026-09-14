# ==============================================================================
# XMARS.os — Standalone GitHub Repository Initializer (Windows)
# ==============================================================================

param(
    [string]$RepoName = "XMARS.os",
    [string]$Visibility = "private"
)

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  XMARS.os STANDALONE GITHUB REPOSITORY INITIALIZER" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

$currentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $currentDir

if (-not (Test-Path ".git")) {
    Write-Host "[*] Initializing local git repository..." -ForegroundColor Yellow
    git init
    git branch -M main
}

Write-Host "[*] Staging all XMARS.os files..." -ForegroundColor Yellow
git add .
git commit -m "feat(xmars): Initial commit of XMARS.os Sovereign Neural Command Operating System"

if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-Host "[*] GitHub CLI detected. Creating remote repository '$RepoName'..." -ForegroundColor Green
    gh repo create $RepoName --$Visibility --source=. --remote=origin --push
    Write-Host "[+] Repository created and synchronized successfully!" -ForegroundColor Green
} else {
    Write-Host "[!] GitHub CLI (gh) not detected." -ForegroundColor Yellow
    Write-Host "[*] To link to a remote GitHub repository manually:" -ForegroundColor Yellow
    Write-Host "    1. Create repository '$RepoName' at https://github.com/new"
    Write-Host "    2. Run: git remote add origin https://github.com/YOUR_USER/$RepoName.git"
    Write-Host "    3. Run: git push -u origin main"
}

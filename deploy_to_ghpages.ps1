$ErrorActionPreference = "Continue"
$publicDir = Join-Path $PSScriptRoot "public"

Write-Host "=== Cleaning up old .git in public ===" 
if (Test-Path "$publicDir\.git") {
    Remove-Item -Recurse -Force "$publicDir\.git"
}

Write-Host "=== Initializing git in public ==="
Push-Location $publicDir
try {
    git init 2>$null | Out-Null
    git config user.email "billybell991@yahoo.com"
    git config user.name "Billy Bell"
    git config core.autocrlf true
    git checkout -b gh-pages 2>$null | Out-Null
    
    Write-Host "=== Adding files ==="
    git add -A 2>$null | Out-Null
    
    Write-Host "=== Committing ==="
    $commitOutput = git commit -m "Deploy site" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: git commit failed with exit code $LASTEXITCODE"
        Write-Host $commitOutput
        exit 1
    }
    
    $commitHash = git rev-parse --short HEAD 2>&1
    Write-Host "=== Commit created: $commitHash ==="
    
    Write-Host "=== Adding remote ==="
    git remote add origin https://github.com/billybell991/bell-favorite-recipes.git 2>$null | Out-Null
    
    Write-Host "=== Force pushing to gh-pages ==="
    git push origin gh-pages --force 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: git push failed with exit code $LASTEXITCODE"
        exit 1
    }
    
    Write-Host "=== SUCCESS! Site deployed to gh-pages branch ==="
} finally {
    Pop-Location
}

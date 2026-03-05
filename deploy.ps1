$ErrorActionPreference = "Continue"
$projectDir = "c:\Stuff\Bell_Recipes_Project"
$publicDir = Join-Path $projectDir "public"
$tempDir = Join-Path $env:TEMP "bell-deploy"

# Clean temp
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy built site
Write-Host "Copying files..."
Copy-Item -Recurse "$publicDir\*" $tempDir -Force

# Git init and commit
Write-Host "Setting up git..."
git -C $tempDir init 2>$null
git -C $tempDir config user.email "billybell991@yahoo.com"
git -C $tempDir config user.name "Billy Bell"
git -C $tempDir config core.autocrlf true
git -C $tempDir checkout -b gh-pages 2>$null
git -C $tempDir add -A 2>$null
git -C $tempDir commit -m "Deploy site" 2>$null

$hash = git -C $tempDir rev-parse --short HEAD 2>&1
Write-Host "Commit: $hash"

# Push
Write-Host "Pushing to GitHub..."
git -C $tempDir remote add origin https://github.com/billybell991/bell-favorite-recipes.git
git -C $tempDir push origin gh-pages --force 2>&1

Write-Host "DONE - Exit: $LASTEXITCODE"

# Cleanup
Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue

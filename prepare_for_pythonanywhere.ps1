# Prepare databases for PythonAnywhere migration
# Run this script on your local Windows machine before deploying

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Prepare for PythonAnywhere" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = $PSScriptRoot

# Check if databases exist
$dbPath1 = Join-Path $projectPath "integrated_users.db"
$dbPath2 = Join-Path $projectPath "smart_response.db"

Write-Host "Checking for databases..." -ForegroundColor Yellow

if (Test-Path $dbPath1) {
    $size1 = (Get-Item $dbPath1).Length / 1MB
    Write-Host "✅ Found: integrated_users.db ($([math]::Round($size1, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "❌ Not found: integrated_users.db" -ForegroundColor Red
    Write-Host "   This is OK if starting fresh on PythonAnywhere" -ForegroundColor Gray
}

if (Test-Path $dbPath2) {
    $size2 = (Get-Item $dbPath2).Length / 1MB
    Write-Host "✅ Found: smart_response.db ($([math]::Round($size2, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "❌ Not found: smart_response.db" -ForegroundColor Red
    Write-Host "   This is OK if starting fresh on PythonAnywhere" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Choose an option:" -ForegroundColor Cyan
Write-Host "1) Create backup for migration (copy databases to 'databases_for_upload' folder)"
Write-Host "2) Create compressed archive (for easier upload)"
Write-Host "3) Skip (start fresh on PythonAnywhere)"
Write-Host ""

$choice = Read-Host "Enter choice (1, 2, or 3)"

switch ($choice) {
    "1" {
        # Create backup folder
        $backupFolder = Join-Path $projectPath "databases_for_upload"
        New-Item -ItemType Directory -Force -Path $backupFolder | Out-Null
        
        Write-Host ""
        Write-Host "Creating backup copies..." -ForegroundColor Yellow
        
        if (Test-Path $dbPath1) {
            Copy-Item $dbPath1 (Join-Path $backupFolder "production_integrated_users.db")
            Write-Host "✅ Copied: production_integrated_users.db" -ForegroundColor Green
        }
        
        if (Test-Path $dbPath2) {
            Copy-Item $dbPath2 (Join-Path $backupFolder "production_smart_response.db")
            Write-Host "✅ Copied: production_smart_response.db" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "✅ Databases ready for upload!" -ForegroundColor Green
        Write-Host "   Location: $backupFolder" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. In PythonAnywhere, go to Files tab"
        Write-Host "2. Navigate to: /home/yourusername/ai-model-compare/databases/"
        Write-Host "3. Upload both .db files from: databases_for_upload\"
        Write-Host "4. Reload your web app"
        Write-Host ""
    }
    
    "2" {
        # Create compressed archive
        $timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
        $archiveName = "databases_backup_$timestamp.zip"
        $archivePath = Join-Path $projectPath $archiveName
        
        Write-Host ""
        Write-Host "Creating compressed archive..." -ForegroundColor Yellow
        
        $filesToCompress = @()
        if (Test-Path $dbPath1) { $filesToCompress += $dbPath1 }
        if (Test-Path $dbPath2) { $filesToCompress += $dbPath2 }
        
        if ($filesToCompress.Count -gt 0) {
            Compress-Archive -Path $filesToCompress -DestinationPath $archivePath -Force
            
            $archiveSize = (Get-Item $archivePath).Length / 1MB
            Write-Host "✅ Created: $archiveName ($([math]::Round($archiveSize, 2)) MB)" -ForegroundColor Green
            Write-Host ""
            Write-Host "Next steps:" -ForegroundColor Cyan
            Write-Host "1. In PythonAnywhere Files tab, upload: $archiveName"
            Write-Host "2. In PythonAnywhere Bash console, run:"
            Write-Host "   cd ~/ai-model-compare/databases"
            Write-Host "   unzip ~/ai-model-compare/$archiveName"
            Write-Host "   mv integrated_users.db production_integrated_users.db"
            Write-Host "   mv smart_response.db production_smart_response.db"
            Write-Host "3. Reload your web app"
        } else {
            Write-Host "❌ No databases found to compress" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    "3" {
        Write-Host ""
        Write-Host "✅ Skipping database migration" -ForegroundColor Green
        Write-Host "   Databases will be created automatically on PythonAnywhere" -ForegroundColor Gray
        Write-Host "   Users will register fresh accounts" -ForegroundColor Gray
        Write-Host ""
    }
    
    default {
        Write-Host ""
        Write-Host "❌ Invalid choice. Exiting." -ForegroundColor Red
        Write-Host ""
        exit 1
    }
}

# Show deployment checklist reminder
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ready for PythonAnywhere Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Follow the checklist: PYTHONANYWHERE_CHECKLIST.md" -ForegroundColor Yellow
Write-Host "📖 Full guide: PYTHONANYWHERE_DEPLOYMENT.md" -ForegroundColor Yellow
Write-Host ""
Write-Host "Don't forget:" -ForegroundColor Cyan
Write-Host "  ✅ Have your OpenAI API key ready"
Write-Host "  ✅ Know your PythonAnywhere username"
Write-Host "  ✅ Estimated time: 20-30 minutes"
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

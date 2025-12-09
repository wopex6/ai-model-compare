# Upload Database to PythonAnywhere
# Quick script to prepare and upload your local database

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Update PythonAnywhere Database" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = $PSScriptRoot
$dbPath1 = Join-Path $projectPath "integrated_users.db"
$dbPath2 = Join-Path $projectPath "smart_response.db"

# Check if databases exist
Write-Host "Checking local databases..." -ForegroundColor Yellow
Write-Host ""

$db1Exists = Test-Path $dbPath1
$db2Exists = Test-Path $dbPath2

if ($db1Exists) {
    $size1 = (Get-Item $dbPath1).Length / 1MB
    $modified1 = (Get-Item $dbPath1).LastWriteTime
    Write-Host "✅ integrated_users.db" -ForegroundColor Green
    Write-Host "   Size: $([math]::Round($size1, 2)) MB" -ForegroundColor Gray
    Write-Host "   Modified: $modified1" -ForegroundColor Gray
} else {
    Write-Host "❌ integrated_users.db not found" -ForegroundColor Red
    Write-Host "   Location: $dbPath1" -ForegroundColor Gray
}

Write-Host ""

if ($db2Exists) {
    $size2 = (Get-Item $dbPath2).Length / 1MB
    $modified2 = (Get-Item $dbPath2).LastWriteTime
    Write-Host "✅ smart_response.db" -ForegroundColor Green
    Write-Host "   Size: $([math]::Round($size2, 2)) MB" -ForegroundColor Gray
    Write-Host "   Modified: $modified2" -ForegroundColor Gray
} else {
    Write-Host "❌ smart_response.db not found" -ForegroundColor Red
    Write-Host "   Location: $dbPath2" -ForegroundColor Gray
}

Write-Host ""

if (-not $db1Exists -and -not $db2Exists) {
    Write-Host "❌ No databases found to upload!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure you're in the correct directory:" -ForegroundColor Yellow
    Write-Host "  $projectPath" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Get database info
Write-Host "Analyzing databases..." -ForegroundColor Yellow
Write-Host ""

if ($db1Exists) {
    # Try to get record counts (requires sqlite3)
    if (Get-Command sqlite3 -ErrorAction SilentlyContinue) {
        $userCount = & sqlite3 $dbPath1 "SELECT COUNT(*) FROM users;" 2>$null
        $sessionCount = & sqlite3 $dbPath1 "SELECT COUNT(*) FROM user_sessions;" 2>$null
        
        if ($userCount) {
            Write-Host "📊 Database Statistics:" -ForegroundColor Cyan
            Write-Host "   Users: $userCount" -ForegroundColor Gray
            if ($sessionCount) {
                Write-Host "   Sessions: $sessionCount" -ForegroundColor Gray
            }
            Write-Host ""
        }
    }
}

# Show options
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Choose Upload Method" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1) Prepare for manual upload via PythonAnywhere Files tab (EASIEST)" -ForegroundColor White
Write-Host "   - Creates 'for_upload' folder with renamed files"
Write-Host "   - Upload via PythonAnywhere web interface"
Write-Host ""
Write-Host "2) Create compressed archive (for slow connections)" -ForegroundColor White
Write-Host "   - Creates .zip file"
Write-Host "   - Smaller upload size"
Write-Host ""
Write-Host "3) Show manual upload instructions" -ForegroundColor White
Write-Host "   - Step-by-step guide"
Write-Host ""
Write-Host "4) Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1-4)"

switch ($choice) {
    "1" {
        # Create upload folder
        $uploadFolder = Join-Path $projectPath "for_upload_to_pythonanywhere"
        New-Item -ItemType Directory -Force -Path $uploadFolder | Out-Null
        
        Write-Host ""
        Write-Host "Preparing files..." -ForegroundColor Yellow
        Write-Host ""
        
        if ($db1Exists) {
            $destPath = Join-Path $uploadFolder "production_integrated_users.db"
            Copy-Item $dbPath1 $destPath -Force
            Write-Host "✅ Copied: production_integrated_users.db" -ForegroundColor Green
        }
        
        if ($db2Exists) {
            $destPath = Join-Path $uploadFolder "production_smart_response.db"
            Copy-Item $dbPath2 $destPath -Force
            Write-Host "✅ Copied: production_smart_response.db" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✅ Files Ready for Upload!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "📁 Location: $uploadFolder" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📋 Next Steps:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. Go to PythonAnywhere (https://www.pythonanywhere.com)" -ForegroundColor White
        Write-Host "2. Login to your account" -ForegroundColor White
        Write-Host "3. Click 'Files' tab" -ForegroundColor White
        Write-Host "4. Navigate to: /home/yourusername/ai-model-compare/databases/" -ForegroundColor White
        Write-Host ""
        Write-Host "⚠️  IMPORTANT: Backup first!" -ForegroundColor Red
        Write-Host "   - Right-click existing database → Download" -ForegroundColor Gray
        Write-Host "   - Save as backup with today's date" -ForegroundColor Gray
        Write-Host ""
        Write-Host "5. Click 'Upload a file'" -ForegroundColor White
        Write-Host "6. Upload: production_integrated_users.db" -ForegroundColor White
        Write-Host "   - Confirm overwrite when asked" -ForegroundColor Gray
        Write-Host "7. Upload: production_smart_response.db" -ForegroundColor White
        Write-Host "   - Confirm overwrite when asked" -ForegroundColor Gray
        Write-Host ""
        Write-Host "8. Go to 'Web' tab" -ForegroundColor White
        Write-Host "9. Click the green 'Reload' button" -ForegroundColor White
        Write-Host "10. Test your app!" -ForegroundColor White
        Write-Host ""
        
        # Open folder
        Write-Host "Opening upload folder..." -ForegroundColor Gray
        Start-Process explorer.exe $uploadFolder
    }
    
    "2" {
        # Create compressed archive
        $timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
        $archiveName = "database_update_$timestamp.zip"
        $archivePath = Join-Path $projectPath $archiveName
        
        Write-Host ""
        Write-Host "Creating compressed archive..." -ForegroundColor Yellow
        Write-Host ""
        
        $filesToCompress = @()
        if ($db1Exists) { $filesToCompress += $dbPath1 }
        if ($db2Exists) { $filesToCompress += $dbPath2 }
        
        Compress-Archive -Path $filesToCompress -DestinationPath $archivePath -Force
        
        $archiveSize = (Get-Item $archivePath).Length / 1MB
        
        Write-Host "✅ Created: $archiveName" -ForegroundColor Green
        Write-Host "   Size: $([math]::Round($archiveSize, 2)) MB" -ForegroundColor Gray
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✅ Archive Ready!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Next Steps:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. Upload $archiveName to PythonAnywhere" -ForegroundColor White
        Write-Host "   - Via Files tab" -ForegroundColor Gray
        Write-Host "   - To: /home/yourusername/ai-model-compare/" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. In PythonAnywhere Bash console, run:" -ForegroundColor White
        Write-Host ""
        Write-Host "   cd ~/ai-model-compare/databases" -ForegroundColor Cyan
        Write-Host "   # Backup first!" -ForegroundColor Red
        Write-Host "   sqlite3 production_integrated_users.db `".backup 'backup_$(Get-Date -Format 'yyyyMMdd').db'`"" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "   # Extract archive" -ForegroundColor Gray
        Write-Host "   cd ~/ai-model-compare" -ForegroundColor Cyan
        Write-Host "   unzip $archiveName" -ForegroundColor Cyan
        Write-Host "   mv integrated_users.db databases/production_integrated_users.db" -ForegroundColor Cyan
        Write-Host "   mv smart_response.db databases/production_smart_response.db" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "3. Reload web app in Web tab" -ForegroundColor White
        Write-Host ""
    }
    
    "3" {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  Manual Upload Instructions" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Your databases are located at:" -ForegroundColor Yellow
        if ($db1Exists) {
            Write-Host "  $dbPath1" -ForegroundColor Gray
        }
        if ($db2Exists) {
            Write-Host "  $dbPath2" -ForegroundColor Gray
        }
        Write-Host ""
        Write-Host "📋 Steps:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "1. ⚠️  BACKUP FIRST on PythonAnywhere:" -ForegroundColor Red
        Write-Host "   Files tab → databases folder → Right-click → Download" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Go to PythonAnywhere Files tab" -ForegroundColor White
        Write-Host "   Navigate to: /home/yourusername/ai-model-compare/databases/" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. Upload integrated_users.db" -ForegroundColor White
        Write-Host "   Rename to: production_integrated_users.db" -ForegroundColor Gray
        Write-Host "   Overwrite existing file" -ForegroundColor Gray
        Write-Host ""
        Write-Host "4. Upload smart_response.db" -ForegroundColor White
        Write-Host "   Rename to: production_smart_response.db" -ForegroundColor Gray
        Write-Host "   Overwrite existing file" -ForegroundColor Gray
        Write-Host ""
        Write-Host "5. Web tab → Click 'Reload' button" -ForegroundColor White
        Write-Host ""
        Write-Host "6. Test your app" -ForegroundColor White
        Write-Host ""
    }
    
    "4" {
        Write-Host ""
        Write-Host "Exiting..." -ForegroundColor Gray
        Write-Host ""
        exit 0
    }
    
    default {
        Write-Host ""
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        Write-Host ""
        exit 1
    }
}

Write-Host ""
Write-Host "📖 For detailed instructions, see:" -ForegroundColor Cyan
Write-Host "   UPDATE_DATABASE_PYTHONANYWHERE.md" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

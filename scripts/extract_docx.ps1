Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Web

$files = @(
    'C:\Users\trabc\Documents\calibration app.docx',
    'C:\Users\trabc\Documents\Reality discussion.docx'
)

foreach ($f in $files) {
    Write-Output '=================================================='
    Write-Output ('FILE: ' + $f)
    Write-Output '=================================================='
    if (Test-Path $f) {
        $tmp = Join-Path $env:TEMP ((Split-Path $f -Leaf) + '.copy.zip')
        Copy-Item -LiteralPath $f -Destination $tmp -Force
        $f = $tmp
        $zip = [System.IO.Compression.ZipFile]::OpenRead($f)
        $entry = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
        $reader = New-Object System.IO.StreamReader($entry.Open())
        $xml = $reader.ReadToEnd()
        $reader.Close()
        $zip.Dispose()
        $xml = $xml -replace '</w:p>', "`n"
        $xml = $xml -replace '<[^>]+>', ''
        [System.Web.HttpUtility]::HtmlDecode($xml)
    } else {
        Write-Output 'FILE NOT FOUND'
    }
}

param()

# Settings
$reportDir = "C:\Users\admin\Desktop\SSOT_Agentic_Brain\audit_reports"
$reportPath = Join-Path $reportDir "full_drive_audit_report.md"
$excludePattern = "\.gemini"
$samplePercent = 0.10

# Ensure report directory exists
if (-not (Test-Path -Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

Write-Host "Starting filesystem audit..."

# Enumerate directories (excluding .gemini)
$allDirs = Get-ChildItem -Path 'C:\' -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch $excludePattern }
$dirCount = $allDirs.Count

# Enumerate files (excluding .gemini)
$allFiles = Get-ChildItem -Path 'C:\' -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch $excludePattern }
$fileCount = $allFiles.Count

Write-Host "Total directories: $dirCount"
Write-Host "Total files: $fileCount"

# Determine sample size (at least 1 if there are files)
if ($fileCount -gt 0) {
    $sampleSize = [Math]::Ceiling($fileCount * $samplePercent)
    if ($sampleSize -gt $fileCount) { $sampleSize = $fileCount }
} else {
    $sampleSize = 0
}

Write-Host "Sampling $sampleSize files (~{0:P0} of total)" -f $samplePercent

# Sample files randomly
if ($sampleSize -gt 0) {
    $sampledFiles = $allFiles | Get-Random -Count $sampleSize
} else {
    $sampledFiles = @()
}

$successCount = 0
$failureCount = 0
$failDetails = @()

foreach ($file in $sampledFiles) {
    try {
        # Attempt to read first line (or minimal bytes) without output
        Get-Content -Path $file.FullName -TotalCount 1 -ErrorAction Stop | Out-Null
        $successCount++
    } catch {
        $failureCount++
        $msg = "{0}: {1}" -f $file.FullName, $_.Exception.Message
        $failDetails += $msg
    }
}

# Build markdown report
$md = @()
$md += "# Full Drive Filesystem Audit Report"
$md += "Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
$md += ""
$md += "| Metric | Value |"
$md += "|--------|------|"
$md += "| Total directories scanned (excluding .gemini) | $dirCount |"
$md += "| Total files scanned (excluding .gemini) | $fileCount |"
$md += "| Sampled files for pressure test (~10%) | $sampleSize |"
$md += "| Successful reads | $successCount |"
$md += "| Failed reads | $failureCount |"
$md += ""
if ($failureCount -gt 0) {
    $md += "## Failure Details (up to 50 entries)"
    $md += ""
    $md += "| File Path | Error Message |"
    $md += "|-----------|---------------|"
    $displayCount = [Math]::Min(50, $failDetails.Count)
    foreach ($line in $failDetails[0..($displayCount-1)]) {
        $parts = $line -split ': ', 2
        $path = $parts[0]
        $err = $parts[1]
        $md += "| $path | $err |"
    }
}

# Write report
$mdString = $md -join "`n"
Set-Content -Path $reportPath -Value $mdString -Encoding UTF8

Write-Host "Audit complete. Report written to $reportPath"

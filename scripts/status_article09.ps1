$ErrorActionPreference = 'Continue'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StateDir = Join-Path $ProjectRoot 'state'
$PidFile = Join-Path $StateDir 'pipeline.pid'
$LaunchFile = Join-Path $StateDir 'launch.json'

if (Test-Path -LiteralPath $LaunchFile) {
    $Launch = Get-Content -LiteralPath $LaunchFile -Raw | ConvertFrom-Json
    Write-Output "Stage: $($Launch.stage)"
    Write-Output "Started: $($Launch.started_at)"
    Write-Output "PID: $($Launch.pid)"
    $Process = Get-Process -Id ([int]$Launch.pid) -ErrorAction SilentlyContinue
    if ($null -ne $Process) {
        Write-Output "Process: RUNNING"
        Write-Output "CPU time: $([math]::Round($Process.CPU,1)) seconds"
        Write-Output "RAM: $([math]::Round($Process.WorkingSet64/1GB,2)) GB"
    } elseif (Test-Path -LiteralPath (Join-Path $StateDir 'SUCCESS')) {
        Write-Output "Process: COMPLETE"
    } elseif (Test-Path -LiteralPath (Join-Path $StateDir 'FAILED')) {
        Write-Output "Process: FAILED"
        Get-Content -LiteralPath (Join-Path $StateDir 'FAILED')
    } else {
        Write-Output "Process: NOT RUNNING (interrupted or stage-specific completion)"
    }
    if (Test-Path -LiteralPath $Launch.stdout) {
        Write-Output "`nRecent stdout:"
        Get-Content -LiteralPath $Launch.stdout -Tail 25
    }
    if ((Test-Path -LiteralPath $Launch.stderr) -and (Get-Item -LiteralPath $Launch.stderr).Length -gt 0) {
        Write-Output "`nRecent stderr:"
        Get-Content -LiteralPath $Launch.stderr -Tail 25
    }
} else {
    Write-Output 'No launch record exists.'
}

$Tasks = Get-ChildItem -LiteralPath (Join-Path $StateDir 'tasks') -Filter '*.json' -ErrorAction SilentlyContinue
if ($Tasks) {
    $Rows = foreach ($Task in $Tasks) {
        try { Get-Content -LiteralPath $Task.FullName -Raw | ConvertFrom-Json } catch { $null }
    }
    Write-Output "`nTask ledger:"
    $Rows | Group-Object status | Select-Object Name,Count | Format-Table -AutoSize
}

Write-Output "`nGPU snapshot:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader


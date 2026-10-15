param(
    [ValidateSet('setup','data','audit','embeddings','backend','pilot','freeze','final','test','report','notebook','article','all')]
    [string]$Stage = 'all',
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = 'C:\Users\Admin Riset\miniconda3\envs\quantum_env\python.exe'
$StateDir = Join-Path $ProjectRoot 'state'
$LogDir = Join-Path $ProjectRoot 'logs'
$PidFile = Join-Path $StateDir 'pipeline.pid'

New-Item -ItemType Directory -Force -Path $StateDir, $LogDir | Out-Null
if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "quantum_env interpreter not found: $PythonExe"
}

if (Test-Path -LiteralPath $PidFile) {
    $ExistingPid = (Get-Content -LiteralPath $PidFile -Raw).Trim()
    if ($ExistingPid -match '^\d+$') {
        $ExistingProcess = Get-Process -Id ([int]$ExistingPid) -ErrorAction SilentlyContinue
        if ($null -ne $ExistingProcess) {
            throw "Pipeline is already running with PID $ExistingPid"
        }
    }
}

$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Stdout = Join-Path $LogDir "article09_${Stage}_${Timestamp}.out.log"
$Stderr = Join-Path $LogDir "article09_${Stage}_${Timestamp}.err.log"
$Arguments = @((Join-Path $ProjectRoot 'run_article09.py'), $Stage)
if ($Resume) { $Arguments += '--resume' }

$Process = Start-Process -FilePath $PythonExe -ArgumentList $Arguments -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru
$Process.Id | Out-File -LiteralPath $PidFile -Encoding ascii
@{
    pid = $Process.Id
    stage = $Stage
    started_at = (Get-Date).ToString('o')
    stdout = $Stdout
    stderr = $Stderr
    resume = [bool]$Resume
    python = $PythonExe
} | ConvertTo-Json | Out-File -LiteralPath (Join-Path $StateDir 'launch.json') -Encoding utf8

Write-Output "STARTED PID=$($Process.Id) STAGE=$Stage"
Write-Output "STDOUT=$Stdout"
Write-Output "STDERR=$Stderr"
Write-Output "No automatic monitoring is active. Use scripts\status_article09.ps1 only when needed."


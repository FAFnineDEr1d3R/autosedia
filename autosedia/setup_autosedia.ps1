<#
.SYNOPSIS
    Setup Python environment on Windows.
.DESCRIPTION
    - Checks for Python 3.11.7 via the py launcher.
    - Installs Python if missing (via winget or Chocolatey).
    - Creates a virtual environment.
    - Activates it, upgrades pip, installs dependencies from requirements.txt.
    - Deactivates the environment.
#>

# Stop on errors and enforce strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Allow this script to run activation commands
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# === Configuration ===
$PythonVersion = '3.11.7'
$VenvName      = 'autosedia_venv'
$ScriptDir     = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ReqFile       = Join-Path $ScriptDir 'requirements.txt'

# === Helper: print & run ===
function Run {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Command
    )
    Write-Host "▶ $($Command -join ' ')"
    & $Command
}

# === 1. Ensure Python $PythonVersion is installed ===
try {
    $pyVerOutput = & py --version 2>&1
} catch {
    $pyVerOutput = $null
}

if ($pyVerOutput -and $pyVerOutput -match [regex]::Escape($PythonVersion)) {
    Write-Host "Python $PythonVersion detected: $pyVerOutput"
} else {
    Write-Host "Python $PythonVersion not found."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Installing Python $PythonVersion via winget..."
        Run winget install --exact --id Python.Python.3.11 --silent
    }
    elseif (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "Installing Python $PythonVersion via Chocolatey..."
        Run choco install python --version $PythonVersion -y
    }
    else {
        Write-Error "Neither winget nor Chocolatey is available. Please install Python $PythonVersion manually from https://www.python.org/downloads/windows/"
        exit 1
    }

    # Re-check installation
    $pyVerOutput = & py --version 2>&1
    if (-not ($pyVerOutput -and $pyVerOutput -match [regex]::Escape($PythonVersion))) {
        Write-Error "Failed to install Python $PythonVersion. Exiting."
        exit 1
    }
}

# Choose the py launcher invocation for 3.11
$majorMinor = ($PythonVersion -split '\.')[0..1] -join '.'
$PythonCmd  = "py -$majorMinor"

# === 2. Create virtual environment ===
$VenvPath = Join-Path $ScriptDir $VenvName
Write-Host "==> Creating virtual environment at $VenvPath"
Run $PythonCmd -m venv $VenvPath

# === 3. Activate venv & install dependencies ===
Write-Host "==> Activating virtual environment and installing dependencies"
$activateScript = Join-Path $VenvPath 'Scripts\Activate.ps1'
if (Test-Path $activateScript) {
    & $activateScript
} else {
    Write-Error "Activation script not found at $activateScript"
    exit 1
}

Run pip install --upgrade pip

if (Test-Path $ReqFile) {
    Run pip install -r $ReqFile
} else {
    Write-Warning "requirements.txt not found at $ReqFile"
}

# === 4. Deactivate ===
if (Get-Command deactivate -ErrorAction SilentlyContinue) {
    Write-Host "==> Deactivating virtual environment"
    deactivate
} else {
    Write-Warning "Could not find 'deactivate' command. To exit the venv, close this shell or manually remove the environment variables."
}

Write-Host 'Setup complete!'
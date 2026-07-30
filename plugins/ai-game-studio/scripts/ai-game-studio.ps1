[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $StudioArguments
)

$scriptPath = Join-Path $PSScriptRoot "ai_game_studio.py"
$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $pythonLauncher) {
    & $pythonLauncher.Source -3 $scriptPath @StudioArguments
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $python) {
    Write-Error "Python 3 is required. Run the read-only doctor after installing Python from python.org."
    exit 127
}

& $python.Source $scriptPath @StudioArguments
exit $LASTEXITCODE

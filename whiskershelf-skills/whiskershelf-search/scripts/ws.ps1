# ws.ps1 — PowerShell wrappers for Windows users.
# Usage:
#   .\ws.ps1 search "spiking neural network"
#   .\ws.ps1 papers
#   .\ws.ps1 detail "Spikformer v2.pdf"
#   .\ws.ps1 tags "Spikformer v2.pdf"
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet('search','papers','detail','tags')]
    [string]$Command,
    [Parameter(Mandatory=$false, Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Rest
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Map = @{
    'search' = 'ws_search.py'
    'papers' = 'ws_papers.py'
    'detail' = 'ws_detail.py'
    'tags'   = 'ws_tags_get.py'
}
$Py = $Map[$Command]
& python "$ScriptDir\$Py" @Rest
exit $LASTEXITCODE

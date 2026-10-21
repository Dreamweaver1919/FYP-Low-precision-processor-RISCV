param(
  [Parameter(Mandatory=$true)][string]$Config,
  [Parameter(Mandatory=$true)][string]$Suite,
  [int]$Seed=1,
  [int]$MaxCycles=200000,
  [int]$GrantMax=0,
  [int]$ResponseMax=1
)
$ErrorActionPreference='Stop'
$pythonExe='C:\Users\CEG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $pythonExe "$PSScriptRoot\run_tests.py" --config $Config --suite $Suite --seed $Seed --max-cycles $MaxCycles --grant-max $GrantMax --response-max $ResponseMax
exit $LASTEXITCODE

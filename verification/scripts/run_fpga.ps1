param(
  [ValidateSet('frozen_ff_pulp1','overlay_nn0','overlay_nn1')][string]$Config='frozen_ff_pulp1',
  [ValidateSet('core_ooc','system_ooc')][string]$Stage='core_ooc',
  [double]$ClockPeriodNs=10,
  [int]$TimeoutSeconds=1800,
  [string]$ImageDir='',
  [string]$OutDir=''
)
$pythonExe='C:/Users/CEG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$arguments=@("$PSScriptRoot/run_fpga.py",'--config',$Config,'--stage',$Stage,
  '--clock-ns',"$ClockPeriodNs",'--timeout',"$TimeoutSeconds")
if($ImageDir){$arguments+=@('--image-dir',$ImageDir)}
if($OutDir){$arguments+=@('--out',$OutDir)}
& $pythonExe @arguments
exit $LASTEXITCODE

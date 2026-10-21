param(
    [ValidateSet('alu','dotp','decoder')][string]$Unit='alu',
    [string]$Vectors='',
    [string]$Out='',
    [switch]$BaselineRed
)
$ErrorActionPreference='Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$out = if($Out){[IO.Path]::GetFullPath($Out)}else{Join-Path $root ('artifacts/verification/arithmetic/' + $Unit + $(if($BaselineRed){'_red'}else{'_green'}))}
New-Item -ItemType Directory -Path $out -Force | Out-Null
$vendor = Join-Path $root 'vendor/cv32e40p/rtl'
$overlay = Join-Path $root 'rtl/core'
$package = Join-Path $overlay 'include/cv32e40p_pkg.sv'
if($BaselineRed -or !(Test-Path -LiteralPath $package)){$package=Join-Path $vendor 'include/cv32e40p_pkg.sv'}
$sources = @($package)
if($Unit -eq 'decoder') {
    $sources += @((Join-Path $vendor 'include/cv32e40p_apu_core_pkg.sv'),(Join-Path $vendor 'include/cv32e40p_fpu_pkg.sv'))
    $baseDecoder = (Get-Content -LiteralPath (Join-Path $vendor 'cv32e40p_decoder.sv') -Raw).Replace('module cv32e40p_decoder','module cv32e40p_decoder_baseline')
    $baseDecoder | Set-Content -LiteralPath (Join-Path $out 'decoder_baseline.sv') -Encoding ascii
    $sources += (Join-Path $out 'decoder_baseline.sv')
    if(!$BaselineRed){$sources += Join-Path $overlay 'cv32e40p_decoder.sv'}
} else {
    $sources += Join-Path $root ('rtl/nn/cv32e40p_nn_' + $Unit + '.sv')
}
$sources += Join-Path $root ('verification/tb/tb_nn_' + $Unit + '.sv')
$sources | ForEach-Object { 'sv xil_defaultlib "' + $_.Replace('\','/') + '"' } | Set-Content -LiteralPath (Join-Path $out 'sources.prj') -Encoding ascii
$started = [DateTime]::UtcNow
$meta = [ordered]@{unit=$Unit; baseline_red=[bool]$BaselineRed; started_utc=$started.ToString('o'); sources=@()}
foreach($source in $sources){
    $meta.sources += @{path=$source; sha256=$(if(Test-Path -LiteralPath $source){(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLower()}else{$null})}
}
if($Vectors){$meta.vectors=@{path=[IO.Path]::GetFullPath($Vectors); sha256=(Get-FileHash -LiteralPath $Vectors -Algorithm SHA256).Hash.ToLower()}}
$meta | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $out 'run.json') -Encoding utf8
$phase='compile'
$result=[ordered]@{status='UNRUNNABLE'; unit=$Unit; count=0}
Push-Location $out
try {
    $compile = @('--sv','--prj','sources.prj','--log','xvlog.log')
    if($BaselineRed -and $Unit -eq 'decoder'){$compile += @('-d','NN_BASELINE_RED')}
    & 'E:/vivado/2026.1/Vivado/bin/xvlog.bat' @compile
    if($LASTEXITCODE -ne 0){throw "xvlog $Unit failed: $LASTEXITCODE"}
    $phase='elaborate'
    & 'E:/vivado/2026.1/Vivado/bin/xelab.bat' ('xil_defaultlib.tb_nn_' + $Unit) --mt 2 --timescale 1ns/1ps --snapshot unit --log xelab.log
    if($LASTEXITCODE -ne 0){throw "xelab $Unit failed: $LASTEXITCODE"}
    $phase='simulate'
    $sim = @('unit','--runall','--log xsim.log')
    if($Vectors){$sim += '--testplusarg "VECTORS=' + [IO.Path]::GetFullPath($Vectors).Replace('\','/') + '"'}
    $sim | Set-Content -LiteralPath xsim.args -Encoding ascii
    & 'E:/vivado/2026.1/Vivado/bin/xsim.bat' --file xsim.args
    if($LASTEXITCODE -ne 0){throw "xsim $Unit failed: $LASTEXITCODE"}
    $phase='verify'
    $simulation = Get-Content -LiteralPath xsim.log -Raw
    $marker = [regex]::Match($simulation, ('NN_' + $Unit.ToUpper() + '_PASS count=(\d+)'))
    if(!$marker.Success -or $simulation -match '(?m)^(Fatal:|Error:|ERROR:)'){throw "Missing PASS marker or simulation failure for $Unit"}
    $result.status='PASS'
    $result.count=[int]$marker.Groups[1].Value
    if($Unit -eq 'decoder'){$result.named_forms=72; $result.legacy_funct6=44; $result.legacy_output_controls=72}
} catch {
    $result.status=if($phase -in @('simulate','verify')){'FAIL'}else{'UNRUNNABLE'}
    $result.error=$_.Exception.Message
    throw
} finally {
    $result.phase=$phase
    $result.elapsed_seconds=([DateTime]::UtcNow-$started).TotalSeconds
    $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'result.json') -Encoding utf8
    Pop-Location
}

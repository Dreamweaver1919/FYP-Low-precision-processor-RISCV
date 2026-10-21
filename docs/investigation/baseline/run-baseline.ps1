$ErrorActionPreference = 'Stop'
$vivadoBin = 'E:\vivado\2026.1\Vivado\bin'
$rtl = 'E:/cv32e40p-master/cv32e40p-master/rtl'
Push-Location $PSScriptRoot
try {
    & "$vivadoBin\xvlog.bat" --sv --prj baseline.prj -i "$rtl/include" -i "$rtl/vendor/pulp_platform_common_cells/include" --log xvlog.log
    if ($LASTEXITCODE -ne 0) { throw "xvlog failed: $LASTEXITCODE" }
    foreach ($pulp in @(0, 1)) {
        @('--generic_top "COREV_PULP=' + $pulp + '"', '--generic_top "COREV_CLUSTER=0"', '--generic_top "FPU=0"', '--generic_top "ZFINX=0"') | Set-Content -LiteralPath "xelab-pulp$pulp.args" -Encoding ascii
        & "$vivadoBin\xelab.bat" xil_defaultlib.cv32e40p_top xil_defaultlib.glbl -L unisims_ver --file "xelab-pulp$pulp.args" --mt 2 --timescale 1ns/1ps --snapshot "baseline_pulp$pulp" --log "xelab_pulp$pulp.log"
        if ($LASTEXITCODE -ne 0) { throw "xelab COREV_PULP=$pulp failed: $LASTEXITCODE" }
    }
} finally { Pop-Location }


"""Execute an actual common ROM through the FPGA system wrapper using XSim."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from run_tests import ROOT,VIVADO,config,resolve_sources,invoke
from build_sw import build


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--config',choices=['frozen_ff_pulp1','overlay_nn0','overlay_nn1'],required=True)
    p.add_argument('--test',default='rv32_smoke')
    p.add_argument('--image-dir',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    meta={'config':a.config,'test':a.test,'scope':'system wrapper simulation','status':'RUNNING'}
    try:
        if a.image_dir:
            import shutil
            meta['image_origin']=str(a.image_dir.resolve())
            for name in ('imem.hex','dmem.hex','expected.json'):
                shutil.copy2(a.image_dir/name,out/name)
            if (a.image_dir/'benchmark.json').exists():
                shutil.copy2(a.image_dir/'benchmark.json',out/'benchmark.json')
                meta['benchmark_manifest_sha256']=hashlib.sha256((out/'benchmark.json').read_bytes()).hexdigest()
        else: build(a.test,'rv32imc',1,out)
        expected=json.loads((out/'expected.json').read_text())['signature']
        digest_words=next((i for i,x in enumerate(expected) if x is None),len(expected))
        (out/'expected.hex').write_text(''.join(f'{x or 0:08x}\n' for x in expected+[0]*(16384-len(expected))))
        (out/'expected_mask.hex').write_text(''.join(f'{0 if x is None else 0xffffffff:08x}\n' for x in expected+[0]*(16384-len(expected))))
        meta['digest_words']=digest_words
        meta['imem_sha256']=hashlib.sha256((out/'imem.hex').read_bytes()).hexdigest()
        meta['dmem_sha256']=hashlib.sha256((out/'dmem.hex').read_bytes()).hexdigest()
        sources=resolve_sources(a.config,platform='fpga')
        sources += [ROOT/'rtl/platform/fpga/fyp_nn_system.sv',ROOT/'verification/tb/tb_fyp_nn_system.sv']
        meta['sources']=[{'path':str(x),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sources if x.exists()]
        (out/'sources.prj').write_text(''.join(f'sv xil_defaultlib "{x.as_posix()}"\n' for x in sources if x.exists())+
            'verilog xil_defaultlib "E:/vivado/2026.1/Vivado/data/verilog/src/glbl.v"\n')
        cfg=config(a.config)
        args=[VIVADO/'xvlog.bat','--sv','--prj','sources.prj','-i',ROOT/'rtl/core/include',
              '-i',ROOT/'vendor/cv32e40p/rtl/include','-i',ROOT/'vendor/cv32e40p/rtl/vendor/pulp_platform_common_cells/include']
        if cfg['overlay']: args += ['-d','FYP_OVERLAY']
        invoke(args,out,'xvlog.stdout.log')
        (out/'xelab.args').write_text(f'--generic_top "NN_ENABLE={cfg["nn"]}"\n--generic_top "EXPECTED_WORDS={len(expected)}"\n--generic_top "DIGEST_WORDS={digest_words}"\n')
        invoke([VIVADO/'xelab.bat','xil_defaultlib.tb_fyp_nn_system','xil_defaultlib.glbl','-L','unisims_ver',
                '--file','xelab.args','--mt','2','--snapshot','wrapper'],out,'xelab.stdout.log')
        (out/'run.tcl').write_text('run all\nquit\n')
        if (out/'result_sv.json').exists(): (out/'result_sv.json').unlink()
        invoke([VIVADO/'xsim.bat','wrapper','--tclbatch','run.tcl'],out,'xsim.stdout.log')
        result=json.loads((out/'result_sv.json').read_text())
        if result['status']!='PASS': raise ValueError('wrapper did not pass')
        meta.update(result)
        print(json.dumps({'artifact':str(out),**result},indent=2))
        return 0
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
        meta['status']='FAIL';meta['error']=str(exc)
        print(str(exc),file=sys.stderr)
        return 1
    finally: (out/'run.json').write_text(json.dumps(meta,indent=2)+'\n')


if __name__=='__main__': raise SystemExit(main())

"""Record immutable origins and reproducible overlay diff; never mutate originals."""
import difflib
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
XPR_HASH = '9d348bcda279dbd563006ed12d1ae816f06b0ff66022e54145c753f7af3f0e82'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package():
    frozen=json.loads((ROOT/'vendor/cv32e40p/SOURCE.json').read_text())
    origins=[]
    for entry in frozen['files']:
        local=ROOT/entry['path']
        if sha(local)!=entry['sha256']:
            raise RuntimeError(f'Frozen snapshot changed: {local}')
        if entry['path'].startswith('vendor/cv32e40p/'):
            original=Path(frozen['origin'])/local.relative_to(ROOT/'vendor/cv32e40p')
            origin_kind='external_cv32e40p_checkout'
            origin_relative_path=local.relative_to(ROOT/'vendor/cv32e40p').as_posix()
        elif entry['path']=='rtl/platform/fpga/cv32e40p_clock_gate.sv':
            original=ROOT/'FYP.srcs/sources_1/new/cv32e40p_clock_gate.sv'
            origin_kind='original_fyp_project'
            origin_relative_path='FYP.srcs/sources_1/new/cv32e40p_clock_gate.sv'
        else:
            original=Path(frozen['origin'])/'bhv/cv32e40p_sim_clock_gate.sv'
            origin_kind='external_cv32e40p_checkout'
            origin_relative_path='bhv/cv32e40p_sim_clock_gate.sv'
        if sha(original)!=entry['sha256']:
            raise RuntimeError(f'Original differs from recorded baseline: {original}')
        origins.append({'snapshot_path':entry['path'],'origin_kind':origin_kind,
                        'origin_relative_path':origin_relative_path,
                        'sha256':entry['sha256'],'matches_snapshot':True})
    if sha(ROOT/'FYP.xpr')!=XPR_HASH:
        raise RuntimeError('Original FYP.xpr changed')
    origins.append({'snapshot_path':'FYP.xpr','origin_kind':'original_fyp_project',
                    'origin_relative_path':'FYP.xpr','sha256':XPR_HASH,'matches_initial':True})
    out=ROOT/'artifacts/delivery'
    out.mkdir(parents=True,exist_ok=True)
    files=[]
    for directory in ('rtl','verification','scripts','docs/results','docs/superpowers','vendor/cv32e40p'):
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and
                     '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pb','.log'))
    files.extend(p for p in (ROOT/'README-xpulpnn.md',ROOT/'FYP.xpr',ROOT/'docs/investigation/paper-analysis.md',
                            ROOT/'docs/investigation/2026-10-20-xpulpnn-feasibility-review-zh.md',
                            ROOT/'docs/investigation/upstream-comparison.json',
                            ROOT/'docs/investigation/baseline/baseline.prj',
                            ROOT/'docs/investigation/verification-progress.md',
                            ROOT/'.superpowers/sdd/2026-10-20-xpulpnn-cv32e40p/progress.md') if p.exists())
    # Pin the measured common ROM so the README's system rebuild works from this
    # source bundle without depending on an unarchived previous simulation run.
    common=ROOT/'artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671'
    expected_rom={'imem.hex':'48763bbe9aaa8a77dea7fe0103f143106381714fca78c1fce4fe2fca4359089a',
                  'dmem.hex':'591eb7ddfc7ae37061e60600eba5d524ff64e8aa515dde8ab41f2ea1a8154d10'}
    for name,digest in expected_rom.items():
        if sha(common/name)!=digest:
            raise RuntimeError(f'Common ROM changed: {name}')
    files.extend(common/name for name in ('imem.hex','dmem.hex','benchmark.json','expected.json',
                                         'build.json','test.elf','test.disasm','test.map'))
    files.extend(ROOT/name for name in ('artifacts/verification/summary.json',
        'artifacts/verification/benchmark-comparison.json','artifacts/fpga/summary.json',
        'artifacts/delivery/release-evidence.json'))
    manifest={'original_integrity':'PASS','originals':origins,
              'sources':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sorted(set(files))],
              'scope':'Local functional reproduction, DATE2020-local-v1; no author binary compatibility claim',
              'archive_scope':'Sources, approved specification/plan, reports, pinned common ROM and evidence indexes. Full historical simulation logs and Vivado checkpoints remain in the original workspace; regenerate projects after relocation.',
              'external_D_prototype':'not included and never written by this implementation; no initial whole-tree hash was recorded'}
    (out/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    diff=[]
    for changed in sorted((ROOT/'rtl/core').rglob('*.sv')):
        base=ROOT/'vendor/cv32e40p/rtl'/changed.relative_to(ROOT/'rtl/core')
        diff.extend(difflib.unified_diff(base.read_text().splitlines(keepends=True),
                    changed.read_text().splitlines(keepends=True),
                    fromfile=base.relative_to(ROOT).as_posix(),tofile=changed.relative_to(ROOT).as_posix()))
    (out/'core-overlays.patch').write_text(''.join(diff))
    with zipfile.ZipFile(out/'xpulpnn-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(set(files)):
            archive.write(p,p.relative_to(ROOT).as_posix())
        archive.write(out/'source-manifest.json','source-manifest.json')
        archive.write(out/'core-overlays.patch','core-overlays.patch')
    with zipfile.ZipFile(out/'xpulpnn-source.zip') as archive:
        bad=archive.testzip()
        if bad is not None:
            raise RuntimeError(f'Archive CRC failure: {bad}')
        for entry in manifest['sources']:
            if hashlib.sha256(archive.read(entry['path'])).hexdigest()!=entry['sha256']:
                raise RuntimeError(f'Archive source hash mismatch: {entry["path"]}')
    print(json.dumps({'status':'PASS','original_files_checked':len(origins),
                      'archived_files':len(set(files)),'archive_integrity':'PASS',
                      'archive_sha256':sha(out/'xpulpnn-source.zip'),'output':str(out)},indent=2))


if __name__=='__main__':
    package()

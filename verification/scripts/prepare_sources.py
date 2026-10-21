"""Freeze the existing local baseline without modifying its source checkout."""
import hashlib
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
ORIGIN = pathlib.Path('E:/cv32e40p-master/cv32e40p-master')
DEST = ROOT / 'vendor/cv32e40p'


def prepare():
    manifest_path = DEST / 'SOURCE.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for f in manifest['files']:
            p = ROOT / f['path']
            if hashlib.sha256(p.read_bytes()).hexdigest() != f['sha256']:
                raise RuntimeError(f'Frozen source changed; refusing overwrite: {p}')
        return manifest
    if DEST.exists():
        raise RuntimeError('Incomplete source destination exists; refusing to overwrite it')
    DEST.mkdir(parents=True)
    shutil.copytree(ORIGIN / 'rtl', DEST / 'rtl')
    shutil.copy2(ORIGIN / 'LICENSE', DEST / 'LICENSE')
    mappings = [
        (ROOT / 'FYP.srcs/sources_1/new/cv32e40p_clock_gate.sv', ROOT / 'rtl/platform/fpga/cv32e40p_clock_gate.sv'),
        (ORIGIN / 'bhv/cv32e40p_sim_clock_gate.sv', ROOT / 'rtl/platform/sim/cv32e40p_clock_gate.sv'),
    ]
    for src, dst in mappings:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise RuntimeError(f'Refusing to overwrite platform file: {dst}')
        shutil.copy2(src, dst)
    files = sorted(p for p in DEST.rglob('*') if p.is_file()) + [p[1] for p in mappings]
    manifest = {'origin': str(ORIGIN), 'key_files_match_upstream_commit': 'b353438ff469c030c89f6804f3b24a2852880e8b',
                'note': 'Pinned local snapshot; commit match established for 10 key files only.',
                'files': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    m = prepare()
    print(f'Frozen and verified {len(m["files"])} source/platform files')

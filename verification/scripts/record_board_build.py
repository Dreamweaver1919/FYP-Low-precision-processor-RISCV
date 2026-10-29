"""Record final 50 MHz bitstream hashes and reject changed source inputs."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('directory', type=Path)
    a=p.parse_args()
    build=json.loads((a.directory/'build.json').read_text())
    if build['status'] != 'PASS': raise ValueError('initial build failed')
    for item in build['sources']:
        if sha(ROOT/item['path']) != item['sha256']:
            raise ValueError('source changed since build: '+item['path'])
    for name,digest in build['memory_sha256'].items():
        if sha(a.directory/name) != digest: raise ValueError('memory changed: '+name)
    metrics=json.loads((a.directory/'implementation_50mhz.json').read_text())
    if metrics['period_ns'] != 20 or min(metrics['wns_ns'],metrics['whs_ns']) < 0 or metrics['drc_errors']:
        raise ValueError('final implementation did not meet 50 MHz')
    build['initial_implementation']=build['implementation']
    build['implementation']=metrics
    build['bitstream_sha256']=sha(a.directory/'board.bit')
    build['probes_sha256']=sha(a.directory/'board.ltx')
    build['finalization_script']={'path':'scripts/check_board_50mhz.tcl',
                                  'sha256':sha(ROOT/'scripts/check_board_50mhz.tcl')}
    (a.directory/'build.json').write_text(json.dumps(build,indent=2)+'\n')
    print(json.dumps({'config':build['config'],'build_id':build['build_id'],
                      'bitstream_sha256':build['bitstream_sha256'],'implementation':metrics},indent=2))


if __name__ == '__main__': main()

"""Independent-model per-form random stress and per-lane background sweeps.

SC vectors present already replicated B to the unit API; core ISA tests separately
exercise ID broadcast/forwarding. This does not claim full-register exhaustion.
"""
import argparse
import hashlib
import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'verification'))
from model.packed import alu, dot
from model.isa import ALU_OPCODES


def generate(out, seed):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    forms = json.loads((ROOT / 'verification/manifests/xpulpnn_isa.json').read_text())['forms']
    metadata = {'seed': seed, 'random_per_form': 1000, 'scalar_unit_vectors_prebroadcast': True,
                'exhaustion_scope': 'lane element pairs with independently varied other lanes', 'forms': {}}
    with (out / 'alu.hex').open('w') as af, (out / 'dot.hex').open('w') as df:
        for form in forms:
            if form['op'] == 'qnt':
                continue
            op, width, scalar = form['op'], form['width'], form['scalar']
            mask, lanes = (1 << width) - 1, 32 // width
            rep = sum(1 << (width * lane) for lane in range(lanes))
            is_dot = op.startswith(('dot', 'sdot'))
            signed_mode = 0 if op.endswith('up') else 1 if op.endswith('usp') else 3
            count = 0

            def emit(a, b_raw, acc):
                nonlocal count
                b = (b_raw & mask) * rep if scalar else b_raw
                if is_dot:
                    expected = dot(width, signed_mode, a, b_raw, acc, scalar)
                    df.write(f'{width:x} {signed_mode:x} {a:08x} {b:08x} {acc:08x} {expected:08x}\n')
                else:
                    expected = alu(op, width, a, b_raw, scalar)
                    af.write(f'{ALU_OPCODES[op]:x} {int(op in ("avg", "avgu")):x} {width:x} {a:08x} {b:08x} {expected:08x}\n')
                count += 1

            for index in range(1000):
                acc = rng.getrandbits(32) if op.startswith('sdot') else 0
                if op.startswith('sdot') and index < 4:
                    acc = (0, 0xffffffff, 0x7fffffff, 0x80000000)[index]
                emit(rng.getrandbits(32), rng.getrandbits(32), acc)
            random_count = count
            for lane in range(lanes):
                for x in range(mask + 1):
                    for y in (range(mask + 1) if op != 'abs' else (0,)):
                        a = (rng.getrandbits(32) & ~(mask << (lane * width))) | (x << (lane * width))
                        b_lane = 0 if scalar else lane
                        b = (rng.getrandbits(32) & ~(mask << (b_lane * width))) | (y << (b_lane * width))
                        acc = rng.choice((0, 0xffffffff, 0x7fffffff, 0x80000000)) if op.startswith('sdot') else 0
                        emit(a, b, acc)
            metadata['forms'][form['name']] = {'random': random_count, 'lane_background': count - random_count, 'total': count}
    metadata['files'] = {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                                'vectors': sum(1 for _ in p.open())}
                         for p in (out / 'alu.hex', out / 'dot.hex')}
    metadata['total_forms'] = len(metadata['forms'])
    (out / 'vectors.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args()
    result = generate(args.out, args.seed)
    print(json.dumps({'forms': result['total_forms'], 'counts': result['files']}, indent=2))

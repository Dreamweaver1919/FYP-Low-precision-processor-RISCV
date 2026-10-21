import argparse
import hashlib
import json
import pathlib
import random
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from model.packed import alu, dot
from model.isa import ALU_OPCODES


def generate(out, seed=1, random_count=10000):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    counts = {}
    with (out/'alu.hex').open('w') as af, (out/'dot.hex').open('w') as df:
        for width in (4,2):
            mask = (1<<width)-1
            rep = sum(1<<(i*width) for i in range(32//width))
            pairs = [(x*rep,y*rep) for x in range(mask+1) for y in range(mask+1)]
            pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(random_count)]
            for op, code in ALU_OPCODES.items():
                for a,b in pairs:
                    e = alu(op,width,a,b)
                    af.write(f'{code:02x} {int(op in ("avg","avgu")):x} {width:x} {a:08x} {b:08x} {e:08x}\n')
                counts[f'{op}{width}'] = len(pairs)
            for mode in (0,1,3):
                for a,b in pairs:
                    c = rng.getrandbits(32)
                    df.write(f'{width:x} {mode:x} {a:08x} {b:08x} {c:08x} {dot(width,mode,a,b,c):08x}\n')
                counts[f'dot{width}_{mode}'] = len(pairs)
    meta = {'seed':seed,'random_per_op':random_count,'counts':counts,
            'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'alu.hex',out/'dot.hex')}}
    (out/'vectors.json').write_text(json.dumps(meta,indent=2)+'\n')
    return meta


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--random-count',type=int,default=10000)
    a=p.parse_args()
    m=generate(a.out,a.seed,a.random_count)
    print(f'Generated {sum(m["counts"].values())} independent ALU/dot vectors')

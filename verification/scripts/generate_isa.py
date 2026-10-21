import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from model.isa import forms

ROOT = pathlib.Path(__file__).resolve().parents[2]


def generate():
    fs = forms()
    dst = ROOT / 'verification/manifests/xpulpnn_isa.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps({'abi':'DATE2020-local-v1','opcode':123,'forms':fs}, indent=2)+'\n')
    header = ['/* Private legacy test glue. Public typed API is xpulpnn.h. avg wraps BEFORE shift. */',
              '#ifndef XPULPNN_WORDS_H','#define XPULPNN_WORDS_H','#include <stdint.h>']
    for f in fs:
        name = f['name'].replace('.','_')
        # RISC-V R-type funct7 consists of funct6 followed by reserved bit25=0.
        rs2 = 'zero' if f['op']=='abs' else '%2'
        header += [f'static inline uint32_t nn_{name}(uint32_t a, uint32_t b, uint32_t acc) {{',
                   '  uint32_t r = acc;',
                   f'  __asm__ volatile (".insn r 0x7b, {f["funct3"]}, {f["funct6"]<<1}, %0, %1, {rs2}" : "+r"(r) : "r"(a), "r"(b) : "memory");',
                   '  return r;','}']
    header += ['#endif','']
    out = ROOT / 'verification/sw/common/xpulpnn_words.h'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(header))
    print(f'Generated {len(fs)} forms')


if __name__ == '__main__': generate()

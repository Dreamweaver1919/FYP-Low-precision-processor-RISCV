"""Directed CPU programs for pipeline and preserved legacy behavior.

Expected values use independent packed/linear-threshold models. No RTL data
path is imported. Files emitted in each run directory preserve exact programs.
"""
import json
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model.isa import encode, forms
from model.packed import alu, dot
from model.quant import quantize_pair


def word(op, bits, rd=7, ra=5, rb=6, sc=False):
    return f"  .word 0x{encode(op,bits,sc,rd,ra,rb):08x}"


def generate(test, out, seed=1):
    rng=random.Random(seed)
    lines=['.option norvc','.section .text,"ax"','.global main','main:',
           '  la s0,signature_start']
    expected=[]
    data=[]
    def save(value,reg=7):
        lines.extend([f'  sw x{reg},0(s0)','  addi s0,s0,4'])
        expected.append(value & 0xffffffff)
    if test=='disabled_isa':
        # All 72 otherwise legal forms must trap when the feature is disabled.
        # Preserve rd and verify exact fault PC, rather than accepting any trap.
        legal=forms()
        lines.extend(['  la s1,trap_records','  la s2,expected_pcs',
                      '  li t0,0x12345678','  la t1,tables'])
        data.extend(['expected_pcs:']+[f'.word fault_{n}' for n in range(len(legal))])
        data.extend(['.balign 64','tables:','.space 128'])
        for n,f in enumerate(legal):
            lines.extend(['  li t2,0x5aa55aa5',f'fault_{n}:',
                          word(f['op'],f['width'],rb=0 if f['op']=='abs' else 6,sc=f['scalar'])])
            save(0x5aa55aa5)
        lines.extend(['  li a0,0','  ret','.global trap_fail','trap_fail:',
                      '  csrr a5,mcause','  sw a5,0(s1)','  csrr a5,mepc','  lw a6,0(s2)',
                      '  sub a6,a5,a6','  sw a6,4(s1)','  addi s1,s1,8','  addi s2,s2,4',
                      '  addi a5,a5,4','  csrw mepc,a5','  mret',
                      '.section .signature,"aw",@nobits',f'.space {len(legal)*4}',
                      'trap_records:',f'.space {len(legal)*8}', '.section .data,"aw"']+data)
        expected += [v for _ in legal for v in (2,0)]
        (out/'extra_expected.json').write_text(json.dumps({'data_requests':72*4+3})+'\n')
        source=out/(test+'.S');source.write_text('\n'.join(lines)+'\n')
        return source,expected
    if test=='dependencies':
        # Consecutive sdot uses the previous rd as its third forwarded source.
        for bits in (4,2):
            for mode,op in ((0,'sdotup'),(1,'sdotusp'),(3,'sdotsp')):
                for scalar in (False,True):
                    a,b=rng.getrandbits(32),rng.getrandbits(32)
                    acc=0xfffffff0
                    lines.extend([f'  li t0,0x{a:08x}',f'  li t1,0x{b:08x}',
                                  f'  li t2,0x{acc:08x}'])
                    for _ in range(20):
                        lines.append(word(op,bits,sc=scalar))
                        acc=dot(bits,mode,a,b,acc,scalar)
                    # Immediately consume final accumulator with another NN op.
                    lines.append(word('add',bits,rd=7,ra=7,rb=5))
                    save(alu('add',bits,acc,a))
            a,b=0x89abcdef,0x76543210
            data.extend([f'load_{bits}:',f'.word 0x{a:08x},0x{b:08x}'])
            lines.extend([f'  la t3,load_{bits}','  li t0,0','  lw t0,0(t3)',
                          word('add',bits,rd=5,ra=5,rb=5),
                          '  lw t1,4(t3)',word('sdotusp',bits,rd=6,ra=5,rb=6)])
            save(dot(bits,1,alu('add',bits,a,a),b,b),reg=6)
        # Back-to-back qnt with alternating precision, including rd=rs1, rd=rs2.
        thresholds=list(range(-7,8))
        data.extend(['.balign 64','tables:']+
                    [f'.word {x}' for x in thresholds]+['.word 0']+
                    [f'.word {x}' for x in thresholds]+['.word 0',
                    'qnt_values:','.word 0x0008fff8','.word tables'])
        packed=0x0008fff8
        lines.extend(['  la t3,qnt_values','  lw t0,0(t3)','  lw t1,4(t3)',
                      word('qnt',2,rd=7),word('qnt',4,rd=28)])
        save(quantize_pair(2,-8,8,thresholds[:3],thresholds[:3]))
        save(0x78,reg=28)
        lines.extend([word('qnt',2,rd=5),word('qnt',4,rd=6)])
        result=quantize_pair(2,-8,8,thresholds[:3],thresholds[:3])
        save(result,reg=5)
        save(quantize_pair(4,result,0,thresholds,thresholds),reg=6)
    elif test=='wrong_path':
        lines.extend(['  li t0,0x000ffffb','  li t1,1','  li t2,0x12345678',
                      '  beq zero,zero,skip_bad',word('qnt',2),'skip_bad:',
                      '  la t1,tables','  bne t0,zero,skip_good',
                      word('qnt',4),'skip_good:'])
        save(0x12345678)
        data.extend(['.balign 64','tables:','.space 128'])
        (out/'extra_expected.json').write_text(json.dumps({'data_requests':4})+'\n')
    elif test=='hwloop':
        # lp.setupi loop0: immediate count=4, end=PC+5*4. Four-instruction
        # body puts qnt immediately before the end and tests the held jump.
        lines.extend(['  li t0,0x000ffffb','  la t1,tables','  li s1,0',
                      f'  .word 0x{(4<<20)|(5<<15)|(4<<12)|(6<<8)|0x2b:08x}',
                      'loop_body:','  addi s1,s1,1',word('qnt',2),
                      '  add s1,s1,t2','  nop'])
        save(32,reg=9)
        save(7)
        data.extend(['.balign 64','tables:','.word -10,0,10','.space 52',
                     '.word -10,0,10','.space 52'])
        (out/'extra_expected.json').write_text(json.dumps({'data_requests':21})+'\n')
    elif test=='legacy_misc':
        def legacy(fn,f3=0,rb=6,bit25=0):
            return f'  .word 0x{(fn<<26)|(bit25<<25)|(rb<<20)|(5<<15)|(f3<<12)|(7<<7)|0x7b:08x}'
        a,b=0x817fc35a,0x01234567
        # Every lane of signed/unsigned byte and halfword extraction.
        for bits in (8,16):
            for unsigned in (False,True):
                for lane in range(32//bits):
                    lines.extend([f'  li t0,0x{a:08x}',
                                  legacy(46,(bits==8)|(2 if unsigned else 0),lane>>1,lane&1)])
                    x=(a>>(bits*lane))&((1<<bits)-1)
                    if not unsigned and x>>(bits-1): x-=1<<bits
                    save(x)
        for bits in (8,16):
            control=0x00010203 if bits==8 else 1
            lines.extend([f'  li t0,0x{a:08x}',f'  li t1,0x{control:08x}',
                          legacy(48,int(bits==8))])
            save(int.from_bytes(a.to_bytes(4,'little')[::-1],'little') if bits==8
                 else ((a<<16)|(a>>16)))
        for high in (0,1):
            lines.extend([f'  li t0,0x{a:08x}',f'  li t1,0x{b:08x}',legacy(60,bit25=high)])
            save((((a>>(16*high))&0xffff)<<16)|((b>>(16*high))&0xffff))
        lines.extend(['  li t0,0x80010002',legacy(23,rb=0)])
        save(0x7fff0002)  # complex conjugate preserves real, negates imaginary
    else:
        raise ValueError(test)
    lines.extend(['  li a0,0','  ret','.section .signature,"aw",@nobits',
                  f'.space {4*len(expected)}','.section .data,"aw"']+data)
    source=out/(test+'.S')
    source.write_text('\n'.join(lines)+'\n')
    return source,expected

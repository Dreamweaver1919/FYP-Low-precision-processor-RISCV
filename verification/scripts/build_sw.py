"""Freestanding stock-GCC build and strict byte-to-word image conversion."""
import argparse
import hashlib
import json
import pathlib
import random
import subprocess
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from model.isa import forms, encode
from model.packed import alu, dot
from model.quant import quantize_pair
from model.kernels import datasets, pack_row, reference

ROOT = pathlib.Path(__file__).resolve().parents[2]
BIN = pathlib.Path('D:/fyp-xpulpnn/tools/xpack-riscv-none-elf-gcc-15.2.0-1/bin')


def convert_verilog_image(text):
    mem = {}
    address = 0
    for line in text.splitlines():
        line = line.split('//')[0]
        for token in line.split():
            if token.startswith('@'): address = int(token[1:],16)
            else:
                value = int(token,16)
                if not 0 <= value <= 255: raise ValueError('expected byte-addressed objcopy image')
                if not (0 <= address < 0x10000 or 0x10000000 <= address < 0x10010000):
                    raise ValueError(f'image address out of range: {address:#x}')
                if address in mem: raise ValueError('overlapping image bytes')
                mem[address] = value
                address += 1
    images = []
    for base in (0,0x10000000):
        words=[]
        for address in range(base,base+0x10000,4):
            words.append(sum(mem.get(address+i,0)<<(8*i) for i in range(4)))
        images.append(words)
    return images


def arithmetic_source(out, seed, legacy=False):
    rng=random.Random(seed)
    lines=['.option norvc','.section .text,"ax"','.global main','main:','  la s0,signature_start']
    expected=[]
    cases=[]
    legacy_fn={'add':0,'sub':2,'avg':4,'avgu':6,'min':8,'minu':10,'max':12,'maxu':14,
               'srl':16,'sra':18,'sll':20,'abs':28,'dotup':32,'dotusp':34,'dotsp':36,
               'sdotup':38,'sdotusp':40,'sdotsp':42}
    for f in forms():
        if f['op']=='qnt': continue
        width = (16 if f['width']==4 else 8) if legacy else f['width']
        for index in range(8):
            a,b,c = (rng.getrandbits(32) for _ in range(3))
            if index==0: a,b,c=0xffffffff,0xffffffff,0xfffffffe
            rd=5 if index==3 else 6 if index==4 else 0 if index==5 else 7
            ra=0 if index==6 else 5
            rb=0 if f['op']=='abs' or index==7 else 6
            effective_a=0 if ra==0 else a
            effective_b=0 if rb==0 else b
            acc=a if rd==5 else b if rd==6 else 0 if rd==0 else c
            word=((legacy_fn[f['op']]<<26)|(rb<<20)|(ra<<15)|(f['funct3']<<12)|(rd<<7)|0x7b) if legacy else encode(f['op'],f['width'],f['scalar'],rd,ra,rb)
            lines += [f'  li t0,0x{a:08x}',f'  li t1,0x{b:08x}',f'  li t2,0x{c:08x}',
                      f'  .word 0x{word:08x}',
                      f'  sw x{rd},0(s0)','  addi s0,s0,4']
            op=f['op']
            if op in ('dotup','dotusp','dotsp','sdotup','sdotusp','sdotsp'):
                mode={'up':0,'usp':1,'sp':3}[op[4:] if op.startswith('sdot') else op[3:]]
                e=dot(width,mode,effective_a,effective_b,acc if op.startswith('sdot') else 0,f['scalar'])
            else: e=alu(op,width,effective_a,effective_b,f['scalar'])
            if rd==0: e=0
            expected.append(e)
            cases.append({'form':f['name'],'width':width,'index':index,'rd':rd,'rs1':ra,'rs2':rb,'a':a,'b':b,'c':c,'expected':e})
    lines += ['  li a0,0','  ret','.section .signature,"aw",@nobits',f'.space {len(expected)*4}']
    source=out/('legacy_xpulp.S' if legacy else 'nn_arithmetic.S')
    source.write_text('\n'.join(lines)+'\n')
    (out/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    return source,expected


def quant_source(out, seed):
    rng=random.Random(seed)
    cases=[(2,-5,15,[-10,0,10],[-10,0,10]),
           (4,-8,8,list(range(-7,8)),list(range(-7,8))),
           (2,0,0,[0,0,0],[-1,0,1]),
           (4,-32768,32767,list(range(-7,8)),list(range(-15,0))),
           (2,10,-10,[-10,0,10],[-100,-10,10]),
           (4,3,-4,list(range(-7,8)),list(range(-10,5)))]
    for n in range(200):
        q=4 if n%2==0 else 2
        count=(1<<q)-1
        cases.append((q,rng.randrange(-32768,32768),rng.randrange(-32768,32768),
                      sorted(rng.randrange(-32768,32768) for _ in range(count)),
                      sorted(rng.randrange(-32768,32768) for _ in range(count))))
    lines=['.option norvc','.section .text,"ax"','.global main','main:','  la s0,signature_start']
    data=['.section .data,"aw"']
    expected=[]
    for n,(q,a,b,t0,t1) in enumerate(cases):
        packed=(a&0xffff)|((b&0xffff)<<16)
        rd=5 if n==3 else 6 if n==4 else 0 if n==5 else 7
        lines += [f'  li t0,0x{packed:08x}','  li t1,1',f'  la t3,base_pointer_{n}',
                  '  lw t1,0(t3)',f'  .word 0x{encode("qnt",q,False,rd,5,6):08x}',
                  f'  sw x{rd},0(s0)','  addi s0,s0,4']
        expected.append(0 if rd==0 else quantize_pair(q,a,b,t0,t1))
        data += ['.balign 64',f'table_{n}:']
        for table in (t0,t1):
            data += [f'.word 0x{x&0xffffffff:08x}' for x in table]
            data += [f'.space {(16-len(table))*4}']
        data += [f'base_pointer_{n}:',f'.word table_{n}']
    lines += ['  li a0,0','  ret','.section .signature,"aw",@nobits',f'.space {len(expected)*4}']+data
    source=out/'nn_quant.S';source.write_text('\n'.join(lines)+'\n')
    (out/'cases.json').write_text(json.dumps([{'q':q,'a0':a,'a1':b,'t0':t0,'t1':t1} for q,a,b,t0,t1 in cases],indent=2)+'\n')
    return source,expected


def bad_base_source(out):
    bases=[0x10000004,0xffffffc0,0x1000003f,0xffffffff]
    lines=['.option norvc','.section .text,"ax"','.global main','main:',
           '  la s0,signature_start','  la s1,trap_records','  la s2,expected_pcs']
    labels=['bad_alu']+[f'bad_{n}' for n in range(len(bases))]
    data=['.section .data,"aw"','expected_pcs:']+[f'.word {label}' for label in labels]
    data += ['base_values:']+[f'.word 0x{b:08x}' for b in bases]
    lines += ['  li t0,0x000ffffb','  la t1,valid_tables','  addi t1,t1,0',
              f'  .word 0x{encode("qnt",2,False,7,5,6):08x}',
              '  sw x7,0(s0)','  addi s0,s0,4',
              '  li t0,0x000ffffb','  la t1,valid_tables','  addi t1,t1,4',
              '  li t2,0x12345678',
              f'bad_alu: .word 0x{encode("qnt",2,False,7,5,6):08x}',
              '  sw t2,0(s0)','  addi s0,s0,4']
    for n,base in enumerate(bases):
        q=2 if n%2==0 else 4
        lines += ['  li t0,0x000ffffb','  li t1,0x10000000','  li t2,0x12345678',f'  la t3,base_values+{4*n}',
                  '  lw t1,0(t3)',f'bad_{n}: .word 0x{encode("qnt",q,False,7,5,6):08x}',
                  '  sw t2,0(s0)','  addi s0,s0,4']
    lines += ['  li a0,0','  ret','.global trap_fail','trap_fail:',
              '  csrr a5,mcause','  sw a5,0(s1)','  csrr a5,mepc','  lw a6,0(s2)',
              '  sub a6,a5,a6','  sw a6,4(s1)','  addi s1,s1,8','  addi s2,s2,4',
              '  addi a5,a5,4','  csrw mepc,a5','  mret',
              '.section .signature,"aw",@nobits',f'.space {(len(labels)+1)*4}','trap_records:',f'.space {len(labels)*8}',
              '.section .data,"aw"','.balign 64','valid_tables:','.word -10,0,10','.space 52','.word -10,0,10','.space 52']+data
    source=out/'nn_quant_bad_base.S';source.write_text('\n'.join(lines)+'\n')
    return source,[7]+[0x12345678]*len(labels)+[x for _ in labels for x in (2,0)]


def benchmark_header(out,seed):
    data=datasets(seed);expected=[];lines=['#include "kernels.h"']
    meta=[]
    for index,d in enumerate(data):
        q=d['q'];stride=(d['k']+32//q-1)//(32//q)
        a=pack_row(d['image'],q) if d['image'] is not None else sum((pack_row(row,q) for row in d['a']),[])
        b=sum((pack_row(row,q) for row in d['b']),[])
        for name,values in (('a',a),('b',b)):
            lines += [f'static const uint32_t data_{index}_{name}[]={{'+','.join(f'0x{x:08x}u' for x in values)+'};']
        lines += [f'static const int32_t thresholds_{index}[8][16] __attribute__((aligned(64)))={{']
        for table in d['thresholds']: lines += ['{'+','.join(str(x) for x in table+[0]*(16-len(table)))+'},']
        lines += ['};']
        expected += reference(d)
        meta.append({'name':d['name'],'m':d['m'],'k':d['k'],'n':d['n'],'q':q,'stride_words':stride,
                     'logical_macs':d['m']*d['k']*d['n'],
                     'nn_physical_lane_macs':d['m']*stride*(32//q)*d['n'],
                     'output_words':d['m']*d['n']//2})
    lines += [f'static const dataset_t bench_datasets[{len(data)}]={{']
    for index,d in enumerate(data):
        stride=(d['k']+32//d['q']-1)//(32//d['q'])
        lines += [f'{{{d["m"]},{d["k"]},{d["n"]},{d["q"]},{int(d["kind"]=="conv")},{stride},data_{index}_a,data_{index}_b,thresholds_{index}}},']
    metrics=len(data)*16+4+16
    lines += ['};',f'#define BENCH_DATASETS {len(data)}',f'#define BENCH_OUTPUT_WORDS {len(expected)}',f'#define BENCH_SIGNATURE_WORDS {len(expected)+metrics}',
              'static const uint32_t bench_expected[]={'+','.join(f'0x{x:08x}u' for x in expected)+'};']
    (out/'benchmark_data.h').write_text('\n'.join(lines)+'\n')
    (out/'benchmark.json').write_text(json.dumps({'datasets':meta,'output_words':len(expected),
                                                 'metrics_offset':len(expected),'metrics_per_dataset':16,
                                                 'throughput_offset':len(expected)+len(data)*16+4,
                                                 'primary_denominator':'legacy dot8 including packed input unpack/sign extension and software binary-search quantization',
                                                 'preparation':'MatMul packed input copy; Conv im2col and packing from packed NHWC image; zero-padded final reduction block',
                                                 'seed':seed},indent=2)+'\n')
    return expected+[None]*metrics


def event_source(out, mode):
    lines=['.option norvc','.section .text,"ax"','.global main','main:',
           '  la s0,signature_start','  li t0,0x000ffffb','  la t1,event_tables']
    if mode=='irq': lines += ['  li t3,0x800','  csrs mie,t3','  csrsi mstatus,8']
    lines += (['  li t1,0x30000000'] if mode=='unmapped' else ['  lw s4,0(t1)'])
    lines += ['before_event_qnt:',f'  .word 0x{encode("qnt",2,False,7,5,6):08x}',
              'after_event_qnt:','  sw t2,0(s0)']
    if mode in ('irq','debug','debug_pre','step'):
        lines += ['  la t3,event_record','1: lw t4,0(t3)','  beqz t4,1b',
                  '  sw t4,4(s0)','  lw t4,4(t3)','  sw t4,8(s0)']
    lines += ['  li a0,0','  ret']
    if mode=='irq':
        lines += ['.global trap_fail','trap_fail:','  csrr a5,mcause','  la a6,event_record',
                  '  sw a5,4(a6)','  li a5,1','  sw a5,0(a6)','  li a5,0x800','  csrc mie,a5','  mret']
    if mode in ('debug','debug_pre'):
        target='before_event_qnt' if mode=='debug_pre' else 'after_event_qnt'
        lines += ['.global debug_entry','debug_entry:','  csrr a5,dpc',f'  la a6,{target}',
                  '  sub a5,a5,a6','  la a6,event_record','  sw a5,4(a6)','  li a5,1',
                  '  sw a5,0(a6)','  dret']
    if mode=='step':
        lines += ['.global debug_entry','debug_entry:','  la a6,event_record','  lw a5,0(a6)',
                  '  bnez a5,step_completed','  li a5,1','  sw a5,0(a6)',
                  '  la a5,before_event_qnt','  csrw dpc,a5','  csrsi dcsr,4','  dret',
                  'step_completed:','  csrr a5,dpc','  la a6,after_event_qnt','  sub a5,a5,a6',
                  '  la a6,event_record','  sw a5,4(a6)','  li a5,2','  sw a5,0(a6)',
                  '  csrci dcsr,4','  dret']
    lines += ['.section .signature,"aw",@nobits',f'.space {12 if mode in ("irq","debug","debug_pre","step") else 4}',
              '.section .data,"aw"','.balign 64','event_tables:','.word -10,0,10','.space 52',
              '.word -10,0,10','.space 52','event_record:','.word 0,0']
    source=out/f'nn_{mode}.S';source.write_text('\n'.join(lines)+'\n')
    return source,[7,1,0x8000000b] if mode=='irq' else [7,1,0] if mode in ('debug','debug_pre') else [7,2,0] if mode=='step' else [7]


def build(test, isa, seed, out):
    out=pathlib.Path(out).resolve(); out.mkdir(parents=True,exist_ok=True)
    common=ROOT/'verification/sw/common'
    if test in ('nn_arithmetic','legacy_xpulp'): source,expected=arithmetic_source(out,seed,test=='legacy_xpulp')
    elif test=='nn_quant': source,expected=quant_source(out,seed)
    elif test=='nn_quant_bad_base': source,expected=bad_base_source(out)
    elif test=='bench_common':
        source=ROOT/'verification/sw/bench/conv.c'
        expected=benchmark_header(out,seed)
    elif test in ('nn_irq','nn_debug','nn_debug_pre','nn_reset','nn_step','nn_hold','nn_unmapped'):source,expected=event_source(out,test[3:])
    elif test in ('dependencies','wrong_path','legacy_misc','hwloop','disabled_isa'):
        from extra_cases import generate
        source,expected=generate(test,out,seed)
    elif test=='rv32_smoke':
        source=ROOT/'verification/sw/tests/rv32_smoke.S'
        expected=[42,20,341,2,9,0x1122aa44,0x1122aa44]
    else: raise ValueError(f'unknown test {test}')
    elf=out/'test.elf'
    args=[str(BIN/'riscv-none-elf-gcc.exe'),'-march=rv32imc_zicsr','-mabi=ilp32','-mcmodel=medany',
          '-nostdlib','-nostartfiles','-ffreestanding','-fno-builtin','-fno-pic','-fno-pie',
          '-msmall-data-limit=0','-mno-relax','-O2','-I',str(common),'-I',str(out),'-I',str(ROOT/'verification/sw/bench'),'-T',str(common/'link.ld'),
          '-Wl,-Map='+str(out/'test.map'),str(common/'crt0.S'),str(common/'vectors.S'),str(source),'-o',str(elf)]
    if test=='bench_common':
        args[-2:-2]=[str(ROOT/'verification/sw/bench'/name) for name in ('matmul.c','kernels_xpulp.c','kernels_xpulpnn.c','kernels_scalar.c')]
    subprocess.run(args,check=True,capture_output=True,text=True)
    subprocess.run([str(BIN/'riscv-none-elf-objcopy.exe'),'-O','verilog',str(elf),str(out/'image.bytes.hex')],check=True)
    with (out/'test.disasm').open('w') as f:
        subprocess.run([str(BIN/'riscv-none-elf-objdump.exe'),'-D',str(elf)],check=True,stdout=f)
    images=convert_verilog_image((out/'image.bytes.hex').read_text())
    for name,words in zip(('imem.hex','dmem.hex'),images):
        (out/name).write_text(''.join(f'{x:08x}\n' for x in words))
    expectation={'test':test,'isa':isa,'seed':seed,'signature':expected}
    if test in ('nn_arithmetic','legacy_xpulp'): expectation['data_requests']=len(expected)+3
    elif test=='nn_quant_bad_base': expectation['data_requests']=32
    elif test=='nn_quant':
        cases=json.loads((out/'cases.json').read_text())
        expectation['data_requests']=sum(2*c['q']+2 for c in cases)+3
    if (out/'extra_expected.json').exists():expectation.update(json.loads((out/'extra_expected.json').read_text()))
    (out/'expected.json').write_text(json.dumps(expectation,indent=2)+'\n')
    (out/'build.json').write_text(json.dumps({'command':args,'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),
                                             'test':test,'isa':isa,'seed':seed},indent=2)+'\n')
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',required=True)
    p.add_argument('--isa',choices=('rv32imc','xpulp','xpulpnn'),default='rv32imc')
    p.add_argument('--seed',type=int,default=1);p.add_argument('--out',required=True)
    a=p.parse_args()
    try: print(build(a.test,a.isa,a.seed,a.out))
    except subprocess.CalledProcessError as e:
        print(e.stderr or e, file=sys.stderr);raise SystemExit(1)

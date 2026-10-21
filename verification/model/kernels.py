"""Independent scalar MatMul/valid Conv and stored low-bit data layouts."""
import random
from .quant import quantize_pair


def pack_row(values, q):
    lanes=32//q
    result=[]
    for start in range(0,len(values),lanes):
        word=0
        for lane,value in enumerate(values[start:start+lanes]):
            if not -(1<<(q-1)) <= value < (1<<(q-1)):raise ValueError('value outside signed lane')
            word|=(value&((1<<q)-1))<<(lane*q)
        result.append(word)
    return result


def unpack_row(words,count,q):
    if len(words)!=(count+32//q-1)//(32//q):raise ValueError('physical row length mismatch')
    values=[]
    for index in range(count):
        value=(words[index//(32//q)]>>((index%(32//q))*q))&((1<<q)-1)
        values.append(value-(1<<q) if value&(1<<(q-1)) else value)
    return values


def datasets(seed):
    rng=random.Random(seed); result=[]
    for q in (4,2):
        low,high=-(1<<(q-1)),(1<<(q-1))
        for kind in ('matmul','conv','tail'):
            m,k,n=(8,32,8) if kind=='matmul' else (36,72,8) if kind=='conv' else (2,35,2)
            image=None
            if kind!='conv':rows=[[rng.randrange(low,high) for _ in range(k)] for _ in range(m)]
            else:
                image=[rng.randrange(low,high) for _ in range(8*8*8)]
                rows=[[image[((oy+ky)*8+(ox+kx))*8+ci] for ky in range(3) for kx in range(3) for ci in range(8)]
                      for oy in range(6) for ox in range(6)]
            weights=[[rng.randrange(low,high) for _ in range(k)] for _ in range(n)]
            thresholds=[[((j-(1<<(q-1))+1)*(16 if q==4 else 8))+channel for j in range((1<<q)-1)] for channel in range(n)]
            result.append({'name':f'{kind}_q{q}','kind':kind,'q':q,'m':m,'k':k,'n':n,
                           'a':rows,'b':weights,'image':image,'thresholds':thresholds})
    return result


def reference(data):
    output=[]
    for row in data['a']:
        accumulators=[sum(x*y for x,y in zip(row,col)) for col in data['b']]
        if any(not -32768<=a<=32767 for a in accumulators):raise ValueError('benchmark accumulator must fit int16')
        for channel in range(0,data['n'],2):
            output.append(quantize_pair(data['q'],accumulators[channel],accumulators[channel+1],
                                        data['thresholds'][channel],data['thresholds'][channel+1]))
    return output

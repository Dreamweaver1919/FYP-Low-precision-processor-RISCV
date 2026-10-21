"""Reviewed local encoding data; numerical operations are implemented elsewhere."""
FUNCTIONS = {'add':0x1e,'sub':0x1f,'avg':0x21,'avgu':0x23,
             'min':0x25,'minu':0x27,'max':0x29,'maxu':0x2b,
             'srl':0x2c,'sra':0x2d,'sll':0x2f,'abs':0x31,
             'dotup':0x33,'dotusp':0x35,'dotsp':0x37,
             'sdotup':0x39,'sdotusp':0x3a,'sdotsp':0x3b,'qnt':0x3d}
ALU_OPCODES = {'add':24,'sub':25,'avg':24,'avgu':26,'min':16,'minu':17,
               'max':18,'maxu':19,'srl':37,'sra':36,'sll':39,'abs':20}


def forms():
    result = []
    for op, fn in FUNCTIONS.items():
        for width, bit in ((4,0),(2,1)):
            for scalar in ((False,) if op in ('abs','qnt') else (False,True)):
                f3 = bit | (4 if scalar else 0)
                result.append({'name':op+('.sc' if scalar else '')+('.n' if width==4 else '.c'),
                               'op':op,'width':width,'scalar':scalar,'funct6':fn,'funct3':f3,
                               'mask':0xfff0707f if op=='abs' else 0xfe00707f,
                               'value':(fn<<26)|(f3<<12)|0x7b})
    return result


def encode(op, width, scalar, rd, rs1, rs2=0):
    if width not in (2,4) or scalar and op in ('abs','qnt'):
        raise ValueError('illegal instruction form')
    if op == 'abs' and rs2 != 0:
        raise ValueError('abs requires rs2=x0')
    if any(not 0 <= r < 32 for r in (rd,rs1,rs2)):
        raise ValueError('invalid register')
    f3 = (1 if width == 2 else 0) | (4 if scalar else 0)
    return (FUNCTIONS[op]<<26)|(rs2<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|0x7b

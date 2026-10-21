"""Independent mathematical oracle for the local DATE2020 instruction ABI."""
MASK32 = (1 << 32) - 1


def signed(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def alu(op, width, a, b=0, scalar=False):
    if width not in (2, 4, 8, 16):
        raise ValueError('unsupported packed width')
    mask = (1 << width) - 1
    result = 0
    for lane in range(32 // width):
        x = (a >> (lane * width)) & mask
        y = (b >> (0 if scalar else lane * width)) & mask
        sx, sy = signed(x, width), signed(y, width)
        if op == 'add': v = x + y
        elif op == 'sub': v = x - y
        elif op == 'avg': v = signed(x + y, width) >> 1
        elif op == 'avgu': v = ((x + y) & mask) >> 1
        elif op == 'min': v = min(sx, sy)
        elif op == 'minu': v = min(x, y)
        elif op == 'max': v = max(sx, sy)
        elif op == 'maxu': v = max(x, y)
        elif op == 'abs': v = abs(sx)
        elif op == 'srl': v = x >> (y & (width - 1))
        elif op == 'sra': v = sx >> (y & (width - 1))
        elif op == 'sll': v = x << (y & (width - 1))
        else: raise ValueError(f'unknown ALU op {op}')
        result |= (v & mask) << (lane * width)
    return result & MASK32


def dot(width, signed_mode, a, b, acc=0, scalar=False):
    if width not in (2, 4, 8, 16) or signed_mode not in (0, 1, 3):
        raise ValueError('invalid dot width/signed mode')
    mask = (1 << width) - 1
    total = acc & MASK32
    for lane in range(32 // width):
        x = (a >> (lane * width)) & mask
        y = (b >> (0 if scalar else lane * width)) & mask
        if signed_mode & 2: x = signed(x, width)
        if signed_mode & 1: y = signed(y, width)
        total += x * y
    return total & MASK32

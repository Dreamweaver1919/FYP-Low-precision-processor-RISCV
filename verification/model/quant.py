"""Quantization oracle uses linear rank counting, not the hardware search tree."""
def quantize_pair(q, a0, a1, t0, t1):
    if q not in (2, 4):
        raise ValueError('q must be 2 or 4')
    mask = (1 << q) - 1
    out = 0
    for channel, (activation, table) in enumerate(((a0, t0), (a1, t1))):
        if len(table) != mask or any(x > y for x, y in zip(table, table[1:])):
            raise ValueError('thresholds must have required length and be nondecreasing')
        if not -32768 <= activation <= 32767 or any(not -32768 <= t <= 32767 for t in table):
            raise ValueError('activation and thresholds must be int16')
        rank = sum(t <= activation for t in table)
        out |= ((rank - (1 << (q - 1))) & mask) << (channel * q)
    return out

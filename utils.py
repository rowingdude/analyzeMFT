""" This is a port of bitparse.py using the work from Willi Ballenthin """


def parse_little_endian_signed(buf):
    if not buf[-1] & 0b10000000:
        return parse_little_endian_signed_positive(buf)
    else:
        return parse_little_endian_signed_negative(buf)

def parse_little_endian_signed_positive(buf):
    ret = 0
    for i, b in enumerate(buf):
        ret += b * (1 << (i * 8))
    return ret

def parse_little_endian_signed_negative(buf):
    ret = 0
    for i, b in enumerate(buf):
        ret += (b ^ 0xFF) * (1 << (i * 8))

    return (ret + 1) * -1

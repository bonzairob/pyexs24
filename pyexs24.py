import struct
# PORTED FROM https://github.com/matt-allan/renoise-exs24/blob/master/exs24.lua


DEBUG = True


def byte_str_to_int(byte_str):
    return int( str(byte_str).encode('hex'), 16 )

def int_to_byte_str(anint):
    return struct.pack(">I", anint)




# binary things

def twos_complement(value, bits):
    # if sign bit is set (128 - 255 for 8 bit)
    if (value & (1 << (bits - 1))) != 0:
        return value - (1 << bits)
    # end
    return value
# end


def read_dword(fh, big_endian):
    read_bytes = fh.read(4)
    if (not read_bytes or len(read_bytes) < 4):
        return None
    else:
        dword = (
            byte_str_to_int(read_bytes[0])
            | (byte_str_to_int(read_bytes[1]) << 8)
            | (byte_str_to_int(read_bytes[2]) << 16)
            | (byte_str_to_int(read_bytes[3]) << 24)
        )
        if big_endian:
            byte_str_to_int(int_to_byte_str(dword)[::-1])
        # end
        return dword
    # end
# end





# custom things

def zero_rtrim(string):
    return str.rstrip(string, chr(0x00))


def dprint(*args):
    if DEBUG:
        print args




# main things

def load_exs(path):
    fh = open(path, "rb")
    if fh == None:
        return False
    # end

    fh.seek(16)
    magic = fh.read(4)

    if magic != "SOBT" and magic != "SOBJ" and magic != "TBOS" and magic != "JBOS":
        return False
    # end

    dprint("Magic", magic)



    big_endian = False
    if magic == "SOBT" or magic == "SOBJ":
        big_endian = True
    # end

    is_size_expanded = False
    fh.seek(4)
    header_size = read_dword(fh, big_endian)
    if header_size > 0x8000:
        is_size_expanded = True
    # end

    dprint("is_size_expanded", is_size_expanded)


    exs = {'zones' : [], 'samples' : []}
    i = 0
    fh.seek(0,2) #go to the end of the file - 0=start, 1=relative, 2=end
    data_size = fh.tell()

    dprint('size', data_size)


    while (i + 84 < data_size):
        dprint('WHILE...')

        fh.seek(i)
        sig = read_dword(fh, big_endian)
        dprint("sig", sig, hex(sig))

        fh.seek(i + 4)
        size = read_dword(fh, big_endian)
        dprint("size", size, hex(size))

        fh.seek(i + 16)
        magic = fh.read(4)
        dprint("magic", magic)

        if is_size_expanded and size > 0x8000:
            size = size - 0x8000
        # end

        dprint('size', size, hex(size))

        # chunk_type = bit.rshift(bit.band(sig, 0x0F000000), 24)
        dprint('(sig & 0x0F000000)', hex(sig & 0x0F000000))

        chunk_type = (sig & 0x0F000000) >> 24

        dprint('chunk_type', hex(chunk_type))

        if chunk_type == 0x01:
            if size < 104:
                return False
            # end
            exs['zones'].append( create_zone(fh, i, size + 84, big_endian) )
        elif chunk_type == 0x03:
            if size != 336 and size != 592:
                return False
            # end
            exs['samples'].append( create_sample(fh, i, size + 84, big_endian) )
        # end
        i = i + size + 84
    # end

    return exs
# end






def create_zone(fh, i, size, big_endian):
    dprint('create_zone')
    zone = {}

    fh.seek(i + 8)
    zone['id']  = read_dword(fh, big_endian)

    fh.seek(i + 20)
    zone['name'] = zero_rtrim(fh.read(64))

    fh.seek(i + 84)
    zone_opts = byte_str_to_int(fh.read(1))
    zone['pitch'] = (zone_opts & (1 << 1)) == 0
    zone['oneshot'] = (zone_opts & (1 << 0)) != 0
    zone['reverse'] = (zone_opts & (1 << 2)) != 0

    fh.seek(i + 85)
    zone['key'] = byte_str_to_int(fh.read(1))

    fh.seek(i + 86)
    zone['fine_tuning'] = twos_complement( byte_str_to_int(fh.read(1)), 8)

    fh.seek(i + 87)
    zone['pan'] = twos_complement( byte_str_to_int(fh.read(1)), 8)

    fh.seek(i + 88)
    zone['volume'] = twos_complement( byte_str_to_int(fh.read(1)), 8)
    fh.seek(i + 164)
    zone['coarse_tuning'] = twos_complement( byte_str_to_int(fh.read(1)), 8)

    fh.seek(i + 90)
    zone['key_low'] = byte_str_to_int(fh.read(1))

    fh.seek(i + 91)
    zone['key_high'] = byte_str_to_int(fh.read(1))

    zone['velocity_range_on'] = (zone_opts & (1 << 3)) != 0

    fh.seek(i + 93)
    zone['velocity_low'] = byte_str_to_int(fh.read(1))

    fh.seek(i + 94)
    zone['velocity_high'] = byte_str_to_int(fh.read(1))

    fh.seek(i + 96)
    zone['sample_start'] = read_dword(fh, big_endian)

    fh.seek(i + 100)
    zone['sample_end'] = read_dword(fh, big_endian)

    fh.seek(i + 104)
    zone['loop_start'] = read_dword(fh, big_endian)

    fh.seek(i + 108)
    zone['loop_end'] = read_dword(fh, big_endian)

    fh.seek(i + 112)
    zone['loop_crossfade'] = read_dword(fh, big_endian)

    fh.seek(i + 117)
    loop_opts = byte_str_to_int(fh.read(1))
    zone['loop_on'] = (loop_opts & (1 << 0)) != 0
    zone['loop_equal_power'] = (loop_opts & (1 << 1)) != 0

    if (zone_opts & (1 << 6)) == 0:
        zone['output'] = -1
    else:
        fh.seek(i + 166)
        zone['output'] = byte_str_to_int(fh.read(1))
    # end

    fh.seek(i + 172)
    zone['group_index'] = read_dword(fh, big_endian)

    fh.seek(i + 176)
    zone['sample_index'] = read_dword(fh, big_endian)

    zone['sample_fade'] = 0
    if size > 188:
        fh.seek(i + 188)
        zone['sample_fade'] = read_dword(fh, big_endian)
    # end

    zone['offset'] = 0
    if size > 192:
        fh.seek(i + 192)
        zone['offset'] = read_dword(fh, big_endian)
    # end
    return zone
# end

def create_sample(fh, i, size, big_endian):
    dprint('create_sample')
    sample = {}

    fh.seek(i + 8)
    sample['id']  = read_dword(fh, big_endian)

    fh.seek(i + 20)
    sample['name'] = zero_rtrim(fh.read(64))

    fh.seek(i + 88)
    sample['length'] = read_dword(fh, big_endian)

    fh.seek(i + 92)
    sample['sample_rate'] = read_dword(fh, big_endian)

    fh.seek(i + 96)
    sample['bit_depth'] = byte_str_to_int(fh.read(1))

    fh.seek(i + 112)
    sample['type'] = read_dword(fh, big_endian)

    fh.seek(i + 164)
    sample['file_path'] = zero_rtrim(fh.read(256))

    if size > 420:
        fh.seek(i + 420)
        sample['file_name'] = zero_rtrim(fh.read(256))
    else:
        fh.seek(i + 20)
        sample['file_name'] = zero_rtrim(fh.read(64))
    # end

    return sample
# end






if __name__ == '__main__':
    import sys
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint( load_exs( sys.argv[1] ) )
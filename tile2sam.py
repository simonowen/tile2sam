#!/usr/bin/env python
#
# https://github.com/simonowen/tile2sam
"""Extracts tiled SAM graphics data from an image file"""

import os
import re
import sys
import struct
import argparse
import operator
from PIL import Image     # requires Pillow ("python -m pip install pillow")

instr_timings = [
    # regex, bytes, tstates
    (r'ld\s+\w,\(hl\)', 1, 8),                          # ld r,(hl)
    (r'ld\s+\(hl\),[bcdehla]', 1, 8),                   # ld (hl),r
    (r'ld\s+\(hl\),.*', 2, 12),                         # ld (hl),n
    (r'ld\s+[bcdehla],[bcdehla]', 1, 4),                # ld r,r
    (r'ld\s+\w,[^(]+', 2, 8),                           # ld r,n
    (r'ld\s+sp,hl', 1, 8),                              # ld sp,hl
    (r'ld\s+\w\w,[^(]+', 3, 12),                        # ld rr,n
    (r'ld\s+\(.*?\),hl', 3, 20),                        # ld (nn),hl
    (r'ld\s+\(.*?\),(bc|de|sp)', 4, 24),                # ld (nn),rr
    (r'(add|adc|sbc)\s+hl,\w\w', 1, 8),                 # add|adc|sbc hl,rr
    (r'(add|adc|sbc)\s+a,[bcdehla]', 1, 4),             # add|adc|sbc a,r
    (r'(add|adc|sbc)\s+a,.*', 2, 8),                    # add|adc|sbc a,n
    (r'(inc|dec|and|or|xor|sub)\s+[bcdehla]', 1, 4),    # inc|dec|and|or|xor r
    (r'(inc|dec|and|or|xor|sub)\s+.*', 2, 8),           # inc|dec|and|or|xor n
    (r'(inc|dec)\s+\w\w', 1, 8),                        # inc|dec rr
    (r'(ldi|ldd)', 2, 20),
    (r'(pop\s+\w\w)', 1, 12),
    (r'(push\s+\w\w)', 1, 16),
    (r'ex de,hl', 1, 4),
    (r'scf', 1, 4),
    (r'ret', 1, 12),
    (r'd(ef)?s\s+\d+', 0, 0),                           # ds/defs
    (r'@?\w+:', 0, 0),                                  # label
    (r'', 0, 0),
]

z80_routines = ['unmasked', 'masked', 'save', 'restore', 'clear', 'rect']

def bpp_from_mode(m):
    if m not in [1, 2, 3, 4]:
        sys.exit(f"error: invalid screen mode ({m}), must be 1-4")
    return [1, 1, 2, 4][m - 1]

def rgb_from_index(i):
    """Map SAM palette index to RGB tuple"""
    intensities = [0x00, 0x24, 0x49, 0x6d, 0x92, 0xb6, 0xdb, 0xff]
    red = intensities[(i & 0x02) | ((i & 0x20) >> 3) | ((i & 0x08) >> 3)]
    green = intensities[((i & 0x04) >> 1) | ((i & 0x40) >> 4) | ((i & 0x08) >> 3)]
    blue = intensities[((i & 0x01) << 1) | ((i & 0x10) >> 2) | ((i & 0x08) >> 3)]
    return (red, green, blue)

def generate_sam_palette():
    """Create a list of RGB values for the SAM palette of 128 colours"""
    palette = [rgb_from_index(i) for i in range(128)]
    return palette

def colour_distance_squared(colour1, colour2):
    """Square of the Euclidian distance between two colours"""
    dist_squared = sum((a - b) ** 2 for a, b in zip(colour1, colour2))
    return dist_squared

def closest_palette_index(colour, palette):
    """Return the palette index that best matches the supplied RGB colour"""
    dists_squared = {colour_distance_squared(colour, c) : c for c in palette}
    closest_index = dists_squared[min(dists_squared)]
    idx = [i for i, c in enumerate(palette) if c == closest_index][0]
    return idx

def palettise_image(img, palette):
    """Map image to nearest colours in a given palette"""
    img_palette = img.getcolors()
    if img_palette is None:
        sys.exit("error: source image has too many colours!")
    col_map = {x[1] : closest_palette_index(x[1], palette) for x in img_palette}

    img_pal = Image.new('P', img.size)
    img_pal.putpalette([c for tup in palette for c in tup])
    pal_pixels = img_pal.load()
    pixels = img.load()

    # PIL Image.quantize always dithers, so convert manually.
    width, height = img.size
    for x in range(width):
        for y in range(height):
            pal_pixels[x, y] = col_map[pixels[x, y]]

    return img_pal

def read_palette(pal):
    """Read palette from file, or as colour list"""
    try:
        with open(pal, 'rb') as f:
            return [c & 0x7f for c in bytearray(f.read())]
    except IOError:
        try:
            return [int(x, 0) & 0x7f for x in pal.split(',')]
        except ValueError:
            sys.exit("error: invalid colour list")

def clut_index(colour, clut):
    """Return the (first) CLUT index corresponding to the supplied colour"""
    matches = [i for i, c in enumerate(clut) if c == colour]
    return matches[0]

def clutise_image(img, clut):
    """Map palette colour indicies to colour look-up table indices"""
    col_map = {x[1] : clut_index(x[1], clut) for x in img.getcolors()}
    return img.point(lambda i: col_map.get(i, 0))

def crop_image(img, geometry):
    """Clip image to given geometry string"""
    try:
        crop = [int(x) for x in re.findall(r"\d+", geometry)]
        if len(crop) == 2:      # WxH
            img = img.crop(crop)
        elif len(crop) == 4:    # WxH+X+Y
            img = img.crop((crop[2], crop[3], crop[2]+crop[0], crop[3]+crop[1]))
        else:
            raise ValueError
        return img
    except (ValueError, IndexError):
        sys.exit("error: invalid crop region (should be WxH or WxH+X+H)")

def scale_image(img, scale):
    """Scale image by given factor(s)"""
    try:
        factors = [float(x) for x in re.findall(r"[\d.]+", scale)] * 2
        return img.resize([int(n * factors[i]) for i, n in enumerate(img.size)], Image.NEAREST)
    except (ValueError, IndexError):
        sys.exit("error: invalid scale factors")

def get_tile_size(size):
    """Return width and height given a 1D or 2D size"""
    try:
        dimensions = [int(x, 0) for x in re.findall(r"\d+", size)] * 2
        return dimensions[:2]
    except (ValueError, IndexError):
        sys.exit("error: invalid tile dimensions")

def get_tile_selection(tile_select, max_tiles):
    """Determine the tile selection to extract"""
    if tile_select is None:
        return [(0, max_tiles - 1)]

    try:
        if int(tile_select) > 0:
            return [(0, min(int(tile_select, 0), max_tiles) - 1)]
    except ValueError:
        try:
            # Convert list of N and N-M selections to pairs of N-M ranges.
            range_items = [x.strip() for x in tile_select.split(',')]
            ranges = [[int(x, 0) for x in r.split('-')] for r in range_items]
            selection = [x * 2 if len(x) == 1 else x[:2] for x in ranges]
        except (ValueError, IndexError):
            sys.exit("error: invalid tile count or range")
    return selection

def group_split(items, group_size):
    """Split a list into groups of a given size"""
    it = iter(items)
    return list(zip(*[it] * group_size))

def image_data_bytes(img_data, bpp=4):
    """Convert CLUT entries to SAM display byte rows"""
    byte_groups = group_split(img_data, 8 // bpp)
    data_bytes = [sum([n << (bpp * i)
                    for i,n in enumerate(reversed(t))]) for t in byte_groups]

    mask_value = (1 << bpp) - 1
    mask_bytes = [sum([(mask_value if n else 0) << (bpp * i)
                    for i,n in enumerate(reversed(t))]) for t in byte_groups]

    return data_bytes, mask_bytes

###############################################################################
# Code Generation Helpers

def nominal_timing(instrs):
    instrs = [instr.strip() for instr in instrs]
    unknown = [instr for instr in instrs if not [regex for regex,_,_ in instr_timings if re.fullmatch(regex, instr)]]
    if unknown:
        sys.exit(f'error: no timings for instruction(s): {unknown}')
    #debug = { instr:[tstates for regex,size,tstates in instr_timings if re.fullmatch(regex, instr)][0] for instr in instrs }

    return sum([next(tstates
        for regex,size,tstates in instr_timings if re.fullmatch(regex, instr))
            for instr in instrs])

def fastest_code(*code):
    return min(*code, key=lambda x: sum(nominal_timing(z) for z in x))

def format_code(label, code):
    indent = ' ' * 8
    text = f'{label}:\n' if label else ''
    text += indent + f'\n{indent}'.join(code) + '\n\n'
    return re.sub(r'^\s+(@?\w+:)', r'\1', text, flags=re.MULTILINE)

class ValueStream:
    def __init__(self, data, *, regs):
        self.data = data
        self.regs = regs
        self.cache = {}
        self.index = 0

        self.values, self.changes = self.get_values(self.data)

    def next_value(self, code):
        if self.index in self.changes:
            code += self.changes[self.index][1]

        val = self.values[self.index]
        self.index += 1
        return val

    def spare_pair(self):
        free = ''.join([r for r in self.regs if r not in self.values[self.index:]])
        rr = 'bc' if 'bc' in free else 'de'
        return rr if rr in free else None

    def get_cacheable(self, data):
        mru = []
        count = {}
        first = {}
        last = {}
        cacheable = []

        for i,b in enumerate(data):
            count[b] = count.get(b, 0) + 1
            first[b] = first.get(b, i)
            last[b] = i

            if b in mru:
                mru.remove(b)
            mru.append(b)

            candidates = [x for x in mru if count[x] >= 2]

            if len(candidates) >= len(self.regs):
                b0 = candidates[0]
                idx = mru.index(b0)

                if len(candidates) > len(self.regs):
                    if count[b0] >= 2:
                        cacheable.append((b0, first[b0], last[b0]))
                    idx += 1

                for i in range(idx):
                    del count[mru[i]]
                    del first[mru[i]]
                mru = mru[idx:]

        cacheable += [(x, first[x], last[x]) for x in mru if count[x] >= 2]
        return cacheable

    def get_values(self, data):
        values = []
        changes = {}
        cache = {}

        cacheable = self.get_cacheable(data)

        for i,b in enumerate(data):
            if data[i] not in cache:
                scoped = [(val, first - i) for val, first, last in cacheable if i <= last]
                pending = [x[0] for x in sorted(scoped, key=lambda kv: kv[1])][:len(self.regs)]

                if data[i] in pending:
                    cache = { k: v for k, v in cache.items() if k in pending }
                    adding = [x for x in pending if x not in cache]
                    free = ''.join([r for r in self.regs if r not in cache.values()])

                    code = []
                    while adding:
                        r = 'bc' if 'bc' in free else 'de'
                        if r in free and len(adding) >= 2:
                            code.append(f'ld {r},&{adding[0]:02x}{adding[1]:02x}')
                        else:
                            r = free[0]
                            code.append(f'ld {r},&{adding[0]:02x}')

                        cache.update({ adding[idx]: r[idx] for idx in range(len(r)) })
                        adding = adding[len(r):]
                        free = free.replace(r, '')

                    if code:
                        changes[i] = (cache, code)

            values.append(cache.get(b, f'&{b:02x}'))

        return values, changes

def reg8_delta(a, b):
    """Determine 8-bit difference, allowing wrap-around"""
    delta = b - a if b > a else 256 + b - a
    return delta - 256 if delta > 127 else delta

def reg8_change(a, b, *, reg, value_stream=None):
    """Change an 8-bit register from a to b"""
    delta = reg8_delta(a, b)
    dist = abs(delta)
    code = []
    values = []

    if dist <= 4:
        instr = f'inc {reg}' if delta > 0 else f'dec {reg}'
        code += [instr] * dist
    else:
        val = value_stream.next_value(code) if value_stream else dist
        values.append(val)

        code.append(f'ld a,{reg}')
        code.append(f'add a,{val}' if delta > 0 else f'sub {val}')
        code.append(f'ld {reg},a')

    return code, values

def reg16_change(a, b, *, reg='hl', spare_pair=None, value_stream=None):
    """Change register pair from a to b"""
    code = []
    values = []
    carry = ((a ^ b) & 0x80) != 0

    if not carry:
        al, ah, = a & 0xff, a >> 8
        bl, bh = b & 0xff, b >> 8

        low = reg8_change(al, bl, reg=reg[1], value_stream=value_stream)
        high = reg8_change(ah, bh, reg=reg[0], value_stream=value_stream)
        code, values = map(operator.add, low, high)
    elif a != b:
        delta = b - a

        if spare_pair:
            code = [f'ld {spare_pair},{delta}', f'add hl,{spare_pair}']
        else:
            dist = abs(delta)

            val = value_stream.next_value(code) if value_stream else dist & 0xff
            values.append(val)

            code.append(f'ld a,{reg[1]}')
            code.append(f'add a,{val}' if delta > 0 else f'sub {val}')
            code.append(f'ld {reg[1]},a')

            if delta > 0 and delta < 256:
                code += [f'adc a,{reg[0]}', f'sub {reg[1]}', f'ld {reg[0]},a']
            else:
                val = value_stream.next_value(code) if value_stream else dist >> 8
                values.append(val)

                code.append(f'ld a,{reg[0]}')
                code.append(f'adc a,{val}' if delta > 0 else f'sbc a,{val}')
                code.append(f'ld {reg[0]},a')

    return code, values

###############################################################################
# Routine Generators

def generate_draw_poke(image_data, mask_data, width_bytes, height, *, masked=True):
    """Generate drawing code that pokes data into memory"""
    spare_pair = None

    # 2 outer passes to determine if a register pair is spare
    for _ in range(2):
        image_addrs = []
        mask_addrs = []
        values = []
        last_addr = 0
        dx = 1

        # Even lines down, odd lines up, in zig-zag pattern
        for p in range(2):
            for y in range(0, height, 2) if p == 0 else reversed(range(1, height, 2)):
                for x in range(width_bytes) if dx > 0 else reversed(range(width_bytes)):
                    idx_data = y * width_bytes + x
                    if mask_data[idx_data]:
                        addr = y * 128 + x
                        values += reg16_change(last_addr, addr, spare_pair=spare_pair)[1]

                        if masked and mask_data[idx_data] and mask_data[idx_data] != 0xff:
                            values.append(~mask_data[idx_data] & 0xff)
                            mask_addrs.append(addr)

                        values.append(image_data[idx_data])
                        image_addrs.append(addr)

                        last_addr = addr

                dx = -dx

        stream = ValueStream(values, regs='bcde')
        spare_pair = stream.spare_pair()

    code = []
    last_addr = 0

    for addr in image_addrs:
        code += reg16_change(last_addr, addr, spare_pair=spare_pair, value_stream=stream)[0]

        val = stream.next_value(code)

        if addr in mask_addrs:
            code.append('ld a,(hl)')
            code.append(f'and {val}')

            val = stream.next_value(code)

            code.append(f'or {val}')
            code.append('ld (hl),a')
        else:
            code.append(f'ld (hl),{val}')

        last_addr = addr

    code.append('ret')
    return code

def generate_save_restore_ldi(mask_data, width_bytes, height):
    """Generate save/restore code that uses LDI"""
    image_addrs = []

    # Even lines down, odd lines up, all left-to-right
    for p in range(2):
        for y in range(0, height, 2) if p == 0 else reversed(range(1, height, 2)):
            for x in range (width_bytes):
                if mask_data[y * width_bytes + x]:
                    addr = y * 128 + x
                    image_addrs.append(addr)

    last_addr = 0
    save_code = []
    restore_code = ['ex de,hl']

    for addr in image_addrs:
        save_code += reg16_change(last_addr, addr, spare_pair='bc')[0]
        save_code.append('ldi')

        restore_code += reg16_change(last_addr, addr, reg='de')[0]
        restore_code.append('ldi')

        last_addr = addr + 1

    save_code += ['ret']
    restore_code.append('ret')

    return save_code, restore_code

def generate_save_restore_mem_stack(mask_data, width_bytes, height):
    """Generate save/restore code that uses both memory access and stack"""
    mask_addrs = []
    stack_space = 0
    dx = 1

    # Even lines down, odd lines up, in zig-zag pattern
    for p in range(2):
        for y in range(0, height, 2) if p == 0 else reversed(range(1, height, 2)):
            for x in range(width_bytes) if dx > 0 else reversed(range(width_bytes)):
                idx_data = y * width_bytes + x
                if mask_data[idx_data]:
                    addr = y * 128 + x
                    mask_addrs.append(addr)
                    stack_space += 1

            dx = -dx

    last_addr = 0
    first_byte = True
    save_code = ['ld (@+sp_restore+1),sp', 'ex de,hl', f'ld bc,{(stack_space + 1) & ~1}', 'add hl,bc', 'ld sp,hl', 'ex de,hl']

    for addr in mask_addrs:
        save_code += reg16_change(last_addr, addr, spare_pair='bc')[0]

        if first_byte:
            save_code.append('ld e,(hl)')
        else:
            save_code += ['ld d,(hl)', 'push de']

        last_addr = addr
        first_byte = not first_byte

    if not first_byte:
        save_code.append('push de')

    save_code += ['@sp_restore:', 'ld sp,0', 'ret']
    restore_code = ['ld (@+sp_restore+1),sp', 'ex de,hl', 'ld sp,hl', 'ex de,hl']

    last_addr = 0
    first_byte = (stack_space & 1) == 0

    if not first_byte:
        restore_code.append('pop de')

    for addr in reversed(mask_addrs):
        restore_code += reg16_change(last_addr, addr, spare_pair='bc')[0]

        if first_byte:
            restore_code += ['pop de', 'ld (hl),d']
        else:
            restore_code.append('ld (hl),e')

        last_addr = addr
        first_byte = not first_byte

    restore_code += ['@sp_restore:', 'ld sp,0', 'ret']

    return save_code, restore_code

def generate_clear_push(mask_data, width_bytes, height):
    """Generate display clear code that (mostly) uses the stack"""
    line_ends = []
    last_addr = 0

    line_data = group_split(mask_data, width_bytes)

    for p in range(2):
        for y in range(0, height, 2) if p == 0 else reversed(range(1, height, 2)):
            start = next((i for i, m in enumerate(line_data[y]) if m), None)
            if start != None:
                end = next((i for i, m in reversed(list(enumerate(line_data[y]))) if m)) + 1
                end_addr = y * 128 + end

                line_ends.append((end_addr, end - start))

    code = ['ld (@+sp_restore+1),sp', 'ld de,0']
    for end_addr, fill_len in line_ends:
        odd = fill_len & 1
        code += reg16_change(last_addr, end_addr - odd, reg='hl', spare_pair='bc')[0]
        last_addr = end_addr - odd

        if odd:
            code.append('ld (hl),e')

        if fill_len > 1:
            code.append('ld sp,hl')
            code += ['push de'] * (fill_len // 2)

    code += ['@sp_restore:', 'ld sp,0', 'ret']
    return code

def generate_clear_rect_push(width_bytes, height):
    """Generate rect clearing code for the given size"""
    line_ends = []
    last_addr = 0

    for p in range(2):
        for y in range(0, height, 2) if p == 0 else reversed(range(1, height, 2)):
            end_addr = y * 128 + width_bytes
            line_ends.append(end_addr)

    code = ['ld (@+sp_restore+1),sp', 'ld de,0']
    for end_addr in line_ends:
        odd = width_bytes & 1
        code += reg16_change(last_addr, end_addr - odd, reg='hl', spare_pair='bc')[0]
        last_addr = end_addr - odd

        if odd:
            code.append('ld (hl),e')

        if width_bytes > 1:
            code.append('ld sp,hl')
            code += ['push de'] * (width_bytes // 2)

    code += ['@sp_restore:', 'ld sp,0', 'ret']
    return code

###############################################################################
# Tile Converters

def tile_to_code(args, img_tile, idx_tile):
    """Generate code routines for the given tile image"""
    if args.mode != 4:
        sys.exit("error: code generation requires mode 4")
    elif args.shift:
        sys.exit("error: code generation doesn't support non-zero shifts")

    names = [x.strip() for x in args.names.split(',')] if args.names else []
    name = names[idx_tile] if idx_tile < len(names) else f'sprite{idx_tile}'

    shifted = args.shift != 0
    width_bytes = (img_tile.width + 1) // 2
    width, height = width_bytes * 2, img_tile.height

    img0 = Image.new(img_tile.mode, (width, height))
    img1 = Image.new(img_tile.mode, (width, height))
    img0.paste(img_tile, (0, 0))
    img1.paste(img_tile, (1, 0))

    image_data0, mask_data0 = image_data_bytes(img0.getdata())
    image_data1, mask_data1 = image_data_bytes(img1.getdata())
    mask_data = list(map(operator.or_, mask_data0, mask_data1)) if shifted else mask_data0
    no_image_data = [0] * len(mask_data)
    full_mask_data = [0xff] * len(mask_data)

    masked_code0 = generate_draw_poke(image_data0, mask_data0, width_bytes, height)
    masked_code1 = generate_draw_poke(image_data1, mask_data1, width_bytes, height)
    unmasked_code0 = generate_draw_poke(image_data0, mask_data0, width_bytes, height, masked=False)
    unmasked_code1 = generate_draw_poke(image_data1, mask_data1, width_bytes, height, masked=False)
    save_restore_mem_stack_code = generate_save_restore_mem_stack(mask_data, width_bytes, height)
    save_restore_ldi_code = generate_save_restore_ldi(mask_data, width_bytes, height)
    clear_poke_code = generate_draw_poke([0] * len(mask_data), mask_data, width_bytes, height, masked=False)
    clear_push_code = generate_clear_push(mask_data, width_bytes, height)
    rect_poke_code = generate_draw_poke(no_image_data, full_mask_data, width_bytes, height, masked=False)
    rect_push_code = generate_clear_rect_push(width_bytes, height)

    if not args.quiet:
        print(f"Code timings for '{name}':")
        print(f" masked draw even/odd = {nominal_timing(masked_code0)}T / {nominal_timing(masked_code1)}T")
        print(f" unmasked draw even/odd = {nominal_timing(unmasked_code0)}T / {nominal_timing(unmasked_code1)}T")
        print(f" save/restore (mem+stack) = {nominal_timing(save_restore_mem_stack_code[0])}T / {nominal_timing(save_restore_mem_stack_code[1])}T")
        print(f" save/restore (ldi) = {nominal_timing(save_restore_ldi_code[0])}T / {nominal_timing(save_restore_ldi_code[1])}T")
        print(f" clear (poke) = {nominal_timing(clear_poke_code)}T")
        print(f" clear (push) = {nominal_timing(clear_push_code)}T")
        print(f" clear rect (poke) = {nominal_timing(rect_poke_code)}T")
        print(f" clear rect (push) = {nominal_timing(rect_push_code)}T")

    code = "; tile2sam.py generated code\n\n"
    coord_code = ['srl h', 'rr l'] if args.low else ['scf', 'rr h', 'rr l']

    routines = [x.strip() for x in args.code.split(',')]
    invalid = [x for x in routines if x not in z80_routines]
    if invalid:
        sys.exit(f"invalid routine(s): {invalid}\nvalid routines: {','.join(z80_routines)}")

    if 'masked' in routines:
        label = f'masked_{name}'
        if not shifted:
            code += format_code(label, masked_code0)
        else:
            code += format_code(label, coord_code + [f'jp c,{label}1'])
            code += format_code(f'{label}0', masked_code0)
            code += format_code(f'{label}1', masked_code1)

    if 'unmasked' in routines:
        label = f'unmasked_{name}'
        if not shifted:
            code += format_code(label, unmasked_code0)
        else:
            code += format_code(label, coord_code + [f'jp c,{label}1'])
            code += format_code(f'{label}0', unmasked_code0)
            code += format_code(f'{label}1', unmasked_code1)

    if 'save' in routines or 'restore' in routines:
        save_code, restore_code = fastest_code(save_restore_mem_stack_code, save_restore_ldi_code)
        code += format_code(f'save_{name}', coord_code + save_code)
        code += format_code(f'restore_{name}', coord_code + restore_code)

    if 'clear' in routines:
        clear_code = coord_code + fastest_code([clear_poke_code], [clear_push_code])[0]
        code += format_code(f'clear_{name}', clear_code)

    if 'rect' in routines:
        rect_code = coord_code + fastest_code([rect_poke_code], [rect_push_code])[0]
        code += format_code(f'clear_rect_{width_bytes}x{height}', rect_code)

    return code

def tile_to_data(args, img_tile):
    """Convert colour indices to display and mask byte data"""
    bits_per_pixel = bpp_from_mode(args.mode)
    pixels_per_byte = 8 // bits_per_pixel

    pad_left = args.shift or 0
    pad_right = (-(pad_left + img_tile.width) % pixels_per_byte)

    sprite_width = pad_left + img_tile.width + pad_right
    img_sprite = Image.new(img_tile.mode, (sprite_width, img_tile.height))
    img_sprite.paste(img_tile, (pad_left, 0))

    return image_data_bytes(img_sprite.getdata(), bits_per_pixel)[0]

def main(args):
    """Main Program"""

    if args.mode not in [1, 2, 3, 4]:
        sys.exit(f"error: invalid screen mode ({args.mode}), must be 1-4")

    tile_width, tile_height = get_tile_size(args.tilesize)

    try:
        img = Image.open(args.image).convert("RGB")
    except IOError as err:
        sys.exit(err)

    if not args.quiet:
        print(f"Source image {args.image} is {img.size[0]}x{img.size[1]}")

    if args.crop:
        img = crop_image(img, args.crop)
        if not args.quiet:
            print(f"Cropped image to {img.size[0]}x{img.size[1]}")

    if args.scale:
        img = scale_image(img, args.scale)
        if not args.quiet:
            print(f"Scaled image to {img.size[0]}x{img.size[1]}")

    tiles_x = img.width // tile_width
    tiles_y = img.height // tile_height
    tile_select = get_tile_selection(args.tiles, tiles_x * tiles_y)
    img.crop((0, 0, tiles_x * tile_width, tiles_y * tile_height))

    if not tiles_x or not tiles_y:
        sys.exit(f"error: no tiles found for size {tile_width}x{tile_height}")
    elif not args.quiet:
        print(f"Contains {tiles_x}x{tiles_y} grid of {tile_width}x{tile_height} tiles")

    sam_palette = generate_sam_palette()
    img_pal = palettise_image(img, sam_palette)

    bits_per_pixel = bpp_from_mode(args.mode)

    palette = sorted([c[1] for c in img_pal.getcolors()])
    if len(palette) > (1 << bits_per_pixel):
        print(palette)
        sys.exit(f"error: too many colours ({len(palette)}) for screen mode {args.mode}")

    if args.clut is None:
        clut = palette
    else:
        clut = read_palette(args.clut)
        clut += list(set(palette).difference(set(clut)))

    if len(clut) > (1 << bits_per_pixel):
        sys.exit(f"error: clut has too many entries ({len(clut)}) for mode {args.mode}")

    img_clut = clutise_image(img_pal, clut)

    gfx_data, index_data = [], []
    code_text = ''
    num_tiles = 0

    for start, end in tile_select:
        step = +1 if start <= end else -1
        for idx_tile in range(start, end + step, step):
            x = (idx_tile % tiles_x) * tile_width
            y = (idx_tile // tiles_x) * tile_height

            img_tile = img_clut.crop((x, y, x + tile_width, y + tile_height))
            if img_tile.width == 0:
                continue

            if args.code:
                code_text += tile_to_code(args, img_tile, idx_tile)
            else:
                index_data.append(len(gfx_data))
                gfx_data += tile_to_data(args, img_tile)

            num_tiles += 1

    basename = os.path.splitext(args.output or args.image)[0]

    if gfx_data:
        with open(args.output or f"{basename}.bin", 'ab+' if args.append else 'wb') as f:
            f.write(bytearray(gfx_data))

        if not args.quiet:
            print(f"{num_tiles} tile(s) of size {tile_width}x{tile_height} "
                f"for mode {args.mode} = {len(gfx_data)} bytes")

    if code_text:
        with open(args.output or f"{basename}.asm", 'a+' if args.append else 'w') as f:
            f.write(code_text)

    if args.pal:
        with open(f"{basename}.pal", 'wb') as f:
            f.write(bytearray(clut))

    if args.index and index_data:
        with open(f"{basename}.idx", 'wb') as f:
            f.write(bytearray(struct.pack(f">{len(index_data)}H", *index_data)))

    if not args.quiet:
        print(f"{len(clut)} colours: {clut}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert SAM graphics images to code or data files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m', '--mode', default=4, type=int, help="output data screen mode (1-4)")
    parser.add_argument('-c', '--clut', help="custom colour file or list")
    parser.add_argument('-o', '--output', help="custom output filename")
    parser.add_argument('-a', '--append', default=False, action='store_true', help="append to existing output file")
    parser.add_argument('-p', '--pal', default=False, action='store_true', help="write clut to .pal file")
    parser.add_argument('-i', '--index', default=False, action='store_true', help="write offsets index to .idx")
    parser.add_argument('-t', '--tiles', help="tile count or list of ranges (N-M)")
    parser.add_argument('-z', '--code', help="Z80 code to generate")
    parser.add_argument('-n', '--names', help="Names for sprite labels")
    parser.add_argument('-0', '--low', default=False, action='store_true', help="screen at 0 instead of 0x8000")
    parser.add_argument('-q', '--quiet', default=False, action='store_true', help="quiet mode")
    parser.add_argument('--crop', help="crop region (WxH or WxH+X+Y)")
    parser.add_argument('--scale', help="scale region (S or HxV)")
    parser.add_argument('--shift', default=None, type=int, help="pixels to shift right")
    parser.add_argument('image')
    parser.add_argument('tilesize')
    main(parser.parse_args())

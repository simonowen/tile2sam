#!/usr/bin/env python
#
# https://github.com/simonowen/tile2sam
"""Extracts tiled SAM graphics data from an image file"""

import os
import re
import sys
import struct
import argparse
from PIL import Image     # requires Pillow ("pip install pillow")

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
        return img.resize([int(n * factors[i]) for i, n in enumerate(img.size)])
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
    """Detetermine the tile selection to extract"""
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

def main(args):
    """Main Program"""

    if args.mode not in [1, 2, 3, 4]:
        sys.exit("error: invalid screen mode ({}), must be 1-4".format(args.mode))

    tile_width, tile_height = get_tile_size(args.tilesize)

    try:
        img = Image.open(args.image).convert("RGB")
    except IOError as err:
        sys.exit(err)

    if not args.quiet:
        print("Image {} is {}x{}".format(args.image, *img.size))

    if args.crop:
        img = crop_image(img, args.crop)
        if not args.quiet:
            print("Cropped image to {}x{}".format(*(img.size)))

    if args.scale:
        img = scale_image(img, args.scale)
        if not args.quiet:
            print("Scaled image to {}x{}".format(*(img.size)))

    tiles_x = img.width // tile_width
    tiles_y = img.height // tile_height
    tile_select = get_tile_selection(args.tiles, tiles_x * tiles_y)
    img.crop((0, 0, tiles_x * tile_width, tiles_y * tile_height))

    sam_palette = generate_sam_palette()
    img_pal = palettise_image(img, sam_palette)

    bits_per_pixel = [1, 1, 2, 4][args.mode - 1]
    pixels_per_byte = 8 // bits_per_pixel
    pad_pixels = args.shift + (-(tile_width + args.shift) % pixels_per_byte)

    palette = [c[1] for c in img_pal.getcolors()]
    if len(palette) > (1 << bits_per_pixel):
        sys.exit("error: too many colours ({}) for screen mode {}".format(len(palette), args.mode))

    # Default to the required colours, but allow the starting colours to be specified.
    if args.clut is None:
        clut = palette
    else:
        clut = read_palette(args.clut)
        clut += list(set(palette).difference(set(clut)))

    if len(clut) > (1 << bits_per_pixel):
        sys.exit("error: clut has too many entries ({}) for mode {}".format(len(clut), args.mode))

    img_clut = clutise_image(img_pal, clut)

    tile_data, tile_offsets = [], []
    num_tiles = 0
    for start, end in tile_select:
        step = +1 if start <= end else -1
        for index in range(start, end + step, step):
            x = (index % tiles_x) * tile_width
            y = (index // tiles_x) * tile_height
            img_tile = img_clut.crop((x, y, x + tile_width, y + tile_height))
            if img_tile.width == 0:
                continue

            # Split the data into pixels rows of the tile width.
            it_tile_data = iter(img_tile.getdata())
            pixel_rows = zip(*[it_tile_data] * tile_width)

            # Pad rows for shifting space, plus alignment to the next byte boundary.
            padded_rows = [x + (0, ) * pad_pixels for x in pixel_rows]

            # Shift the image data to the right if requested.
            if args.shift > 0:
                padded_rows = [x[-args.shift:] + x[:len(x) - args.shift] for x in padded_rows]

            # Flatten the list of rows and break into byte-sized groups of pixels.
            it_padded_pixels = iter([x for x in padded_rows for x in x])
            byte_pixels = zip(*[it_padded_pixels] * pixels_per_byte)

            # Combine the pixel groups in the correct order for the output data.
            data = [sum([value << (index * bits_per_pixel)
                    for index, value in enumerate(reversed(pix))])
                    for pix in byte_pixels]

            tile_offsets += (len(tile_data),)
            tile_data += data
            num_tiles += 1

    if args.output is None:
        basename = os.path.splitext(args.image)[0]
        output_file = basename + '.bin'
    else:
        output_file = args.output

    basename = os.path.splitext(output_file)[0]
    with open(output_file, 'wb') as f:
        f.write(bytearray(tile_data))

    if args.pal:
        with open(basename + '.pal', 'wb') as f:
            f.write(bytearray(clut))

    if args.index:
        with open(basename + '.idx', 'wb') as f:
            f.write(bytearray(struct.pack(">{}H".format(len(tile_offsets)), *tile_offsets)))

    if not args.quiet:
        print("{} colours: {}".format(len(clut), clut))
        print("{} tile(s) of size {}x{} for mode {} = {} bytes".format(
            num_tiles, tile_width + pad_pixels, tile_height, args.mode, len(tile_data)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extracts tiled SAM graphics data from an image file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m', '--mode', default=4, type=int, help="output data screen mode (1-4)")
    parser.add_argument('-c', '--clut', help="custom colour file or list")
    parser.add_argument('-o', '--output', help="custom output data file")
    parser.add_argument('-p', '--pal', default=False, action='store_true', help="write clut to .pal file")
    parser.add_argument('-i', '--index', default=False, action='store_true', help="write offsets index to .idx")
    parser.add_argument('-t', '--tiles', help="tile count or list of ranges (N-M)")
    parser.add_argument('-q', '--quiet', action='store_true', default=False, help="quiet mode")
    parser.add_argument('--crop', help="crop region (WxH or WxH+X+Y)")
    parser.add_argument('--scale', help="scale region (S or HxV)")
    parser.add_argument('--shift', default=0, type=int, help="pixels to shift right")
    parser.add_argument('image')
    parser.add_argument('tilesize')
    main(parser.parse_args())

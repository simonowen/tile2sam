.PHONY: clean

test:	all
	@echo Comparing results
	@cmp -s font.bin golden/font.bin >/dev/null || echo MISMATCH: font.bin
	@cmp -s font_right.bin golden/font_right.bin >/dev/null || echo MISMATCH: font_right.bin
	@cmp -s font_right.idx golden/font_right.idx >/dev/null || echo MISMATCH: font_right.idx
	@cmp -s sprites.bin golden/sprites.bin >/dev/null || echo MISMATCH: sprites.bin
	@cmp -s sprites.pal golden/sprites.pal >/dev/null || echo MISMATCH: sprites.pal
	@cmp -s sprites_rev.bin golden/sprites_rev.bin >/dev/null || echo MISMATCH: sprites_rev.bin
	@cmp -s sprites_rev.pal golden/sprites_rev.pal >/dev/null || echo MISMATCH: sprites_rev.pal
	@cmp -s sprites_shift.bin golden/sprites_shift.bin >/dev/null || echo MISMATCH: sprites_shift.bin
	@cmp -s sprites_mono.bin golden/sprites_mono.bin >/dev/null || echo MISMATCH: sprites_mono.bin
	@cmp -s tiles.bin golden/tiles.bin >/dev/null || echo MISMATCH: tiles.bin
	@cmp -s tiles.pal golden/sprites.pal >/dev/null || echo MISMATCH: tiles.pal
	@cmp -s tiles_mono.bin golden/tiles_mono.bin >/dev/null || echo MISMATCH: tiles_mono.bin
	@cmp -s mode2.bin golden/mode2.bin >/dev/null || echo MISMATCH: mode2.bin
	@cmp -s mode3.bin golden/mode3.bin >/dev/null || echo MISMATCH: mode3.bin
	@cmp -s mode4.bin golden/mode4.bin >/dev/null || echo MISMATCH: mode4.bin
	@cmp -s mode3.pal golden/mode3.pal >/dev/null || echo MISMATCH: mode3.pal
	@cmp -s mode4.pal golden/mode4.pal >/dev/null || echo MISMATCH: mode4.pal
	@echo Done.

all:	font.bin font_right.bin \
		sprites.bin sprites_rev.bin sprites_shift.bin sprites_mono.bin \
		tiles.bin tiles_mono.bin \
		mode2.dsk mode3.dsk mode4.dsk
	@echo Extracting tiles

font.bin:	font.png
	@../tile2sam.py -q --mode 2 font.png 6x8

font_right.bin:	font.png
	@../tile2sam.py -q --mode 1 --shift 2 --index -o font_right.bin font.png 6x8


sprites.bin:	sprites.png
	@../tile2sam.py -q --clut 0,127,34,123,85,106,110,96,6,68,29,25,99,122,126,119 --pal --tiles 102 sprites.png 12x12

sprites_rev.bin:	sprites.png
	@../tile2sam.py -q --pal --tiles 101-0 -o sprites_rev.bin sprites.png 12x12

sprites_shift.bin:	sprites.png
	@../tile2sam.py -q --clut sprites.pal --shift 1 --tiles 102 -o sprites_shift.bin sprites.png 12x12

sprites_mono.bin:	sprites_mono.png
	@../tile2sam.py -q --mode 1 --tiles 76 sprites_mono.png 12


tiles.bin:	tiles.png
	@../tile2sam.py -q --clut sprites.pal --pal --tiles 0-240,241,242-251 tiles.png 6

tiles_mono.bin:	tiles_mono.png
	@../tile2sam.py -q --mode 1 --tiles 192 tiles_mono.png 6


mode2.bin:	mode2.png
	@../tile2sam.py -q --crop 512x384+32+48 --scale 0.5x0.5 --mode 2 mode2.png 256x192

mode3.bin:	mode3.png
	@../tile2sam.py -q --crop 512x384+32+48 --scale 1.0x0.5 --mode 3 --pal mode3.png 512x192

mode4.bin:	mode4.png
	@../tile2sam.py -q --crop 512x384+32+48 --scale 0.5 --pal mode4.png 256x192


mode2.dsk:	mode2.bin
	@pyz80.py mode2.asm >/dev/null

mode3.dsk:	mode3.bin
	@pyz80.py mode3.asm >/dev/null

mode4.dsk:	mode4.bin
	@pyz80.py mode4.asm >/dev/null


clean:
	rm -f *.bin *.pal *.idx *.dsk *.map

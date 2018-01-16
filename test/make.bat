@echo off
if "%1"=="clean" goto clean

echo Extracting tiles
..\tile2sam.py -q --mode 2 font.png 6x8
..\tile2sam.py -q --mode 1 --shift 2 --index -o font_right.bin font.png 6x8
..\tile2sam.py -q --clut 0,127,34,123,85,106,110,96,6,68,29,25,99,122,126,119 --pal --tiles 102 sprites.png 12x12
..\tile2sam.py -q --pal --tiles 101-0 -o sprites_rev.bin sprites.png 12x12
..\tile2sam.py -q --clut sprites.pal --shift 1 --tiles 102 -o sprites_shift.bin sprites.png 12x12
..\tile2sam.py -q --mode 1 --tiles 76 sprites_mono.png 12
..\tile2sam.py -q --clut sprites.pal --pal --tiles 0-240,241,242-251 tiles.png 6
..\tile2sam.py -q --mode 1 --tiles 192 tiles_mono.png 6
..\tile2sam.py -q --crop 512x384+32+48 --scale 0.5x0.5 --mode 2 mode2.png 256x192
..\tile2sam.py -q --crop 512x384+32+48 --scale 1.0x0.5 --mode 3 --pal mode3.png 512x192
..\tile2sam.py -q --crop 512x384+32+48 --scale 0.5 --pal mode4.png 256x192
pyz80.py mode2.asm >nul
pyz80.py mode3.asm >nul
pyz80.py mode4.asm >nul

echo Comparing results
fc /b font.bin golden\font.bin >nul || echo MISMATCH: font.bin
fc /b font_right.bin golden\font_right.bin >nul || echo MISMATCH: font_right.bin
fc /b font_right.idx golden\font_right.idx >nul || echo MISMATCH: font_right.idx
fc /b sprites.bin golden\sprites.bin >nul || echo MISMATCH: sprites.bin
fc /b sprites.pal golden\sprites.pal >nul || echo MISMATCH: sprites.pal
fc /b sprites_rev.bin golden\sprites_rev.bin >nul || echo MISMATCH: sprites_rev.bin
fc /b sprites_rev.pal golden\sprites_rev.pal >nul || echo MISMATCH: sprites_rev.pal
fc /b sprites_shift.bin golden\sprites_shift.bin >nul || echo MISMATCH: sprites_shift.bin
fc /b sprites_mono.bin golden\sprites_mono.bin >nul || echo MISMATCH: sprites_mono.bin
fc /b tiles.bin golden\tiles.bin >nul || echo MISMATCH: tiles.bin
fc /b tiles.pal golden\sprites.pal >nul || echo MISMATCH: tiles.pal
fc /b tiles_mono.bin golden\tiles_mono.bin >nul || echo MISMATCH: tiles_mono.bin
fc /b mode2.bin golden\mode2.bin >nul || echo MISMATCH: mode2.bin
fc /b mode3.bin golden\mode3.bin >nul || echo MISMATCH: mode3.bin
fc /b mode4.bin golden\mode4.bin >nul || echo MISMATCH: mode4.bin
fc /b mode3.pal golden\mode3.pal >nul || echo MISMATCH: mode3.pal
fc /b mode4.pal golden\mode4.pal >nul || echo MISMATCH: mode4.pal

goto end

:clean
	del /q *.bin *.pal *.idx *.dsk 2>nul

:end
echo Done.

@echo off

setlocal
set NAME=demo1

if "%1"=="clean" goto clean

tile2sam -v sprite.png 11x11 --code masked,save,restore --names ghost --pal --low %*
if errorlevel 1 goto end
pyz80 -I samdos2 --mapfile=%NAME%.map %NAME%.asm
if errorlevel 1 goto end

goto end

:clean
del /q *.bin *.pal *.dsk %NAME%.map sprite.asm 2>nul

:end
endlocal

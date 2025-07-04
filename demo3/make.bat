@echo off

setlocal
set NAME=demo3

if "%1"=="clean" goto clean

..\tile2sam.py sprites.png 11x11 --code masked,copy --names cherry,strawb,orange,bell,apple,grapes,galax,key --pal --low %*
if errorlevel 1 goto end
pyz80.py -I samdos2 --mapfile=%NAME%.map %NAME%.asm
if errorlevel 1 goto end

goto end

:clean
del /q *.bin *.pal *.dsk *.map sprites.asm 2>nul

:end
endlocal

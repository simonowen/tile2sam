@echo off

setlocal
set NAME=demo2

if "%1"=="clean" goto clean

tile2sam sprites.png 11x11 --code masked,save,restore --names cherry,strawb,orange,bell,apple,grapes,galax,key --pal --bkgcol=60 %*
if errorlevel 1 goto end
pyz80 -I samdos2 --mapfile=%NAME%.map %NAME%.asm
if errorlevel 1 goto end

goto end

:clean
del /q *.bin *.pal *.dsk *.map sprites.asm 2>nul

:end
endlocal

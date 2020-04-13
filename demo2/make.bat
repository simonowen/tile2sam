@echo off

setlocal
set NAME=demo2

if "%1"=="clean" goto clean

..\tile2sam.py -q sprites.png 12x11 --code masked,save,restore --names cherry,strawb,orange,bell,apple,grapes,galax,key --pal
if errorlevel 1 goto end
pyz80.py -I samdos2 --mapfile=%NAME%.map %NAME%.asm
if errorlevel 1 goto end

goto end

:clean
del /q *.bin *.pal *.dsk *.map sprites.asm 2>nul

:end
endlocal

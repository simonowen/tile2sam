.PHONY: clean

NAME=demo2

${NAME}.dsk:    ${NAME}.asm sprites.asm
	@pyz80.py -I samdos2 --mapfile=${NAME}.map ${NAME}.asm

sprites.asm:	sprites.png
	@../tile2sam.py sprites.png 11x11 --code masked,save,restore --names cherry,strawb,orange,bell,apple,grapes,galax,key --pal --bkgcol=60

clean:
	rm -f ${NAME}.dsk ${NAME}.map sprites.pal sprites.asm

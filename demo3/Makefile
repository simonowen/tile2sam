.PHONY: clean

NAME=demo3

${NAME}.dsk:    ${NAME}.asm sprites.asm
	@pyz80.py -I samdos2 --mapfile=${NAME}.map ${NAME}.asm

sprites.asm:	sprites.png
	@../tile2sam.py sprites.png 11x11 --code masked,copy --names cherry,strawb,orange,bell,apple,grapes,galax,key --pal --low

clean:
	rm -f ${NAME}.dsk ${NAME}.map sprites.pal sprites.asm

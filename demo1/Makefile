.PHONY: clean

NAME=demo1

${NAME}.dsk:    ${NAME}.asm sprite.asm
	@pyz80.py -I samdos2 --mapfile=${NAME}.map ${NAME}.asm

sprite.asm:	sprite.png
	@../tile2sam.py sprite.png 11x11 --code masked,save,restore --names ghost --pal --low

clean:
	rm -f ${NAME}.dsk ${NAME}.map sprite.pal sprite.asm

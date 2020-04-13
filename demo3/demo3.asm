; Demo 3 - draw unmasked sprites with background clear

lmpr:   equ 250
hmpr:   equ 251
vmpr:   equ 252

rom0_off: equ %00100000
mode4:  equ %01100000

base:   equ &8000
interrupt: equ &0038
lastpos: equ &e000

        org 0
        dump base+$
        autoexec

        di
        ld  a,1+rom0_off
        out (lmpr),a
        ld  a,4+mode4
        out (vmpr),a
        ld  sp,base
        ld hl,palette_end-1
        ld c,&f8
        ld b,palette_end-palette
        otdr
        jp init

init:   call flip
        ei
        jr  $

        org interrupt
        dump base+$
        ld  c,sprite1-sprite0
        call flip
        call clear
        call move
        call draw
        ei
        ret

flip:   in  a,(vmpr)
        ld  b,a
        xor %00000010
        out (vmpr),a
        ld  a,b
        and %00011111
        out (hmpr),a
        ret

clear: ld  iy,lastpos
        ld  b,num_sprites
@loop:
        ld  a,(iy)
        add a,a
        add a,clear_funcs\256
        ld  l,a
        adc a,clear_funcs/256
        sub l
        ld h,a
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld  (@calladdr+1),hl
        ld  l,(iy+1)
        ld  h,(iy+2)
        push bc
        ld  b,0
        add iy,bc
@calladdr:
        call 0
        pop bc
        djnz @-loop
        ret

draw:   ld  iy,lastpos
        ld  ix,sprite0
        ld  hl,draw_funcs
        ld  b,num_sprites
@loop:
        ld  a,(ix)
        ld  (iy),a
        add a,a
        add a,draw_funcs\256
        ld  l,a
        adc a,draw_funcs/256
        sub l
        ld h,a
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld  (@calladdr+1),hl
        ld  l,(ix+1)
        ld  h,(ix+2)
        ld (iy+1),l
        ld (iy+2),h
        push bc
        ld  b,0
        add ix,bc
        add iy,bc
@calladdr:
        call 0
        pop bc
        djnz @-loop
        ret

move:   ld  ix,sprite0
        ld  b,num_sprites
        ld  e,c
        ld  d,0
@loop:  
        ld  a,(ix+1)
        add a,(ix+3)
        ld  (ix+1),a
        jr  z,revy
        cp  256-12-1
        jr  c,no_revy
revy:   
        ld  a,(ix+3)
        neg
        ld  (ix+3),a
no_revy:
        ld  a,(ix+2)
        add a,(ix+4)
        ld  (ix+2),a
        jr  z,revx
        cp  192-11-1
        jr  c,no_revx
revx:   
        ld  a,(ix+4)
        neg
        ld  (ix+4),a
no_revx:
        add ix,de
        djnz @-loop
        ret

sprite0:
        db 0, &38,&33, -1,1
sprite1:
        db 1, &5e,&73, 1,1
        db 2, &18,&9a, -1,1
        db 3, &71,&26, 1,-1
        db 4, &de,&0b, -1,-1
        db 5, &4a,&59, -1,1
        db 6, &21,&a3, -1,-1
        db 7, &e4,&6f, 1,-1
        db 0, &99,&24, 1,-1
        db 1, &4b,&39, 1,-1
        db 2, &3f,&88, 1,1
        db 3, &2b,&99, 1,-1
        db 4, &eb,&56, 1,-1
        db 5, &9f,&9d, 1,1
        db 6, &a5,&ac, -1,1
        db 7, &7d,&77, -1,-1
        db 0, &99,&76, 1,-1
        db 1, &1e,&62, 1,1
        db 2, &3d,&9c, -1,-1
        db 3, &9d,&27, 1,1
        db 4, &28,&a3, 1,-1
        db 5, &99,&83, -1,1
        db 6, &6d,&52, 1,-1
        db 7, &82,&7e, 1,1
        db 0, &2b,&89, -1,-1
        db 1, &2f,&3e, 1,1
        db 2, &b4,&34, -1,1
        db 3, &3d,&5f, -1,-1
        db 4, &6d,&2c, -1,1
        db 5, &3e,&09, 1,-1
        db 6, &70,&a2, -1,1
        db 7, &5d,&62, -1,1
        db 0, &52,&94, -1,-1
        db 1, &d1,&11, -1,-1
        db 2, &53,&9e, -1,1
        db 3, &47,&9a, 1,1
        db 4, &8f,&54, -1,-1
        db 5, &16,&46, 1,-1
        db 6, &5e,&ac, 1,-1
        db 7, &7a,&1c, 1,1
        db 0, &0c,&a5, 1,-1
        db 1, &c4,&59, -1,-1
        db 2, &c4,&1c, -1,-1
        db 3, &da,&05, -1,-1
        db 4, &85,&6e, 1,-1
        db 5, &91,&a2, -1,1
        db 6, &2d,&35, 1,-1
sprite_end:

num_sprites: equ (sprite_end-sprite0) / (sprite1-sprite0)

draw_funcs:
        dw unmasked_cherry
        dw unmasked_strawb
        dw unmasked_orange
        dw unmasked_bell
        dw unmasked_apple
        dw unmasked_grapes
        dw unmasked_galax
        dw unmasked_key

clear_funcs:
        dw clear_cherry
        dw clear_strawb
        dw clear_orange
        dw clear_bell
        dw clear_apple
        dw clear_grapes
        dw clear_galax
        dw clear_key

palette:
        MDAT "sprites.pal"
palette_end:

        INC "sprites.asm"

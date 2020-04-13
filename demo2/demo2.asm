; Demo 2 - draw masked sprites with background save/restore

lmpr:   equ 250
hmpr:   equ 251
vmpr:   equ 252

rom0_off: equ %00100000
mode4:  equ %01100000

base:   equ &8000
interrupt: equ &0038
lastpos: equ &e000
save_buffers: equ &f000

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
        call grid
        call flip
        call grid
        ei
        jr  $

        org interrupt
        dump base+$
        ld  c,sprite1-sprite0
        call flip
        call restore
        call move
        call save
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

grid:   ld  hl,&8000
        ld  c,&11
@loop:  ld  b,&80
@rloop: ld  (hl),c
        inc l
        jr  nz,@-rloop
        ld  a,h
        add a,4
        ld  h,a
        cp  &e0
        jr  c,@-loop

@loop:  ld  h,&80
@cloop: ld  (hl),c
        set 7,l
        ld  (hl),c
        res 7,l
        inc h
        ld  a,h
        cp  &e0
        jr  c,@-cloop
        ld  a,l
        add a,4
        ld  l,a
        jp  p,@-loop

        ld  hl,lastpos
        ld  de,sprite1-sprite0
        ld  c,&ff
        ld  b,num_sprites
@loop:  ld  (hl),c
        add hl,de
        djnz @-loop
        ret

save:   ld  ix,sprite0
        ld  iy,lastpos
        ld  b,num_sprites
        ld  de,save_buffers
@loop:
        push bc
        ld  a,(ix)
        ld  (iy),a
        inc a
        jr  z,no_save
        dec a
        add a,a
        add a,save_funcs\256
        ld  l,a
        adc a,save_funcs/256
        sub l
        ld h,a
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld  (@calladdr+1),hl
        ld  l,(ix+1)
        ld  h,(ix+2)
        ld  (iy+1),l
        ld  (iy+2),h
        push de
@calladdr:
        call 0
        pop de
no_save:
        ld  hl,6*11
        add hl,de
        ld  de,sprite1-sprite0
        add ix,de
        add iy,de
        ex  de,hl
        pop bc
        djnz @-loop
        ret

restore:
        ld  iy,lastpos
        ld  b,num_sprites
        ld  de,save_buffers
@loop:
        push bc
        ld  a,(iy)
        inc a
        jr  z,no_restore
        dec a
        add a,a
        add a,restore_funcs\256
        ld  l,a
        adc a,restore_funcs/256
        sub l
        ld h,a
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld  (@calladdr+1),hl
        ld  l,(iy+1)
        ld  h,(iy+2)
        push de
@calladdr:
        call 0
        pop de
no_restore:
        ld  hl,6*11
        add hl,de
        ld  de,sprite1-sprite0
        add iy,de
        ex  de,hl
        pop bc
        djnz @-loop
        ret

draw:   ld  ix,sprite0
        ld  hl,draw_funcs
        ld  b,num_sprites
@loop:
        push bc
        ld  a,(ix)
        inc a
        jr  z,no_draw
        dec a
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
@calladdr:
        call 0
no_draw:
        pop bc
        ld  de,sprite1-sprite0
        add ix,de
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
        db 0, &38,&32, -1,1
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
sprite_end:

num_sprites: equ (sprite_end-sprite0) / (sprite1-sprite0)

draw_funcs:
        dw masked_cherry
        dw masked_strawb
        dw masked_orange
        dw masked_bell
        dw masked_apple
        dw masked_grapes
        dw masked_galax
        dw masked_key

save_funcs:
        dw save_cherry
        dw save_strawb
        dw save_orange
        dw save_bell
        dw save_apple
        dw save_grapes
        dw save_galax
        dw save_key

restore_funcs:
        dw restore_cherry
        dw restore_strawb
        dw restore_orange
        dw restore_bell
        dw restore_apple
        dw restore_grapes
        dw restore_galax
        dw restore_key

palette:
        MDAT "sprites.pal"
palette_end:

        INC "sprites.asm"

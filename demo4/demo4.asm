; Demo 4 - draw many masked sprites, restoring from a pristine screen copy

status:       equ 249
lmpr:         equ 250
hmpr:         equ 251
vmpr:         equ 252

rom0_off:     equ %00100000
mode4:        equ %01100000
frameint:     equ %00001000

base:         equ &e000
lastpos:      equ &6000

sprite_width:  equ 12
sprite_height: equ 12

        org base
        dump $
        autoexec

        di
        ld   a,4+mode4
        out  (vmpr),a
        ld   sp,stack_end

        call flip
        call grid
        call flip
        call grid

        ld   hl,0
        ld   de,&8000
        ld   bc,&6000
        ldir

        ld   hl,palette_end-1
        ld   c,&f8
        ld   b,palette_end-palette
        otdr

loop:   call waitint

        ld   c,sprite1-sprite0
        call flip
        call restore
        call move
        call save
        call draw

        jr loop

waitint:in   a,(status)
        and  frameint
        jr   nz,waitint
waitend:in   a,(status)
        and  frameint
        jr   z,waitend
        ret

flip:   in   a,(vmpr)
        ld   b,a
        xor  %00000010
        out  (vmpr),a
        ld   a,b
        and  %00011111
        or   rom0_off
        out  (lmpr),a
        ret

grid:   ld   hl,&0000
        ld   c,&11
@loop:  ld   b,&80
@rloop: ld   (hl),c
        inc  l
        jr   nz,@-rloop
        ld   a,h
        add  a,4
        ld   h,a
        cp   &e0
        jr   c,@-loop

@loop:  ld   h,&00
@cloop: ld   (hl),c
        set  7,l
        ld   (hl),c
        res  7,l
        inc  h
        ld   a,h
        cp   &e0
        jr   c,@-cloop
        ld   a,l
        add  a,4
        ld   l,a
        jp   p,@-loop

        ld   hl,lastpos
        ld   de,sprite1-sprite0
        ld   c,&ff
        ld   b,num_sprites
@loop:  ld   (hl),c
        add  hl,de
        djnz @-loop
        ret

save:   ld   ix,sprite0
        ld   iy,lastpos
        ld   b,num_sprites
@loop:
        push bc
        ld   a,(ix)
        ld   (iy),a
        inc  a
        jr   z,no_save
        ld   l,(ix+1)
        ld   h,(ix+2)
        ld   (iy+1),l
        ld   (iy+2),h
no_save:
        ld   de,sprite1-sprite0
        add  ix,de
        add  iy,de
        pop  bc
        djnz @-loop
        ret

restore:
        ld   iy,lastpos
        ld   b,num_sprites
@loop:
        push bc
        ld   a,(iy)
        inc  a
        jr   z,no_restore
        dec  a
        add  a,a
        add  a,restore_funcs\256
        ld   l,a
        adc  a,restore_funcs/256
        sub  l
        ld   h,a
        ld   a,(hl)
        inc  hl
        ld   h,(hl)
        ld   l,a
        ld   (@calladdr+1),hl
        ld   l,(iy+1)
        ld   h,(iy+2)
@calladdr:
        call 0
no_restore:
        ld   de,sprite1-sprite0
        add  iy,de
        pop  bc
        djnz @-loop
        ret

draw:   ld   ix,sprite0
        ld   hl,draw_funcs
        ld   b,num_sprites
@loop:
        push bc
        ld   a,(ix)
        inc  a
        jr   z,no_draw
        dec  a
        add  a,a
        add  a,draw_funcs\256
        ld   l,a
        adc  a,draw_funcs/256
        sub  l
        ld   h,a
        ld   a,(hl)
        inc  hl
        ld   h,(hl)
        ld   l,a
        ld   (@calladdr+1),hl
        ld   l,(ix+1)
        ld   h,(ix+2)
@calladdr:
        call 0
no_draw:
        pop  bc
        ld   de,sprite1-sprite0
        add  ix,de
        djnz @-loop
        ret

move:   ld   ix,sprite0
        ld   b,num_sprites
        ld   e,c
        ld   d,0
@loop:  
        ld   a,(ix+1)
        add  a,(ix+3)
        ld   (ix+1),a
        jr   z,revx
        cp   256-sprite_width
        jr   c,no_revx
revx:
        ld   a,(ix+3)
        neg
        ld   (ix+3),a
        add  a,(ix+1)
        ld   (ix+1),a
no_revx:
        ld   a,(ix+2)
        add  a,(ix+4)
        ld   (ix+2),a
        jr   z,revy
        cp   192-sprite_height
        jr   c,no_revy
revy:
        ld   a,(ix+4)
        neg
        ld   (ix+4),a
        add  a,(ix+2)
        ld   (ix+2),a
no_revy:

        add  ix,de
        djnz @-loop
        ret

sprite0:
        db 0, &38,&33, -1,1
sprite1:
        db 1, &5e,&73, 1,1
        db 2, &18,&9a, -1,1
        db 3, &71,&26, 1,-1
        db 4, &7e,&0b, 1,-1
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
        db 0, &99,&76, -1,-1
        db 1, &1e,&62, 1,1
        db 2, &3d,&9c, -1,-1
        db 3, &9d,&27, 1,1
        db 4, &d8,&a3, -1,-1
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

restore_funcs:
        dw copy_cherry
        dw copy_strawb
        dw copy_orange
        dw copy_bell
        dw copy_apple
        dw copy_grapes
        dw copy_galax
        dw copy_key

palette:
        MDAT "sprites.pal"
palette_end:

        INC "sprites.asm"
sprites_end:

        defs 64
stack_end:

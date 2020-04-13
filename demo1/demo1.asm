; Demo 1 - single sprite save/draw/remove
lmpr: equ 250
vmpr: equ 252

coords0: equ &0103 ; @3,1

        org &8000
        dump $
        autoexec

        di
        call bkg_text

        ld  (oldsp+1),sp
        ld  sp,new_stack

        in  a,(lmpr)
        push af
        in  a,(vmpr)
        push af
        and %00011111
        or  %00100000
        out (lmpr),a

        ld  hl,palette_end-1
        ld  c,&f8
        ld  b,palette_end-palette
        otdr

        call delay

        ld  hl,coords0
        ld  de,sprite0_buf
        call save_ghost

        ld  hl,coords0
        call masked_ghost

        call delay

        ld  hl,coords0
        ld  de,sprite0_buf
        call restore_ghost

        call delay

        pop af
        out (vmpr),a
        pop af
        out (lmpr),a
oldsp:
        ld  sp,0
        ei
        ret

delay:  ld  b,5
@loop:  dec hl
        ld  a,h
        or  l
        jr  nz,@-loop
        djnz @-loop
        ret

bkg_text:
        ld  a,2         ; main screen
        call &0112      ; SETSTRM - set stream in A
        ld  hl,text
        ld  b,8
@loop:  ld  a,(hl)
        rst &10
        inc hl
        djnz @-loop
        ret

text:   defb 22,0,0,"1","2",13,"3","4"

palette:
        MDAT "sprite.pal"
palette_end:

        defs 32
new_stack:

sprite0_buf: defs 6*11
sprite1_buf: defs 6*11

        INC "sprite.asm"

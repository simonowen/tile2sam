vmpr:           equ &fc
vmpr_mode2:     equ %00100000
screen_page:    equ 2

                org &8000
                dump $
                autoexec

                di

                ld  a,vmpr_mode2+screen_page
                out (vmpr),a

                ld  hl,&4000*(screen_page+1)+&2000
                ld  bc,&1807
attr_loop:      ld  (hl),c
                inc l
                jr  nz,attr_loop
                inc h
                djnz attr_loop

                halt

                dump screen_page,0
                mdat "mode2.bin"

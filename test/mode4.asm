vmpr:           equ &fc
vmpr_mode4:     equ %01100000
screen_page:    equ 2

                org &8000
                dump $
                autoexec

                di

                ld  hl,palette_end-1
                ld  b,palette_end-palette
                ld  c,&f8
                otdr

                ld  a,vmpr_mode4+screen_page
                out (vmpr),a

                halt

palette:        mdat "mode4.pal"
palette_end:

                dump screen_page,0
                mdat "mode4.bin"

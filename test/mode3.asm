vmpr:           equ &fc
vmpr_mode3:     equ %01000000
screen_page:    equ 2

                org &8000
                dump $
                autoexec

                di

                ld  hl,palette_end-1
                ld  b,palette_end-palette
                ld  c,&f8
                otdr

                ld  a,vmpr_mode3+screen_page
                out (vmpr),a

                halt

palette:        mdat "mode3.pal"
palette_end:

                dump screen_page,0
                mdat "mode3.bin"

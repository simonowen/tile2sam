import glob
import os
import subprocess
import sys

NAME = "demo1"


def clean() -> None:
    patterns = ["*.bin", "*.pal", "*.dsk", f"{NAME}.map", "sprite.asm"]
    for pattern in patterns:
        for f in glob.glob(pattern):
            os.remove(f)


def build(extra) -> None:
    result = subprocess.run(
        ["tile2sam", "-v", "sprite.png", "11x11",
         "--code", "masked,save,restore", "--names", "ghost", "--pal", "--low", *extra]
    )
    if result.returncode != 0:
        sys.exit(result.returncode)

    result = subprocess.run(
        ["pyz80", "-I", "samdos2", f"--mapfile={NAME}.map", f"{NAME}.asm"]
    )
    if result.returncode != 0:
        sys.exit(result.returncode)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean()
    elif len(sys.argv) > 1 and sys.argv[1] == "run":
        build(sys.argv[2:])
        os.startfile(f"{NAME}.dsk")
    else:
        build(sys.argv[1:])

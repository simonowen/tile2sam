import glob
import os
import subprocess
import sys

_here = os.path.dirname(__file__)
DEMOS = sorted(os.path.basename(d) for d in glob.glob(os.path.join(_here, "demo*")) if os.path.isdir(d))


def run_demos(arg=None):
    for demo in DEMOS:
        cmd = [sys.executable, "make.py"]
        if arg:
            cmd.append(arg)
        result = subprocess.run(cmd, cwd=os.path.join(_here, demo))
        if result.returncode != 0:
            sys.exit(result.returncode)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg not in (None, "clean"):
        print(f"Unknown command: {arg}", file=sys.stderr)
        sys.exit(1)
    run_demos(arg)

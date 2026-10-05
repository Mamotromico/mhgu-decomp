"""Print the `;; entry <addr>` block(s) matching the given address(es).

Usage: show_func.py <disasm.txt> <addr> [addr ...]
"""
import re
import sys

entry_re = re.compile(r"^;; entry (\w+)")
insn_re = re.compile(r"^\s+([0-9a-f]{8})\s+(.*)$")


def main(argv):
    path = argv[1]
    want = {int(a, 16) for a in argv[2:]}
    cur = None
    printing = False
    with open(path) as f:
        for line in f:
            m = entry_re.match(line)
            if m:
                cur = int(m.group(1), 16)
                printing = cur in want
                if printing:
                    print(line.rstrip("\n"))
                continue
            if printing:
                if insn_re.match(line) or line.strip() == "":
                    print(line.rstrip("\n"))
                else:
                    printing = False


if __name__ == "__main__":
    main(sys.argv)

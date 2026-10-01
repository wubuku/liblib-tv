import sys
s = sys.stdin.read()
s = s.replace("    return true;", "    return globalThis.__hosted === true;", 1)
sys.stdout.write(s)

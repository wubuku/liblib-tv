import sys
s = sys.stdin.read()
s = s.replace("const [sort, setSort] = useState",
              "const [sort, setSort] = useState; void setSort;", 1)
sys.stdout.write(s)

import sys
s = sys.stdin.read()
s = s.replace("restart: boolean } | null>(null);",
              "restart: boolean } | null>(null); void setArtCritiqueStartRequest;", 1)
sys.stdout.write(s)

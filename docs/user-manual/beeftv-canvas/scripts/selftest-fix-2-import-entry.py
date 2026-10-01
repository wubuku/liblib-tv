import sys
s = sys.stdin.read()
s = s.replace('<input ref={inputRef} type="file"',
              '<input ref={inputRef} onClick={() => inputRef.current?.click()} type="file"', 1)
sys.stdout.write(s)

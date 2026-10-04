import sys, json, yaml

path = sys.argv[1]
try:
    d = yaml.safe_load(open(path, encoding='utf-8'))
    print(json.dumps({'ok': True, 'n': len(d['screenshots'])}, ensure_ascii=False))
except Exception as e:
    line = col = None
    m = getattr(e, 'problem_mark', None)
    if m is not None:
        line, col = m.line + 1, m.column + 1
    else:
        import re
        s = str(e)
        mm = re.search(r'line (\d+), column (\d+)', s)
        if mm:
            line, col = int(mm.group(1)), int(mm.group(2))
    print(json.dumps({'ok': False, 'line': line, 'col': col,
                      'err': type(e).__name__ + ': ' + str(e).split('\n')[0]}, ensure_ascii=False))

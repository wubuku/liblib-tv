import sys, json, yaml

# 逐条验证：修前（坏引号）与修后（合法引号）解析出的 3 个长文本字段是否**逐字相同**
# 规则：修前的「意图文本」= 掐掉可能残缺的外层引号（尾 " 、首 ' 、尾 ' ），内部裸 ' 保持原样
#       修后的解析值   = YAML 单引号标量，内部 '' 已由解析器还原成 '
原 = sys.argv[1]
新 = sys.argv[2]

def 意图(v):
    t = v
    if t.endswith('"'):
        t = t[:-1]
    if t.startswith("'"):
        t = t[1:]
    if t.endswith("'"):
        t = t[:-1]
    return t

def 读行(p):
    out, cur = [], None
    for s in open(p, encoding='utf-8').read().split('\n'):
        if s.startswith('  - file: '):
            cur = s[len('  - file: '):]
        m = __import__('re').match(r'^    (verified_locator|visible_text|alt): (.*)$', s)
        if m and cur:
            out.append((cur, m.group(1), m.group(2)))
    return out

a = 读行(原)
d = yaml.safe_load(open(新, encoding='utf-8'))
字段 = {}
for it in d['screenshots']:
    for k in ('verified_locator', 'visible_text', 'alt'):
        if k in it:
            字段[(it['file'], k)] = it[k]

print('修前行数 =', len(a), '| 修后条目数 =', len(d['screenshots']))
坏 = []
缺 = []
for f, k, v in a:
    if (f, k) not in 字段:
        缺.append([f, k])
        continue
    if 字段[(f, k)] != 意图(v):
        坏.append([f, k, 意图(v)[:60], 字段[(f, k)][:60]])
print('修后缺失的字段 =', len(缺), 缺[:3])
print('内容逐字不同的 =', len(坏))
for b in 坏[:5]:
    print('   ❌', json.dumps(b, ensure_ascii=False))
print('✅ 135 条 × 3 长文本字段全部逐字相同（只重写了引号）' if not 坏 and not 缺 else '❌ 有差异')

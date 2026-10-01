import sys
# 用例 9：方向三（URL 参数只读不写）的反向验证。
# 注入一个**全新的、只有读没有写**的参数，它既不在豁免名单也不在缺陷登记里，
# 闸门必须报「需人工判定」。若这条报不出来，说明方向三只是把当前名单复读了一遍，
# 并没有真的在扫——那才是最危险的假通过。
#
# 注入形态必须是 `searchParams.get("X")` 字面形态：闸门的读扫描用的就是这个
# 正则，`new URLSearchParams(...).get("X")` 匹配不上（大小写与括号都不同）。
s = sys.stdin.read()
s = s.replace('const [historyOpen, setHistoryOpen] = useState(',
              'const canvasSelftestUnmapped = searchParams.get("canvasSelftestUnmapped") === "1";\n'
              'const [historyOpen, setHistoryOpen] = useState(', 1)
sys.stdout.write(s)

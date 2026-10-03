import sys
# 用例 43（能抓方向）：**整行删掉**任务页的 H1。
#
# 旧判据是 `open(path).readline()` 之后判 `startswith("# ")`，
# 读不到就 `continue` ——**那一页从此不再被任何方向检查**。
# 实测（Batch 250）：这么注入之后闸 9 报 **rc=0**，还打印
#   ✓ 任务索引双向一致：**28 个任务页全部登记**，29 条链接文字与页面标题一致
# 真树是 29 个任务页。**少了一页，数字自己都不打架了，还照印「29 条一致」**——
# 而那 29 条里有 1 条根本没被比过。
#
# 新判据必须报「全文没有任何 H1」。**这条用例钉的是「不再静默」**；
# 「真的去比了那一页」由用例 44 钉——两者不是同一件事，见那里。
s = sys.stdin.read()
anchor = "# 素材库（资产页）\n"
assert anchor in s, "锚点未命中：asset-library.md 的 H1 不在预期位置"
s = s.replace(anchor, "", 1)
assert s != anchor, "注入空转"
sys.stdout.write(s)

import os
# 用例 44（能抓方向，**本批鉴别力最强的一条**）：H1 挪到第 2 行，且索引链接文字写错。
#
# 与用例 43 的区别是本用例的全部意义：
#   43 注入之后页面**真的没有 H1**，新判据报「全文没有任何 H1」——
#      而**只读首行的旧判据在同一个注入上也是「读不到 H1」**，两者走的是同一条分支。
#      换句话说 43 单独并不能证明「全篇扫」这件事被验过了。
#   44 注入之后页面**有 H1，只是不在首行**，所以新判据必须**跨过首行去找到它并比**。
#      只读首行的判据会整页跳过，于是索引里那个写错的链接**永远比不到**。
#
# 实测（Batch 250，判据改前 vs 改后，同一个注入）：
#   改前 rc=0  ✓ 任务索引双向一致：28 个任务页全部登记，29 条链接文字与页面标题一致
#   改后 rc=1  ✗ 索引里 asset-library.md 的链接文字「素材库（错的）」与页面标题「素材库（资产页）」既不相同
# **改前那一行是本批最刺眼的证据**：链接文字明明写着「素材库（错的）」，
# 而它「与页面标题一致」。
#
# 本脚本**改两个文件**（页面 + 索引），所以不走 `run_file_case` 的 stdin/stdout 单文件通道，
# 改用 `run_fail_case` + 直接执行——那条路径的「注入空转」判定看的是 SNAP_FILES 的 md5，
# 而 `10-tasks/asset-library.md` 是本批才加进 SNAP_FILES 的（见那里的注释）。
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

page = os.path.join(ROOT, "10-tasks", "asset-library.md")
idx = os.path.join(ROOT, "10-tasks", "README.md")

s = open(page, encoding="utf-8").read()
h1 = "# 素材库（资产页）\n"
assert s.startswith(h1), "锚点未命中：asset-library.md 首行不是预期的 H1"
open(page, "w", encoding="utf-8").write("<!-- 首行不是 H1，真 H1 在第 2 行 -->\n" + s)

t = open(idx, encoding="utf-8").read()
link = "[素材库（资产页）](asset-library.md)"
assert link in t, "锚点未命中：索引里没有预期的素材库链接"
t = t.replace(link, "[素材库（错的）](asset-library.md)", 1)
open(idx, "w", encoding="utf-8").write(t)

assert open(page, encoding="utf-8").read() != s, "注入空转：页面没变"

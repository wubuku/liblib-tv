#!/usr/bin/env python3
"""静态扫描：每一处 role 浮层的 (文件:行, 可访问名, data-testid)。

用途：动态普查（`verify-jimeng-batch83x`）只能扫**打开过**的浮层；这一支扫
**源码里存在**的，于是能回答「还有哪些没被任何判据打开过」。

跑法：  python3 scripts/jimeng_role_layer_scan.py            # 全仓
        python3 scripts/jimeng_role_layer_scan.py jimeng     # 只看 jimeng

### 写它是因为踩了两次「边界画错」

① **按目录划边界。** 批 832 的清单是数 `src/components/jimeng/nodes/` 得来的，
   于是漏掉 `jimeng/` 根目录下 13 处 `role="listbox"` —— 它们同样是节点内浮层
   （生成面板里的模型/比例/时长下拉）。**目录不是边界，role 属性才是。**

② **扫描器自己有 bug，却报得像结论。** 第一版把 56 处 role 浮层**全部**报成
   「无名无锚点」，可 `image-tools-menu` 明明就在第 131 行。根因：正则的
   `(?P<mid>...)` 已经把标签属性吃进去了，我又从 `m.end()` 往后找
   `data-testid` —— 等于**在属性之后**找。
   **恒假的判据比没有判据更危险**：它会让人以为有 56 个缺口，然后去"修"。
   写扫描器时先拿一个**已知有答案**的点验一下（这里就是 832 的 17 个锚点）。

③ **同一个洞，另一种形状（批 842）。** ② 修的是「在 `m.end()` 之后找」，
   换成了 `(?P<mid>...)` 那一段。**但那一段是从 `role="…"` 之后开始的** ——
   于是「`data-testid` 写在 `role=` **前面**」的标签照样漏。
   实测 `JimengAiDrawer` 的
       `<div className=… data-testid="canvas-agent-session-menu" role="dialog" …>`
   被报成「无 data-testid」，而锚点明明就在上一行。
   **属性顺序不该影响结论。** 现在改成把**整个开标签**都当成属性窗口，
   并给自检加一条专门盯「testid 在 role 之前」这个形状的用例。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src"
FILTER = sys.argv[1] if len(sys.argv) > 1 else ""
# ⚠️ 窗口是**整个开标签**，不是 `role=` 之后那一段。
#
#    实现上刻意**不**用「从每个 `<` 起匹配」的正则：那要么贪婪（吞到文件尾再
#    回溯找 `role=`，全仓跑到 >180s 超时），要么惰性（还是要从每个 `<` 试，
#    实测 2m3s）。这里反过来做 —— `role="dialog|menu|listbox|popover"` 在整个
#    仓库里是**稀有**的，先定位它，再**往回**找本标签的起点（最近的、在上一个
#    `>` 之后的那个 `<`），往前窗口就是 `attrs`，往后窗口到下一个 `>` 就是 `mid`。
#    量级从 O(文件长 × `<` 的个数) 降到 O(命中数)。
ROLE = re.compile(r'role="(dialog|menu|listbox|popover)"')
# 属性窗口：到 `<` 或 `>` 为止（`\{[^{}]*\}` 让 JSX 表达式整体通过）
ATTRWIN = re.compile(r'(?:[^<>]|\{[^{}]*\})*')

rows = []
for f in sorted(ROOT.rglob("*.tsx")):
    rel = f.relative_to(ROOT)
    if FILTER and FILTER not in str(rel):
        continue
    src = f.read_text(encoding="utf-8")
    for m in ROLE.finditer(src):
        # 标签自身的属性 = **整个开标签**。往回找起点：离 `role=` 最近的、
        # 且在上一个 `>` 之后的那个 `<`（`>` 之后说明已经出了上一个标签）。
        # 只取 `role=` **之后**那一段的话，属性顺序就成了结论的一部分
        # —— 那不是判据，那是巧合。
        # ⚠️ 更早的两版分别写成「`src[m.end():]`」（整个标签**之后**，56 处全
        #    报成「无名无锚点」）和「从每个 `<` 起匹配」（跑到超时）。
        #    **恒假/恒慢的扫描器比没有扫描器更危险**：恒假的会让人以为有 56 个
        #    缺口然后去"修"，恒慢的会让人以为它坏了然后关掉。
        lt = src.rfind("<", 0, m.start())
        gt = src.rfind(">", 0, m.start())
        if lt < 0 or lt < gt:
            continue                      # 找不到开标签（字符串里的 role= 等）
        attrs = src[lt:m.start()]
        mm = ATTRWIN.match(src, m.end())
        mid = mm.group(0) if mm else ""
        own = attrs + " " + mid
        # ⚠️ JSX 开标签里**允许 `//` 注释**，而注释里常提到别的 data-testid。
        #    实测 `JimengAudioNode` 的注释写着 data-testid="flow-node-selected-tag"，
        #    不剥掉的话扫描器会把它当成这一行的真锚点，于是**真的**锚点
        #    `audio-node-tag-picker` 反而「丢失」。先剥注释再匹配属性。
        own = re.sub(r"//[^\n]*", "", own)
        line = src[:lt].count("\n") + 1
        al = re.search(r'aria-label=("([^"]*)"|\{([^}]*)\})', own)
        lb = re.search(r'aria-labelledby=("([^"]*)"|\{([^}]*)\})', own)
        tid = re.search(r'data-testid=("([^"]*)"|\{([^}]*)\})', own)
        rows.append({
            "loc": f"{rel}:{line}",
            "role": m.group(1),
            "name": (al.group(2) or al.group(3)) if al else
                    (f"labelledby={lb.group(2) or lb.group(3)}" if lb else "—"),
            "tid": (tid.group(2) or tid.group(3)) if tid else "—",
        })

NO_TID = [r for r in rows if r["tid"] == "—"]
NO_NAME = [r for r in rows if r["name"] == "—"]
BOTH = [r for r in rows if r["tid"] == "—" and r["name"] == "—"]

scope = f"（过滤：{FILTER}）" if FILTER else ""
print(f"共 {len(rows)} 处 role 浮层 {scope}")
print(f"\n无 data-testid（{len(NO_TID)} 处）：")
for r in NO_TID:
    print(f"  {r['loc']:58} {r['role']:8} name={r['name'][:40]}")
print(f"\n无可访问名（{len(NO_NAME)} 处）：")
for r in NO_NAME:
    print(f"  {r['loc']:58} {r['role']:8} tid={r['tid']}")
print(f"\n两样都无（{len(BOTH)} 处）：")
for r in BOTH:
    print(f"  {r['loc']}")

# 自检：拿一个**已知有答案**的点验扫描器本身。
# 832 的 17 个锚点全部应当在，且「两样都无」应当是 0 —— 不是 0 就是扫描器坏了。
KNOWN = ["text-bg-palette", "image-tools-menu", "audio-node-tag-picker",
         "video-node-tag-picker", "gen-model-listbox", "gen-video-size-listbox",
         "gen-mode-listbox", "gen-duration-listbox", "audio-gen-type-listbox",
         "audio-music-model-listbox", "audio-music-duration-listbox",
         "audio-voice-model-listbox", "audio-gen-mode-listbox",
         "audio-all-voices-listbox", "audio-voice-filter-listbox",
         "image-gen-model-listbox", "image-gen-size-listbox"]
if not FILTER or "jimeng" in FILTER:
    found = {r["tid"] for r in rows}
    miss = [t for t in KNOWN if t not in found]
    print(f"\n自检：832 的 {len(KNOWN)} 个锚点{'全部命中 ✓' if not miss else '缺失 ' + str(miss)}")
    print(f"自检：「两样都无」= {len(BOTH)}（非 0 说明扫描器自己坏了）")

# ── 自检（批 842 补）：**属性顺序**不许影响结论 ────────────────────
# 上一条自检盯的是"锚点在不在"，盯不住"锚点写在 role 的哪一侧"——
# 832 那 17 个锚点恰好都写在 `role=` **后面**，于是扫描器把
# `JimengAiDrawer` 里写在**前面**的 4 处锚点全报成「无 data-testid」，
# 而自检一路绿灯。**自检覆盖不到的那一半，就等于没有自检。**
# 这里用**合成夹具**直接验三种顺序，不依赖任何真实文件。
def _probe(fragment: str) -> str:
    """对一段合成 JSX 跑一遍与正式扫描同样的窗口逻辑。"""
    m = ROLE.search(fragment)
    if not m:
        return "—"
    lt = fragment.rfind("<", 0, m.start())
    gt = fragment.rfind(">", 0, m.start())
    if lt < 0 or lt < gt:
        return "—"
    own = fragment[lt:m.start()] + " " + (
        ATTRWIN.match(fragment, m.end()).group(0)
        if ATTRWIN.match(fragment, m.end()) else "")
    own = re.sub(r"//[^\n]*", "", own)
    t = re.search(r'data-testid=("([^"]*)"|\{([^}]*)\})', own)
    return (t.group(2) or t.group(3)) if t else "—"


ORDER_CASES = [
    ('<div data-testid="a-before" role="dialog" aria-label="X" />', "a-before",
     "data-testid 写在 role **之前**"),
    ('<div role="dialog" data-testid="b-after" aria-label="X" />', "b-after",
     "data-testid 写在 role **之后**"),
    ('<div className="c"\n  data-testid="c-multiline"\n  role="listbox"\n/>',
     "c-multiline", "跨行 + 在 role 之前"),
]
order_bad = [(why, _probe(frag), want) for frag, want, why in ORDER_CASES
             if _probe(frag) != want]
print(f"自检：属性顺序不影响结论 —— 3 种写法"
      f"{'全部认出 ✓' if not order_bad else '认错了 ' + str(order_bad)}"
      f"（三种写法里只要有一种认不出，扫描器就是在按顺序而不是按语义判）")

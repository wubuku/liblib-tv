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
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src"
FILTER = sys.argv[1] if len(sys.argv) > 1 else ""
ATTR = re.compile(
    r'role="(dialog|menu|listbox|popover)"'
    r'(?P<mid>(?:[^<>]|\{[^{}]*\})*)',
    re.S,
)

rows = []
for f in sorted(ROOT.rglob("*.tsx")):
    rel = f.relative_to(ROOT)
    if FILTER and FILTER not in str(rel):
        continue
    src = f.read_text(encoding="utf-8")
    for m in ATTR.finditer(src):
        # 标签自身的属性 = role= 与下一个 > 之间那段（`mid` 已经含在里面了）。
        # ⚠️ 曾经写成 `src[m.end():]` —— 那是**属性之后**，会把 56 处全报成
        #    「无名无锚点」。恒假的扫描器比没有扫描器更危险。
        own = m.group("mid")
        # ⚠️ JSX 开标签里**允许 `//` 注释**，而注释里常提到别的 data-testid。
        #    实测 `JimengAudioNode` 的注释写着 data-testid="flow-node-selected-tag"，
        #    不剥掉的话扫描器会把它当成这一行的真锚点，于是**真的**锚点
        #    `audio-node-tag-picker` 反而「丢失」。先剥注释再匹配属性。
        own = re.sub(r"//[^\n]*", "", own)
        line = src[:m.start()].count("\n") + 1
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

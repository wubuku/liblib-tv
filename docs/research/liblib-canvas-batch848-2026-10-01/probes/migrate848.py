#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 848：**第八次迁移** —— 把 840／841 两条门禁与两个探针的
「**那一页内容未实测 ⟹ 显示如实说明**」断言**翻成「那一页已实测并实现」**。

## 为什么必须改

★ batch 848 把第五段的「我的音色」「AI 生成」两页**实测并实现**了
⟹ ⟹ 840／841 的那条断言（点那两枚页签 ⟹ 应当出现「**未实测**」说明）
⟹ ⟹ **照原样跑必然红** ⟹ ⟹ 必须改。

★ ★ **期望值跟着语义走**（★ 与第七次迁移同一个原则）：
  | 门禁 | 上一批的期望 | 本批的期望 | 为什么 |
  | --- | --- | --- | --- |
  | `840` | 「我的音色」页显示**未实测**说明 | 该页显示**实测出来的空态**「暂无音色数据」，且**没有**「未实测」字样 | ★ 那一页**已经实测并实现**了 ⟹ ⟹ 继续写「未实测」是**假陈述** |
  | `841` | 「AI 生成」页显示**未实测**说明 | 该页显示**实测出来的**「生成音色」＋「生成历史」，且**没有**「未实测」字样 | ★ 同上 |

★ 「**未实测的入口只显示如实说明、不编造控件**」这条**纪律没有变**
⟹ ⟹ 它现在由 **842／843** 承载（★ 它们盯的是**第四段**「服装造型」里那两枚
**仍未实现**的子页签 ⟹ ⟹ 第四段的 raw 本批只测了、没实现）。

★ ★ **期望值不手打**：两条新期望的文案都从**本批入库的源站 raw**
（`source-848-p3.json`／`source-848-p4.json`）**机器提取**。

## 改了什么（**逐处精确替换** ⟹ ⟹ 不用正则乱扫）

| 文件 | 改动 |
| --- | --- |
| `clone847.py` | 读数里加 `我的音色空态`（★ 实测空态的盒 ＋ 文案） |
| `clone840.py` | 读数里加 `我的音色空态`（★ 实测空态的盒 ＋ 文案） |
| `clone841.py` | 读数里加 `AI页`（★ 内容区盒 ＋「生成音色」＋「生成历史」） |
| `verify-liblib-batch847.py` | S7 的期望与措辞翻成「已实现」（★ **它自己**也是那条断言的作者） |
| `verify-liblib-batch840.py` | 读本批 raw 取期望文案；S7 的期望与措辞翻成「已实现」 |
| `verify-liblib-batch841.py` | 同上（S5） |

★ ★ **为什么 847 自己的门禁也要改**：★ batch 847 的 S7 写的是
「点「我的音色」⟹ 显示**如实说明** ＋ **0 张卡** ＋ **0 枚工具**」
⟹ ⟹ 本批把那两页**实测并实现**了 ⟹ ⟹ 「如实说明」没了（⟹ ⟹ 变成实测出来的空态）
⟹ ⟹ 而「0 枚工具」也**错了**（★ 源站实测：那一页**也有**两枚工具 ⟹ ⟹ clone 之前
写「0 枚工具」是**既存偏差**）⟹ ⟹ 照原样跑必然红 ⟹ ⟹ 必须一起改。

★ 迁移完必须**三条门禁全绿**（847 7/7、840 7/7、841 6/6）
⟹ ⟹ 否则说明「迁移」把别的东西改坏了。

## 用法

    python3 migrate848.py --dry-run   # 只核对锚点，**不写文件**
    python3 migrate848.py             # 真正改（并**逐处**校验唯一命中）
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]

P840 = "docs/research/liblib-canvas-batch840-2026-10-01/probes/clone840.py"
P841 = "docs/research/liblib-canvas-batch841-2026-10-01/probes/clone841.py"
P847 = "docs/research/liblib-canvas-batch847-2026-10-01/probes/clone847.py"
G840 = "scripts/verify-liblib-batch840.py"
G841 = "scripts/verify-liblib-batch841.py"
G847 = "scripts/verify-liblib-batch847.py"

# ★★ 每一项都是 (相对路径, [(旧串, 新串), ...]) ⟹ ⟹ **必须唯一命中**
EDITS = [
    # ── clone847.py：读「我的音色」页的**实测空态**（★ 847 自己那条断言也要翻）──
    (P847, [
        ("  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n",
         "  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n"
         "  // ★★ **batch 848 起**：★ 「我的音色」页**已实测并实现** ⟹ ⟹ 读它的**实测空态**\n"
         "  out['我的音色空态']=(()=>{const e=root.querySelector(\"[data-character-editor-voice-empty='mine']\");\n"
         "    return e?{...rel(e),text:txt(e)}:null;})();\n"),
    ]),
    # ── clone840.py：读「我的音色」页的**实测空态** ──
    (P840, [
        ("  out['空态']=(()=>{const e=q('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n",
         "  out['空态']=(()=>{const e=q('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n"
         "  // ★★ **batch 848 起**：★ 「我的音色」页**已实测并实现** ⟹ ⟹ 读它的**实测空态**\n"
         "  out['我的音色空态']=(()=>{const e=q(\"[data-character-editor-voice-empty='mine']\");\n"
         "    return e?{...rel(e),text:txt(e)}:null;})();\n"),
    ]),
    # ── clone841.py：读「AI 生成」页的**实测内容** ──
    (P841, [
        ("  out['空态']=(()=>{const e=q('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n",
         "  out['空态']=(()=>{const e=q('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n"
         "  // ★★ **batch 848 起**：★ 「AI 生成」页**已实测并实现** ⟹ ⟹ 读它的**实测内容**\n"
         "  out['AI页']=(()=>{const e=q('[data-character-editor-voice-ai]');\n"
         "    if(!e)return null;\n"
         "    const g=e.querySelector('[data-character-editor-voice-generate]');\n"
         "    const t=e.querySelector('[data-character-editor-voice-history] h3');\n"
         "    return {...rel(e),生成按钮:g?txt(g):null,历史标题:t?txt(t):null};})();\n"),
    ]),
    # ── verify-liblib-batch847.py：★ **它自己**那条断言也要翻 ──
    (G847, [
        # ① 常量
        ('RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"\n',
         'RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"\n'
         '# ★★ **batch 848 起**：★ 「我的音色」页**已实测并实现** ⟹ ⟹ 期望值从那份 raw 取\n'
         'RAW848_P3 = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p3.json"\n'),
        # ② 先算出两个期望（★ 机器提取 ⟹ ⟹ 不手打）
        ('    return {\n        "右栏盒": R(src["右栏盒"]),\n',
         '    # ★★ **batch 848 起**：★ 「我的音色」页的**实测空态文案**与**工具数**\n'
         '    #   （★ 机器提取自**本批入库的源站 raw** ⟹ ⟹ 不手打 ⟹ ⟹ 也**更正**了\n'
         '    #   batch 847 写的「0 枚工具」——★ 源站实测：那一页**也有**两枚工具）\n'
         '    def _walk(n):\n'
         '        yield n\n'
         '        for k in (n.get("c2") or []):\n'
         '            yield from _walk(k)\n'
         '    _p3 = read_json(RAW848_P3)\n'
         '    _mine = [n for n in _walk(_p3["★整棵子树"])\n'
         '             if (n.get("x") or "") == "暂无音色数据"\n'
         '             and "h-24" in (n.get("c") or "")]\n'
         '    if len(_mine) != 1:\n'
         '        raise SystemExit("848 raw 里的「暂无音色数据」识别不唯一：%d 个" % len(_mine))\n'
         '    _p3_tools = [n for n in _walk(_p3["★整棵子树"])\n'
         '                 if n.get("t") == "BUTTON" and n.get("ar") in ("搜索", "筛选音色")]\n'
         '\n'
         '    return {\n        "右栏盒": R(src["右栏盒"]),\n'),
        # ③ 把两个期望放进表里
        ('        "★模态原点": {"x": ox, "y": oy},\n    }\n',
         '        "★模态原点": {"x": ox, "y": oy},\n'
         '        "★我的音色空态文案": _mine[0]["x"],\n'
         '        "★我的音色工具数": len(_p3_tools),\n'
         '    }\n'),
        # ④ S7 的清单：加新读数
        ('        "★切到我的音色_空态说明": (mine.get("空态") or "")[:90],\n'
         '        "★切到我的音色_卡数": len(mine.get("音色卡") or []),\n'
         '        "★切到我的音色_工具数": len((mine.get("工具行") or {}).get("按钮") or []),\n',
         '        "★切到我的音色_空态说明": (mine.get("空态") or "")[:90],\n'
         '        "★切到我的音色_卡数": len(mine.get("音色卡") or []),\n'
         '        "★切到我的音色_工具数": len((mine.get("工具行") or {}).get("按钮") or []),\n'
         '        # ★★ **batch 848 起**：★ 那一页**已实现** ⟹ ⟹ 读**实测空态**\n'
         '        "★切到我的音色_实测空态文案": (mine.get("我的音色空态") or {}).get("text"),\n'),
        # ⑤ S7 的**期望**：翻成「已实现」
        ('         and bool(mine.get("空态"))\n'
         '         and len(mine.get("音色卡") or []) == 0\n'
         '         and len((mine.get("工具行") or {}).get("按钮") or []) == 0\n',
         '         and not mine.get("空态")\n'
         '         and (mine.get("我的音色空态") or {}).get("text") == exp["★我的音色空态文案"]\n'
         '         and len(mine.get("音色卡") or []) == 0\n'
         '         and len((mine.get("工具行") or {}).get("按钮") or []) == exp["★我的音色工具数"]\n'),
        # ⑥ S7 的**措辞**
        ('        "★ 且点「我的音色」⟹ 显示**如实说明** ＋ **0 张卡** ＋ **0 枚工具**"\n'
         '        "（★ 那一页的控件**源站未实测** ⟹ ⟹ **不编造**）⟹ ⟹ 切回「音色库」⟹ 20 张卡回来",\n',
         '        "★ 且点「我的音色」⟹ 显示的是**实测出来的空态**「暂无音色数据」"\n'
         '        "（★ **batch 848 起**：那一页**已实测并实现** ⟹ ⟹ 不再有「未实测」说明）"\n'
         '        "＋ **0 张卡** ＋ **2 枚工具**（★ 源站实测：那一页**也有**工具行 ⟹ ⟹ 更正了"\n'
         '        "batch 847 写的「0 枚工具」）⟹ ⟹ 切回「音色库」⟹ 20 张卡回来",\n'),
    ]),
    # ── verify-liblib-batch840.py ──
    (G840, [
        # ① 常量：读本批入库的源站 raw
        ('RAW = BATCH / "raw"\n',
         'RAW = BATCH / "raw"\n'
         '# ★★ **batch 848 起**：★ 「我的音色」页**已实测并实现** ⟹ ⟹ 期望值从那份 raw 取\n'
         'RAW848_P3 = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p3.json"\n'),
        # ② 期望值：机器提取「暂无音色数据」这句文案
        ('    e["右列"] = R(r4["asides"][1]["box"])\n',
         '    e["右列"] = R(r4["asides"][1]["box"])\n'
         '    # ★★ **batch 848 起**：★ 「我的音色」页的**实测空态文案**（★ 机器提取 ⟹ ⟹ 不手打）\n'
         '    def _walk(n):\n'
         '        yield n\n'
         '        for k in (n.get("c2") or []):\n'
         '            yield from _walk(k)\n'
         '    _p3 = read_json(RAW848_P3)\n'
         '    _mine = [n for n in _walk(_p3["★整棵子树"])\n'
         '             if (n.get("x") or "") == "暂无音色数据"\n'
         '             and "h-24" in (n.get("c") or "")]\n'
         '    if len(_mine) != 1:\n'
         '        raise SystemExit("848 raw 里的「暂无音色数据」识别不唯一：%d 个" % len(_mine))\n'
         '    e["_我的音色空态文案"] = _mine[0]["x"]\n'),
        # ③ S7 的判据：从「未实测说明」翻成「实测出来的空态」
        ('    s7_says_unmeasured = bool(seg5_empty and "未实测" in seg5_empty)\n'
         '    s7_says_measured = bool(seg5_empty and "已实测" in seg5_empty)\n',
         '    s7_says_unmeasured = bool(seg5_empty and "未实测" in seg5_empty)\n'
         '    s7_says_measured = bool(seg5_empty and "已实测" in seg5_empty)\n'
         '    # ★★★ **batch 848 起再改**：★ 「我的音色」页**已实测并实现** ⟹ ⟹ 它**不再**是\n'
         '    #   「未实测」说明 ⟹ ⟹ 期望**翻成**：显示的是**实测出来的空态** ＋ **没有**「未实测」字样\n'
         '    #   ⟹ ⟹ ★ 「未实测入口只显示如实说明」这条**纪律**由 **842／843** 继续承载\n'
         '    #     （★ 它们盯的是**第四段**那两枚**仍未实现**的子页签）\n'
         '    s7_mine_empty = after_seg5.get("我的音色空态") or {}\n'
         '    s7_shows_measured_empty = bool(\n'
         '        s7_mine_empty.get("text") == exp["_我的音色空态文案"])\n'),
        # ④ S7 的清单里加新读数
        ('        "★第五段_空态说明里写了「未实测」": s7_says_unmeasured,\n'
         '        "★第五段_空态说明里写了「已实测」": s7_says_measured,\n',
         '        "★第五段_空态说明里写了「未实测」": s7_says_unmeasured,\n'
         '        "★第五段_空态说明里写了「已实测」": s7_says_measured,\n'
         '        # ★★ **batch 848 起**：★ 那一页**已实现** ⟹ ⟹ 读**实测空态**\n'
         '        "★我的音色_实测空态文案": s7_mine_empty.get("text"),\n'
         '        "★我的音色_显示的是实测空态": s7_shows_measured_empty,\n'),
        # ⑤ S7 的**期望**：翻成「已实现」
        ('        (s7["★第五段_页签数"] == 0 and s7["★第五段_滑杆数"] == 0\n'
         '         and bool(seg5_empty) and s7_says_unmeasured\n'
         '         and not s7["★第五段_空态说明里写了「已实测」"]\n',
         '        (s7["★第五段_页签数"] == 0 and s7["★第五段_滑杆数"] == 0\n'
         '         and not seg5_empty and s7_shows_measured_empty\n'
         '         and not s7_says_unmeasured\n'
         '         and not s7["★第五段_空态说明里写了「已实测」"]\n'),
        # ⑥ S7 的**措辞**：要跟期望一致（★ 判据的标题就是它承诺的东西）
        ('        "S7 ★★★ **未实测的那一页显示空态说明、不编造控件**：★ **batch 847 起换靶**——"\n'
         '        "左列五段**全部实现** ⟹ ⟹ 「仍未实现的那一段」**没有靶子了** ⟹ ⟹ 改盯"\n'
         '        "**第五段里那一页内容未实测的页签**（「我的音色」）"\n',
         '        "S7 ★★★ **那一页已实测并实现**：★ **batch 848 起再改**——「我的音色」页"\n'
         '        "**已实测并实现**（★ batch 848 raw 入库）⟹ ⟹ 期望**翻成**：显示的是"\n'
         '        "**实测出来的空态**「暂无音色数据」⟹ ⟹ 且**没有**「未实测」字样"\n'
         '        "（★ 「未实测入口只显示如实说明」这条纪律由 **842／843** 承载）"\n'),
    ]),
    # ── verify-liblib-batch841.py ──
    (G841, [
        # ① 常量
        ('RAW = BATCH / "raw"\n',
         'RAW = BATCH / "raw"\n'
         '# ★★ **batch 848 起**：★ 「AI 生成」页**已实测并实现** ⟹ ⟹ 期望值从那份 raw 取\n'
         'RAW848_P4 = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p4.json"\n'),
        # ② 期望值：机器提取「生成音色」「生成历史」两句文案
        ('    exp["_源站积分全未变"] = all(\n',
         '    # ★★ **batch 848 起**：★ 「AI 生成」页的**实测文案**（★ 机器提取 ⟹ ⟹ 不手打）\n'
         '    def _walk(n):\n'
         '        yield n\n'
         '        for k in (n.get("c2") or []):\n'
         '            yield from _walk(k)\n'
         '    _p4 = read_json(RAW848_P4)\n'
         '    _gen = [n for n in _walk(_p4["★整棵子树"]) if n.get("ar") == "生成音色"]\n'
         '    _his = [n for n in _walk(_p4["★整棵子树"]) if n.get("t") == "H3"]\n'
         '    if len(_gen) != 1 or len(_his) != 1:\n'
         '        raise SystemExit("848 raw 里的「生成音色」/「生成历史」识别不唯一：%d / %d"\n'
         '                         % (len(_gen), len(_his)))\n'
         '    exp["_AI页_生成按钮文案"] = "生成音色"\n'
         '    exp["_AI页_历史标题文案"] = _his[0].get("x")\n'
         '    exp["_源站积分全未变"] = all(\n'),
        # ③ S5 的判据
        ('    s5_says_unmeasured = bool(seg5_empty and "未实测" in seg5_empty)\n'
         '    s5_says_measured = bool(seg5_empty and "已实测" in seg5_empty)\n',
         '    s5_says_unmeasured = bool(seg5_empty and "未实测" in seg5_empty)\n'
         '    s5_says_measured = bool(seg5_empty and "已实测" in seg5_empty)\n'
         '    # ★★★ **batch 848 起再改**：★ 「AI 生成」页**已实测并实现** ⟹ ⟹ 它**不再**是\n'
         '    #   「未实测」说明 ⟹ ⟹ 期望**翻成**：显示的是**实测出来的**「生成音色」＋「生成历史」\n'
         '    ai_page = seg5.get("AI页") or {}\n'
         '    s5_shows_measured_ai = bool(\n'
         '        ai_page.get("生成按钮") and exp["_AI页_生成按钮文案"] in ai_page.get("生成按钮")\n'
         '        and ai_page.get("历史标题") == exp["_AI页_历史标题文案"])\n'),
        # ④ S5 的清单里加新读数
        ('        "★第五段_空态说明里写了「未实测」": s5_says_unmeasured,\n'
         '        "★第五段_空态说明里写了「已实测」": s5_says_measured,\n',
         '        "★第五段_空态说明里写了「未实测」": s5_says_unmeasured,\n'
         '        "★第五段_空态说明里写了「已实测」": s5_says_measured,\n'
         '        # ★★ **batch 848 起**：★ 那一页**已实现** ⟹ ⟹ 读**实测内容**\n'
         '        "★AI页_生成按钮文案": ai_page.get("生成按钮"),\n'
         '        "★AI页_历史标题文案": ai_page.get("历史标题"),\n'
         '        "★AI页_显示的是实测内容": s5_shows_measured_ai,\n'),
        # ⑤ S5 的**期望**：翻成「已实现」
        ('        (s5["★第五段_页签数"] == 0 and s5["★第五段_滑杆数"] == 0\n'
         '         and bool(seg5_empty)\n'
         '         and s5_says_unmeasured\n'
         '         and not s5["★第五段_空态说明里写了「已实测」"]\n',
         '        (s5["★第五段_页签数"] == 0 and s5["★第五段_滑杆数"] == 0\n'
         '         and not seg5_empty\n'
         '         and s5_shows_measured_ai\n'
         '         and not s5_says_unmeasured\n'
         '         and not s5["★第五段_空态说明里写了「已实测」"]\n'),
        # ⑥ S5 的**措辞**
        ('        "S5 ★★★ **未实测的那一页仍显示空态说明、0 控件**（★ batch 847 起换靶：左列五段"\n'
         '        "**全部实现** ⟹ ⟹ 「仍未实现的那一段」**没有靶子了** ⟹ ⟹ 改盯**第五段里那一页"\n'
         '        "内容未实测的页签**（「AI 生成」）；★ 且说明文案**要**写「未实测」—— ★ 那一页"\n'
         '        "的控件**根本就没测过** ⟹ ⟹ 写「已实测」才是**假陈述**",\n',
         '        "S5 ★★★ **那一页已实测并实现**（★ batch 848 起再改）：「AI 生成」页**已实测并实现**"\n'
         '        "（★ batch 848 raw 入库）⟹ ⟹ 期望**翻成**：显示的是**实测出来的**「生成音色」"\n'
         '        "＋「生成历史」⟹ ⟹ 且**没有**「未实测」字样（★ 「未实测入口只显示如实说明」"\n'
         '        "这条纪律由 **842／843** 承载）",\n'),
    ]),
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    total = 0
    for rel, pairs in EDITS:
        path = ROOT / rel
        src = path.read_text(encoding="utf-8")
        for old, new in pairs:
            n = src.count(old)
            if n != 1:
                print("✘ %s：锚点命中 %d 处（应为 1）：%r" % (rel, n, old[:70]))
                return 2
            src = src.replace(old, new, 1)
            total += 1
        if not dry:
            path.write_text(src, encoding="utf-8")
        print("  %s %s（%d 处）" % ("[dry-run]" if dry else "✔ 已改", rel, len(pairs)))
    print("共 %d 处替换%s" % (total, "（dry-run，未写文件）" if dry else ""))
    if dry:
        return 0
    # ★ 改完自检：两个文件仍能编译（⟹ ⟹ 语法错当场发现 ⟹ ⟹ 而不是等门禁报错）
    import py_compile
    for rel in (P840, P841, P847, G840, G841, G847):
        try:
            py_compile.compile(str(ROOT / rel), doraise=True)
        except Exception as exc:  # noqa: BLE001
            print("✘ %s 编译失败：%s" % (rel, exc))
            return 2
    print("✔ 四个文件都能编译")
    # ★★ **迁移脚本自己也要有自检**：探针里的 READ 是**一整段 JS** ⟹ ⟹
    #   ★ **Python 编译得过 ≠ JS 语法对** —— ★ 本批第一版就栽在这：
    #   插入的选择器里带了一对 `"`，而 READ 是 **三引号**字符串 ⟹ ⟹ 字符串被截断
    #   ⟹ ⟹ Python 侧毫无异常 ⟹ ⟹ 直到运行时才报 SyntaxError ⟹ ⟹ 而症状是
    #   「门禁 0/7 全红」⟹ ⟹ 极易误判成「迁移把实现改坏了」。
    #   ⟹ ⟹ 正解：用 **node --check** 把那段 JS 真的验一遍。
    import importlib.util
    import shutil
    import subprocess
    import tempfile
    node = shutil.which("node")
    if not node:
        print("★ 找不到 node ⟹ ⟹ 跳过 JS 语法自检（★ PATH 里没有 node）")
        return 0
    for rel in (P840, P841, P847):
        spec = importlib.util.spec_from_file_location("probe_mod_%s" % abs(hash(rel)),
                                                       ROOT / rel)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)          # ★ 只取常量 ⟹ ⟹ 不跑 main
        js = getattr(mod, "READ", None)
        if not js:
            print("✘ %s 里没有 READ 常量" % rel)
            return 2
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as f:
            f.write("(" + js + ");")
            tmp = f.name
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
        if r.returncode != 0:
            print("✘ %s 的 READ 段 JS 语法错：%s" % (rel, (r.stderr or "")[:300]))
            return 2
        print("✔ %s 的 READ 段 JS 语法通过" % rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())

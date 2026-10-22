#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 849：**第九次迁移** —— 把 842／843 两条门禁与两个探针的
「**第四段那一页内容未实测 ⟹ 显示如实说明**」断言
**翻成「那一页已实测并实现」**。

## 为什么必须改

★ batch 849 把第四段的「服装」「AI 生成」两页**实测并实现**了
⟹ ⟹ 842／843 的那条断言（点那两枚子页签 ⟹ 应当出现「**未实测**」说明）
⟹ ⟹ **照原样跑必然红** ⟹ ⟹ 必须改。
★ 实测：迁移前 **842 6/7（S6 红）／843 6/7（S6 红）** ⟹ ⟹ **恰好就是那一条**。

★ ★ **期望值跟着语义走**（★ 与第七、八次迁移同一个原则）：
  | 门禁 | 上一批的期望 | 本批的期望 | 为什么 |
  | --- | --- | --- | --- |
  | `842` | 「服装」页显示**未实测**说明 | 该页显示**实测出来的**小标题「服装」＋ **7 枚**分类 chip ＋ **24 张**服装卡，且**没有**「未实测」字样 | ★ 那一页**已经实测并实现**了 ⟹ ⟹ 继续写「未实测」是**假陈述** |
  | `843` | 「AI 生成」页显示**未实测**说明 | 该页显示**实测出来的**输入框 ＋「确认生成」，且**没有**「未实测」字样 | ★ 同上 |

★ ★ **「未实测的入口只显示如实说明、不编造控件」这条纪律没有变**
⟹ ⟹ 它现在由 **846** 承载（★ 846 盯的是第四段**第一页**「造型」的实现细节
⟹ ⟹ 且 846 自己的 S7 仍要求 README 写明「服装」「AI 生成」两页**当时**未实测
⟹ ⟹ ★ 那是 batch 846 当时的状态记录 ⟹ ⟹ 按规矩**保留原样**
⟹ ⟹ 并在 **batch 849 的 README** 里指向它）。

★ ★ **期望值不手打**：新期望的**文案与数量**都从**已入库的源站 raw**
（`source-848-p1.json`／`source-848-p2.json`）**机器提取**
（★ 提取脚本：`probes/gen849_data.py`）。

## 改了什么（**逐处精确替换** ⟹ ⟹ 不用正则乱扫）

| 文件 | 改动 |
| --- | --- |
| `clone842.py` | 读数里加 `服装页`（★ 小标题文字 ＋ 分类 chip 数 ＋ 服装卡数） |
| `clone843.py` | 读数里加 `AI页`（★ 有没有输入框 ＋ 有没有「确认生成」） |
| `verify-liblib-batch842.py` | S6 的期望与措辞翻成「已实现」 |
| `verify-liblib-batch843.py` | 同上（S6） |

★ ★ **两个探针加的字段**必须**互不重叠**：
`clone842` 加「**服装页**」（第四段第一枚子页签）⟹ ⟹ `clone843` 加「**AI页**」
（第四段第二枚子页签）⟹ ⟹ 各读各的 ⟹ ⟹ 阴性对照才能「每条只翻它自己那一条」。

## 用法

    python3 migrate849.py --dry-run   # 只核对锚点，**不写文件**
    python3 migrate849.py             # 真正改（并**逐处**校验唯一命中）
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]

P842 = "docs/research/liblib-canvas-batch842-2026-10-01/probes/clone842.py"
P843 = "docs/research/liblib-canvas-batch843-2026-10-01/probes/clone843.py"
G842 = "scripts/verify-liblib-batch842.py"
G843 = "scripts/verify-liblib-batch843.py"
G846 = "scripts/verify-liblib-batch846.py"
# ★ ★ **846 也要迁移**（★ 第九次迁移实际翻了**三条**，不是两条）：
#   846 的 S6 断言「点「服装」子页签 ⟹ 显示**如实说明** ＋ **没有**任何控件」
#   ⟹ ⟹ 本批把那页**实测并实现**了 ⟹ ⟹ 照原样跑必然红
#   ⟹ ⟹ ★ 实测确认：迁移前 846 **6/7（S6 红）**
RAW848_P1 = "docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p1.json"

# ★★ 每一项都是 (相对路径, [(旧串, 新串), ...]) ⟹ ⟹ **必须唯一命中**
EDITS = [
    # ── clone846.py：读第四段「服装」页的**实测内容**（★ 849 的选择器）──
    ("docs/research/liblib-canvas-batch846-2026-10-01/probes/clone846.py", [
        ("  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n",
         "  out['空态']=(()=>{const e=root.querySelector('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n"
         "  // ★★ **batch 849 起**：★ 第四段「服装」页**已实测并实现**\n"
         "  //   ⟹ ⟹ 846 的探针只读 846 自己的选择器 ⟹ ⟹ 这里**另读** 849 的那套\n"
         "  out['服装页']={\n"
         "    小标题文字:(()=>{const e=root.querySelector('[data-character-editor-outfit-clothes-title]');\n"
         "      return e?txt(e):null;})(),\n"
         "    分类chip数:root.querySelectorAll('[data-character-editor-outfit-clothes-chip]').length,\n"
         "    服装卡数:root.querySelectorAll('[data-character-editor-outfit-clothes-card]').length};\n"),
    ]),
    # ── verify-liblib-batch846.py：S6 的期望翻成「已实现」──
    (G846, [
        # ① 期望值：从**入库的源站 raw** 机器提取（★ 不手打）
        ("def build_expectations() -> dict:\n",
         "def clothes_expect() -> dict:\n"
         "    \"\"\"★ 从**入库的源站 raw**（848 的 p1）机器提取第四段「服装」页的期望。\n"
         "\n"
         "    ★ ★ 为什么**必须**机器提取：\n"
         "    #   「小标题文案」是「服装」、chip 数 ＝ 7、卡数 ＝ 24\n"
         "    #   ⟹ ⟹ 手打**可能**对 ⟹ ⟹ 但**改**了源站就会错 ⟹ ⟹ 而门禁要钉的是源站\n"
         "    \"\"\"\n"
         "    raw = read_json(RAW848_P1)\n"
         "    root = raw[\"★整棵子树\"]\n"
         "\n"
         "    def walk(n):\n"
         "        yield n\n"
         "        for k in n.get(\"c2\") or []:\n"
         "            yield from walk(k)\n"
         "\n"
         "    h3 = [n for n in walk(root)\n"
         "          if n.get(\"t\") == \"H3\" and (n.get(\"b\") or [0])[0] >= 1297]\n"
         "    if len(h3) != 1:\n"
         "        raise SystemExit(\"✘ P1 的小标题数 %d ≠ 1\" % len(h3))\n"
         "    chipbox = [n for n in walk(root)\n"
         "               if \"flex-wrap\" in (n.get(\"c\") or \"\") and \"gap-1.5\" in (n.get(\"c\") or \"\")]\n"
         "    if len(chipbox) != 1:\n"
         "        raise SystemExit(\"✘ P1 的 chip 容器数 %d ≠ 1\" % len(chipbox))\n"
         "    chips = [n for n in (chipbox[0].get(\"c2\") or []) if n.get(\"t\") == \"BUTTON\"]\n"
         "    grid = [n for n in walk(root) if \"grid-cols-3\" in (n.get(\"c\") or \"\")]\n"
         "    if len(grid) != 1:\n"
         "        raise SystemExit(\"✘ P1 的网格数 %d ≠ 1\" % len(grid))\n"
         "    cards = grid[0].get(\"c2\") or []\n"
         "    return {\n"
         "        \"小标题\": h3[0].get(\"x\"),\n"
         "        \"chip数\": len(chips),\n"
         "        \"卡数\": len(cards),\n"
         "    }\n"
         "\n"
         "\n"
         "def build_expectations() -> dict:\n"),
        # ② 期望表里加一项
        ("        \"★像素对照\": read_json(PIXDIFF).get(\"像素对照\"),\n",
         "        \"★像素对照\": read_json(PIXDIFF).get(\"像素对照\"),\n"
         "        # ★★ **batch 849 起**：★ 第四段「服装」页**已实测并实现**\n"
         "        #   ⟹ ⟹ S6 的期望翻成「显示的是**实测出来的**内容」\n"
         "        #   ⟹ ⟹ 期望值**从入库的源站 raw 机器提取**（★ 不手打）\n"
         "        \"_服装页期望\": clothes_expect(),\n"),
        # ③ 常量
        ("RAW841 = ROOT / \"docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json\"\n",
         "RAW841 = ROOT / \"docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json\"\n"
         "# ★★ **batch 849 起**：第四段「服装」页的期望值从这份 raw 机器提取\n"
         "RAW848_P1 = ROOT / \"docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p1.json\"\n"),
        # ④ 详情字典
        ("        \"★切到服装_空态说明\": (clothes.get(\"空态\") or \"\")[:80],\n"
         "        \"★切到服装_有控件吗\": bool(clothes.get(\"H3\") or clothes.get(\"chip\")\n"
         "                                   or clothes.get(\"色块\") or clothes.get(\"卡片\")),\n",
         "        \"★切到服装_空态说明\": (clothes.get(\"空态\") or \"\")[:80],\n"
         "        \"★切到服装_有控件吗\": bool(clothes.get(\"H3\") or clothes.get(\"chip\")\n"
         "                                   or clothes.get(\"色块\") or clothes.get(\"卡片\")),\n"
         "        # ★★ **batch 849 起**：★ 那一页**已经实测并实现**\n"
         "        \"★切到服装_实测小标题\": (clothes.get(\"服装页\") or {}).get(\"小标题文字\"),\n"
         "        \"★期望_服装页_小标题\": exp[\"_服装页期望\"][\"小标题\"],\n"
         "        \"★切到服装_实测chip数\": (clothes.get(\"服装页\") or {}).get(\"分类chip数\"),\n"
         "        \"★期望_服装页_chip数\": exp[\"_服装页期望\"][\"chip数\"],\n"
         "        \"★切到服装_实测卡数\": (clothes.get(\"服装页\") or {}).get(\"服装卡数\"),\n"
         "        \"★期望_服装页_卡数\": exp[\"_服装页期望\"][\"卡数\"],\n"),
        # ⑤ 断言
        ("         and bool(s6[\"★切到服装_空态说明\"])\n"
         "         and not s6[\"★切到服装_有控件吗\"]),\n",
         "         # ★★ **batch 849 起**：★ 那一页**已经实测并实现**\n"
         "         #   ⟹ ⟹ 断言翻成「显示的是**实测出来的**内容 ＋ **没有**「未实测」字样」\n"
         "         and s6[\"★切到服装_实测小标题\"] == s6[\"★期望_服装页_小标题\"]\n"
         "         and s6[\"★切到服装_实测chip数\"] == s6[\"★期望_服装页_chip数\"]\n"
         "         and s6[\"★切到服装_实测卡数\"] == s6[\"★期望_服装页_卡数\"]\n"
         "         and not s6[\"★切到服装_空态说明\"]),\n"),
        # ⑥ 措辞
        ("        \"★ 点「服装」子页签 ⟹ 显示**如实说明**（★ 那一页的控件**源站未实测** ⟹ ⟹ \"\n"
         "        \"**不编造**控件）⟹ ⟹ 且切过去后**没有**任何控件\" % exp[\"★源站滚动高\"],\n",
         "        \"★ 点「服装」子页签 ⟹ ★ **batch 849 起**：那一页**已实测并实现** ⟹ ⟹ \"\n"
         "        \"显示**实测出来的**小标题「%s」＋ **%d 枚**分类 chip ＋ **%d 张**服装卡，\"\n"
         "        \"且**没有**「未实测」字样（★ 期望值**从入库的源站 raw 机器提取**）\"\n"
         "        % (exp[\"★源站滚动高\"], exp[\"_服装页期望\"][\"小标题\"],\n"
         "           exp[\"_服装页期望\"][\"chip数\"], exp[\"_服装页期望\"][\"卡数\"]),\n"),
    ]),
    # ── clone842.py：读第四段「服装」页的**实测内容** ──
    (P842, [
        ("  out['空态']=(()=>{const e=q('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n",
         "  out['空态']=(()=>{const e=q('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n"
         "  // ★★ **batch 849 起**：★ 第四段「服装」页**已实测并实现**\n"
         "  //   ⟹ ⟹ 读它的**实测内容**（小标题 ＋ 分类 chip ＋ 服装卡）\n"
         "  out['服装页']={\n"
         "    小标题文字:(()=>{const e=q('[data-character-editor-outfit-clothes-title]');\n"
         "      return e?txt(e):null;})(),\n"
         "    分类chip数:root.querySelectorAll('[data-character-editor-outfit-clothes-chip]').length,\n"
         "    服装卡数:root.querySelectorAll('[data-character-editor-outfit-clothes-card]').length};\n"),
    ]),
    # ── clone843.py：读第四段「AI 生成」页的**实测内容** ──
    (P843, [
        ("  out['空态']=(()=>{const e=q('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n",
         "  out['空态']=(()=>{const e=q('[data-character-editor-empty]');\n"
         "    return e?txt(e):null;})();\n"
         "  // ★★ **batch 849 起**：★ 第四段「AI 生成」页**已实测并实现**\n"
         "  //   ⟹ ⟹ 读它的**实测内容**（输入框 ＋「确认生成」）\n"
         "  out['AI页']={\n"
         "    有输入框:Boolean(root.querySelector('[data-character-editor-outfit-ai-textarea]')),\n"
         "    有确认生成:Boolean(root.querySelector('[data-character-editor-outfit-ai-generate]'))};\n"),
    ]),
    # ── verify-liblib-batch842.py：S6 的期望翻成「已实现」──
    (G842, [
        # ① 期望值：从**入库的源站 raw** 机器提取（★ 不手打）
        ("    seg5 = rt.get(\"D2_第四段_服装\") or {}\n"
         "    seg5_empty = seg5.get(\"空态\")\n",
         "    seg5 = rt.get(\"D2_第四段_服装\") or {}\n"
         "    seg5_empty = seg5.get(\"空态\")\n"
         "    # ★★ **batch 849 起**：★ 第四段「服装」页**已实测并实现**\n"
         "    #   ⟹ ⟹ 期望**从入库的源站 raw 机器提取**（★ 不手打）\n"
         "    seg5_page = seg5.get(\"服装页\") or {}\n"
         "    exp_clothes = exp[\"_服装页期望\"]\n"),
        # ② 判据内容
        ("    s6_says_unmeasured = bool(seg5_empty and \"未实测\" in seg5_empty)\n"
         "    s6_says_measured = bool(seg5_empty and \"已实测\" in seg5_empty)\n",
         "    s6_says_unmeasured = bool(seg5_empty and \"未实测\" in seg5_empty)\n"
         "    s6_says_measured = bool(seg5_empty and \"已实测\" in seg5_empty)\n"
         "    # ★★ **batch 849 起**：★ 那一页**已经实测并实现**\n"
         "    #   ⟹ ⟹ 断言翻成「显示的是**实测出来的**内容 ＋ **没有**「未实测」字样」\n"
         "    s6_has_measured_title = (seg5_page.get(\"小标题文字\") == exp_clothes[\"小标题\"])\n"
         "    s6_has_measured_chips = (seg5_page.get(\"分类chip数\") == exp_clothes[\"chip数\"])\n"
         "    s6_has_measured_cards = (seg5_page.get(\"服装卡数\") == exp_clothes[\"卡数\"])\n"
         "    s6_no_unmeasured = not seg5_empty\n"),
        # ③ 详情字典
        ("        \"★第五段_空态说明里写了「未实测」\": s6_says_unmeasured,\n"
         "        \"★第五段_空态说明里写了「已实测」\": s6_says_measured,\n",
         "        \"★第五段_空态说明里写了「未实测」\": s6_says_unmeasured,\n"
         "        \"★第五段_空态说明里写了「已实测」\": s6_says_measured,\n"
         "        \"★第四段_服装页_小标题\": seg5_page.get(\"小标题文字\"),\n"
         "        \"★期望_服装页_小标题\": exp_clothes[\"小标题\"],\n"
         "        \"★第四段_服装页_分类chip数\": seg5_page.get(\"分类chip数\"),\n"
         "        \"★期望_服装页_分类chip数\": exp_clothes[\"chip数\"],\n"
         "        \"★第四段_服装页_服装卡数\": seg5_page.get(\"服装卡数\"),\n"
         "        \"★期望_服装页_服装卡数\": exp_clothes[\"卡数\"],\n"
         "        \"★第四段_服装页_没有未实测说明\": s6_no_unmeasured,\n"),
        # ④ 断言
        ("        (s6[\"★第五段_页签数\"] == 0 and s6[\"★第五段_滑杆数\"] == 0\n"
         "         and s6[\"★第五段_卡片数\"] == 0 and bool(seg5_empty)\n"
         "         and s6_says_unmeasured\n"
         "         and not s6[\"★第五段_空态说明里写了「已实测」\"]\n"
         "         and s6[\"★源站那趟_积分全程未变\"]),\n",
         "        (s6[\"★第五段_页签数\"] == 0 and s6[\"★第五段_滑杆数\"] == 0\n"
         "         and s6[\"★第五段_卡片数\"] == 0\n"
         "         and s6_has_measured_title and s6_has_measured_chips\n"
         "         and s6_has_measured_cards and s6_no_unmeasured\n"
         "         and not s6_says_unmeasured\n"
         "         and s6[\"★源站那趟_积分全程未变\"]),\n"),
        # ⑤ 措辞
        ("        \"S6 ★★★ **未实测的那一页仍是空态说明**（★ batch 847 起换靶：左列五段**全部实现**\"\n"
         "        \"⟹ ⟹ 「仍未实现的那一段」**没有靶子了** ⟹ ⟹ 改盯**第四段里那一页内容未实测的\"\n"
         "        \"子页签**（「服装」））⟹ **页签数 %d**（★ 源站实测：页签行**只在「脸部精修」段存在**）\"\n"
         "        \"＋ 滑杆 %d 条 ＋ 卡片 %d 张；★ 且文案**要**写「未实测」—— ★ 那一页的控件\"\n"
         "        \"**根本就没测过** ⟹ ⟹ 写「已实测」才是**假陈述**\"\n"
         "        % (s6[\"★第五段_页签数\"], s6[\"★第五段_滑杆数\"], s6[\"★第五段_卡片数\"]),\n",
         "        \"S6 ★★★ **第四段「服装」页已实测并实现**（★ batch 849 起：★ 那一页**已经实测并实现**\"\n"
         "        \"⟹ ⟹ 断言**翻成**「显示的是**实测出来的**内容 ＋ **没有**「未实测」字样」）\"\n"
         "        \"⟹ **页签数 %d**（★ 源站实测：页签行**只在「脸部精修」段存在**）\"\n"
         "        \"＋ 滑杆 %d 条 ＋ 卡片 %d 张；★ 小标题 ==「%s」＋ **%d 枚**分类 chip ＋ **%d 张**服装卡\"\n"
         "        \"（★ 期望值**从入库的源站 raw 机器提取**）\"\n"
         "        % (s6[\"★第五段_页签数\"], s6[\"★第五段_滑杆数\"], s6[\"★第五段_卡片数\"],\n"
         "            exp_clothes[\"小标题\"], exp_clothes[\"chip数\"], exp_clothes[\"卡数\"]),\n"),
    ]),
    # ── verify-liblib-batch843.py：S6 的期望翻成「已实现」──
    (G843, [
        ("    other = rt.get(\"D_第四段_AI生成\") or {}\n"
         "    back = rt.get(\"E_切回脸部精修\") or {}\n",
         "    other = rt.get(\"D_第四段_AI生成\") or {}\n"
         "    back = rt.get(\"E_切回脸部精修\") or {}\n"
         "    # ★★ **batch 849 起**：★ 第四段「AI 生成」页**已实测并实现**\n"
         "    other_page = other.get(\"AI页\") or {}\n"),
        ("        \"★第五段_空态说明\": other.get(\"空态\"),\n",
         "        \"★第五段_空态说明\": other.get(\"空态\"),\n"
         "        \"★第四段_AI页_有输入框\": other_page.get(\"有输入框\"),\n"
         "        \"★第四段_AI页_有确认生成\": other_page.get(\"有确认生成\"),\n"),
        ("        (s6[\"★第五段_页签数\"] == 0 and s6[\"★第五段_卡片数\"] == 0\n"
         "         and bool(s6[\"★第五段_空态说明\"]) and s6[\"★切回_页签数\"] == 6\n"
         "         and s6[\"★源站那趟_积分全程未变\"]),\n",
         "        (s6[\"★第五段_页签数\"] == 0 and s6[\"★第五段_卡片数\"] == 0\n"
         "         and s6[\"★第五段_空态说明\"] is None\n"
         "         and bool(s6[\"★第四段_AI页_有输入框\"])\n"
         "         and bool(s6[\"★第四段_AI页_有确认生成\"])\n"
         "         and s6[\"★切回_页签数\"] == 6\n"
         "         and s6[\"★源站那趟_积分全程未变\"]),\n"),
        ("        \"S6 ★★★ **结构事实**：源站实测**页签行只在「脸部精修」段存在** ⟹ ⟹ \"\n"
         "        \"点左列**第四段**（服装造型）⟹ 再点「AI 生成」子页签 ⟹ **页签数 %s** ＋ 0 张卡 ＋ 出现空态说明；切回「脸部精修」⟹ \"\n",
         "        \"S6 ★★★ **结构事实**：源站实测**页签行只在「脸部精修」段存在** ⟹ ⟹ \"\n"
         "        \"点左列**第四段**（服装造型）⟹ 再点「AI 生成」子页签 ⟹ **页签数 %s** ＋ 0 张卡 ＋ \"\n"
         "        \"★ **batch 849 起**：那一页**已实测并实现** ⟹ ⟹ 显示**实测出来的**输入框 ＋「确认生成」，\"\n"
         "        \"且**没有**「未实测」字样；切回「脸部精修」⟹ \"\n"),
    ]),
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    total = 0
    skipped = 0
    for rel, pairs in EDITS:
        p = ROOT / rel
        src = p.read_text(encoding="utf-8")
        for old, new in pairs:
            n = src.count(old)
            if n == 0:
                # ★ ★ **幂等**：★ 若**新串**已在 ⟹ ⟹ 说明这一处**已经迁过** ⟹ ⟹ 跳过
                #   ⟹ ⟹ ⟹ 否则「第二次跑迁移」会因为「旧串没了」而报错 ⟹ ⟹ 不可重放
                if src.count(new) >= 1:
                    skipped += 1
                    continue
                print("✘ %s：锚点命中 0 处（应为 1）\n%s" % (rel, old[:160]))
                return 2
            if n != 1:
                print("✘ %s：锚点命中 %d 处（应为 1）\n%s" % (rel, n, old[:160]))
                return 2
            total += 1
            if not dry:
                src = src.replace(old, new, 1)
        if not dry:
            p.write_text(src, encoding="utf-8")
            print("✔ 改了 %s（%d 处）" % (rel, len(pairs)))
    print("\n共 %d 处%s（跳过 %d 处已迁过的）"
          % (total, "（dry-run，未写文件）" if dry else "", skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())

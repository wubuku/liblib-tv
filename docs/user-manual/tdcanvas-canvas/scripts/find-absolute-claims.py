#!/usr/bin/env python3
"""找出读者页里所有带「绝对词」的句子（候选清单，**非门禁**）

用法：
    python3 scripts/find-absolute-claims.py .        # **默认：只报可证伪的那些（约 34 处，逐条能过）**
    python3 scripts/find-absolute-claims.py . --all  # 全部候选（400 处量级，精度很低，仅作覆盖面存档）

**它是什么**：M253 抓到两条错（R103「穷尽 9 种组合」漏了一档、R104「节点永远落在 16 的整数倍上」
缺两个前提），根因都是**把带条件的结论写成了不带条件的**。M253 同时留下一条判据：
「凡出现绝对词的句子，同页必须能找到它的开关或例外所在」。
**这条判据没法一步做成门禁**（§13.0 已经否掉过两种自动锚点设计），所以分两步：

1. **本脚本**：把候选句全部捞出来，**供人分类**。
2. `check-absolute-claims.py`（门禁）：只校验**手读建立的登记表**——
   每条绝对断言都要在**同一页**指得出它的限定词或例外，逐字命中才算过。

★ **所以本脚本的输出不是「有错的地方」，而是「需要人看一眼的地方」**——
它必然有大量误报（修辞用法、正确的绝对陈述），**把它的输出当缺陷清单用就是误用它**。

**★ 判据上的两个刻意选择（都是踩出来的）**：
- **只扫读者页，不扫账本**：`AUDIT.md` / `PROGRESS.md` / `SOURCE_OBSERVATIONS.md` /
  `PUBLISH.md` 本来就要原样引述旧说法（含已订正的绝对句），扫它们必然全是"命中"。
- **句子按中文句读切分，按行输出去重**：同一段引注块里同一句常跨行拼接，
  按行切会把一句话算成两半、从而漏掉限定词与被限定句的**同页**关系。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 绝对词表。**每一项都标了它在中文里最常见的另一种用法**——
# 分类时先看这一栏，能省掉大半误报。
ABSOLUTE_WORDS = {
    "永远": "「永远是它左边那个」这类指位置的说法不是断言；「节点永远落在…」是断言",
    "恒": "多与「为 / 定 / 等」连用（恒为 8 个）；也可能是「恒定」的省写",
    "穷尽": "几乎总是断言（穷尽 N 种），**这一档误报最少**",
    "一律": "断言或规定（删除一律回首页）",
    "从不": "断言（从不弹提示）",
    "任何": "**误报重灾区**：既可能是绝对断言（任何入口都没有），"
            "也可能是泛指（任何时候都可以）",
    "全部": "**误报重灾区**：既可能指「全应用全部 N 个」的计数断言，"
            "也可能是「把每条都点一遍」这类动作",
    "绝对": "多为修辞（绝对横坐标）；少数是真断言",
    "没有": "**误报重灾区**：「没有确认弹窗」是断言，「没有别的办法」是修辞",
    "任何时候": "常与「都可以 / 都一样」连用，多为泛指",
}

# 句读切分：中文句号/问号/叹号/分号 + 换行。**引号内的句读不切**——
# 引文里常有整句引用，拆开就没法判断限定词关系了。
SENT_SPLIT = re.compile(r"(?<=[。；！？])")
# 行内链接与图片要拿掉：它们的文字不是句子，切出来全是噪声
MARKUP = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
# 代码片段
CODE = re.compile(r"`[^`]*`")


def sentences(text: str) -> list[str]:
    out: list[str] = []
    for raw_line in text.split("\n"):
        line = MARKUP.sub("", raw_line)
        line = CODE.sub("〔代码〕", line)
        if line.lstrip().startswith(("|", "-", "*", ">", "#")) and "|" in line:
            # 表格行与列表行另行处理：整行作为一个「句」更实用
            out.append(line.strip())
            continue
        for piece in SENT_SPLIT.split(line):
            piece = piece.strip().strip(">").strip()
            if piece:
                out.append(piece)
    return out


# 「这句话有没有反例」的最窄判据：**句子里同时出现绝对词与一个数**。
#
# ★ **为什么只留这一类**（M254 实测）：全量扫描是 **404 处**，而其中绝大多数是
# 「没有确认弹窗」「不联网、不同步」这类**正确的绝对陈述**或修辞用法——
# **它们没有反例，也就无从证伪**，把它们列进清单只会让人放弃看。
# 而「N 个 / N 种 / 永远 N」这类**带数的绝对句**是唯一能被一个反例推翻的，
# 也正是 R103（漏了第 10 种）与 R104（前提缺了两个）撞上的那一种形状。
# ★ **M254 实测出来的收窄**（这是本工具最要紧的一处设计）：
#   全量扫描 404 处、只要求「含绝对词 + 含任意数字」仍有 287 处——
#   **绝大多数是「没有确认弹窗」「不联网、不同步」这类正确的绝对陈述**，
#   **它们没有反例，也就无从证伪**，列进清单只会让人放弃看。
#   收到 **「穷尽 / 恒 / 永远 / 一律」+「一个计数词」** 这 34 处之后，
#   清单才小到能逐条判断「它的限定词在哪、写得对不对」。
#   ★ **这又是 F55 的反面**：不是「量具覆盖得够不够」，是**「判据有没有收窄到它自称的那一类」**——
#   一个量出 287 的判据和一个量出 34 的判据，**用的是同一份文本、同一套切句逻辑**。
COUNTABLE = re.compile(r"[0-9]|[一二三四五六七八九十两百千万]")
# 只与计数搭配时才是断言的这几个词
COUNTING_ABSOLUTES = ("穷尽", "恒", "永远", "一律")
COUNT_UNIT = re.compile(
    r"[0-9]+\s*(?:个|种|条|项|档|张|款|处|行|页|步|次|倍|种)"
    r"|[一二三四五六七八九十两]\s*(?:个|种|条|项|档|张|款|处|行|页|步|次|倍|种)")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    scan_all = "--all" in sys.argv
    root = Path(args[0] if args else ".").resolve()
    targets = [root / "README.md", root / "00-quickstart.md", root / "20-reference.md",
               root / "30-concepts.md", root / "90-troubleshooting.md"]
    targets += sorted((root / "10-tasks").glob("*.md"))

    total = 0
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        # 句子 → 行号：按前缀匹配定位，**只取第一次出现**（重复句在前文已列过）
        used: set[int] = set()
        hits: list[tuple[int, str, list[str]]] = []
        for sent in sentences(text):
            words = [w for w in ABSOLUTE_WORDS if w in sent]
            if not words:
                continue
            if not scan_all:
                if not any(w in sent for w in COUNTING_ABSOLUTES):
                    continue
                if not COUNT_UNIT.search(sent):
                    continue
            ln = next((i + 1 for i, l in enumerate(lines)
                       if sent[:24] in l and (i + 1) not in used), None)
            if ln is None:
                continue
            used.add(ln)
            hits.append((ln, sent, words))
        if not hits:
            continue
        print(f"\n=== {path.relative_to(root)} · {len(hits)} 处 ===")
        for ln, sent, words in hits:
            total += 1
            mark = "、".join(words)
            snippet = sent if len(sent) <= 150 else sent[:150] + "…"
            print(f"  L{ln:<5} [{mark}] {snippet}")

    if not scan_all:
        print(f"\n合计 {total} 处**可证伪**候选（穷尽/恒/永远/一律 + 一个计数）。")
        print("★ 这类是唯一有反例的形状——R103 与 R104 撞上的就是它。")
        print("★ 仍然不是缺陷清单：这 34 条**绝大多数是对的**，"
              "要逐条判断的是「它的限定词在哪、写得对不对」。")
        print("★ 逐条结论要写进 `check-absolute-claims.py` 的登记表，"
              "**登记表才是门禁守的东西——本脚本的输出不是**。")
    else:
        print(f"\n合计 {total} 处候选（全量）。")
        print("★ **这是覆盖面存档，不是待办清单**——修辞用法与正确陈述占绝大多数。")
        print("★ 要干活请去掉 --all。")
    print("★ 分类后，只有「同页找不到它的开关或例外」的那几条要进 `check-absolute-claims.py` 的登记表。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

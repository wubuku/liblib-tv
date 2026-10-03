#!/usr/bin/env python3
"""可数断言台账一致性校验（第二十三道门禁，M199 新增）。

**背景（M199 的真实起因）**：手册把同一个数字在好几个页面重述——
「图片节点 13 个按钮」这一条事实在四个页面各出现一次，台账 21 条事实合起来
占了 52 处。**数字一多，改一处就一定会漏另一处**，而漏掉的那处不会报错，
只会安静地变成错的。M199 之前，只有截图和 `PROGRESS.md` 的批次记录能追到
某个数字的出处，**正文自己不带索引**。

本门禁守的是 `SOURCE_OBSERVATIONS.md` 的 13.1 台账，做且只做四件事：

1. **短语对不上**——有人改写了那句话却没更新台账（重述位置是逐字短语，
   不是行号也不是整句：行号会随上方任何编辑失效，整句会在改写措辞时失效）。
2. **数字对不上**——页面上的数字改了，台账里的实测值没改。
3. **条数对不上**——表头声明的条数／处数与表体实际行数不一致。
4. **结构坏掉**——ID 重复或写法不对、依据为空、某条一个重述位置都没有、
   重述位置指向了内部账本而不是对外发布页。

**它拦不住什么（这条必须写在门禁自己的文档字符串里，否则维护者会高估它）**：

M199 先试过做「覆盖率」门禁——扫描正文里所有可数断言、要求每一条都进台账。
**两个设计都被否掉了**，因为判据做不出「窄到能全对」（M195 立的规矩）：

* 锚点式（页 + 短语 + 邻近数字）：自动生成的锚点产出「具条和…翻遍」这类坏锚点，
  **只会造出假失败**。
* 字面量式（每条事实在每个重述页都必须出现「13 个按钮」这个句式）：R44 订正之后，
  Dock 的「8」落在表格单元格里，**会对正确文本报错**。

更要紧的是**漏检**：判据放宽到「任意数字 + 任意量词」，发布页里约 1700 处命中；
第一版那套窄判据只捞到 31 处，漏掉了「共 7 个：」「还有 7 个同样只有图标」
「列的是 **14 项**」「整页有 17 个可见按钮」这类真实断言，
还把「Dock 的第 2/3/4 个图标」这种**序数**当成了计数。

所以台账是**手读建立的**，本门禁只保证「已经进表的那 21 条不会悄悄跑偏」，
**不保证正文里的可数断言被穷尽**。详见 `SOURCE_OBSERVATIONS.md` 的 13.0。

用法：
    python3 scripts/check-fact-ledger.py .
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LEDGER_FILE = "SOURCE_OBSERVATIONS.md"
SECTION_HEAD = "### 13.1 台账本体"
SECTION_TAIL = "### 13.2"

# 台账只索引**对外发布页**。指向 PROGRESS / AUDIT / PUBLISH 的「重述位置」
# 等于把「我在账本里写过」当成「读者能查到的出处」——那不是本表要解决的问题。
BODY_PAGES = {
    "README.md",
    "00-quickstart.md",
    "20-reference.md",
    "30-concepts.md",
    "90-troubleshooting.md",
}
BODY_DIRS = ("10-tasks/",)

COUNT_RE = re.compile(r"本表共 \*\*(\d+) 条事实、(\d+) 处重述位置\*\*")
ROW_RE = re.compile(r"^\|\s*(?P<id>F\d{2})\s*\|(?P<stmt>[^|]*)\|(?P<ev>[^|]*)\|(?P<loc>[^|]*)\|\s*$")
SITE_RE = re.compile(r"`(?P<file>[^`]+)`「(?P<phrase>[^」]+)」")
ID_RE = re.compile(r"^F\d{2}$")


def is_published(rel: str) -> bool:
    if rel in BODY_PAGES:
        return True
    return any(rel.startswith(d) and rel.endswith(".md") for d in BODY_DIRS)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    src = root / LEDGER_FILE
    if not src.exists():
        print(f"[可数台账] 找不到 {LEDGER_FILE}")
        return 1
    text = src.read_text(encoding="utf-8")

    start = text.find(SECTION_HEAD)
    if start < 0:
        print(f"[可数台账] {LEDGER_FILE} 里找不到「{SECTION_HEAD}」小节。\n"
              "  本门禁守的就是这张表；它被改名时请同步修改本门禁，不要让它静默失效。")
        return 1
    end = text.find(SECTION_TAIL, start)
    body = text[start : end if end > 0 else len(text)]

    errs: list[str] = []

    m = COUNT_RE.search(body)
    if not m:
        errs.append("表体上方找不到「本表共 N 条事实、M 处重述位置」这句数量声明")
        declared = (None, None)
    else:
        declared = (int(m.group(1)), int(m.group(2)))

    rows = [mm for mm in (ROW_RE.match(l) for l in body.splitlines()) if mm]
    # ★ 表格单元格里不能出现字面 `|`，所以短语也不能带。一行以 `| F` 开头却解析不出来，
    #   几乎必然是重述位置里抄进了竖线。**指名报错，别让它悄悄少一行。**
    for line in body.splitlines():
        if re.match(r"^\|\s*F\d", line) and not ROW_RE.match(line):
            errs.append("台账行解析不了（列数不对）——多半是重述位置或依据里带了字面竖线："
                        + line.strip()[:80])
    sites_total = 0
    seen_ids: set[str] = set()

    for row in rows:
        fid = row.group("id")
        stmt = row.group("stmt").strip()
        ev = row.group("ev").strip()
        loc = row.group("loc")

        if not ID_RE.match(fid):
            errs.append(f"事实 ID 写法不合法：{fid}（应为 F + 两位数字，如 F01）")
        if fid in seen_ids:
            errs.append(f"事实 ID 重复：{fid}")
        seen_ids.add(fid)

        if not stmt:
            errs.append(f"{fid} 的陈述与实测值为空")
        if not ev or ev in {"-", "—", "待补", "TODO", "无"}:
            errs.append(f"{fid} 的依据为空或写成了占位词——**只给数字不给方法的条目不许进台账**")

        sites = [s for s in SITE_RE.finditer(loc)]
        if not sites:
            errs.append(f"{fid} 一个重述位置都没有——它要么该删，要么该补上「读者在哪儿能看到它」")
        sites_total += len(sites)

        nums = {int(c) for c in stmt if c.isdigit()}
        nums = {n for n in nums if 0 < n < 10000}
        hit_num = False

        for s in sites:
            rel = s.group("file").strip()
            phrase = s.group("phrase").strip()
            if not is_published(rel):
                errs.append(f"{fid} 的重述位置 {rel} 不是对外发布页——"
                            "本表索引的是读者能查到的出处，不是内部账本")
                continue
            path = root / rel
            if not path.exists():
                errs.append(f"{fid} 的重述位置指向不存在的文件：{rel}")
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            hit = [i + 1 for i, l in enumerate(lines) if phrase in l]
            if not hit:
                errs.append(f"{fid} 的重述位置短语在 {rel} 里找不到：{phrase!r}\n"
                            "    要么是那句被改写了（**连台账一起更新**），要么是短语抄错了。")
                continue
            if nums and any(any(str(n) in lines[i - 1] for n in nums) for i in hit):
                hit_num = True

        if nums and not hit_num:
            errs.append(f"{fid} 的实测值 {sorted(nums)} 在它的任何一处重述位置所在行里都没出现——"
                        "**页面上的数字和台账里的数字对不上**")

    if declared[0] is not None:
        if declared[0] != len(rows):
            errs.append(f"台账声明的条数与表体行数对不上：声明 {declared[0]} 条，表体 {len(rows)} 行")
        if declared[1] != sites_total:
            errs.append(f"台账声明的重述位置数与实际处数对不上：声明 {declared[1]} 处，表体 {sites_total} 处")

    if errs:
        print(f"[可数台账] {len(errs)} 处对不上：")
        for e in errs:
            print("  - " + e)
        print(
            "\n  改数字的顺序：先在 13.1 表里找到事实 ID → 按「重述位置」列逐处改正文 →\n"
            "  改完跑本门禁。**只改正文不同步台账，正是这道闸要拦的事。**"
        )
        return 1

    print(f"  [ ok ] 可数台账：{len(rows)} 条事实、{sites_total} 处重述位置，"
          f"短语逐字命中、实测值与所在行对得上")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

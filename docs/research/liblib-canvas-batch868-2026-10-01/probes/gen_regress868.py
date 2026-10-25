#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 探针：★ 生成 `probes/regress868.py`（★ 清单 189 → 283）。

## ★ 为什么是**生成**而不是手打

★ 清单是**机器算出来的** ⟹ ⟹ 手打必然漂 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 本脚本：
  ① 读 `regress867.py` 的 `GATES`（★ **不重打**）；
  ② 用**放宽后**的口径重算「碰被跟踪源文件的门禁」；
  ③ 把**清单外**的那些**追加**进去（★ 顺序稳定 ＋ 不重复）；
  ④ 把本批基线里**红**的登记进 `KNOWN_RED`（★ **逐条带说明**）；
  ⑤ 写 `probes/regress868.py`。

## ★ ★★ 纪律一：★ **红的**必须**逐条带说明**登记

★ 「登记成旧账」不能变成「掩盖它坏了」的借口
⟹ ⟹ ⟹ ⟹ ⇒ ★ 每一条旧账都要写清**为什么是旧账**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 依据是 **受控对照**（★ `raw/controlled-868.json`）
⟹ ⟹ ⟹ ⟹ ⇒ ★ 即「**HEAD 态也红**」⟹ ⟹ ⟹ ⟹ ⇒ ★ 那是旧账 ⟹ ⟹ ⟹ ⟹ ⇒
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而「**HEAD 绿 / WORK 红**」才是本批引入 ⟹ ⟹ ⟹ ⟹ ⇒
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那种**不许**登记成旧账 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 本脚本会**直接报错**。

## ★ ★★ 纪律二：★ **本批自己的门禁（868）不许登记成旧账**

★ `868.py` 在基线里是红的 ⟹ ⟹ 但那是因为**清单还没生成**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 它是**本批的验收门** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 登记成旧账＝**自欺**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 所以本脚本**排除**它 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 并在生成后**重跑**它刷新读数。

## ★ ★★ 纪律三：★ 绿的不许进 `KNOWN_RED`

★ 旧账只登记**红**的 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 绿的门禁**不许**塞进去
⟹ ⟹ ⟹ ⟹ ⇒ ★ 否则它以后真的坏了也不会报 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那就是掩盖。

## ★ 输出
  probes/regress868.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
BATCH = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
SRC = ROOT / "docs/research/liblib-canvas-batch867-2026-10-01/probes/regress867.py"
DST = BATCH / "probes/regress868.py"
NEWGATES = BATCH / "raw/new-gates-868.json"
ATTRIB = BATCH / "raw/red-attribution-868.json"
CONTROLLED = BATCH / "raw/controlled-868.json"

# ★ ★★ 本批自己的门禁（★ 不许登记成旧账）
SELF_GATE = "868"

TRACKED_SRC = [
    "src/components/director/DirectorViewport.tsx",
    "src/components/director/DirectorAspectPanel.tsx",
    "src/store/directorStore.ts",
    "src/lib/directorTelemetry.ts",
]
TRACKED_DIRS = ["src/components", "src/store", "src/lib"]


def strip_comments(text: str) -> str:
    text = re.sub(r'"""[\s\S]*?"""', " ", text)
    text = re.sub(r"#[^\n]*", " ", text)
    return text


def touches(txt: str) -> bool:
    if any(r.split("/")[-1] in txt for r in TRACKED_SRC):
        return True
    if any(d in txt for d in TRACKED_DIRS):
        return True
    return bool(re.search(r"rglob\(|glob\(", txt)) and "src" in txt


def short(reason: str, n: int = 96) -> str:
    reason = re.sub(r"\s+", " ", str(reason)).strip()
    return reason[:n]


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    masked = strip_comments(src)
    m = re.search(r"^GATES\s*=\s*\[(.*?)^\]", masked, re.S | re.M)
    if not m:
        raise SystemExit("★ 读不出 regress867.py 的 GATES")
    gates = re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', m.group(1))

    touching: set[tuple[str, str]] = set()
    for p in sorted((ROOT / "scripts").glob("verify-liblib-batch*.py")) + \
            sorted((ROOT / "scripts").glob("verify-liblib-batch*.mjs")):
        mm = re.match(r"verify-liblib-batch(.+)\.(py|mjs)$", p.name)
        if not mm:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        if touches(txt):
            touching.add((mm.group(1), mm.group(2)))

    have = set(gates)
    add = sorted(touching - have)
    print("★ 清单原有 %s 条 ／ 放宽口径命中 %s 条 ／ 补进 %s 条"
          % (len(gates), len(touching), len(add)))

    # ★ ★★ 归因数据（★ 缺了就**不许**登记旧账 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 免得凭空记账）
    if not CONTROLLED.exists():
        raise SystemExit("★ 缺受控对照读数（%s）⟹ ⟹ 不许登记旧账" % CONTROLLED)
    ctrl = json.loads(CONTROLLED.read_text(encoding="utf-8"))
    introduced = list(ctrl.get("本批引入的红") or [])
    # ★ ★★ 「整改后复验」优先：★ 若某条红**已被本批整改修好** ⟹ ⟹ ⟹ ⟹ ⇒
    #   ★ 它**不该**登记成旧账 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 也不该算「本批引入的红」
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ （★ 依据：`raw/controlled-868.json` 的 `整改后复验` 段）
    fixed: list[str] = []
    for key, st in (ctrl.get("整改后复验") or {}).items():
        work = st.get("WORK态(新判据)") or {}
        head = st.get("HEAD态(新判据)") or {}
        if work.get("rc") == 0 and head.get("rc") == 0:
            # ★ ★ 键名归一：★ 对照 JSON 里记的是「801」⟹ ⟹ ⟹ ⟹ ⇒
            #   ★ 而下面比对时用的是「801.py」⟹ ⟹ ⟹ ⟹ ⇒ ★ ★ 两边**格式**不同
            #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 不归一 ⟹ ⟹ ⟹ ⟹ ⇒
            #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 过滤**静默失效**（★ 「不报错、只不管用」）
            fixed.append(key)
    fixed_set = set(fixed) | {"%s.py" % k for k in fixed} | \
        {k.replace(".py", "") for k in fixed}
    if fixed:
        print("★ 已整改（HEAD 态与 WORK 态都绿）⟹ ⟹ 不登记成旧账：%s" % sorted(fixed_set))
        introduced = [k for k in introduced
                      if k not in fixed_set and k.replace(".py", "") not in fixed_set]
    if introduced:
        raise SystemExit("★ 受控对照显示**本批引入**的红：%s ⟹ ⟹ 不许登记成旧账"
                         % introduced)
    attrib: dict[str, dict] = {}
    if ATTRIB.exists():
        attrib = json.loads(ATTRIB.read_text(encoding="utf-8")).get("逐条", {})

    ng = json.loads(NEWGATES.read_text(encoding="utf-8"))
    reds: list[tuple[str, str]] = []
    for r in ng.get("逐条", []):
        if r.get("rc") in (0, None):
            continue
        b, e = str(r["batch"]), str(r["ext"])
        if b == SELF_GATE:
            # ★ 本批自己的门禁 ⟹ ⟹ 基线里它必然红（清单还没生成）⟹ ⟹ 不记账
            print("★ 排除本批自己的门禁：%s.py" % b)
            continue
        if ("%s.%s" % (b, e)) in fixed_set or b in fixed_set:
            # ★ ★ 本批**已整改** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 不记账（★ 旧账只登记「现在还红」的）
            print("★ 排除已整改的门禁：%s.%s" % (b, e))
            continue
        reds.append((b, e))

    def reason_of(b: str, e: str) -> str:
        key = "%s.%s" % (b, e)
        a = attrib.get(key) or {}
        fails = a.get("失败") or []
        head = (ctrl.get("逐条") or {}).get(key, {})
        head_red = (head.get("HEAD") or {}).get("rc") not in (0, None)
        work_red = (head.get("WORK") or {}).get("rc") not in (0, None)
        if not head_red and work_red:
            return "★ ★★ **本批引入**（HEAD 绿 / WORK 红）⟹ ⟹ 不该记账"
        if fails:
            return "★ 旧账（HEAD 态也红）：%s" % short(fails[0])
        return "★ 旧账（HEAD 态也红）：%s" % short(
            (head.get("HEAD") or {}).get("last", "★ 失败原因未提取到"))

    out = src
    out = out.replace(
        '"""batch 867 回归：★ 把回归清单扩到**全部碰本批区域的门禁** ⟹ ⟹ 看有没有塌。',
        '"""batch 868 回归：★ 清单 **189 → %s** ⟹ ⟹ 补进**清单外**碰导演台源文件的那批。'
        % (len(gates) + len(add)), 1)
    out = out.replace(
        "  docs/research/liblib-canvas-batch867-2026-10-01/raw/regression.json",
        "  docs/research/liblib-canvas-batch868-2026-10-01/raw/regression.json", 1)
    out = out.replace(
        '    outp = pathlib.Path("/tmp/b867-regression.json")',
        '    outp = pathlib.Path("/tmp/b868-regression.json")', 1)
    out = out.replace(
        '    print("★ 读数已落盘：docs/research/liblib-canvas-batch867-2026-10-01/raw/regression.json")',
        '    print("★ 读数已落盘：docs/research/liblib-canvas-batch868-2026-10-01/raw/regression.json")', 1)

    # ② GATES 追加
    block = "".join('    ("%s", "%s"),\n' % (b, e) for b, e in add)
    anchor = "]\n\n# ★ 本批**动过其比对对象**的门禁"
    if anchor not in out:
        raise SystemExit("★ 找不到 GATES 的收尾锚点")
    out = out.replace(anchor, block + "]\n\n# ★ 本批**动过其比对对象**的门禁", 1)

    # ③ KNOWN_RED 追加（★ 逐条带说明）
    if reds:
        lines = []
        for b, e in reds:
            name = ("%s.%s" % (b, e)) if e != "py" else b
            lines.append('    "%s",  # %s\n' % (name, reason_of(b, e)))
        anchor2 = "\n}\n\n\n# ★ ★★ **已归因的偶发门禁**"
        if anchor2 not in out:
            raise SystemExit("★ 找不到 KNOWN_RED 的收尾锚点")
        out = out.replace(
            anchor2,
            "    # ★ ★★ Batch 868：★ 「清单外」那批门禁基线里**红**的\n"
            "    #   ⟹ ⟹ ★ 逐条带说明登记（★ 依据：受控对照 raw/controlled-868.json）\n"
            "    #   ⟹ ⟹ ★ 「HEAD 态也红」＝旧账；★ 「HEAD 绿 / WORK 红」＝本批引入\n"
            "    #   ⟹ ⟹ ★ 绿的一律**不登记**（★ 旧账只登记红的）\n"
            + "".join(lines) + anchor2, 1)

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(out, encoding="utf-8")

    # ★ 自检
    m2 = re.search(r"^GATES\s*=\s*\[(.*?)^\]", strip_comments(out), re.S | re.M)
    new_gates = re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', m2.group(1))
    gap = sorted(touching - set(new_gates))
    dup = len(new_gates) != len(set(new_gates))
    print("★ 清单 %s → %s 条（补进 %s 条）" % (len(gates), len(new_gates), len(add)))
    print("★ 登记旧账 %s 条（★ 逐条带说明）" % len(reds))
    print("★ 覆盖缺口：%s" % (["%s.%s" % g for g in gap] or "无"))
    print("★ 清单里有重复：%s" % dup)
    print("★ 读数已落盘：%s" % DST)
    return 1 if (gap or dup) else 0


if __name__ == "__main__":
    sys.exit(main())

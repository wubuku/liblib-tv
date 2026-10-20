#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1012 修复的**阳性对照**：把新判据逐个弄坏，确认它们**会红**。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**背景**：1032 批发现 1012 的 `P1_hold_2012` / `P9_hold_2012` **一直是红的**，
而 1015 批的改写横幅早就写下了「分母 187 已经过期」——
**但那条横幅只是文字，没改判据；而且红绿只写在 `/tmp` 的 out 里 ⇒ 没有任何门看它**
⇒ 一条判据红了半年没人知道。

⇒ 本脚本回答的问题是：**修好之后，这两条判据真的有牙吗？**
⇒ 「P1..P9 全 True」本身**不能**回答这个问题 —— **恒真的判据也全 True**。

做法（照 1032 门 P4 的做法：**注入式变异必红**）：
  · 把 1012 探针**复制**到临时目录（**不改真源** —— 1032 批的教训：
    「测试不许改真源」，第一版 self-test 照写不误，跑一次就把真白名单写坏了）；
  · 在副本里把 `ROOT` / `GOLDEN` / `OUT` 三个路径改到临时处
    ⇒ **副本碰不到真仓的 golden**（否则变异体会把坏 golden 写回仓里）；
  · 注入变异后跑副本，读它打印的 `P1..P9 = [...]`。

| 变异 | 期望 | 它证明什么 |
|---|---|---|
| 阴性对照（未变异） | P 全 True | 前提成立：1012 本身是绿的 |
| **M1**：P1 的恒等式改错（`len(PV) - 1` → `len(PV)`） | **P1 假** | 新 P1 **不是恒真** |
| **M2**：拆掉「历史变量数」这个出处来源 | **P9 假** | P9 的绿**确实依赖**历史来源 ⇒ P9 有牙 |
| **M3**：拆掉「仓库批次号」这个出处来源 | **P9 仍绿** | ⭐ 见下面「两个来源重叠」 |

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「两个来源重叠」—— 第一版自检在这里红了，而红的是「我的期望」**
  第一版把 M3 的期望写成「P9 必须假」，跑出来 P9 仍绿 ⇒ 自检报 FAILED。
  ⇒ 回头查，**不是判据没牙，是我的期望从一开始就不可能成立**：
  ⇒ ⇒ 「历史来源」（git 里每一版 audit 的 `global_detection_2012` 块）
  ⇒ ⇒ **已经覆盖了 1013 / 1014 / 1015 这三个批次号**（1015 批的改写横幅里写着它们）
  ⇒ ⇒ ⇒ 所以拆掉「批次号来源」之后，P9 仍能找到出处 ⇒ ⇒ ⇒ **P9 仍绿**
  ⇒ ⇒ ⇒ 而「历史变量数」（186 / 187 / 190）**只能**由历史来源覆盖
  ⇒ ⇒ ⇒ ⇒ 批次号来源**够不着**它们 ⇒ ⇒ ⇒ ⇒ 所以 M2 一拆，P9 必红。
  ⇒ ⇒ ⇒ ⇒ **⇒ 结论：P9 的绿由「历史来源」承重；「批次号来源」当前是冗余的。**
  ⇒ ⇒ ⇒ ⇒ ⇒ 它仍然值得留着：历史不可用（git 不可用 / 历史被裁剪）时，
  ⇒ ⇒ ⇒ ⇒ ⇒ 它是批次号的唯一出处 —— 但那时 P9 仍应为**降级 null**（不是红）。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **⇒ 这也逼出 1012 的第二处修**：
  历史来源不可用时，audit 文案里的历史变量数**必然**无出处 ⇒ P9 **必然红**
  ⇒ ⇒ 而那是**仪器没到位**，不是「文案里的数没有出处」⇒ ⇒ ⇒ **降级不是红**
  ⇒ ⇒ ⇒ 所以 P9 在那种情形下记 `null`，且 `hold_verdicts` 里**原样保留 `null`**
  ⇒ ⇒ ⇒ （写成 `bool(None)` 就是 `False` ⇒ 把「仪器没到位」伪装成「判据为假」）。

⚠️⭐⭐⭐⭐⭐ **每一步替换都断言「替换确实发生」** ——
  否则「变异没注入 ⇒ 门照常绿 ⇒ 误判成『门有牙』」⇒ 假阴性。

⚠️⭐⭐⭐⭐⭐ **阴性对照来自 1012 自己的产物**（`/tmp/b1012-global-detection.json`）
  —— 不重跑一遍 1012 来做对照：
  因为两个变异体各要 ~110s，再加一次阴性对照就超过 1015 通道 B 的 300s 超时。
  ⇒ 而 1015 通道 B 按文件名排序跑 ⇒ `jimeng_probe1012_global_detection.py`
  ⇒   **排在** `jimeng_probe1012_mutation_selfcheck.py` **之前** ⇒ 产物一定在。
  ⇒ 单独手跑时若产物不存在 ⇒ 本脚本只跑 M1 并明确标注「P9 自检降级未跑」。
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "scripts/jimeng_probe1012_global_detection.py"
PY = sys.executable
OUT1012 = Path("/tmp/b1012-global-detection.json")

MUT_P1 = ("M1 P1 恒等式改错", "N_OTHER_VARS == len(PV) - 1", "N_OTHER_VARS == len(PV)")
MUT_HIST = ("M2 拆掉历史变量数来源", "    _allowed |= _HIST_NUMS", "    pass  # MUT")
MUT_BATCH = ("M3 拆掉仓库批次号来源", "_allowed |= _batch_numbers_in_repo()",
             "pass  # MUT")

RE_ROOT = re.compile(r"^ROOT = Path\(__file__\)\.resolve\(\)\.parent\.parent$", re.M)
RE_GOLDEN = re.compile(
    r'^GOLDEN = ROOT / "docs/research/jimeng-canvas/global-detection-1012\.json"$', re.M)
RE_OUT = re.compile(r'^OUT = "/tmp/b1012-global-detection\.json"$', re.M)


def build_variant(tmp, muts):
    """复制探针到 tmp 并注入变异；每一步替换都断言确实发生。"""
    txt = SRC.read_text(encoding="utf-8")
    txt, n = RE_ROOT.subn('ROOT = Path(r"%s")' % ROOT, txt)
    assert n == 1, "ROOT 行没匹配上（源文件变形了，变异体无效）"
    txt, n = RE_GOLDEN.subn('GOLDEN = Path(r"%s")' % (tmp / "golden.json"), txt)
    assert n == 1, "GOLDEN 行没匹配上"
    txt, n = RE_OUT.subn('OUT = r"%s"' % (tmp / "out.json"), txt)
    assert n == 1, "OUT 行没匹配上"
    for label, old, new in muts:
        assert old in txt, "变异点没找到：%s（%r）" % (label, old)
        assert txt.count(old) == 1, "变异点不唯一：%s" % label
        txt = txt.replace(old, new)
    p = tmp / "probe1012_mutant.py"
    p.write_text(txt, encoding="utf-8")
    return p


def run_variant(p, timeout=280):
    """跑变异体并解析 `P1..P9 = [...]`；拿不到读数就是仪器坏了（不是红）。"""
    try:
        r = subprocess.run([PY, str(p)], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"
    m = re.search(r"P1\.\.P9 = \[([^\]]*)\]", r.stdout)
    if not m:
        return None, "NO_PARSE rc=%d err=%s" % (r.returncode, (r.stderr or "")[-300:])
    vals = []
    for x in m.group(1).split(","):
        x = x.strip().lower()
        if x == "true":
            vals.append(True)
        elif x == "false":
            vals.append(False)
        else:
            vals.append(None)      # ⭐ 降级（null）必须与「红（False）」分开
    return vals, "rc=%d n=%d" % (r.returncode, len(vals))


def read_baseline():
    """阴性对照：读 1012 自己产出的 P 数组（它跑过 ⇒ 文件在）。"""
    if not OUT1012.exists():
        return None
    try:
        import json
        d = json.loads(OUT1012.read_text(encoding="utf-8"))
    except Exception:
        return None
    vals = []
    for i in range(1, 10):
        v = d.get("P%d_hold_2012" % i)
        vals.append(None if v is None else bool(v))
    return vals if len(vals) == 9 else None


def main():
    rows = []
    base = read_baseline()
    if base is None:
        rows.append(("阴性对照(1012 自己的产物)", None, "DEGRADED: 没找到 %s" % OUT1012,
                     "跳过（降级不是红）"))
    else:
        ok = all(v is True for v in base)
        rows.append(("阴性对照(1012 自己的产物)", base,
                     "P 全 True" if ok else "P 有假/降级（⇒ 1012 本身就没绿，自检无意义）",
                     "OK" if ok else "FAIL"))
        if not ok:
            print("FATAL: 1012 自己就不是全绿 ⇒ 本自检的前提不成立")
            print("SELFCHECK_1012 -> FAILED")
            sys.exit(1)

    def variant(label, muts, want_false, want_true):
        with tempfile.TemporaryDirectory(prefix="p1012selfcheck-") as td:
            tmp = Path(td)
            vals, info = run_variant(build_variant(tmp, muts))
            if vals is None:
                rows.append((label, None, info, "FAIL（变异体没跑出读数）"))
                return
            bad = []
            for i in want_false:
                if vals[i] is not False:
                    bad.append("P%d 应假却是 %s" % (i + 1, vals[i]))
            for i in want_true:
                if vals[i] is not True:
                    bad.append("P%d 应真却是 %s" % (i + 1, vals[i]))
            rows.append((label, vals, info,
                         "OK" if not bad else "FAIL(" + "; ".join(bad) + ")"))

    # 变体 A：M1 + M2 ⇒ P1 必须假、P9 必须假
    #   ⇒ 「P9 的绿依赖历史来源」⇒ P9 有牙（不是恒真）
    variant("变体A (M1+M2)", [MUT_P1, MUT_HIST], [0, 8], [])
    # 变体 B：M1 + M3 ⇒ P1 必须假、P9 **必须仍绿**
    #   ⇒ 因为历史来源已经覆盖了 1013/1014/1015 ⇒ 拆掉批次号来源不影响出处
    #   ⇒ ⇒ 这是「归因结果」：批次号来源当前**冗余**（承重的是历史来源）
    variant("变体B (M1+M3)", [MUT_P1, MUT_BATCH], [0], [8])

    print("=" * 100)
    for label, vals, info, verdict in rows:
        shown = ("[%s]" % ",".join("T" if v is True else ("F" if v is False else "N")
                                   for v in vals)) if vals else "[]"
        print("%-26s %-14s %-40s %s" % (label, shown, info, verdict))
    print("=" * 100)

    failed = [r for r in rows if r[3].startswith("FAIL")]
    if failed:
        print("SELFCHECK_1012 -> FAILED (n_failed=%d)" % len(failed))
        sys.exit(1)
    print("SELFCHECK_1012 -> PASSED (n_variants=2, 阴性对照=%s)"
          % ("有" if base is not None else "降级未取到"))
    sys.exit(0)


if __name__ == "__main__":
    main()

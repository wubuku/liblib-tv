#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★ batch 869 负控：★ 证明门禁 `869` 的判据**有牙**。

## ★ ★★ 归因方式：**红灯集合差分**（★ 不是「跑出来是红就算」）

★ Batch 866 记过的坑：★ 变异层失败时源码不复原 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 门禁带着污染退出。
★ Batch 868 记过的坑：★ 负控没打红 ⟹ ⟹ ⟹ ⟹ ⇒ ★ **先查变异落点**、再怀疑判据。

★ ★★ 但**光看「跑出来是红」还不够** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 因为门禁**本来就有几条红**
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★（★ 例如「负控证据在库」那条 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 负控还没跑完时它必然红）
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ ⟹ 「恒红」与「因为变异而红」**长得一样**。
★ ⇒ 本脚本的判据是：
★   ★ 目标判据在**变异前**的红色集合里**不出现**（★ 变异前它是绿的），
★   ★ 在**变异后**的红色集合里**出现**（★ 变异把它打红了）。
★ ⇒ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 这叫「**该判据从绿变红**」⟹ ⟹ ⟹ ⟹ ⇒ ★ 才是真归因。

## ★ 每条负控都必须**复原源码**（★ 字节级）

★ ⇒ 用 `try/finally` ⟹ ⟹ **无条件**复原 ⟹ ⟹ 且复原后做**字节级**自检
★ （sha256 逐字比对）⟹ ⟹ 并在**最后**再全量比一遍（★ 跨文件污染守卫）。

## ★ ★★ 变异必须落在【被断言读的那个量】上

★ 本脚本每条都**写明**：★ 门禁的**哪一条判据** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 读**哪个量**
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 变异就动那里。

## ★ 负控清单

| # | 类别 | 变异 | 被测判据 | 读的是哪个量 |
| --- | --- | --- | --- | --- |
| N1 | 源码 | 命中窗口常量 `0.05` → `0.001` | S5 | `DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW` 的值 |
| N2 | 源码 | upsert 容差 `1e-3` → `0.05` | S6 | `DIRECTOR_KEYFRAME_EPSILON` 的值 |
| N3 | 源码 | 时间轴中键改回裸的 `Math.abs(...) <= 0.001` | S8 | 两个 UI 文件里**剥注释后**的 `0.001`／`1e-3` |
| N4 | 源码 | 工具条「添加关键帧」改回切换语义 | S9 | 工具条块里有没有 `addTimelineKeyframe` |
| N5 | 源码 | `866.py` 的动态解析改回写死清单 | S14 | `866.py` 里有没有 `resolve_live_regress` |
| N6 | 证据 | 把运行时读数文件挪走 | S10 | `raw/keyframe-window-869.json` 在不在库 |
| N7 | 证据 | 把读数里 W1 的 `通过` 改成 `false` | S10 | 读数里每条判据的 `通过` |
| N8 | ★运行时 | 把命中窗口改回 `0.001` ⟹ ⟹ ⟹ ⟹ ⇒ ★ **跑探针** | 探针 13 条 | ★ 探针**实测**出来的窗口内外读数 |

★ ★★ **N8 是本批最重要的一条**：★ 它证明的不只是「门禁能红」⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 而是「**那 13 条运行时判据真的在测那个窗口**」⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ 如果
★ ⟹ ⟹ ⟹ ⟹ 探针的判据是**恒真**的（★ 比如写成「有 aria-label 就过」）
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那改回 1e-3 之后它**照样全绿** ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★ N8 就抓不到
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★ 所以 N8 是「**判据有牙**」的直接证据。

## ★ 输出
  raw/negative-audit-869.json
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
BATCH = ROOT / "docs/research/liblib-canvas-batch869-2026-10-01"
OUT = BATCH / "raw/negative-audit-869.json"
GATE = ROOT / "scripts/verify-liblib-batch869.py"
PROBE = BATCH / "probes/keyframe_window869.py"

# ★ ★★ 本批负控会碰的文件（★ 结束后必须**逐字节**回到这里的样子）
MUTATED_FILES = [
    "src/components/director/directorKeyframeWindow.ts",
    "src/components/director/DirectorTimeline.tsx",
    "scripts/verify-liblib-batch866.py",
    "docs/research/liblib-canvas-batch869-2026-10-01/raw/keyframe-window-869.json",
]

RE_NAME = re.compile(r"^\s*FAIL\s+(\S+)\s*$")
RE_CRASH = re.compile(r"Traceback \(most recent call last\)|"
                      r"^\s*\w*Error:", re.M)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate() -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True,
                       text=True, timeout=900, cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def run_probe(out_path: pathlib.Path) -> tuple[int, str]:
    env = dict(os.environ)
    env["KEYFRAME_WINDOW_OUT"] = str(out_path)
    r = subprocess.run([sys.executable, str(PROBE)], capture_output=True,
                       text=True, timeout=900, cwd=str(ROOT), env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def red_names(output: str) -> list[str]:
    """★ 从门禁输出里抽出**红了的那几条判据的名字**（★ 不是「有几行红」）。"""
    names = []
    for ln in output.splitlines():
        m = RE_NAME.match(ln)
        if m:
            names.append(m.group(1))
    return names


def crashed(output: str) -> bool:
    return bool(RE_CRASH.search(output))


def sub_once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError("★ needle 命中 %d 次（⟹ 必须恰好 1 次）⟹ ⟹ %r"
                           % (n, old))
    return text.replace(old, new)


def main() -> int:
    baseline = {rel: sha(ROOT / rel) for rel in MUTATED_FILES}
    results: list[dict] = []
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="neg869-"))

    # ★ ★★ 探针基线（★ 变异前跑一次 ⟹ ⟹ ⟹ ⟹ ⇒ ★ N8 才能做「从全绿变成有红」）
    probe_base_path = tmpdir / "probe-baseline.json"
    pcode, poutput = run_probe(probe_base_path)
    pbase = (json.loads(probe_base_path.read_text(encoding="utf-8"))
             if probe_base_path.exists() else {})
    pbase_fail = [c["判据"] for c in (pbase.get("判据") or []) if not c.get("通过")]
    print("★ 探针基线：退出码 %s，失败 %d 条" % (pcode, len(pbase_fail)))
    if pcode != 0:
        print("  ★ ★ 基线探针**自己就红** ⟹ ⟹ ⟹ ⇒ ★ N8 无从判「从绿变红」")
        print(poutput[-2000:])

    def case(name: str, kind: str, target: str, criterion: str,
             quantity: str, mutate, expect_runtime: bool = False) -> None:
        rel = target
        path = ROOT / rel
        before = path.read_bytes() if path.exists() else None
        row = {"负控": name, "类别": kind, "改哪个文件": rel,
               "被测判据": criterion, "读的是哪个量": quantity}
        try:
            if expect_runtime:
                # ★ ★★ 变异**必须真的落到文件上** ⟹ ⟹ ⟹ ⇒ ★ 否则探针跑的是
                #   ⟹ ⟹ ⟹ ⟹ 未变异的代码 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 必然「全绿」⟹ ⟹ ⟹ ⟹ ⇒ ★
                #   ⟹ ⟹ ⟹ ⟹ 而且**表面上完全看不出异常**（★ 退出码 0、★ 输出干净）
                mutate(path)
                outp = tmpdir / ("probe-%s.json" % re.sub(r"\W+", "_", name))
                code, output = run_probe(outp)
                data = (json.loads(outp.read_text(encoding="utf-8"))
                        if outp.exists() else {})
                after_fail = [c["判据"] for c in (data.get("判据") or [])
                              if not c.get("通过")]
                row["探针退出码"] = code
                row["探针基线失败判据"] = pbase_fail
                row["探针变异后失败判据"] = after_fail
                row["从绿变红的探针判据数"] = len(
                    [c for c in after_fail if c not in pbase_fail])
                row["通过"] = bool(code != 0 and after_fail
                                   and row["从绿变红的探针判据数"] > 0)
            else:
                _bcode, bout = run_gate()
                base_red = red_names(bout)
                mutate(path)
                code, output = run_gate()
                after_red = red_names(output)
                row["变异前红"] = base_red
                row["变异后红"] = after_red
                row["门禁退出码"] = code
                row["★ 归因"] = {
                    "目标判据变异前是绿的": criterion not in base_red,
                    "目标判据变异后红了": criterion in after_red,
                    "门禁崩了": crashed(output),
                }
                row["通过"] = bool(code != 0 and criterion not in base_red
                                   and criterion in after_red)
        except BaseException as exc:  # ★ 变异层自己失败 ⟹ ⟹ ⟹ ⇒ ★ 也算没打红
            row["通过"] = False
            row["异常"] = "%s: %s" % (type(exc).__name__, exc)
        finally:
            if before is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(before)
            row["复原后 sha 一致"] = (path.exists()
                                      and sha(path) == baseline.get(rel))
        results.append(row)
        print("  %s %s（%s）" % ("PASS" if row["通过"] else "FAIL",
                                  name, kind))
        if not row["通过"]:
            print("      证据：%s" % json.dumps(row, ensure_ascii=False)[:1500])

    # ── N1：命中窗口常量改回 1e-3 ────────────────────────────────────
    def m1(path: pathlib.Path) -> None:
        t = path.read_text(encoding="utf-8")
        t = sub_once(t,
                     "export const DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW = 0.05;",
                     "export const DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW = 0.001;")
        path.write_text(t, encoding="utf-8")

    case("N1-命中窗口改回1e-3", "源码",
         "src/components/director/directorKeyframeWindow.ts",
         "source:the-shared-window-constant-equals-the-source-number",
         "DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW 的值", m1)

    # ── N2：两个容差改成同一个数 ──────────────────────────────────────
    def m2(path: pathlib.Path) -> None:
        t = path.read_text(encoding="utf-8")
        t = sub_once(t, "export const DIRECTOR_KEYFRAME_EPSILON = 1e-3;",
                     "export const DIRECTOR_KEYFRAME_EPSILON = 0.05;")
        path.write_text(t, encoding="utf-8")

    case("N2-两个容差混成同一个数", "源码",
         "src/components/director/directorKeyframeWindow.ts",
         "source:the-hit-window-and-the-upsert-epsilon-are-different-numbers",
         "DIRECTOR_KEYFRAME_EPSILON 的值", m2)

    # ── N3：时间轴中键改回裸的 1e-3 命中判据（★ 行数中性）───────────
    def m3(path: pathlib.Path) -> None:
        t = path.read_text(encoding="utf-8")
        old = ("const keyframe = track.keyframes.find((item) =>\n"
               "                                    directorKeyframeHit(\n"
               "                                      item.time,\n"
               "                                      timeline.currentTime,\n"
               "                                    ),\n"
               "                                  );")
        new = ("const keyframe = track.keyframes.find((item) =>\n"
               "                                    Math.abs(\n"
               "                                      item.time - timeline.currentTime,\n"
               "                                    ) <= 0.001,\n"
               "                                  );")
        t = sub_once(t, old, new)
        path.write_text(t, encoding="utf-8")

    case("N3-时间轴塞回裸0.001命中判据", "源码",
         "src/components/director/DirectorTimeline.tsx",
         "source:the-timeline-and-the-inspector-carry-no-bare-hit-epsilon",
         "两个 UI 文件里**剥注释后**的 0.001／1e-3", m3)

    # ── N4：工具条改回切换语义 ──────────────────────────────────────
    def m4(path: pathlib.Path) -> None:
        t = path.read_text(encoding="utf-8")
        t = sub_once(t, "onClick={() => addTimelineKeyframe()}",
                     "onClick={() => toggleTimelineKeyframe()}")
        path.write_text(t, encoding="utf-8")

    case("N4-工具条改回切换语义", "源码",
         "src/components/director/DirectorTimeline.tsx",
         "source:the-toolbar-add-keyframe-stays-an-upsert",
         "工具条块里有没有 addTimelineKeyframe", m4)

    # ── N5：866 门禁的动态解析改回写死 ───────────────────────────────
    def m5(path: pathlib.Path) -> None:
        t = path.read_text(encoding="utf-8")
        t = sub_once(t, "def resolve_live_regress()", "def _disabled_resolver()")
        t = sub_once(
            t,
            "live_regress, gates, prev_regress = resolve_live_regress()",
            'live_regress, gates, prev_regress = HISTORIC_REGRESS, '
            'parse_gates(HISTORIC_REGRESS.read_text(encoding="utf-8")), None')
        path.write_text(t, encoding="utf-8")

    case("N5-866改回写死回归清单", "源码",
         "scripts/verify-liblib-batch866.py",
         "source:the-regression-list-resolves-the-live-one-dynamically",
         "866.py 里有没有 resolve_live_regress", m5)

    # ── N6：把运行时读数挪走 ─────────────────────────────────────────
    def m6(path: pathlib.Path) -> None:
        path.unlink()

    case("N6-运行时读数挪走", "证据",
         "docs/research/liblib-canvas-batch869-2026-10-01/raw/keyframe-window-869.json",
         "runtime:the-keyframe-window-probe-readings-are-in-the-repo",
         "raw/keyframe-window-869.json 在不在库", m6)

    # ── N7：把读数里 W1 改成红 ───────────────────────────────────────
    def m7(path: pathlib.Path) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("判据") or []:
            if row.get("判据", "").startswith("W1:"):
                row["通过"] = False
                break
        else:
            raise RuntimeError("读数里找不到 W1 判据")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    case("N7-读数里W1改成红", "证据",
         "docs/research/liblib-canvas-batch869-2026-10-01/raw/keyframe-window-869.json",
         "runtime:the-keyframe-window-probe-readings-are-in-the-repo",
         "读数里每条判据的『通过』", m7)

    # ── N8：★ 运行时负控（★ 改回 1e-3 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 探针必须报红）─────
    def m8(path: pathlib.Path) -> None:
        t = path.read_text(encoding="utf-8")
        t = sub_once(t,
                     "export const DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW = 0.05;",
                     "export const DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW = 0.001;")
        path.write_text(t, encoding="utf-8")

    case("N8-★运行时负控：窗口改回1e-3后探针必须报红", "运行时",
         "src/components/director/directorKeyframeWindow.ts",
         "探针 13 条（W1/W2/W3/W5/W7/W8…）",
         "★ 探针**实测**出来的窗口内外读数", m8, expect_runtime=True)

    # ── 跨文件污染守卫 ───────────────────────────────────────────────
    after = {rel: sha(ROOT / rel) for rel in MUTATED_FILES if (ROOT / rel).exists()}
    polluted = [rel for rel in MUTATED_FILES
                if after.get(rel) != baseline.get(rel)]
    print("★ 跨文件污染守卫：%s" % ("干净" if not polluted else "污染 %s" % polluted))
    if polluted:
        results.append({"负控": "跨文件污染守卫", "类别": "守卫",
                        "通过": False, "证据": {"污染文件": polluted}})

    bad = [r for r in results if not r.get("通过")]
    OUT.write_text(json.dumps(
        {"负控": results, "失败数": len(bad), "总条数": len(results),
         "探针基线失败判据": pbase_fail,
         "跨文件污染": polluted,
         "★ 说明": "★ 每条负控都自声明改哪个文件 ＋ 字节级复原 ＋ sha 自检"
                   " ＋ **红灯集合差分**归因"},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("★ %d 条负控，%d 失败 ⟹ ⟹ 落盘：%s"
          % (len(results), len(bad), OUT.relative_to(ROOT)))
    shutil.rmtree(tmpdir, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

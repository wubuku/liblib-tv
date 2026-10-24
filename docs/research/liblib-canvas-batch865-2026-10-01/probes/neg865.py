#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 865 阴性对照：★ 每条变异都必须让 865 门禁**具名**翻红。

## ★ 变异清单（每条都对应门禁里的一条判据）

| # | 变异 | 应命中的判据 |
| --- | --- | --- |
| N1 | 三分线层去掉 `overflow-hidden` | 静态：裁剪类 ＋ 运行时：裁剪/圆角 |
| N2 | 三分线层 `aria-hidden` 改成 false | 静态：`aria-hidden` ＋ 运行时：aria |
| N3 | 竖线百分比 33.333% → 50% | 静态：百分比逐字 ＋ 运行时：线的相对位置 |
| N4 | 开关的 left 改回「相对框」写法 | 静态：容器坐标 ＋ 运行时：开关位置 |
| N5 | 开关的 top 改回「相对框」写法 | 同上 |
| N6 | 往「空框」里塞一个子元素 | 运行时：框是空框 |
| N7 | ★ 把坐标控件挪回视口右上角 | ★ 运行时：每枚坐标控件按钮都命中自己 |

★ ★ **N7 最要紧**：它能**重现 batch 864 的后遗症**
（864 把坐标控件降到 `z-10` 之后 ⟹ ⟹ 取景框上那枚开关反过来盖住了
坐标控件的「X 反向」「Z 正向」两枚按钮）⟹ ⟹
⟹ ⟹ 865 门禁**必须**能抓住它 ⟹ ⟹ 否则这条门禁对 864 的回归是瞎的。

## ★ 纪律（沿用 batch 863／864 的教训）

- 每条变异**行数中性**；
- ★ 变异**必须真的落地**（`apply_mutation` 返回变异后的源码）；
- 变异后**等 dev server 重编**（10s）⟹ ⟹ 否则运行时判据读到的是旧编译产物；
- 跑完**字节级还原**；
- 「命中预期判据」＝ 红灯原文里**出现**那条判据名。

## 用法
  python3 neg865.py              # 正式模式
  python3 neg865.py --observe    # 只打印首条红灯（定归因关键字用）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch865.py"
VIEW = ROOT / "src/components/director/DirectorViewport.tsx"

FILES = {"view": VIEW}

MUTATIONS = [
    {
        "id": "N1",
        "desc": "三分线层去掉 overflow-hidden（源站的圆角裁剪）",
        "file": "view",
        "old": 'className="pointer-events-none absolute overflow-hidden rounded-xl"',
        "new": 'className="pointer-events-none absolute rounded-xl"',
        "expect": "source:the-thirds-layer-carries-the-source-clipping-classes",
    },
    {
        "id": "N2",
        "desc": "三分线层的 aria-hidden 改成 false",
        "file": "view",
        # ★ ★ 锚点必须**唯一**：★ `aria-hidden="true"` 在本文件出现 **11 处**
        #   ⟹ ⟹ 第一版用裸 `aria-hidden="true"` ⟹ ⟹ `replace(…, 1)` 改到了
        #   ⟹ ⟹ 第 2570 行**别处**那一处 ⟹ ⟹ 三分线层**根本没被改**
        #   ⟹ ⟹ 负控打空（rc=0、零红灯）。
        "old": ('          // ★ 源站逐字：`"aria-hidden":!0` ⟹ ⟹ 这层对辅助技术**不可见**\n'
                '          aria-hidden="true"'),
        "new": ('          // ★ 源站逐字：`"aria-hidden":!0` ⟹ ⟹ 这层对辅助技术**不可见**\n'
                '          aria-hidden="false"'),
        "expect": "source:the-thirds-layer-carries-the-source-clipping-classes",
    },
    {
        "id": "N3",
        "desc": "竖线百分比 33.333% → 50%",
        "file": "view",
        "old": 'left: "33.333%"',
        "new": 'left: "50%"',
        "expect": "source:the-clone-line-percentages-match-the-source-verbatim",
    },
    {
        "id": "N4",
        "desc": "开关的 left 改回「相对框」写法（旧结构）",
        "file": "view",
        "old": "left: frameLeft + frameWidth - 40,",
        "new": "left: frameWidth - 40,",
        "expect": "source:the-toggle-uses-the-source-container-coordinates",
    },
    {
        "id": "N5",
        "desc": "开关的 top 改回「相对框」写法（旧结构）",
        "file": "view",
        "old": "top: frameTop + 8,",
        "new": "top: 8,",
        "expect": "source:the-toggle-uses-the-source-container-coordinates",
    },
    {
        "id": "N6",
        "desc": "往「空框」里塞一个子元素（破坏空框）",
        "file": "view",
        "old": '          outlineOffset: "-1px",\n        }}\n      />',
        "new": ('          outlineOffset: "-1px",\n        }}\n      >'
                '<span data-director-fake-child="1" /></div>'),
        "expect": "clone:the-frame-is-empty-like-the-source",
    },
    {
        "id": "N7",
        "desc": "★ 把坐标控件挪回视口右上角（重现 864 的后遗症）",
        "file": "view",
        "old": ('      className="absolute left-3 z-10 h-20 w-20"\n'
                "      style={{ top: 56 }}"),
        "new": ('      className="absolute right-5 top-5 z-10 h-20 w-20"\n'
                "      style={{ top: 20 }}"),
        "expect": "clone:every-gizmo-button-is-hittable-while-the-frame-exists",
    },
]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_mutation(src: str, m: dict) -> tuple[bool, str, str]:
    """★ 返回 (成功, 原因, **变异后的源码**) ⟹ ⟹ 一定要把变异写回去。"""
    if m["old"] not in src:
        return False, f"锚点不存在：{m['old'][:60]!r}", src
    if m["old"] == m["new"]:
        return False, "锚点与替换值相同", src
    mutated = src.replace(m["old"], m["new"], 1)
    if mutated == src:
        return False, "替换后内容没变", src
    return True, "", mutated


def run_gate() -> tuple[int, list[str]]:
    proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=1800)
    fails = [ln.strip() for ln in proc.stdout.splitlines()
             if ln.strip().startswith("FAILED:")]
    if not fails:
        for ln in (proc.stderr or "").splitlines():
            if ln.strip():
                fails.append("CRASH-STDERR: " + ln.strip())
                break
    return proc.returncode, fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observe", action="store_true")
    args = ap.parse_args()

    original = {k: FILES[k].read_bytes() for k in FILES}
    report: list[dict] = []
    try:
        for m in MUTATIONS:
            path = FILES[m["file"]]
            path.write_bytes(original[m["file"]])
            src = original[m["file"]].decode("utf-8")
            ok, why, mutated = apply_mutation(src, m)
            if not ok:
                report.append({"id": m["id"], "desc": m["desc"], "结果": "无法注入",
                               "原因": why})
                print(f"[{m['id']}] 无法注入：{why}")
                continue
            lines_before = src.count("\n")
            path.write_text(mutated, encoding="utf-8")
            lines_after = path.read_text(encoding="utf-8").count("\n")
            injected = m["new"].split("\n")[0] in path.read_text(encoding="utf-8")
            # ★ 等 dev server 重编（运行时判据要看到新源码）
            time.sleep(10)
            rc, fails = run_gate()
            path.write_bytes(original[m["file"]])
            restored = sha_bytes(path.read_bytes()) == sha_bytes(original[m["file"]])
            entry = {
                "id": m["id"], "desc": m["desc"],
                "行数中性": lines_before == lines_after,
                "变异已落地": injected,
                "门禁rc": rc,
                "红条数": len(fails),
                "首条红灯": fails[0] if fails else "",
                "命中预期判据": any(m["expect"] in f for f in fails),
                "字节级还原": restored,
            }
            if not args.observe:
                entry["结果"] = ("PASS" if (rc != 0 and entry["命中预期判据"]
                                           and entry["行数中性"] and injected
                                           and restored)
                                 else "FAIL")
            report.append(entry)
            print(f"[{m['id']}] {m['desc']} ⟹ rc={rc} 红{len(fails)}条 "
                  f"命中预期={entry['命中预期判据']} 行数中性={entry['行数中性']} "
                  f"已落地={injected} 还原={restored}", flush=True)
            if fails:
                print("    首条红灯:", fails[0][:200])
    finally:
        for k, data in original.items():
            FILES[k].write_bytes(data)
        print("★ 最终还原自检：",
              all(sha_bytes(FILES[k].read_bytes()) == sha_bytes(original[k])
                  for k in FILES))

    # ★ ★★ **负控会污染门禁产物** ⟹ ⟹ 必须**重跑一次门禁**把产物刷回基准态。
    #   ★ 现象（实测）：★ N7（坐标控件挪回右上角）那一轮结束后，
    #   ⟹ ⟹ `runtime-audit.json` 里留下的是**变异态**的读数
    #   ⟹ ⟹ 「坐标控件命中」写着「全命中 = False」
    #   ⟹ ⟹ ⟹ 而磁盘上的源码**已经还原** ⟹ ⟹ **产物与源码对不上**。
    #   ⟹ ⟹ 若直接提交 ⟹ ⟹ 提交的产物是**红的** ⟹ ⟹ 而门禁本身是绿的 ⟹ ⟹ 自相矛盾。
    #   ⟹ ⟹ 修法：★ 还原之后**再跑一遍门禁** ⟹ ⟹ 让产物回到基准态。
    print("★ 重跑门禁 ⟹ 刷新 runtime-audit.json（还原变异污染）", flush=True)
    time.sleep(10)
    rc0, fails0 = run_gate()
    print(f"  刷新后：rc={rc0} 红 {len(fails0)} 条", flush=True)
    for f in fails0:
        print("   ", f[:180])

    out = ROOT / ("docs/research/liblib-canvas-batch865-2026-10-01/raw/"
                  "negative-audit.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    if args.observe:
        print("\n（观察模式：未断言）")
        return 0
    bad = [e for e in report if e.get("结果") != "PASS"]
    print(f"\n阴性对照 {len(report) - len(bad)}/{len(report)} 通过")
    for e in bad:
        print("  ★ 未通过：", e.get("id"), e.get("desc"),
              "｜命中预期=", e.get("命中预期判据"),
              "｜首条红灯=", str(e.get("首条红灯"))[:160])
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

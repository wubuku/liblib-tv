#!/usr/bin/env python3
"""Jimeng clone batch 840 verifier —— 全屏浮层：补上锚点，并拆掉一个**判据盲区**。

## 起点

批 832 的 role 型普查记下「`JimengVideoPreview` 1 处无锚点」；那处是
`fixed inset-0 z-[400] role="dialog"`，也就是视频全屏预览。补锚点很容易。
真正的问题是：**补了锚点，几何型普查也照样看不见它。**

## 本批的核心：一个判据把两类东西当成了一类

§54 那条第二通道里有一条排除规则：`w ≥ 1500 && h ≥ 700 → 跳过`（排除铺满全屏
的巨型容器）。批 840 实测（1680×1050 视口）：

    react-flow__renderer  1680×1050  z=4   透明底  21 个可交互子元素  ← 该排除
    react-flow__pane      1680×1050  z=1   透明底  10 个可交互子元素  ← 该排除
    fixed inset-0 z-[400] 1680×1050  z=400 黑/60 底 4 个可交互子元素  ← **真模态**

三者尺寸一模一样，只有身份不同。那条按**尺寸**排除的规则，把全屏模态一起吃掉了。
尺寸是表象，「它就是画布」才是判据。源站侧同样中招：`timeline-fullscreen-editor`
1512×950，连它的 `fixed inset-0 bg-octo-overlay z-50` 遮罩也是同尺寸且**无锚点**。

## 顺带拆掉的第二个问题：浮层会「漏」到下一个状态

`TID2TRIG` 原来**缺**视频节点那两个下拉 ⇒ `close_open()` 从来关不掉它们 ⇒
开着的工具下拉一路漏到后面某个状态被当成那个状态的浮层。839 那轮
「图片节点产出（截帧）」报出的那 1 个候选就是它，**0 才是真值**。
张冠李戴比漏报更坏：它让干净的状态看起来有浮层，还让下一个状态假盲区。
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "scripts" / "jimeng_floating_layer_audit.py"
PREVIEW = ROOT / "src/components/jimeng/JimengVideoPreview.tsx"
OUT = Path("/tmp/jimeng-floating-layers-b840.json")

NEW_TID = "video-fullscreen-preview"
NEW_STATE = "视频全屏预览"

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


def main() -> int:
    env = dict(os.environ)
    env["SNAP_OUT"] = str(OUT)
    r = subprocess.run([sys.executable, str(AUDIT)], capture_output=True,
                       text=True, env=env, cwd=str(ROOT), timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    data = {}
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            data = {"_parse_error": str(e)}
    rows = data.get("rows", [])

    # ── A. 普查本身 ───────────────────────────────────────────────
    print("— A. 普查跑通 —")
    check("A.0 退出码 0（= 0 缺锚点 且 自检通过）", r.returncode == 0,
          f"rc={r.returncode}")
    check("A.1 skipped（前置态没成立）= 0", not data.get("skipped"),
          "; ".join(data.get("skipped", [])[:2]))
    check("A.2 empty（开着却枚举不到 = 判据盲区）= 0", not data.get("empty"),
          "; ".join(data.get("empty", [])[:2]))
    check("A.3 0 个候选缺 data-testid",
          not [x for x in rows if not x["tid"]],
          f"rows={len(rows)}")

    # ── B. 全屏浮层：锚点在、状态在、几何对得上 ─────────────────────
    print("\n— B. 全屏预览：锚点 + 状态 + 几何 —")
    src = PREVIEW.read_text(encoding="utf-8")
    check(f'B.1 源码里有 data-testid="{NEW_TID}"',
          f'data-testid="{NEW_TID}"' in src)
    hit = [x for x in rows if x["state"] == NEW_STATE]
    check(f"B.2 「{NEW_STATE}」这个状态存在且有候选", bool(hit),
          f"命中 {len(hit)} 条")
    tgt = [x for x in hit if x["tid"] == NEW_TID]
    check(f"B.3 它枚举到的正是 {NEW_TID}", bool(tgt),
          f"实际={[x['tid'] for x in hit]}")
    if tgt:
        t = tgt[0]
        # 判据能失败：这几条都不是恒真 —— 全屏模态必须**既大又靠上**。
        check("B.4 它是 fixed（不是画布里绝对定位的东西）",
              t["pos"] == "fixed", f"pos={t['pos']}")
        check("B.5 z-index ≥ 300（压得住画布）", int(t["z"]) >= 300, f"z={t['z']}")
        check("B.6 铺满视口（w≥1600 且 h≥1000）",
              t["w"] >= 1600 and t["h"] >= 1000, f"{t['w']}×{t['h']}")
        check("B.7 role='dialog'（**只作记录**，不是筛选条件 —— 它照样被枚举到）",
              t["role"] == "dialog", f"role={t['role']!r}")

    # ── C. 盲区不许被重新关回去 ────────────────────────────────────
    print("\n— C. 「按尺寸排除」那条规则不许回来（防盲区复现）—")
    asrc = AUDIT.read_text(encoding="utf-8")
    check("C.1 枚举里不再有 `width >= 1500` 这条尺寸排除",
          "width >= 1500" not in asrc,
          "尺寸排除一旦回来，全屏模态立刻重新不可见")
    check("C.2 改成按**身份**排除（自身是流壳 / 包含画布）",
          "FLOW_SHELL" in asrc and "react-flow__viewport-portal" in asrc
          and "e.querySelector('.react-flow__renderer')" in asrc)
    check("C.3 判据**不引用 role** 来筛选候选",
          "getAttribute('role')" in asrc
          and "只作**记录**，不作筛选条件" in asrc)
    # 画布壳必须仍然被排除 —— 排除规则收紧过头也是缺陷（批 840 自己犯过）
    check("C.4 画布壳真的没混进结果（`react-flow__` 0 条）",
          not [x for x in rows if "react-flow__" in x["cls"]],
          f"混入={[x['cls'][:30] for x in rows if 'react-flow__' in x['cls']][:2]}")

    # ── D. 浮层不许「漏」到别的状态名下 ────────────────────────────
    print("\n— D. 张冠李戴：每个锚点只能出现在它自己的状态里 —")
    owner: dict[str, set] = {}
    for x in rows:
        if x["tid"]:
            owner.setdefault(x["tid"], set()).add(x["state"])
    shared = {k: sorted(v) for k, v in owner.items() if len(v) > 1}
    check("D.1 没有锚点同时归属多个状态", not shared, f"串了={shared}")
    for tid, st in (("video-toolbar-capture-menu", "视频工具条·截取帧下拉"),
                    ("video-toolbar-tools-menu", "视频工具条·工具下拉"),
                    (NEW_TID, NEW_STATE)):
        check(f"D.2 {tid} 只出现在「{st}」", owner.get(tid) == {st},
              f"实际={sorted(owner.get(tid, []))}")

    # ── E. 漏的根因被堵住了（不是靠运气不漏）────────────────────────
    print("\n— E. 漏的根因：`close_open()` 现在真能关掉那两个下拉 —")
    check("E.1 TID2TRIG 收录了截取帧下拉",
          '"video-toolbar-capture-menu": "截取帧"' in asrc)
    check("E.2 TID2TRIG 收录了工具下拉",
          '"video-toolbar-tools-menu": "工具"' in asrc)
    check("E.3 定位器同时试 aria-label 与可见文案（那两枚没有 aria-label）",
          "aria-label^=" in asrc and 'button:text-is("{trig}")' in asrc)
    check("E.4 普查完统一收浮层（`step()` 里调 `close_open()`）",
          re.search(r"n = census\(tag\).{0,400}?close_open\(\)", asrc,
                    re.S) is not None)
    check("E.5 截帧状态如实标成 expected_empty（0 才是真值，且写了理由）",
          "本身不打开任何浮层" in asrc)

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 840-fullscreen OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

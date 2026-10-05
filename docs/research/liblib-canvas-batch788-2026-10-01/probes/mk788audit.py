#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 788 汇编器 —— C787-2 的**运行时后果**确认

## 本批确认的事

787 用静态扫描说「往模型库加条目会取消正在进行的运镜绘制」
（`DirectorViewport.tsx:2836-2837`：`addModelLibraryObject(item)` 这个
**store action 调用**在 `directorStore.ts:5190` 写 `motionPathDraft: null`，
与 `setModelLibraryOpen(false)` 同处一个函数体），★ 但**没跑浏览器**。

## ★ 承重预测（可 falsify）

| 臂 | 预测 | 作用 |
| --- | --- | --- |
| `draftOnly` | 草稿**活着** | 读数本身会动（正向对照） |
| ★ `draftThenToggleLib` | ★ 草稿**仍活着** | ★ **关键对照**：归因是「加条目」而非「开了面板」 |
| ★★ `draftThenAddItem` | ★★ 草稿**没了** | 处理臂 |
| `noDraftThenAddItem` | 一切正常 | 证明「加条目」这个动作本身可用 |

## ★ 这是一种**不同于 D1i** 的失效形态

| | D1i（784） | ★ 本批（787 静态 + 788 运行时） |
| --- | --- | --- |
| 触发 | 按一次 `Escape` | 点一次「加入场景」 |
| 前提 | **两个状态同时开着** | **不需要**共活 |
| 用户感知 | 第 1 次没反应，要按第 2 次 | 绘制**静默消失** |
| 归因 | `sIP` 截断了整条链 | **一个操作顺手把另一个状态置空** |

## ★ 读数链（三行行锚定）

`src/components/director/DirectorViewport.tsx`：

```text
 2559|   const viewportGizmoDisabled =
 2560|     timeline.motionPathDraft !== null || phoneVcamRecording;
 2987|           disabled={viewportGizmoDisabled}
  420|        data-director-viewport-gizmo-disabled={disabled}
```

⟹ `[data-director-viewport-gizmo-disabled]` 的值就是 `motionPathDraft !== null`。
⚠ 它 `||` 了 `phoneVcamRecording` ⟹ **只有**在录制**没开**时这个读数才干净。
本批**从不**打开虚拟相机 ⟹ 该混淆项恒为假 ⟹ 由检查 D 单独钉住。

## 纪律

- 派生字段一律**从 `trace` 重算**（R149），不信 raw 里的 `draftAlive`
- 对照臂必须真能区分「处理」与「其他一切」
"""
import json
import pathlib

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch788-2026-10-01"
RAW = REPO / (B + "/raw/vb788a.json")
SMOKE = REPO / (B + "/raw/smoke788.json")
OUT = REPO / (B + "/runtime-audit.json")

DV = "src/components/director/DirectorViewport.tsx"
DS = "src/store/directorStore.ts"

#: ★ 读数链：`(文件, 行, needle)`
READ_CHAIN = [
    (DV, 2559, "const viewportGizmoDisabled ="),
    (DV, 2560, "timeline.motionPathDraft !== null || phoneVcamRecording;"),
    (DV, 2987, "disabled={viewportGizmoDisabled}"),
    (DV, 420, "data-director-viewport-gizmo-disabled={disabled}"),
    # ★ 写入侧那一行（C787-2 的落点）
    (DS, 5190, "motionPathDraft: null,"),
]

#: ★ 臂 ⟶ 预测的 `draftAlive`
EXPECT = {
    "draftOnly": True,
    "draftThenToggleLib": True,      # ★ 对照
    "draftThenAddItem": False,       # ★★ 处理
    "noDraftThenAddItem": False,
}

#: ★ 处理臂与对照臂的**差别**必须在读数里显出来
KEY_PAIR = ("draftThenToggleLib", "draftThenAddItem")


def line_of(rel, n):
    return (REPO / rel).read_text(encoding="utf-8").split("\n")[n - 1]


def recompute(cell):
    """★ 从 `trace` 重算 `draftAlive`，不信 raw 的派生字段。"""
    tr = cell.get("trace") or []
    if not tr:
        return None
    last = tr[-1]["draft"]
    return last == "true"


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    smoke = json.loads(SMOKE.read_text(encoding="utf-8"))
    checks = []

    # ── A：读数链逐行锚定 ──
    det, ok = [], True
    for rel, n, needle in READ_CHAIN:
        code = line_of(rel, n)
        good = needle in code
        ok = ok and good
        det.append({"file": rel, "line": n, "needle": needle, "ok": good,
                    "code": code.strip()[:100]})
    c = {"id": "A:读数链行锚定", "ok": ok, "n": len(READ_CHAIN), "anchors": det,
         "claim": "★ `[data-director-viewport-gizmo-disabled]` ⟹ "
                  "`motionPathDraft !== null`（`:2559-2560` ⟹ `:2987` ⟹ `:420`）"}
    assert ok, "★ 读数链行锚定失败：\n%r" % det
    checks.append(c)

    # ── B：冒烟轮的四个判别式全过 ──
    j = smoke["judgments"]
    need = ["① deskOpen", "② 路径菜单能开", "③ ★ 草稿能造出来",
            "④ 模型库能开", "④ 模型库条目能点"]
    b_ok = all(j.get(k) for k in need)
    c = {"id": "B:冒烟判别式", "ok": b_ok, "n": len(need),
         "detail": {k: j.get(k) for k in need},
         "claim": "★ 造草稿、造对照所需的每一个入口都必须先验能通"}
    assert b_ok, "★ 判别式没过：%r ⟹ 后续读数不可信" % {k: j.get(k) for k in need}
    checks.append(c)

    # ── C：★ 本批的核心对照 —— 只开再关**不**杀草稿，加条目才杀 ──
    by_arm = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            by_arm.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    mism, recomputed = [], {}
    for arm, lst in by_arm.items():
        for rdno, r in lst:
            mine = recompute(r)
            recomputed.setdefault(arm, []).append(mine)
            if mine != EXPECT.get(arm) or mine != r.get("draftAlive"):
                mism.append({"arm": arm, "round": rdno,
                             "recomputed": mine,
                             "rawSays": r.get("draftAlive"),
                             "expect": EXPECT.get(arm)})
    c = {"id": "C:四臂两轮全部符合预测", "ok": not mism,
         "n": sum(len(v) for v in by_arm.values()), "detail": {"mismatch": mism},
         "claim": "★ `draftOnly` True / ★对照 `draftThenToggleLib` True / "
                  "★★处理 `draftThenAddItem` False / `noDraftThenAddItem` False；"
                  "且**重算值与 raw 自报的 `draftAlive` 逐格相同**"}
    assert not mism, "★ 有 %r 与预测或与 raw 不符 ⟹ 结论要重算" % mism
    checks.append(c)

    # ── D：★ 对照臂与处理臂的差别必须**只**在「加条目」那一步 ──
    ctrl = by_arm[KEY_PAIR[0]][0][1]
    treat = by_arm[KEY_PAIR[1]][0][1]
    ctrl_tr = {t["phase"]: t["draft"] for t in (ctrl.get("trace") or [])}
    treat_tr = {t["phase"]: t["draft"] for t in (treat.get("trace") or [])}
    # 对照臂在 afterLibClose 时草稿还在；处理臂在 afterAdd 时才没
    d_ok = (ctrl_tr.get("afterLibClose") == "true"
            and treat_tr.get("afterLibOpen") == "true"
            and treat_tr.get("afterAdd") != "true")
    c = {"id": "D:★ 归因只落在「加条目」那一步", "ok": d_ok, "n": 1,
         "detail": {"controlTrace": ctrl_tr, "treatmentTrace": treat_tr},
         "claim": "★ 对照臂在**关掉**面板之后草稿还是 `true` ⟹ "
                  "「开/关模型库」本身不杀草稿；处理臂在**开面板之后**草稿也还在、"
                  "只有点了「加入场景」才变 ⟹ 归因**唯一地**落在加条目那个动作上"}
    assert d_ok, "★ 归因不唯一：%r" % {"control": ctrl_tr, "treatment": treat_tr}
    checks.append(c)

    # ── E：★ 这个读数有混淆项（`|| phoneVcamRecording`），必须钉住它没被触发 ──
    #    第一版写成「所有 step 的 libOpen 非 null」，而 `makeDraft` 那一步
    #    **本来就没有 read** ⟹ 恒为 null ⟹ 这条断言**永远不成立**。
    probe_src = (REPO / (B + "/probes/dbg788a.py")).read_text(encoding="utf-8")
    touched_vcam = "phone-vcam-trigger" in probe_src
    all_reads = [(t["phase"], (t.get("read") or {}).get("libOpen"))
                 for _a, lst in by_arm.items() for _rd, r in lst
                 for t in (r.get("steps") or []) if "read" in t]
    bad = [x for x in all_reads if x[1] is None]
    e_ok = (not touched_vcam) and not bad
    c = {"id": "E:混淆项未触发", "ok": e_ok, "n": len(all_reads),
         "detail": {"probeTouchesVCam": touched_vcam,
                    "reads": len(all_reads), "readsWithNull": bad[:5]},
         "claim": "★ 读数 `viewportGizmoDisabled` 里 `||` 了 `phoneVcamRecording`，"
                  "本批**从不**点 `[data-director-phone-vcam-trigger]` ⟹ 该混淆项恒假；"
                  "且**每一条**有读数的步骤都必须给出可解析的 `libOpen`（不能是 null）"}
    assert e_ok, ("★ 混淆项可能被触发：probeTouchesVCam=%r，null 读数 %r"
                  % (touched_vcam, bad[:5]))
    checks.append(c)

    out = {
        "batch": 788,
        "claims": {
            "C788-1": "★★ **运行时确认 C787-2**：造出运镜草稿后点「加入场景」，"
                      "草稿**没了**（8 格两轮一致）",
            "C788-2": "★ **归因唯一**：对照臂「只开再关模型库」草稿**仍活着** ⟹ "
                      "杀草稿的不是「开面板」而是「加条目」这个动作",
            "C788-3": "★ 这是一种**不同于 D1i** 的失效形态：D1i 要**两个状态同时开着**"
                      "、靠「按第二次 Escape」；本批**不需要共活**、靠「点一次加入场景」、"
                      "绘制**静默消失**",
            "C788-4": "★ 读数链 `:2559-2560` ⟹ `:2987` ⟹ `:420`；"
                      "⚠ 它 `||` 了 `phoneVcamRecording`，本批不碰虚拟相机 ⟹ 混淆项恒假",
        },
        "arms": {a: EXPECT[a] for a in sorted(EXPECT)},
        "recomputed": {a: sorted(set(v)) for a, v in recomputed.items()},
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(x.get("n", 0) for x in checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ C788-1：四臂两轮（8 格）全部符合预测")
    for a in sorted(EXPECT):
        print("   %-22s 预测 draftAlive=%-5s 实测 %s"
              % (a, EXPECT[a], sorted(set(recomputed.get(a, [])))))
    print("★ C788-2：★ 对照臂「只开再关」草稿仍活着 ⟹ 归因唯一")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

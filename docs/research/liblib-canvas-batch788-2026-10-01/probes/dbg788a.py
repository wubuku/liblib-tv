#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 788 探针 —— 「往模型库加条目 ⟹ 取消正在进行的运镜绘制」的**运行时后果**

## 787 留下的缺口

787 用静态扫描发现 `DirectorViewport.tsx:2836-2837` 里
`addModelLibraryObject(item)`（**store action 调用**，它在
`directorStore.ts:5190` 写 `motionPathDraft: null`）与
`setModelLibraryOpen(false)` 写在**同一个函数体**。
★ 但 787 **没跑浏览器** ⟹ 静态结论只到「同一函数体写两个门状态」这一层。

## 读数：`motionPathDraft !== null` 的 DOM 读数

`DirectorViewport.tsx:2559-2560`：

```text
const viewportGizmoDisabled =
  timeline.motionPathDraft !== null || phoneVcamRecording;
```

它传给 `:2987` 的 `disabled`，再由子组件 `:420` 落成
`data-director-viewport-gizmo-disabled={disabled}` ⟹
`[data-director-viewport-gizmo-disabled]` 的值就是 `motionPathDraft !== null`
（本批不碰虚拟相机录制 ⟹ 不会混淆）。

## ★ 冒烟轮抓到的坑

第一版把入口写成 `[data-director-track-draw-trail="director-camera-main"]`，
⟹ 命中 **0** 个 ⟹ 差点判成「结构上不可判」。
★ 真值是该属性的 `cameraTrack.id`（**轨道 id**），而 `director-camera-main`
是**相机对象 id**。改成「属性存在」选择器后四个判别式全过。

## ★ 四个臂：一个处理 + 三个对照

| 臂 | 做什么 | 预测 | 作用 |
| --- | --- | --- | --- |
| `draftOnly` | 造草稿，**停** | 草稿**活着** | 读数本身会动（正向对照） |
| ★ `draftThenToggleLib` | 造草稿 → 开模型库 → **再点触发器关掉**，**不加条目** | ★ 草稿**仍活着** | ★ **关键对照**：证明归因是「加条目」而不是「开了面板」 |
| ★★ `draftThenAddItem` | 造草稿 → 开模型库 → **点条目** | ★★ 草稿**没了** | 处理臂 |
| `noDraftThenAddItem` | **不造**草稿 → 点条目 | 一切正常 | 证明「加条目」这个动作本身可用 |

★ 没有 `draftThenToggleLib` 的话，「加条目后草稿消失」可以和
「开面板导致草稿消失」「点任意东西导致草稿消失」**无法区分**。

## 格数

4 臂 × 2 轮 = **8 格**
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch788-2026-10-01/raw/vb788a.json")

#: ★ 属性值是**轨道 id**，不是相机对象 id（第一版写死对象 id ⟹ 命中 0）
DRAW = "[data-director-track-draw-trail]"
TOOL = '[data-director-motion-path-draw-tool="pencil"]'
LIB_TRIGGER = "[data-director-model-library-trigger]"
LIB_PANEL = "[data-director-model-library-panel]"
LIB_ADD = "[data-director-model-library-preview-add]"
GIZMO = "[data-director-viewport-gizmo-disabled]"

ARMS = ["draftOnly", "draftThenToggleLib", "draftThenAddItem",
        "noDraftThenAddItem"]

READ = """(giz)=>{const g=document.querySelector(giz);
 return {draft: g ? g.getAttribute('data-director-viewport-gizmo-disabled') : null,
   libPanel: !!document.querySelector('[data-director-model-library-panel]'),
   libOpen: (()=>{const t=document.querySelector('[data-director-model-library-trigger]');
     return t ? t.getAttribute('aria-expanded') : null;})(),
   pathMenu: !!document.querySelector('[data-director-motion-path-menu]')};}"""


def _click(pg, sel):
    s = pg.evaluate(A.SCAN_CLICK, sel)
    if not s.get("pt"):
        return False
    pg.mouse.click(s["pt"][0], s["pt"][1])
    A.settle(pg)
    return True


def make_draft(pg):
    """点两下造出运镜草稿。返回 (成功?, 轨迹)。"""
    if not _click(pg, DRAW):
        return False, ["点不到 %s" % DRAW]
    if not pg.evaluate("()=>!!document.querySelector('[data-director-motion-path-menu]')"):
        return False, ["路径菜单没开"]
    if not _click(pg, TOOL):
        return False, ["点不到 %s" % TOOL]
    A.settle(pg)
    r = pg.evaluate(READ, GIZMO)
    if r["draft"] != "true":
        return False, ["点了工具但草稿没起来（读数=%r）" % r["draft"]]
    return True, [r]


def run_cell(pg, arm):
    A.fresh(pg)
    if not pg.evaluate(
            "()=>!!document.querySelector('[role=\"dialog\"][aria-modal=\"true\"]')"):
        return {"arm": arm, "FAILED": "导演台没打开"}
    steps = []
    need_draft = arm != "noDraftThenAddItem"
    if need_draft:
        ok, why = make_draft(pg)
        steps.append({"phase": "makeDraft", "ok": ok, "why": why})
        if not ok:
            return {"arm": arm, "FAILED": "造不出草稿", "steps": steps}
    else:
        steps.append({"phase": "makeDraft", "ok": True, "why": ["按设计跳过"]})
    steps.append({"phase": "afterDraft", "read": pg.evaluate(READ, GIZMO)})

    if arm in ("draftThenToggleLib", "draftThenAddItem",
               "noDraftThenAddItem"):
        if not _click(pg, LIB_TRIGGER):
            return {"arm": arm, "FAILED": "点不到模型库触发器", "steps": steps}
        steps.append({"phase": "afterLibOpen", "read": pg.evaluate(READ, GIZMO)})
    if arm == "draftThenToggleLib":
        # ★ 只开再关，**不加条目**
        if not _click(pg, LIB_TRIGGER):
            return {"arm": arm, "FAILED": "关不掉模型库", "steps": steps}
        steps.append({"phase": "afterLibClose", "read": pg.evaluate(READ, GIZMO)})
    if arm in ("draftThenAddItem", "noDraftThenAddItem"):
        if not _click(pg, LIB_ADD):
            return {"arm": arm, "FAILED": "点不到模型库条目", "steps": steps}
        steps.append({"phase": "afterAdd", "read": pg.evaluate(READ, GIZMO)})

    reads = [s["read"] for s in steps if "read" in s]
    out = {"arm": arm, "steps": steps, "after": pg.evaluate(READ, GIZMO)}
    draftFlag = (lambda r: r is not None and r["draft"] == "true")
    if arm == "draftOnly":
        out["expect"] = "草稿活着"
        out["draftAlive"] = draftFlag(reads[-1])
    elif arm == "draftThenToggleLib":
        out["expect"] = "★ 只开再关模型库 ⟹ 草稿**仍**活着"
        out["draftAlive"] = draftFlag(reads[-1])
        out["control"] = True
    elif arm == "draftThenAddItem":
        out["expect"] = "★★ 加条目 ⟹ 草稿**没了**"
        out["draftAlive"] = draftFlag(reads[-1])
    else:
        out["expect"] = "不造草稿 ⟹ 加条目后一切正常"
        out["draftAlive"] = draftFlag(reads[-1])
        out["expectDraftAlive"] = False
    # ★ 派生字段一律**从 reads 重算**，不信上游
    out["trace"] = [{"phase": s["phase"],
                     "draft": (s.get("read") or {}).get("draft")}
                    for s in steps if "read" in s]
    return out


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        rounds = []
        for rd in range(2):
            rows = []
            for arm in ARMS:
                cell = None
                for t in range(3):
                    pg = b.new_page()
                    pg.set_default_timeout(15000)
                    try:
                        cell = run_cell(pg, arm)
                    except Exception as e:  # noqa: BLE001
                        cell = {"arm": arm,
                                "FAILED": "%s: %s" % (type(e).__name__, e)}
                    finally:
                        try:
                            pg.close()
                        except Exception:  # noqa: BLE001
                            pass
                    cell["tries"] = t + 1
                    if not cell.get("FAILED"):
                        break
                rows.append(cell)
                print("  round%d %-22s %s" % (
                    rd + 1, arm,
                    ("draftAlive=%s" % cell.get("draftAlive"))
                    if not cell.get("FAILED")
                    else "FAILED:%s" % cell.get("FAILED")), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 788, "arms": ARMS, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

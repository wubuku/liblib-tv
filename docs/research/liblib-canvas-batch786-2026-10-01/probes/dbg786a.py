#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 786 探针 A —— `{modelLibraryOpen, crowdPanelOpen, phoneVcamOpen}`
这三个**能不能同时活着**

## 785 钉死的**事实**（行锚定，静态）

`DirectorViewport.tsx` 里三个打开者，每个都**先无条件关掉另外两个、再打开自己**：

| 打开者 | 跨度 | 先关掉 | 再打开自己 |
| --- | --- | --- | --- |
| `toggleModelLibrary` | `:2825-2829` | `phoneVcamOpen`(`:2826`)、`crowdPanelOpen`(`:2827`) | `:2828` |
| vcam 触发器 `onClick` | `:3536-3541` | `modelLibraryOpen`(`:3538`)、`crowdPanelOpen`(`:3539`) | `:3540` |
| crowd 触发器 `onClick` | `:3556-3560` | `modelLibraryOpen`(`:3557`)、`phoneVcamOpen`(`:3558`) | `:3559` |

⟹ 这是个**三向**互斥（比 783 在 `DirectorTimeline` 里那对**双向**更密）。

## ★ 承重预测（可 falsify）

**P786-2**：三者**永不共活** ⟹ 点开 A 之后点 B，读数必须是「A 已关、B 已开、
第三个仍关」。**六个有序对全部如此。**

**P786-3**（判别力前提）：单点一个触发器时，它自己的 `aria-expanded` 真的会变 `true`
⟹ 否则「全都关着」可能是**探针根本没点到**。

## ★ 为什么必须是**有序对**而不是只测单个

只测「A 单独打开」的话，读数是「B 和 C 都是关的」——而 B、C **本来就关着**，
读数与「A 把它们关掉了」**完全无法区分**。
⟹ 必须先点开 A、再点 B，才看得到「**A 被 B 关掉了**」这个**转变**。

## 格数

第①道·单点 3 格（判别力）+ 第②道·有序对 **6 格** ⟹ **9 格 × 2 轮 = 18 次读数**

## ★ 读数怎么来

三个触发器**都带 `aria-expanded`**（`phoneVcamOpen` `:3534`、`crowdPanelOpen`
`:3555`、`modelLibraryOpen` `:3571` 附近）⟹ 用**它们自己的 ARIA 契约**判，
比猜 class 名可靠；面板本体另有一份交叉核对（`[data-director-crowd-panel]` /
`[data-director-model-library-panel]`）。

⚠ `phoneVcam` 面板**关闭时返回 `null`**（`DirectorPhoneVcamPanel.tsx:395`）⟹
只能靠触发器的 `aria-expanded` 读，这一路**没有**第二来源 ⟹ 单独记下。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch786-2026-10-01/raw/vb786a.json")
BASE = A.BASE
SETTLE = 260
ROUNDS = 2
RETRY = 3

LIB = "[data-director-model-library-trigger]"
VCAM = "[data-director-phone-vcam-trigger]"
CROWD = "[data-director-crowd-trigger]"
BY = {"lib": LIB, "vcam": VCAM, "crowd": CROWD}
NAME = {"lib": "modelLibraryOpen", "vcam": "phoneVcamOpen",
        "crowd": "crowdPanelOpen"}

#: 第①道·单点（判别力）；第②道·**有序对**（6 个）
ARMS = [{"id": "only_" + k, "order": [k]} for k in ("lib", "vcam", "crowd")]
ARMS += [{"id": "%sThen%s" % (a, b), "order": [a, b]}
         for a in ("lib", "vcam", "crowd") for b in ("lib", "vcam", "crowd")
         if a != b]
ARM_IDS = [a["id"] for a in ARMS]

ST = """()=>{const q=(s)=>document.querySelector(s);
 const ex=(s)=>{const e=q(s); return e?e.getAttribute('aria-expanded'):null;};
 return {lib: ex('[data-director-model-library-trigger]'),
   vcam: ex('[data-director-phone-vcam-trigger]'),
   crowd: ex('[data-director-crowd-trigger]'),
   libPanel: !!q('[data-director-model-library-panel]'),
   crowdPanel: !!q('[data-director-crowd-panel]'),
   deskOpen: !!q('[role="dialog"][aria-modal="true"]')};}"""


def _click(pg, sel):
    s = pg.evaluate(A.SCAN_CLICK, sel)
    if not s.get("pt"):
        return False
    pg.mouse.click(s["pt"][0], s["pt"][1])
    A.settle(pg, gap=SETTLE)
    return True


def run_cell(pg, arm):
    # ★ `A.fresh()` **已经**做完 goto / 清 localStorage / 打开导演台 ⟹
    #   第一版在这里又 `goto` + `settle` + `open_desk` 一遍，白白把每格耗时翻倍
    opened = A.fresh(pg)
    if isinstance(opened, dict) and opened.get("FAILED"):
        return {"arm": arm["id"], "FAILED": "导演台没打开：%r" % opened}
    st0 = pg.evaluate(ST)
    if not st0.get("deskOpen"):
        return {"arm": arm["id"], "FAILED": "导演台没打开"}
    steps, ok = [], True
    for key in arm["order"]:
        if not _click(pg, BY[key]):
            ok = False
            steps.append({"clicked": key, "FAILED": "点不到触发器 %s" % BY[key]})
            break
        steps.append({"clicked": key, "read": pg.evaluate(ST)})
    reads = [s["read"] for s in steps if "read" in s]
    out = {"arm": arm["id"], "order": arm["order"], "before": st0,
           "steps": steps, "after": pg.evaluate(ST)}
    if not ok:
        out["FAILED"] = "有点不到"
        return out
    last = reads[-1]
    # ★ 派生字段**只**从 `reads` 重算，不信任何上游字段
    out["openAfter"] = {k: last.get(k) == "true" for k in ("lib", "vcam", "crowd")}
    nOpen = sum(1 for v in out["openAfter"].values() if v)
    out["simultaneouslyOpen"] = nOpen
    out["coLive"] = nOpen >= 2
    if len(arm["order"]) == 1:
        only = arm["order"][0]
        out["expect"] = "自己开、另外两个仍关"
        out["verdict"] = (out["openAfter"][only] is True
                          and sum(1 for k, v in out["openAfter"].items()
                                  if k != only and v) == 0)
        # ★ 判别力：点**之前**它必须是关的，否则「点开了」是空转
        out["discriminator"] = (st0.get(only) == "false")
    else:
        first, second = arm["order"]
        third = [k for k in ("lib", "vcam", "crowd")
                 if k not in (first, second)][0]
        out["expect"] = "%s 被 %s 关掉、%s 开、第三个仍关" % (
            NAME[first], NAME[second], NAME[second])
        out["verdict"] = (out["openAfter"][second] is True
                          and out["openAfter"][first] is False
                          and out["openAfter"][third] is False)
        # ★ 判别力：点第二个**之前**第一个必须是**开**的，
        #   否则「被关掉」根本不是一次转变
        out["discriminator"] = (len(reads) > 1
                                and reads[0].get(first) == "true")
    return out


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        print("浏览器已启动", flush=True)
        rounds = []
        for rd in range(ROUNDS):
            rows = []
            for arm in ARMS:
                cell = None
                for t in range(RETRY):
                    pg = b.new_page()
                    pg.set_default_timeout(15000)
                    try:
                        cell = run_cell(pg, arm)
                    except Exception as e:  # noqa: BLE001
                        cell = {"arm": arm["id"],
                                "FAILED": "%s: %s" % (type(e).__name__, e)}
                    finally:
                        try:
                            pg.close()
                        except Exception:  # noqa: BLE001
                            pass
                    cell["tries"] = t + 1
                    cell["retried"] = t > 0
                    if not cell.get("FAILED"):
                        break
                rows.append(cell)
                print("  %-22s %s" % (arm["id"],
                                       "OK" if cell.get("verdict") else
                                       ("FAILED:%s" % cell.get("FAILED",
                                                              "verdict=false"))),
                      flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
            print("round %d 完成" % (rd + 1), flush=True)
        b.close()
    OUT.write_text(json.dumps({"batch": 786, "arms": ARM_IDS,
                               "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

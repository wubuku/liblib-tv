#!/usr/bin/env python3
"""batch 773 探针 b：只补「中性键对照」那 6 格（探针 a 的循环漏了 neutral 臂）

探针 a 的 `for want in (...)` 补丁没落进文件 ⟹ **中性臂一次都没跑**（48 行/轮
= 45 实验 + 3 SKIP）。不整套重跑（R96），只补这 6 格。

★ 中性对照是**整批推理的前提**，不是锦上添花：
  「`defaultPrevented=true` 就等于桌内那个分支跑了」这条推理，依赖
  「间谍排在桌内那个处理器**之后**」且「桌内那个处理器**不处理** F2」。
  少这一格，整批 30 个 dp=true 都不知道该信几分。

格：6 个浮层 × 1 键（`F2`，桌内**明确不处理**）× 2 轮。
"""
import json
import pathlib
import runpy
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.argv = ["dbg773a.py"]
mod = runpy.run_path(str(HERE / "dbg773a.py"))

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch773-2026-10-01/raw/vb773b.json")
mod["OUT"] = OUT

fresh = mod["fresh"]
click_tree_row = mod["click_tree_row"]
TREE = mod["TREE"]
SPY = mod["SPY"]
SPY_READ = mod["SPY_READ"]
FOCUS_IN = mod["FOCUS_IN"]
SCAN_CLICK = mod["SCAN_CLICK"]
STATE = mod["STATE"]
DESK = mod["DESK"]
DISCLOSURES = mod["DISCLOSURES"]
NEUTRAL_KEY = mod["NEUTRAL_KEY"]


def run_cell(pg, d):
    R = {"id": d["id"], "want": "neutral", "key": NEUTRAL_KEY}
    r = fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    target = mod["CAM"] if d["needs"] == "camera" else None
    if target is None:
        ids = (pg.evaluate(TREE) or {}).get("objectIds") or []
        if not ids:
            R["FAILED"] = "对象树里没有对象"
            return R
        target = ids[0]
    click_tree_row(pg, target)
    t1 = pg.evaluate(TREE)
    R["selectedIds"] = t1.get("selectedIds")
    if target not in (t1.get("selectedIds") or []):
        R["FAILED"] = "目标没选中"
        return R
    R["target"] = target
    R["targetUndeletable"] = (target == mod["CAM"])
    s = pg.evaluate(SCAN_CLICK, d["trigger"])
    if not s.get("pt"):
        R["FAILED"] = "触发器点不动"
        return R
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(650)
    if not pg.evaluate(STATE, [d["panel"]]).get("panelPresent"):
        R["FAILED"] = "点了但浮层没出现"
        return R
    f = pg.evaluate(FOCUS_IN, [d["panel"], "noneditable"])
    R["focus"] = f
    if f.get("err"):
        R["FAILED"] = "放不进焦点：%s" % f["err"]
        return R
    R["spy"] = pg.evaluate(SPY)
    pg.evaluate(SPY_READ)
    R["before"] = pg.evaluate(TREE)
    pg.keyboard.press(NEUTRAL_KEY)
    pg.wait_for_timeout(450)
    log = pg.evaluate(SPY_READ)
    R["spyLog"] = log
    R["after"] = pg.evaluate(TREE)
    hits = [x for x in log if x.get("key")]
    R["eventsSeen"] = len(hits)
    R["keysSeen"] = [x.get("key") for x in hits]
    R["dpAll"] = [x.get("dp") for x in hits]
    R["defaultPrevented"] = hits[-1].get("dp") if hits else None
    R["objectsDelta"] = ((R["after"].get("objectCount") or 0)
                         - (R["before"].get("objectCount") or 0))
    R["deskStillOpen"] = pg.evaluate(DESK).get("open")
    if not hits:
        R["FAILED"] = "间谍一个 keydown 都没收到"
    return R


def main():
    from playwright.sync_api import sync_playwright
    res = {"batch": 773, "probe": "b",
           "question": "只补中性键对照：桌内**不处理**的 F2 必须读到 "
                       "defaultPrevented=false",
           "supersedes": "探针 a 的 `for want in (...)` 补丁没落进文件 ⟹ "
                         "中性臂一次都没跑；不整套重跑（R96）",
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 1440, "height": 1000})
        pg = ctx.new_page()
        try:
            for i in range(2):
                R = {"rows": []}
                res["rounds"].append(R)
                print("round %d" % (i + 1))
                for d in DISCLOSURES:
                    try:
                        r = run_cell(pg, d)
                    except Exception as e:
                        r = {"id": d["id"], "want": "neutral",
                             "key": NEUTRAL_KEY,
                             "FAILED": "%s: %s" % (type(e).__name__,
                                                   str(e)[:150])}
                    R["rows"].append(r)
                    if r.get("FAILED"):
                        print("   %-10s FAILED: %s"
                              % (d["id"], str(r["FAILED"])[:50]))
                    else:
                        print("   %-10s 键流=%-12s defaultPrevented=%s"
                              % (d["id"], r.get("keysSeen"),
                                 r.get("defaultPrevented")))
        finally:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            try:
                br.close()
            except Exception:
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("（已落盘）")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 778 探针 A —— **`Cmd+Z` 的早退是「按设计」还是「缺陷」？按控件类型拆开**

## 这一批要更正的是**我自己上一批的结论**

777 把「焦点在检查器输入框上时删除不可撤销」记成缺陷 **D1d（中-高）**。
但那可能是**按设计**：焦点在输入框时 `Cmd+Z` 本就该撤销**输入框自己的编辑**。
775 的 C775-1 正是「把按设计写成新缺陷」—— 我在 777 犯了一次同族错误。

★ 关键读数（冒烟已测到，方向由源码推出）：
  - `number` input **有**原生撤销栈 ⟹ 早退是**取舍**
  - `range` input **没有**原生撤销栈 ⟹ 那一格**什么都撤不掉** ⟹ **真空**

⟹ **D1d 的范围要按控件类型拆开**，而这**直接缩小了 D14 修法的授权范围**：
number 族的早退语义**不必动**。

## 为什么必须两个读数同时看

只看「场景有没有撤回来」会得出「撤销失效」，而那可能只是
「撤销去了该去的地方」。所以每格同时读：

| 读数 | 含义 |
| --- | --- |
| `valueBefore/After` | 控件**自己**的值变了没 ⟹ **原生撤销**有没有生效 |
| `past/future` | 文档历史走没走 ⟹ **桌的撤销**有没有生效 |

★ 三个读数**都**可能同时「没变」，而那正是**真空**——
只报其中任何一个都会把「真空」误判成「原生撤销」或「文档撤销」。

## 四个动作臂（每族各四臂 ⟹ 按控件类型成对比较）

| 臂 | 做什么 | 区分什么 |
| --- | --- | --- |
| `native` | 聚焦 → 改动 → **`Cmd+Z`（不 blur）** | 原生撤销有没有 |
| `docAfterBlur` | 聚焦 → 改动 → **blur 到非输入控件** → `Cmd+Z` | 改动**进不进历史**、文档撤销有没有 |
| `whileFocused` | 聚焦 → 改动 → **`Cmd+Z`（不 blur）** | 与 `native` 同动作，**但同时**看文档历史 ⟹ 真空格 |
| `delWhileFocused` | 删对象（不进历史的那一步）→ 焦点留在控件 → `Cmd+Z` | 复现 777 的 D1d，**并按族分开** |

## 手势生命周期普查

776/777 都没单独量过「手势从聚焦到提交」的全过程，而它决定
「改动进不进历史」。每族记三阶段：**聚焦后 / 改动后 / blur 后**。

★ 一个我**预测错了**的地方（留作记录）：我以为方向键改 range 会
「开一个永不提交的手势」⟹ 预测之后第一次 `Cmd+Z` 是死键。
**实测否掉了它**：手势确实一直开着，但**blur 时提交**（`past` 0→1），
且**第一次 `Cmd+Z` 就生效**。⟹ 断言炸了是机制读错了，是要改的**发现**，
不是要改的断言。
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
    "liblib-canvas-batch778-2026-10-01/raw/vb778a.json")

CAM = A.CAM
MUG = "director-prop-mug"
#: 两族各一个代表控件（族与族的规模由 776 的普查给出，本批不重复普查）
FAM = {
    # number：变换字段（相机选中时可见）
    "number": {"sel": '[data-director-transform-field]'
                        '[data-director-transform-axis="x"]',
               "oid": CAM, "mutate": "type", "text": "7.5"},
    # range：FOV 滑杆
    "range": {"sel": "[data-director-camera-fov]",
              "oid": CAM, "mutate": "arrows", "text": ""},
}
TREE_BTN = "[data-director-panels-toggle]"
DEL_ROW = '[data-director-delete-object="%s"]' % MUG
ARMS = ["native", "docAfterBlur", "whileFocused", "delWhileFocused"]
SETTLE = 500
MAX_TRIES = 3

STATE = """()=>{const q=(n)=>{const e=document.querySelector('['+n+']');
  return e? (e.getAttribute(n)||'') : null;};
 const ae=document.activeElement;
 return {past:q('data-director-history-past'),
   future:q('data-director-history-future'),
   gesture:q('data-director-active-gesture'),
   lastCommand:q('data-director-last-command'),
   lastDisp:q('data-director-last-disposition'),
   focusTag:ae?ae.tagName:null, focusType:ae?ae.getAttribute('type'):null,
   isInput:!!(ae&&(ae.tagName==='INPUT'||ae.tagName==='TEXTAREA'
     ||ae.tagName==='SELECT'))};}"""

VAL = """(s)=>{const e=document.querySelector(s);
 return e? {value:e.value, type:e.getAttribute('type')} : null;}"""

FOCUS = """(s)=>{const e=document.querySelector(s);
 if(!e) return {err:'no el'};
 if(e.disabled) return {err:'disabled'};
 e.focus({preventScroll:true});
 return {ok:document.activeElement===e, value:e.value,
   type:e.getAttribute('type')};}"""


def _selfcheck(pg, oid):
    r = A.fresh(pg)
    if r.get("FAILED"):
        return False, "导演台没开"
    A.click_tree_row(pg, oid)
    A.settle(pg)
    sel = (pg.evaluate(A.TREE) or {}).get("selectedIds") or []
    if oid not in sel:
        return False, "选中没落在 %s（实为 %r）" % (oid, sel)
    st = pg.evaluate(STATE)
    if st.get("past") != "0" or st.get("future") != "0":
        return False, "起始历史不干净（past=%r future=%r）—— 不是有效读数" % (
            st.get("past"), st.get("future"))
    return True, None


def _mutate(pg, fam, sel):
    """按族的原生交互方式改值：number 键入、range 方向键。"""
    if fam == "number":
        pg.keyboard.press("Meta+a")
        pg.keyboard.type("7.5")
    else:
        for _ in range(5):
            pg.keyboard.press("ArrowUp")
    pg.wait_for_timeout(SETTLE)


def run_cell(pg, fam, arm):
    R = {"family": fam, "arm": arm}
    d = FAM[fam]
    ok, why = _selfcheck(pg, d["oid"])
    if not ok:
        R["FAILED"] = why
        return R
    R["selector"] = d["sel"]
    f = pg.evaluate(FOCUS, d["sel"])
    R["focus"] = f
    if f.get("err") or not f.get("ok"):
        R["FAILED"] = "聚焦失败：%s" % (f.get("err") or "焦点未落上")
        return R
    pg.wait_for_timeout(SETTLE)
    R["stateOnFocus"] = pg.evaluate(STATE)
    R["valueOnFocus"] = pg.evaluate(VAL, d["sel"])
    if arm == "delWhileFocused":
        # ★ 先删对象，**焦点留在控件上**（复现 777 的 D1d）
        s = pg.evaluate(A.SCAN_CLICK, DEL_ROW)
        if not s.get("pt"):
            R["FAILED"] = "按行删除按钮点不动"
            return R
        pg.mouse.click(s["pt"][0], s["pt"][1])
        pg.wait_for_timeout(SETTLE + 150)
        ids = (pg.evaluate(A.TREE) or {}).get("objectIds") or []
        R["mugGoneAfterDel"] = MUG not in ids
        R["pastAfterDel"] = (pg.evaluate(STATE) or {}).get("past")
        # 删除动作会把焦点移走 ⟹ 必须**重新**聚焦，且自证
        f2 = pg.evaluate(FOCUS, d["sel"])
        pg.wait_for_timeout(SETTLE)
        R["focusAfterDel"] = f2
        R["stateBeforeUndo"] = pg.evaluate(STATE)
        if not f2.get("ok"):
            R["FAILED"] = "★ 删除后焦点没能回到控件 —— 这一格不是有效读数"
            return R
    else:
        _mutate(pg, fam, d["sel"])
        R["valueAfterMutate"] = pg.evaluate(VAL, d["sel"])
        R["stateAfterMutate"] = pg.evaluate(STATE)
        if arm == "docAfterBlur":
            fb = pg.evaluate(FOCUS, TREE_BTN)
            pg.wait_for_timeout(SETTLE)
            R["blurFocusOk"] = bool(fb.get("ok"))
            R["stateAfterBlur"] = pg.evaluate(STATE)
            R["valueAtUndo"] = pg.evaluate(VAL, d["sel"])
            if not fb.get("ok"):
                R["FAILED"] = "★ blur 落点没聚焦上 —— 这一格不是有效读数"
                return R
    pg.keyboard.press("Meta+z")
    pg.wait_for_timeout(SETTLE + 150)
    R["stateAfterUndo"] = pg.evaluate(STATE)
    R["valueAfterUndo"] = pg.evaluate(VAL, d["sel"])
    ids = (pg.evaluate(A.TREE) or {}).get("objectIds") or []
    R["mugBack"] = MUG in ids
    R["objects"] = len(ids)
    return R


def run_census(pg, R):
    """手势生命周期普查：聚焦后 / 改动后 / blur 后，每族各三阶段。

    ★ 这是 776/777 都没单独量过的一段，而它决定「改动进不进历史」。
    """
    R["lifecycle"] = []
    for fam, d in FAM.items():
        ok, why = _selfcheck(pg, d["oid"])
        if not ok:
            R["lifecycle"].append({"family": fam, "FAILED": why})
            continue
        row = {"family": fam, "selector": d["sel"]}
        pg.evaluate(FOCUS, d["sel"])
        pg.wait_for_timeout(SETTLE)
        row["onFocus"] = pg.evaluate(STATE)
        _mutate(pg, fam, d["sel"])
        row["afterMutate"] = pg.evaluate(STATE)
        row["valueAfterMutate"] = pg.evaluate(VAL, d["sel"])
        pg.evaluate(FOCUS, TREE_BTN)
        pg.wait_for_timeout(SETTLE)
        row["afterBlur"] = pg.evaluate(STATE)
        row["typeSeen"] = (row["onFocus"] or {}).get("focusType")
        R["lifecycle"].append(row)


def run_round(pg, R):
    R["rows"] = []
    R["lifecycle"] = []
    run_census(pg, R)
    for fam in ("number", "range"):
        for arm in ARMS:
            r, tries = None, 0
            while tries < MAX_TRIES:
                tries += 1
                try:
                    r = run_cell(pg, fam, arm)
                except Exception as e:  # noqa: BLE001
                    r = {"family": fam, "arm": arm,
                         "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
                if not r.get("FAILED"):
                    break
                pg.wait_for_timeout(900 * tries)
            r["tries"] = tries
            if tries > 1:
                r["retried"] = True
            R["rows"].append(r)


def summarize(R):
    for row in R.get("lifecycle") or []:
        if row.get("FAILED"):
            print("   生命周期 %-7s FAILED %s" % (row["family"], row["FAILED"][:40]))
            continue
        o, m, b = row["onFocus"], row["afterMutate"], row["afterBlur"]
        print("   生命周期 %-7s type=%-7s 聚焦后 手势=%-4s past=%s → "
              "改动后 手势=%-4s past=%s → blur后 手势=%-4s past=%s"
              % (row["family"], row.get("typeSeen"),
                 "有" if o["gesture"] else "空", o["past"],
                 "有" if m["gesture"] else "空", m["past"],
                 "有" if b["gesture"] else "空", b["past"]))
    for r in R.get("rows") or []:
        if r.get("FAILED"):
            print("   %-7s %-17s FAILED(试 %s): %s"
                  % (r["family"], r["arm"], r.get("tries"), r["FAILED"][:46]))
            continue
        vb = r.get("valueBeforeUndo") or r.get("valueAtUndo") or {}
        va = (r.get("valueAfterUndo") or {}).get("value")
        s0 = r.get("stateBeforeUndo") or r.get("stateAfterMutate") or {}
        s1 = r.get("stateAfterUndo") or {}
        print("   %-7s %-17s 值 %-7s → %-7s 变化=%-5s ｜ past %s→%s future %s→%s"
              " ｜ 道具回来=%s"
              % (r["family"], r["arm"], vb.get("value"), va,
                 "是" if str(vb.get("value")) != str(va) else "否",
                 s0.get("past"), s1.get("past"), s0.get("future"),
                 s1.get("future"), r.get("mugBack")))


def main():
    res = {"batch": 778, "probe": "a",
           "question": "焦点在检查器控件上时 Cmd+Z 的早退 —— 「按设计」还是「缺陷」？"
                       "**按控件类型拆开**（这一批更正我自己 777 的 D1d）",
           "whyItMatters": "777 把「输入框落点上删除不可撤销」记成缺陷 D1d（中-高），"
                           "但焦点在输入框时 Cmd+Z 本就该撤销**输入框自己的编辑**。"
                           "★ 775 的 C775-1 正是「把按设计写成新缺陷」—— 我在 777 "
                           "犯了一次同族错误。",
           "split": "★ 关键读数：`number` input **有**原生撤销栈 ⟹ 早退是**取舍**；"
                    "`range` input **没有** ⟹ 那一格**什么都撤不掉** ⟹ **真空**。"
                    "⟹ **D1d 的范围按控件类型拆开**，而这**直接缩小 D14 修法的"
                    "授权范围**：number 族的早退语义**不必动**。",
           "threeReadings": "★ 每格必须**同时**读三个量：控件自己的 `value`"
                            "（原生撤销）、`past/future`（文档撤销）、道具是否回来。"
                            "**三个都可能「没变」而那正是真空** —— 只报其中一个"
                            "都会把真空误判成原生撤销或文档撤销。",
           "refutedPrediction": "★ 我**预测错了**并留下记录：以为方向键改 range 会"
                                "「开一个永不提交的手势」⟹ 之后第一次 Cmd+Z 是死键。"
                                "**实测否掉了它**：手势确实一直开着，但 blur 时"
                                "**提交**（past 0→1），且第一次 Cmd+Z 就生效。",
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 1440, "height": 1000})
        pg = ctx.new_page()
        try:
            for i in range(2):
                R = {}
                res["rounds"].append(R)
                print("round %d" % (i + 1))
                run_round(pg, R)
                summarize(R)
        finally:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            try:
                br.close()
            except Exception:  # noqa: BLE001
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("（已落盘）")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

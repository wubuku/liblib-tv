#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 774 探针 B —— **问②：方向① 会不会把 Escape 也一起挡掉？**

## 这个问题为什么必须问

方向① 是「把 `isEditable` 那道早退的判据从按标签名换成按浮层」。
`src/` 现读：`DirectorDesk.tsx:486` 那道 `if (isEditable) return;` 排在
**所有分支之前**——Escape 阶梯 `:549-568` 也在它后面。
**所以「守卫一旦在浮层后代上触发」这个前提，同时意味着
「Escape 阶梯也一起被挡掉」**——问① 根本没量这件事。

## 源码里六个浮层的 Escape「主人」是三种不同的注册阶段

| 浮层 | 自己的 Escape 处理 | 注册阶段 | `preventDefault` | `stopImmediatePropagation` |
| --- | --- | --- | --- | --- |
| phonevcam | `DirectorPhoneVcamPanel.tsx:289` `onClose()` | window **捕获** | 有 | 有 |
| modellib | `DirectorViewport.tsx:2740-2747` `setModelLibraryOpen(false)` | window **捕获** | 有 | 有 |
| preset | `DirectorTimeline.tsx:591` `setPresetPanelLeft(null)` | window **冒泡** | **无** | **无** |
| pathmenu | `DirectorTimeline.tsx:567` `setPathMenuLeft(null)` | window **冒泡** | **无** | **无** |
| export | **没有** | — | — | — |
| crowd | **没有** | — | — | — |

**注册阶段决定一切**：捕获阶段那两个（`useEffect` 在 `open` 时注册）
排在桌内那个（挂载时注册的**冒泡**监听器）**之前**，
而它们带 `stopImmediatePropagation()` ⟹ 桌内那个**根本收不到这个事件**。

preset/pathmenu 相反：冒泡阶段、挂载后才注册 ⟹ 桌内那个**先跑**，
它俩只是跟着把面板关掉。**这正是 D8 的成因**——桌内先跑到了
`closeWorkspace()`，层自己的处理随后才跑，面板是关了，工作区也没了。

## 预测（逐行从源码推出，跑出来就该是这个数）

**无注入**（落点是浮层内第一个非可编辑控件 = 按钮 ⟹ `isEditable` 为假）：

| 浮层 | `defaultPrevented` | 面板 | 导演台 | 为什么 |
| --- | --- | --- | --- | --- |
| export | true | 关 | 开 | 桌内 `:559` `exportPanelOpen` 这一档接住了 |
| preset | true | 关 | **关** | 桌内一路 fall through 到 `closeWorkspace()`（D8） |
| pathmenu | true | 关 | **关** | 同上 |
| phonevcam | **读不到** | 关 | 开 | 捕获阶段 `stopImmediatePropagation` ⟹ 桌内与间谍**都收不到** |
| crowd | true | **开** | **关** | 桌内 fall through；crowd 没有自己的处理 |
| modellib | **读不到** | 关 | 开 | 同 phonevcam |

**注入 α**（守卫真的触发 ⟹ `:486` 直接 return）：

| 浮层 | `defaultPrevented` | 面板 | 导演台 | 净后果 |
| --- | --- | --- | --- | --- |
| export | **false** | **开** | 开 | **回归**：Escape 从「关导出面板」变成**死键** |
| preset | false | 关 | 开 | **修好 D8**（层自己的冒泡处理照跑，桌内不动作） |
| pathmenu | false | 关 | 开 | **修好 D8** |
| phonevcam | **读不到** | 关 | 开 | **无变化**（捕获阶段早于一切） |
| crowd | false | **开** | 开 | 从「丢整个工作区」变成**死键** |
| modellib | **读不到** | 关 | 开 | **无变化** |

### ★「间谍收不到事件」是一条**发现**，不是一次读数失败

phonevcam / modellib 那 4 格上，间谍（window **冒泡**）**一个 keydown 都收不到**。

第一版把这整格判成 `FAILED`（「读数不算数」）。**那是分类错误**：
这两个层的主人在**捕获阶段**注册且带 `stopImmediatePropagation()`，
事件在到达 window 冒泡之前就被掐断 —— 桌内那个处理器与间谍**都收不到**。

于是有两件事必须分开说：

1. `defaultPrevented` 在这两层上**结构上不可读**；
2. **「读不到」本身就是证据** —— 它直接证明传播确实被掐断了，
   而这正是静态层预测的那一条。

三态读数（面板/导演台）**不依赖间谍**，仍然有效，那才是这一格真正的测量。
把它判成「读数不算数」就等于把一条发现写成了失败（R97 的要求：
测不出来要说测不出来，而这里是**测出来了，只是量的是别的东西**）。

★ 由此还多出一条**把静态层与运行时连起来**的预测：
**「间谍收不到」的层集合，恰好等于「静态普查里主人在捕获阶段」的层集合**。
两条独立路径得出同一个集合，才算真的对上了。

## 结论该怎么读

方向① **不是**一道干净的守卫：它对 C/V/Z/Y/Delete 五支是纯收益，
对 Escape 那支会**拆掉 export 的面板关闭**（1/6 的真实功能回归），
并把 crowd 从「丢工作区」换成「按了没反应」。

⟹ 修法必须是**分段**的：C/V/Z/Y/Delete 各自加「焦点在浮层内就早退」，
**Escape 阶梯不能共用那道守卫**——它需要的是另一条规则
（焦点在浮层内时**不 fall through 到 `closeWorkspace()`**），
而那条规则与 D8 的修法**是同一处**。

## 读数

三态读数，缺一不可：
- `deskOpen=False` ⟹ 工作区没了（D8）
- `deskOpen=True` 且 `panelPresent=False` ⟹ 只关了层（正确）
- `deskOpen=True` 且 `panelPresent=True` ⟹ **什么都没发生**（死键）

只报「面板还在不在」会把「导演台没了」读成「面板还在」，
所以三个字段必须一起看（R97 的同族：把两个信号合成一个会丢信息）。

## 格子

6 个浮层 × 2 个臂（无注入 / 注入 α）× `Escape` = **12 格 × 2 轮**。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dbg774a as A  # noqa: E402  复用同一批基础设施与同一个落点规则

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch774-2026-10-01/raw/vb774b.json")


def run_cell(pg, d, arm):
    """arm ∈ {"none", "alpha"}。两臂都落在浮层内第一个**非可编辑**控件上。"""
    R = {"id": d["id"], "arm": arm, "key": "Escape"}
    r = A.fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    target = A.CAM if d["needs"] == "camera" else None
    if target is None:
        ids = (pg.evaluate(A.TREE) or {}).get("objectIds") or []
        if not ids:
            R["FAILED"] = "对象树里没有对象"
            return R
        target = ids[0]
    A.click_tree_row(pg, target)
    t1 = pg.evaluate(A.TREE)
    if target not in (t1.get("selectedIds") or []):
        R["FAILED"] = "目标没选中"
        return R
    R["target"] = target
    s = pg.evaluate(A.SCAN_CLICK, d["trigger"])
    if not s.get("pt"):
        R["FAILED"] = "触发器点不动"
        R["scan"] = s
        return R
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(650)
    st = pg.evaluate(A.STATE, [d["panel"]])
    if not st.get("panelPresent"):
        R["FAILED"] = "点了但浮层没出现"
        return R
    f = pg.evaluate(A.FOCUS_IN, [d["panel"], "noneditable"])
    R["focus"] = f
    if f.get("err"):
        R["FAILED"] = "放不进焦点：%s" % f["err"]
        return R
    R["inject"] = None
    if arm == "alpha":
        R["inject"] = pg.evaluate(A.INJECT_ALPHA)
        if R["inject"].get("err"):
            R["FAILED"] = "注入没做上：%s" % R["inject"]["err"]
            return R
        if not R["inject"].get("took"):
            R["injectionSilent"] = True
    R["spy"] = pg.evaluate(A.SPY)
    pg.evaluate(A.SPY_READ)
    R["before"] = pg.evaluate(A.TREE)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(700)
    log = pg.evaluate(A.SPY_READ)
    R["spyLog"] = log
    hits = [x for x in log if x.get("key") == "Escape"]
    R["eventsSeen"] = len(log)
    last = hits[-1] if hits else None
    R["defaultPrevented"] = last.get("dp") if last else None
    R["targetCE"] = last.get("targetCE") if last else None
    R["targetTag"] = last.get("targetTag") if last else None
    R["keysSeen"] = [x.get("key") for x in log]
    R["dpAll"] = [x.get("dp") for x in log]
    # ★ 三态读数：必须把「桌没了」与「只关了层」与「什么都没发生」分开
    desk = pg.evaluate(A.DESK)
    R["deskOpen"] = bool(desk.get("open"))
    R["panelPresent"] = bool(pg.evaluate(A.STATE, [d["panel"]]).get("panelPresent"))
    if not R["deskOpen"]:
        R["outcome"] = "deskGone"          # D8：丢整个工作区
    elif R["panelPresent"]:
        R["outcome"] = "nothing"           # 死键
    else:
        R["outcome"] = "layerClosedOnly"   # 正确
    # ── ★ 间谍收不到事件，**不是探针坏了** ——
    #   phonevcam / modellib 的 Escape 主人在**捕获阶段**注册且带
    #   `stopImmediatePropagation()` ⟹ 事件在到达 window 冒泡之前就被掐断，
    #   桌内那个处理器与本间谍**都收不到**。
    #   ⟹ `defaultPrevented` 在这两层上**结构上不可读**，
    #   而**「读不到」本身就是证据**：它直接证明传播确实被掐断了。
    #   三态读数不依赖间谍，仍然有效 —— 那才是这一格真正的测量。
    #   （第一版把这种情况整格判成 FAILED，是分类错误：它把一条**发现**
    #     写成了「读数不算数」。这正是 R97 的要求：测不出来要说测不出来。）
    R["spySawNothing"] = not hits
    if not hits:
        R["dpUnreadable"] = (
            "传播在捕获阶段被 stopImmediatePropagation() 掐断 —— 间谍"
            "（window 冒泡）收不到这个事件，桌内那个处理器同样收不到。"
            "**收不到本身就是证据**。")
    return R


def run_round(pg, R):
    R["rows"] = []
    for d in A.DISCLOSURES:
        for arm in ("none", "alpha"):
            try:
                r = run_cell(pg, d, arm)
            except Exception as e:
                r = {"id": d["id"], "arm": arm, "key": "Escape",
                     "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
            R["rows"].append(r)


def summarize(R):
    for r in R.get("rows") or []:
        if r.get("FAILED"):
            print("   %-10s %-6s FAILED: %s"
                  % (r["id"], r["arm"], str(r["FAILED"])[:50]))
            continue
        print("   %-10s %-6s targetCE=%-5s dp=%-5s → %-15s "
              "(桌开=%-5s 面板在=%-5s)%s"
              % (r["id"], r["arm"], r.get("targetCE"),
                 r.get("defaultPrevented"), r.get("outcome"),
                 r.get("deskOpen"), r.get("panelPresent"),
                 "  ★注入没生效" if r.get("injectionSilent") else ""))


def main():
    res = {"batch": 774, "probe": "b",
           "question": "问②：方向① 会不会把 Escape 阶梯也一起挡掉？——"
                       "六个浮层的 Escape「主人」分属三种注册阶段，后果各不相同",
           "whyItMatters": "★ `DirectorDesk.tsx:486` 的 `if (isEditable) return;` "
                           "排在**所有分支之前**，Escape 阶梯 `:549-568` 也在它"
                           "后面 ⟹ 「守卫一旦在浮层后代上触发」这个前提**同时**"
                           "意味着「Escape 一起被挡」。问① 没量这件事",
           "escapeOwners": {
               "phonevcam": "DirectorPhoneVcamPanel.tsx:289 捕获+stopImmediate",
               "modellib": "DirectorViewport.tsx:2740-2747 捕获+stopImmediate",
               "preset": "DirectorTimeline.tsx:591 冒泡、无 preventDefault",
               "pathmenu": "DirectorTimeline.tsx:567 冒泡、无 preventDefault",
               "export": "没有自己的处理（靠桌内 :559 exportPanelOpen 那一档）",
               "crowd": "没有自己的处理 ⟹ 桌内一路 fall through 到 closeWorkspace()"},
           "reading": "★ 三态：`deskGone`（丢工作区）/ `layerClosedOnly`（正确）"
                      "/ `nothing`（死键）。只报「面板还在不在」会把「导演台没了」"
                      "读成「面板还在」——三个字段必须一起看（R97 的同族）",
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
            except Exception:
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("（已落盘）")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

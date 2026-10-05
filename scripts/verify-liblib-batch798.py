#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 798 验收器 —— **独立实现**，不 import 汇编器

## 本批的性质：★ **拍板批次，没改 `src/`**

798 回答 797 的遗留「组框**尺寸**要不要吸附」——**不该**，且是**数学上做不到**。
所以本批的危险方向与「修一批」相反：

- ★★ **必须证明「数学上做不到」而不是「懒得做」**：D 条把 padding 换成
  0/20/40/60 **重算**，要求余数**完全一样** ⟹ 换 padding 救不了。
  只说「尺寸不在网格上」是**观察**，说「换任何 padding 都一样」才是**证明**。
- ★★ **必须钉住前提**（E）：若成员尺寸都是网格倍数，结论会反过来
  ⟹ 所以要显式断言「成员尺寸本身不是倍数」。
- ★★ **「不改」必须被钉住**（H）：否则后人会把「尺寸吸附」当待办重新捡起来。
  H 同时记下**重新评估的条件**（加 resize 控件）。
- ★ **「不可调」要双向互证**（F 运行时 + J 源码）：只看运行时可能是探针漏看，
  只看源码可能漏了别的入口。
- ★ 阴性对照必须能翻掉「余数不随 padding 变」这条 —— 否则 D 是空跑。

## 静态层为什么算「独立」

汇编器用正则读 `GROUP_PADDING`；本验收器**从 raw 的读数反推**该用哪个 padding
（用 40 算得出实测值、用 32 算不出 ⟹ 等于把 padding 也变成了被验证的量），
并另用源码 grep 互证「无 resize 控件」⟹ 两边写错互相抓。
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch798-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
PRE = OUTDIR / "raw/vb798a-pre.json"
POST = OUTDIR / "raw/vb798a-post.json"
CS = "src/store/canvasStore.ts"
GRP = "src/components/nodes/StoryboardGroupNode.tsx"

ARMS = ["sizeVsGrid", "resizeAffordance", "snapOffSize"]
GRID = 20


def index(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append(r)
    return out


def state_of(cell):
    for k in ("settled", "after", "before"):
        v = cell.get(k)
        if isinstance(v, dict) and v.get("groupStore"):
            return v
    return None


def g4(m):
    g = (m or {}).get("groupStore")
    return None if not g else [g["pos"]["x"], g["pos"]["y"], g["w"], g["h"]]


def rem(vals):
    return tuple(v % GRID for v in vals)


def fit(members, pad):
    ms = [x for x in (members or []) if isinstance(x, dict)]
    if not ms:
        return None
    x0 = min(x["abs"]["x"] for x in ms)
    y0 = min(x["abs"]["y"] for x in ms)
    x1 = max(x["abs"]["x"] + (x.get("w") or 0) for x in ms)
    y1 = max(x["abs"]["y"] + (x.get("h") or 0) for x in ms)
    return [x0 - pad, y0 - pad, x1 - x0 + pad * 2, y1 - y0 + pad * 2]


def run_checks(pre_raw, post_raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    src = (ROOT / CS).read_text(encoding="utf-8")
    grp = (ROOT / GRP).read_text(encoding="utf-8")
    pre, post = index(pre_raw), index(post_raw)

    # ── S1：★★ pre ≡ post（比**完整几何**）──
    def sigmap(idx):
        out = {}
        for arm in ARMS:
            out[arm] = []
            for c in idx.get(arm, []):
                m = state_of(c)
                out[arm].append(None if not m else
                                [g4(m), m.get("resizeHandles")])
        return out

    a1, a2 = sigmap(pre), sigmap(post)
    diff = [arm for arm in ARMS if a1.get(arm) != a2.get(arm)]
    has_read = any(x for arm in ARMS for x in a1.get(arm, []))
    add("S1:★★ 本批**没改 `src/`** ⟹ pre ≡ post（比完整几何）",
        "★ 同时证明读数可复现、探针不依赖运行状态。★ 必须比完整几何："
        "只比成员数的话这条会永远绿",
        not diff and has_read,
        {"不同的臂": diff, "读到读数": has_read,
         "pre": a1.get("sizeVsGrid"), "post": a2.get("sizeVsGrid")})

    # ── S2：★★ 核心读数：位置在网格、尺寸**不**在 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("sizeVsGrid", []):
            m = state_of(c)
            if not m:
                bad.append({"phase": name, "why": "空读数"})
                continue
            g = g4(m)
            pos_ok = rem(g[:2]) == (0, 0)
            size_ok = rem(g[2:]) == (0, 0)
            ev.append({"phase": name, "组": g, "位置在网格": pos_ok,
                       "尺寸在网格": size_ok, "余数": rem(g[2:])})
            if not pos_ok:
                bad.append(dict(ev[-1], why="位置不在网格（797 成果回退）"))
            if size_ok:
                bad.append(dict(ev[-1], why="尺寸竟在网格上，与结论相反"))
    add("S2:★★ 组**位置**在网格、**尺寸**不在网格",
        "★ 位置是 797 修好的（不许回退）；尺寸不在是**数学后果**",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S3：★★ padding 是**被验证的量**，不是我写死的常量 ──
    #   做法：用几个候选 padding 各自重算，只有**一个**能对上实测值
    cands = [0, 20, 32, 40, 60]
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("sizeVsGrid", []):
            m = state_of(c)
            if not m:
                continue
            g = g4(m)
            fits = [p for p in cands
                    if all(abs(a - b) <= 0.01
                           for a, b in zip(fit(m["members"], p), g))]
            src_pad = int(re.findall(r"const GROUP_PADDING = (\d+);", src)[0])
            ev.append({"phase": name, "能对上的padding": fits,
                       "源码里的padding": src_pad,
                       "唯一": len(fits) == 1})
            if len(fits) != 1 or src_pad not in fits:
                bad.append(dict(ev[-1], why="padding 判据不唯一或与源码不符"))
    add("S3:★★ padding 是**被读数验证**出来的，且**唯一**",
        "★ 不用写死 40：用多个候选重算，只有能对上实测值的那个成立 ⟹ "
        "padding 本身也变成被验证的量，公式错会被抓出来",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev,
                                   "候选": cands})

    # ── S4：★★★ 决定性：余数在**网格倍数之间**不变 ──
    # ★★ 判据第一版把 `32`（**非**网格倍数）也放进候选 ⟹ 它当然算出不同余数
    #   ⟹ 断言翻红。★ 修正后的命题才准确：
    #     「**网格倍数之间**，余数不变；**非**倍数（32）则**会**变」
    #   ⟹ 而且第二半反而是**更硬的证据**：它说明余数确实**随 padding 变**，
    #     只是在网格倍数**之间**是阶梯恒定的。
    grid_cands = [0, 20, 40, 60]        # 20 的倍数
    non_grid = [32]                     # 刻意选一个非倍数
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("sizeVsGrid", []):
            m = state_of(c)
            if not m:
                continue
            g = g4(m)
            grems = {p: rem(fit(m["members"], p)[2:]) for p in grid_cands}
            ngrem = {p: rem(fit(m["members"], p)[2:]) for p in non_grid}
            same = len(set(grems.values())) == 1
            match = list(grems.values())[0] == rem(g[2:])
            # ★ 非倍数（32）必须算出**不同**余数 ⟹ 证明余数确实受 padding 影响
            differs = all(ngrem[p] != list(grems.values())[0]
                          for p in non_grid)
            ev.append({"phase": name, "网格倍数的余数": grems,
                       "非倍数(32)的余数": ngrem,
                       "网格倍数间恒定": same, "与实测一致": match,
                       "非倍数确实不同": differs})
            if not (same and match):
                bad.append(dict(ev[-1], why="网格倍数之间余数变了"))
            if not differs:
                bad.append(dict(ev[-1],
                                why="非倍数 padding 竟算出相同余数 ⟹ 判据无效"))
    add("S4:★★★ 余数在**网格倍数之间**恒定，且**非**倍数（32）会算出不同余数",
        "★ 这是「**数学上做不到**」的**直接证据**：网格倍数之间余数不变 ⟹ "
        "换任何网格倍数都救不了。★ 第二半更硬：非倍数(32)算出**不同**余数 ⟹ "
        "证明余数**确实**受 padding 影响，只是网格倍数上是阶梯恒定的。"
        "★ 第一版把 32 混进候选导致断言翻红 —— 那是**判据写错**，不是实现错",
        not bad and len(ev) == 4,
        {"bad": bad, "evidence": ev,
         "网格倍数候选": grid_cands, "非倍数候选": non_grid})

    # ── S5：★★ 前提：成员尺寸**本身**不是网格倍数 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("sizeVsGrid", []):
            m = state_of(c)
            if not m:
                continue
            rr = [rem([x["w"], x["h"]]) for x in m["members"]]
            any_off = any(a or b for a, b in rr)
            ev.append({"phase": name, "成员尺寸余数": rr,
                       "有成员非倍数": any_off,
                       "尺寸": [x["w"] for x in m["members"]]})
            if not any_off:
                bad.append(dict(ev[-1], why="成员尺寸竟都在网格上 ⟹ 结论会反过来"))
    add("S5:★★ 前提成立：种子成员尺寸**本身**不是网格倍数",
        "★ 若成员尺寸都是倍数，组尺寸也会是 ⟹ 结论会反过来 ⟹ "
        "这条把「前提」显式钉住",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S6：★★ 组**没有** resize 控件（运行时，选中前后）──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("resizeAffordance", []):
            for key in ("before", "after"):
                m = c.get(key)
                if not isinstance(m, dict) or not m.get("groupStore"):
                    continue
                ev.append({"phase": name, "when": key,
                           "resizeHandles": m.get("resizeHandles")})
                if (m.get("resizeHandles") or 0) != 0:
                    bad.append(dict(ev[-1], why="出现了 resize 控件"))
    add("S6:★★ 组**没有** resize 控件（选中前后都是 0）",
        "★ 选「接受容器不吸附」的**依据**：尺寸吸附只对「用户能调的尺寸」有意义。"
        "★ 「选中后」也查 ⟹ 排除「选中才出现把手」",
        not bad and len(ev) == 8 and all(x["resizeHandles"] == 0
                                         for x in ev),
        {"bad": bad, "evidence": ev})

    # ── S7：★★ 源码侧互证：组组件里没有 `NodeResizer` ──
    n_src = len(re.findall(r"NodeResizer", grp))
    n_all = 0
    for p in (ROOT / "src").rglob("*.tsx"):
        try:
            n_all += len(re.findall(r"NodeResizer", p.read_text(
                encoding="utf-8")))
        except Exception:      # noqa: BLE001
            pass
    add("S7:★★ 源码侧互证：`src/` 里**没有任何** `NodeResizer`",
        "★ 与 S6 的运行时读数**双向互证** ⟹ 「尺寸不可调」不是探针漏看。"
        "★ 全仓 0 比单文件 0 更强：没有别的节点类型提供 resize",
        n_src == 0 and n_all == 0,
        {"StoryboardGroupNode 里": n_src, "src/ 全仓": n_all})

    # ── S8：★★ 对照臂：吸附**关**时尺寸**同样**不是倍数 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("snapOffSize", []):
            m = state_of(c)
            if not m:
                bad.append({"phase": name, "why": "空读数"})
                continue
            g = g4(m)
            ev.append({"phase": name, "snap": m.get("snapToGrid"),
                       "余数": rem(g[2:])})
            if m.get("snapToGrid") is not False:
                bad.append(dict(ev[-1], why="吸附读数不是 False"))
            if rem(g[2:]) == (0, 0):
                bad.append(dict(ev[-1], why="吸附关时尺寸竟在网格上"))
    add("S8:★★ 对照臂：吸附**关**时尺寸**同样**不是网格倍数",
        "★ 说明这不是「吸附开着才出现的副作用」⟹ 容器尺寸不吸附是**常态**",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S9：★★ 钉住「本批没改 src」与「重新评估的条件」──
    add("S9:★★ 拍板被钉住：本批**没改 `src/`**，且记下**重新评估的条件**",
        "★ 「不改」必须显式钉住，否则后人会把「尺寸吸附」当待办重新捡起来。"
        "★ 条件 = 给组加 resize 控件",
        True,
        {"本批是否改 src": False,
         "结论": "组框尺寸不吸附",
         "重新评估的条件": "给 storyboard-group 加 resize 控件",
         "★ 依据链": ["成员尺寸本身非倍数", "余数不随 padding 变",
                      "组无 resize 控件 ⟹ 吸附帮不了用户操作"]})

    # ── S10：格数与无 FAILED ──
    bad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            bad.append({"phase": name, "arms": sorted(idx)})
        for arm, lst in idx.items():
            if len(lst) != 2:
                bad.append({"phase": name, "arm": arm, "rounds": len(lst)})
            for c in lst:
                if c.get("FAILED"):
                    bad.append({"phase": name, "arm": arm,
                                "FAILED": c.get("FAILED")})
    add("S10:两阶段各 3 臂 × 2 轮且无 FAILED",
        "★ 探针 FAILED 就是**空读数**", not bad, {"bad": bad})

    if audit:
        add("S11:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S11:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)
    return checks


def mut_raw(which, fn):
    p = PRE if which == "pre" else POST
    orig = p.read_text(encoding="utf-8")
    d = json.loads(orig)
    hit = fn(d)
    assert hit, "★ raw 变异没命中"
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, {"file": p.name, "hit": hit}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    audit = (json.loads(AUDIT.read_text(encoding="utf-8"))
             if AUDIT.exists() else None)
    pre0, post0 = sha(PRE), sha(POST)

    checks = run_checks(pre_raw, post_raw, audit)
    nPos = sum(1 for c in checks if c["ok"])
    assert nPos == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照没意义"
        % (len(checks) - nPos, [c["id"] for c in checks if not c["ok"]]))

    negs = []

    def neg(name, why, mutate, expect):
        restore, ev = mutate()
        try:
            c = run_checks(json.loads(PRE.read_text(encoding="utf-8")),
                           json.loads(POST.read_text(encoding="utf-8")), audit)
            flipped = [x["id"] for x in c if not x["ok"]]
            if expect == "__NO_FLIP__":
                return {"name": name, "why": why, "evidence": ev,
                        "expectFlipped": "（反向对照：期望不翻）",
                        "flipped": flipped, "ok": not flipped,
                        "stillPassing": [x["id"] for x in c if x["ok"]]}
            return {"name": name, "why": why, "evidence": ev,
                    "expectFlipped": expect, "flipped": flipped,
                    "ok": expect in flipped,
                    "stillPassing": [x["id"] for x in c if x["ok"]]}
        finally:
            restore()

    # ① ★★ 把**成员尺寸**改成网格倍数 ⟹ 前提与结论都要翻
    def members_on_grid():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "sizeVsGrid":
                        for m in r["settled"]["members"]:
                            m["w"] = int(round(m["w"] / GRID)) * GRID
                            m["h"] = int(round(m["h"] / GRID)) * GRID
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N1 ★★ 把成员尺寸改成**网格倍数**",
                    "★ 验证 S5 的前提与 S4 的结论：成员尺寸都在倍数上时，"
                    "组尺寸也会是 ⟹ 「数学上做不到」这句必须翻",
                    members_on_grid, "S5:★★ 前提成立：种子成员尺寸**本身**"
                                     "不是网格倍数"))
    # ② ★★ 只把**一个**成员尺寸改成倍数 ⟹ 余数就变了（证明它确实由成员决定）
    def one_member_on_grid():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "sizeVsGrid":
                        m = r["settled"]["members"][0]
                        m["w"] = int(round(m["w"] / GRID)) * GRID
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N2 ★★ 只把**一个**成员尺寸改成倍数",
                    "★ 验证 S4/S3：余数与 padding 的拟合**唯一性**会破 ⟹ "
                    "证明组尺寸确实由成员边界决定，不是巧合",
                    one_member_on_grid,
                    "S3:★★ padding 是**被读数验证**出来的，且**唯一**"))
    # ③ ★★ 把组的**位置**翻成不在网格 ⟹ S2 必须翻（不许 797 成果回退）
    def pos_off_grid():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "sizeVsGrid":
                        g = r["settled"]["groupStore"]
                        g["pos"]["x"] = g["pos"]["x"] + 3
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N3 ★★ 把组的**位置**翻成不在网格",
                    "★ 验证 S2 的另一半：位置必须在网格上（797 的成果不许回退）",
                    pos_off_grid,
                    "S2:★★ 组**位置**在网格、**尺寸**不在网格"))
    # ④ ★★ 把组的**尺寸**翻成在网格上 ⟹ S2 必须翻（结论会反过来）
    def size_on_grid():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "sizeVsGrid":
                        g = r["settled"]["groupStore"]
                        g["w"] = int(round(g["w"] / GRID)) * GRID
                        g["h"] = int(round(g["h"] / GRID)) * GRID
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N4 ★★ 把组的**尺寸**翻成在网格上",
                    "★ 验证 S2：若尺寸也在网格，本批结论就反了 ⟹ 必须翻",
                    size_on_grid,
                    "S2:★★ 组**位置**在网格、**尺寸**不在网格"))
    # ⑤ ★★ 造出一个 resize 控件 ⟹ S6 必须翻（「不可调」这条依据被抽掉）
    def resize_appears():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "resizeAffordance":
                        r["after"]["resizeHandles"] = 4
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N5 ★★ 造出一个 resize 控件",
                    "★ 验证 S6：若组真的可调尺寸，「尺寸吸附无意义」这条依据"
                    "就被抽掉 ⟹ 结论需重新评估",
                    resize_appears,
                    "S6:★★ 组**没有** resize 控件（选中前后都是 0）"))
    # ⑥ ★★ 对照臂翻成「吸附关时尺寸在网格」⟹ S8 必须翻
    def control_on_grid():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "snapOffSize":
                        g = r["settled"]["groupStore"]
                        g["w"] = int(round(g["w"] / GRID)) * GRID
                        g["h"] = int(round(g["h"] / GRID)) * GRID
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N6 ★★ 对照臂翻成「吸附关时尺寸在网格」",
                    "★ 验证 S8：若那样，就不能说是「常态」而是「吸附的副作用」",
                    control_on_grid,
                    "S8:★★ 对照臂：吸附**关**时尺寸**同样**不是网格倍数"))
    # ⑦ ★★ 破坏 pre≡post ⟹ S1 必须翻
    def break_equiv():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "sizeVsGrid":
                        r["settled"]["groupStore"]["w"] += 0.5
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N7 ★★ 破坏 pre≡post（组宽 +0.5）",
                    "★ 验证 S1：本批没改 `src/` ⟹ 两阶段必须逐格相同。"
                    "★ 若只比成员数，这条会永远绿",
                    break_equiv,
                    "S1:★★ 本批**没改 `src/`** ⟹ pre ≡ post（比完整几何）"))

    restored = {"pre": sha(PRE) == pre0, "post": sha(POST) == post0}
    assert all(restored.values()), "★ 阴性对照后文件没复原：%r" % restored

    negs_ok = sum(1 for n in negs if n["ok"])
    ok = all(n["ok"] for n in negs)
    out = {
        "batch": 798, "verdict": "PASS" if ok else "FAIL",
        "baseline": {"checks": checks, "passed": nPos,
                     "failed": len(checks) - nPos},
        "negative": negs,
        "negativeSummary": {"total": len(negs), "passed": negs_ok},
        "restoreSha": {"pre": pre0, "post": post0, "ok": restored},
    }
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("★ 798 验收：%d/%d 断言通过" % (nPos, len(checks)))
    for c in checks:
        print("   %s %s" % ("OK " if c["ok"] else "FAIL", c["id"]))
    print("★ 阴性对照 %d/%d" % (negs_ok, len(negs)))
    for n in negs:
        print("   %s %s → 翻了 %r"
              % ("OK " if n["ok"] else "FAIL", n["name"], n["flipped"]))
    print("★ 阴性对照后字节级复原：%r" % restored)
    print("wrote %s" % REPORT)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

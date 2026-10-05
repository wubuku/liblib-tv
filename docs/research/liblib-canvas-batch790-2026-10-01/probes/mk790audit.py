#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 790 汇编器 —— 画布行内菜单：**修之前** 4 个格子里 3 个不可用

## 本批是**第一批发界面**（785–789 连续五批只做分析与测量）

目标已更新为「复刻**用户体验**（可交互原型）」。本批第一次改 `src/`，
改的是一个**已记账的缺陷**（batch 755 的高严重度读数）：
重命名 / 复制 / 删除三项**对多数用户不可达**。

## ★ 为什么不直接照抄 755 的结论

755 是**旧读数**。改 `src/` 之前必须先确认缺陷**还在当前代码里**。
⟹ 前置探针用**与后置完全相同**的测量代码跑两遍（`pre` / `post`），
差异只能来自 `src/`。

## ★ 判据要按 CSS 规则算，不能只看几何

我原本以为「`position:absolute` 的菜单能逃出 `static` 列表的 `overflow-y-auto`」
—— **错的**。规则是：祖先的 `overflow` 只裁**在菜单包含块链上**的那些。

- `absolute` ⟹ 包含块 = 最靠近的定位祖先 = 行（`:199` `relative`）
  ⟹ 列表 `:238` 是 `static`、**不在**链上；面板 `:173` 是 `absolute`、**在**链上
  ⟹ ★ **真裁剪者只有 1 个**：面板
- `fixed` ⟹ 包含块 = **视口** ⟹ 任何祖先都裁不到它 ⟹ **真裁剪者 0 个**

★ 第一批后置读数里「裁下边的 = 2」是**假阳性**（只算了几何、没算包含块），
探针因此改写，两个阶段都用**改写后**的判据重跑。

## 读数（同一份探针，pre / post 各 2 轮，8 格全一致）

| 格子 | pre 位置 | pre 真裁剪 | pre 命中 | pre 功能 | post 真裁剪 | post 命中 | post 功能 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| b790-2 张·首行 | `absolute` | 1 | **1/4** | ✗ | **0** | **4/4** | ✓ |
| b790-2 张·末行 | `absolute` | 1 | **0/4** | ✗ | **0** | **4/4** | ✓ |
| b790-6 张·首行 | `absolute` | 0 | 4/4 | ✓ | **0** | **4/4** | ✓ |
| b790-6 张·末行 | `absolute` | 1 | **0/4** | ✗ | **0** | **4/4** | ✓ |

★ **b790-6 张·首行在 pre 就是好的** ⟹ 它是**天然阳性对照**（面板够高、菜单装得下）
⟹ 「pre 的失败」不能被解释成「这份代码根本点不动」。

## 纪律

- 派生字段一律从 raw 重算，不信任何自报字段
- 三类证据互相独立：几何（真裁剪）／命中（`elementFromPoint`）／功能（行内 input）
- ★ **阳性对照**（755 的 R18）：没有它，「不可点」与「我没点到」无法区分
"""
import json
import pathlib

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch790-2026-10-01"
PRE = REPO / (B + "/raw/vb790a-pre.json")
POST = REPO / (B + "/raw/vb790a-post.json")
OUT = REPO / (B + "/runtime-audit.json")

DV = "src/components/director/DirectorViewport.tsx"
CTD = "src/components/CanvasTabDropdown.tsx"

#: ★ 四类动作，全部来自源码的**唯一**真实文案
ACTIONS = ["在新窗口打开", "重命名画布", "复制画布", "删除画布"]
#: ★ 755 记为「不可达」的那三项（第一个是装饰性按钮，755 另有记录）
FUNCTIONAL = ["重命名画布", "复制画布", "删除画布"]


def line_of(rel, n):
    return (REPO / rel).read_text(encoding="utf-8").split("\n")[n - 1]


def index(raw):
    out = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            out.setdefault((r.get("wantCanvases"), r.get("which")), []).append(
                (rd.get("round"), r))
    return out


def hits(cell):
    """★ 从 raw 的 `items` 重算：哪些项**真的**能被命中。"""
    return {it["text"]: bool(it.get("hitIsSelf"))
            for it in (cell.get("items") or [])}


def summary(cell):
    h = hits(cell)
    return {
        "menuPosition": cell.get("menuPosition"),
        "realClippers": len(cell.get("realClippers") or []),
        "hit": h,
        "hitAll": all(h.get(a) for a in ACTIONS),
        "funcOk": bool((cell.get("func") or {}).get("inputAppeared")),
        "rowCount": cell.get("rowCount"),
    }


def main():
    pre_raw, post_raw = (json.loads(p.read_text(encoding="utf-8"))
                         for p in (PRE, POST))
    pre, post = index(pre_raw), index(post_raw)
    checks = []

    def add(cid, desc, cond, detail, claim=None):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail, "claim": claim or desc})

    # ── A：源码行锚定（两个阶段的定位依据）──
    # ★ 行号是**改完之后**从当前文件重新读出来的：改 `src/` 让整份文件行号
    #   位移了 41 行，第一版沿用改动前的 :132/:197/:199 三条全部落空
    #   （读出来是 `setProjectNameDraft("")` 之类）⟹ 纪律：改过文件之后，
    #   锚点必须重新逐行读，**不能**沿用记忆里的旧行号。
    det, ok = [], True
    for label, rel, n, needle in [
        ("面板裁剪者(absolute 时)", CTD, 173, "overflow-hidden rounded-xl border"),
        ("列表(静态 ⟹ 不在包含块链上)", CTD, 238,
         "max-h-60 overflow-y-auto border-t"),
        ("行的包含块", CTD, 244, "group/canvas-row relative"),
    ]:
        code = line_of(rel, n)
        good = needle in code
        # ★ needle 在整份文件里**唯一**：不唯一就说明锚点抓到了错的那一处
        whole = (REPO / rel).read_text(encoding="utf-8")
        uniq = whole.count(needle) == 1
        ok = ok and good and uniq
        det.append({"label": label, "file": rel, "line": n, "ok": good,
                    "needleUnique": uniq, "code": code.strip()[:96]})
    c = {"id": "A:三个裁剪相关行的行锚定", "ok": ok, "n": 3, "anchors": det,
         "claim": "★ 面板 `overflow-hidden`（absolute 时**唯一**的真裁剪者）、"
                  "列表 `overflow-y-auto`（**静态** ⟹ 不在包含块链上）、"
                  "行 `relative`（absolute 时的包含块）"}
    assert ok, "★ 行锚定失败：\n%r" % det
    checks.append(c)

    # ── B：pre 的 4 个格子逐项重算 ──
    pre_sum, pre_bad = {}, []
    for key, lst in sorted(pre.items(), key=lambda kv: str(kv[0])):
        ss = [summary(r) for _rd, r in lst]
        pre_sum["%s张·%s" % key] = ss
        for s in ss:
            if s["menuPosition"] != "absolute" or len(ss) != 2:
                pre_bad.append({"cell": "%s张·%s" % key, "why": "阶段或轮数不对"})
            if s["realClippers"] != (0 if key == (6, "first") else 1):
                pre_bad.append({"cell": "%s张·%s" % key,
                                "realClippers": s["realClippers"]})
    c = {"id": "B:pre 逐格重算（真裁剪者个数）", "ok": not pre_bad, "n": 4,
         "detail": {"cells": pre_sum, "bad": pre_bad},
         "claim": "★ pre 全部是 `absolute`；**只有 6 张·首行**真裁剪者 0"
                  "（面板装得下菜单），其余 3 格都是 1"}
    assert not pre_bad, "★ pre 与预期不符：%r" % pre_bad
    checks.append(c)

    # ── C：★★ pre 的功能三项**够不着**（3/4 格）──
    pre_dead, pre_alive = [], []
    for key, lst in pre.items():
        for _rd, r in lst:
            h = hits(r)
            (pre_alive if all(h.get(a) for a in FUNCTIONAL)
             else pre_dead).append("%s张·%s" % key)
    uniq_dead = sorted(set(pre_dead))
    c = {"id": "C:★★ pre 有 %d/4 格三项功能够不着"
         % (len(uniq_dead) if len(uniq_dead) != 3 else 3), "ok": True, "n": 4,
         "detail": {"够不着的格子": uniq_dead, "够得着的格子":
                    sorted(set(pre_alive))},
         "claim": "★ pre：**重命名 / 复制 / 删除**三项在 %s 三个格子里"
                  "**点不到** ⟹ 755 记的「不可达」在当前代码里**仍然成立**。"
                  "★ 唯一够得着的是 6 张·首行 ⟹ **天然阳性对照**，"
                  "排除「这份代码根本点不动」"}
    assert len(uniq_dead) == 3 and sorted(set(pre_alive)) == ["6张·first"], (
        "★ pre 的三项可达性形状变了：够不着=%r 够得着=%r"
        % (uniq_dead, sorted(set(pre_alive))))
    checks.append(c)

    # ── D：★★ post 全部 4/4 且功能通 ──
    post_sum, post_bad = {}, []
    for key, lst in sorted(post.items(), key=lambda kv: str(kv[0])):
        ss = [summary(r) for _rd, r in lst]
        post_sum["%s张·%s" % key] = ss
        for s in ss:
            if s["menuPosition"] != "fixed" or not s["hitAll"] \
                    or not s["funcOk"] or s["realClippers"] != 0:
                post_bad.append({"cell": "%s张·%s" % key, "got": s})
    c = {"id": "D:★★ post 四格全部 4/4 且功能通", "ok": not post_bad, "n": 4,
         "detail": {"cells": post_sum, "bad": post_bad},
         "claim": "★ 改成 `fixed` 之后：真裁剪者 **0**、四项**全部**命中、"
                  "点「重命名画布」**真的**出行内 input"}
    assert not post_bad, "★ post 仍有问题：%r" % post_bad
    checks.append(c)

    # ── E：★★ 前后逐格对照，差异只来自位置这一项 ──
    # ★ 分两类格子，判据**不能**一刀切：
    #   坏过的格子 ⟹ 必须 pre 不够 4/4 → post 4/4
    #   阳性对照   ⟹ 必须 pre 4/4 **且** post 4/4（不许被我弄坏）
    #   第一版一刀切要求「每格都从坏变好」⟹ 阳性对照当场把断言打红。
    diff, diff_bad, fixed_cells, ctrl_cells = {}, [], [], []
    for key in sorted(pre, key=str):
        a, b = pre[key], post[key]
        if not b:
            diff_bad.append({"cell": "%s张·%s" % key, "why": "post 缺这一格"})
            continue
        for (_r1, ra), (_r2, rb) in zip(a, b):
            sa, sb = summary(ra), summary(rb)
            cell = "%s张·%s" % key
            same_menu_text = (ra.get("menuTexts") == rb.get("menuTexts"))
            d = {"cell": cell,
                 "position": [sa["menuPosition"], sb["menuPosition"]],
                 "realClippers": [sa["realClippers"], sb["realClippers"]],
                 "hitAll": [sa["hitAll"], sb["hitAll"]],
                 "funcOk": [sa["funcOk"], sb["funcOk"]],
                 "rowCount": [sa["rowCount"], sb["rowCount"]],
                 "菜单项完全相同": same_menu_text}
            diff[cell] = d
            # ★ 同一格的行数与菜单项必须一致 ⟹ 变的是**可达性**不是**内容**
            if not same_menu_text or sa["rowCount"] != sb["rowCount"]:
                diff_bad.append(d)
            if sa["hitAll"] and sb["hitAll"]:
                ctrl_cells.append(cell)
                if not (sa["funcOk"] and sb["funcOk"]
                        and sa["realClippers"] == 0
                        and sb["realClippers"] == 0):
                    diff_bad.append(d)          # 对照格必须前后都好
            elif not sa["hitAll"] and sb["hitAll"] and sb["funcOk"]:
                fixed_cells.append(cell)
            else:
                diff_bad.append(d)
    ok_e = (not diff_bad and len(set(fixed_cells)) == 3
            and sorted(set(ctrl_cells)) == ["6张·first"])
    c = {"id": "E:★★ 前后对照：变的是可达性不是内容", "ok": ok_e,
         "n": len(diff), "detail": {"cells": diff, "bad": diff_bad,
                                    "修好的格子": sorted(set(fixed_cells)),
                                    "阳性对照": sorted(set(ctrl_cells))},
         "claim": "★ 每个格子的**行数**与**菜单项**前后完全相同 ⟹ "
                  "变的只有「能不能点到」。★ 三格从「不够 4/4」变成「4/4」，"
                  "第四格（阳性对照 6 张·首行）前后都 4/4 ⟹ **没有把能用的弄坏**"}
    assert not diff_bad, "★ 前后对照不自洽：%r" % diff_bad
    checks.append(c)

    # ── F：两轮完全一致 ──
    two_round = []
    for phase, idx in (("pre", pre), ("post", post)):
        for key, lst in idx.items():
            ss = [summary(r) for _rd, r in lst]
            two_round.append(ss[0] == ss[1])
    c = {"id": "F:两轮逐格完全一致", "ok": all(two_round), "n": len(two_round),
         "detail": {"perCell": two_round},
         "claim": "★ 8 个格子（4 格 × 2 轮）每个的前后读数完全相同 ⟹ "
                  "不是抖动"}
    assert all(two_round), "★ 有格子两轮不一致：%r" % two_round
    checks.append(c)

    out = {
        "batch": 790,
        "kind": "★ 第一批改 src/ 的批次（目标更新为「复刻用户体验」）",
        "claims": {
            "C790-1": "★ 755 记的「重命名/复制/删除不可达」在当前代码里"
                      "**仍然成立** —— 4 个格子里 3 个",
            "C790-2": "★ 真裁剪者**只有 1 个**：面板 `:173` 的 `overflow-hidden`。"
                      "列表 `:197` 的 `overflow-y-auto` **不算**"
                      "（它 `static`，不在包含块链上）⟹ 我第一批的判断是错的",
            "C790-3": "★ 改成 `position: fixed` 后包含块变成**视口** ⟹ "
                      "真裁剪者 0，四格全部 4/4 且功能通",
            "C790-4": "★ 阳性对照（6 张·首行）前后都 4/4 ⟹ 没有把能用的弄坏",
        },
        "pressEquivalent": None,
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(x.get("n", 0) for x in checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ C790-1：755 的不可达**仍然成立** —— pre 有 3/4 格三项功能够不着")
    print("★ C790-2：真裁剪者只有 1 个（面板 `:173`）；列表 `static` 不算 ⟹ "
          "我第一批的判断错了")
    print("★ C790-3：改 `fixed` 后真裁剪者 0，四格全 4/4 且功能通")
    print("★ C790-4：阳性对照（6 张·首行）前后都 4/4")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 789 汇编器 —— 「`sIP` + `sIP`」共活时的**按键次数**

## 承重预测（写进探针 docstring，可 falsify）

★ **P789-1 被否掉了。** 我预测「谁后被打开谁赢」⟹ 实测是
**先打开的那个赢**（`draftThenLib` 第 1 次按 Escape 是
`draft=false, modelLibrary=true` ⟹ 草稿被关、模型库**留着**）。

⟹ 真机制更简单：**监听器按注册顺序调用，先注册的那个 `sIP` 把后面全部截断**；
而两个 effect 都是「状态非空才注册」⟹ **注册顺序 = 打开顺序**
⟹ **先开的赢**。我把它想成了「后开的赢」，方向搞反了。

★ **P789-2 成立**：`libThenDraft` **两轮都结构上不可达** ——
造草稿必须点时间轴上的按钮（pointer 事件）⟹ 模型库的 `pointerdown`
外点关闭（`:2747`）先把模型库关掉。这正是 **C785-2**（四个外点关闭全是
pointer 类 ⟹ 键盘绕过）的直接推论。

## ★ 本批真正的 UX 结论：**要按的次数**

★ 「全清」到底指什么会改变数字，所以**两个端点分开记**：

| 臂 | 面板全清（草稿与库都不再开着） | 桌关掉（阶梯最后一档） | 逐次读数 |
| --- | --- | --- | --- |
| `draftOnly` | 第 1 次 | 第 **3** 次 | P1 草稿关/导出面板在 → P2 导出面板关 → P3 **桌关** |
| `libOnly` | 第 1 次 | 第 **3** 次 | P1 模型库关/导出面板在 → P2 导出面板关 → P3 **桌关** |
| ★★ `draftThenLib` | ★★ 第 **2** 次 | ★★ **3 次里没发生** | P1 **草稿关、模型库仍在** → P2 模型库关 → P3 导出面板关、**桌还在** |

⟹ **两个 `sIP` 主人共活 ⟹ 多按一次**。而 D1i（784）已经证明
「一个 `sIP` + 一个 bubble 共活」要多按一次 ⟹ 这是同一条成本线的延伸。

★ **诚实标注**：本批只按了 **3 次**，所以共活臂那一格写的是
「3 次里没发生」而**不是**「要按 4 次」—— 第 4 次是**外推**，
不是测出来的。真要断言得再跑一格 4 次按压。

## 纪律

- 派生字段一律从 `presses[].read` 重算，不信任何自报字段
- 「结构上不可达」是一个**结论**，必须有源码行的解释与两轮一致性
"""
import json
import pathlib

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch789-2026-10-01"
RAW = REPO / (B + "/raw/vb789a.json")
OUT = REPO / (B + "/runtime-audit.json")

DV = "src/components/director/DirectorViewport.tsx"

#: ★ 两个 `sIP` 主人的行锚定（含**注册**行与 **sIP** 行）
SIP_OWNERS = [
    ("motionPathDraft", 2698, "if (!timeline.motionPathDraft) return;"),
    ("motionPathDraft", 2702, "event.stopImmediatePropagation();"),
    ("motionPathDraft", 2711,
     'window.addEventListener("keydown", handleKeyDown, true);'),
    ("modelLibraryOpen", 2734, "if (!modelLibraryOpen) return;"),
    ("modelLibraryOpen", 2744, "event.stopImmediatePropagation();"),
    ("modelLibraryOpen", 2748,
     'window.addEventListener("keydown", closeOnEscape, true);'),
]

#: ★ 预测（可 falsify）：逐次按压后**应当**是什么
#:   `draft`/`lib` 读数；`exportOpen` 用 `"on"/"off"`；`desk` 表示整张桌是否还在
EXPECT = {
    "draftOnly": [
        {"draft": "false", "lib": "false", "exportOpen": "on", "desk": True},
        {"draft": "false", "lib": "false", "exportOpen": "off", "desk": True},
        {"draft": None, "lib": None, "exportOpen": "off", "desk": False}],
    "libOnly": [
        {"draft": "false", "lib": "false", "exportOpen": "on", "desk": True},
        {"draft": "false", "lib": "false", "exportOpen": "off", "desk": True},
        {"draft": None, "lib": None, "exportOpen": "off", "desk": False}],
    "draftThenLib": [
        {"draft": "false", "lib": "true", "exportOpen": "on", "desk": True},
        {"draft": "false", "lib": "false", "exportOpen": "on", "desk": True},
        {"draft": "false", "lib": "false", "exportOpen": "off", "desk": True}],
}

#: ★ 预测**结构上不可达**的臂
UNREACHABLE = "libThenDraft"


def line_of(rel, n):
    return (REPO / rel).read_text(encoding="utf-8").split("\n")[n - 1]


def read_of(r):
    """★ 从一次按压的读数**重算**成判据形状。

    ★ `desk` 是**直读**（`deskOpen`），不是从「草稿与库两个读数都变 `null`」
    推断出来的 —— 推断只在桌关了之后碰巧成立，一旦某个读数因为别的原因
    消失就会误判。读数里没有 `deskOpen` 就直接判失败。
    """
    r = r or {}
    if "deskOpen" not in r:
        raise AssertionError(
            "★ 读数缺 `deskOpen` ⟹ 「桌还在」是推断的，本批不接受：%r" % r)
    return {"draft": r.get("draft"), "lib": r.get("lib"),
            "exportOpen": "on" if r.get("exportOpen") else "off",
            "desk": bool(r.get("deskOpen"))}


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    checks = []

    # ── A：两个 `sIP` 主人的行锚定 ──
    det, ok = [], True
    for state, n, needle in SIP_OWNERS:
        code = line_of(DV, n)
        good = needle in code
        ok = ok and good
        det.append({"state": state, "line": n, "needle": needle, "ok": good,
                    "code": code.strip()[:100]})
    c = {"id": "A:两个 sIP 主人的行锚定", "ok": ok, "n": len(SIP_OWNERS),
         "anchors": det,
         "claim": "★ 两个主人都是 window **捕获** + `sIP`；两个 effect 都是"
                  "「**状态非空才注册**」⟹ **注册顺序 = 打开顺序**"}
    assert ok, "★ 行锚定失败：\n%r" % det
    checks.append(c)

    # ── B：逐臂逐次读数 ⟹ 预测 ──
    by_arm = {}
    for rd in raw["rounds"]:
        for r in (rd.get("rows") or []):
            by_arm.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    mism, got = [], {}
    for arm, exp in EXPECT.items():
        for rdno, r in by_arm.get(arm, []):
            seq = [read_of(p["read"]) for p in (r.get("presses") or [])]
            got.setdefault(arm, []).append(seq)
            if len(seq) != len(exp):
                mism.append({"arm": arm, "round": rdno, "got": seq,
                             "wantLen": len(exp)})
                continue
            for k, (g, w) in enumerate(zip(seq, exp), 1):
                if any(g[key] != w[key] for key in w):
                    mism.append({"arm": arm, "round": rdno, "press": k,
                                 "got": g, "want": w})
    c = {"id": "B:逐次读数全部符合预测", "ok": not mism,
         "n": sum(len(v) for v in by_arm.values()), "detail": {"mismatch": mism},
         "claim": "★ `draftOnly`/`libOnly` 各 3 次读数、"
                  "`draftThenLib` 3 次读数全部与预测逐字段相同"}
    assert not mism, "★ 有 %r 与预测不符 ⟹ 结论要重算" % mism
    checks.append(c)

    # ── C：★★ 预测被否 —— 先打开的那个赢 ──
    p1 = read_of(by_arm["draftThenLib"][0][1]["presses"][0]["read"])
    c = {"id": "C:★★ P789-1 被否（先开的赢）", "ok": True, "n": 1,
         "detail": {"press1": p1,
                    "myPrediction": "模型库被关（后开的赢）",
                    "actual": "草稿被关、模型库仍在"},
         "claim": "★ 我预测「谁**后**被打开谁赢」⟹ **被否**。实测"
                  "`draftThenLib` 第 1 次按 Escape 是 `draft=false, lib=true` "
                  "⟹ **先打开的草稿赢**。真机制：先注册的那个 `sIP` "
                  "把后面全部截断，而注册顺序 = 打开顺序"}
    assert p1["draft"] == "false" and p1["lib"] == "true", (
        "★ 第 1 次读数与实测不符：%r ⟹ C 的前提变了" % p1)
    checks.append(c)

    # ── D：★ `libThenDraft` 结构上不可达（两轮一致）──
    unr = [(rdno, r) for arm, lst in by_arm.items() if arm == UNREACHABLE
           for rdno, r in lst]
    d_ok = (len(unr) == 2
            and all(r.get("structurallyUnreachable") for _rd, r in unr)
            and all((s.get("libAfterAttempt") == "false")
                    for _rd, r in unr for s in (r.get("setup") or [])
                    if s.get("phase") == "makeDraft"))
    c = {"id": "D:libThenDraft 结构上不可达", "ok": d_ok, "n": len(unr),
         "detail": {"rounds": [rd for rd, _ in unr],
                    "reasons": [r.get("why") for _rd, r in unr]},
         "claim": "★ 先开模型库再造草稿**不可达**：造草稿必须点时间轴上的按钮"
                  "（**pointer 事件**）⟹ 模型库的 `pointerdown` 外点关闭"
                  "（`DirectorViewport.tsx:2747`）先把模型库关掉 ⟹ "
                  "这是 C785-2「四个外点关闭全是 pointer 类」的直接推论"}
    assert d_ok, "★ 不可达的判据不成立：%r" % [(rd, r.get("why"),
                                             r.get("setup"))
                                            for rd, r in unr]
    checks.append(c)

    # ── E：★★ UX 结论 —— 共活要多按一次 ──
    # ★ 两个端点分开记，因为「全清」到底指什么会改变数字：
    #   `panelsGone` = 草稿与模型库都不再开着（**用户自己搞出来的东西**全清）
    #   `deskClosed` = 整张桌关掉（阶梯的**最后一档**）
    e_ok = True
    detail = {}
    for arm, lst in by_arm.items():
        if arm == UNREACHABLE:
            continue
        for rdno, r in lst:
            seq = [read_of(p["read"]) for p in (r.get("presses") or [])]
            pg = [k for k, s in enumerate(seq, 1)
                  if s["draft"] != "true" and s["lib"] != "true"]
            dc = [k for k, s in enumerate(seq, 1) if s["desk"] is False]
            detail.setdefault(arm, []).append({
                "round": rdno,
                "panelsGoneAtPress": pg[0] if pg else None,
                "deskClosedAtPress": dc[0] if dc else None,
                "observedPresses": len(seq),
                # ★ 桌关之后草稿/库读数必然是 `null`（元素已不渲染），
                #   这**不是**「草稿被单独关掉」的证据
                "readsAfterDeskClosed": [
                    k for k, s in enumerate(seq, 1) if s["desk"] is False]})
    both = detail.get("draftThenLib", [])
    alone = detail.get("draftOnly", []) + detail.get("libOnly", [])
    # ★ 断言分两半，各自独立可读：
    #   ① 两个单独臂在**第 3 次**按压把桌关掉
    #   ② 共活臂在**已观测的 3 次里**桌**始终没关**
    e_ok = (all(x["deskClosedAtPress"] == 3 for x in alone)
            and all(x["deskClosedAtPress"] is None for x in both)
            # ★ 顺带一个**正向**证据：共活臂的面板确实比单独臂晚一次才清
            and all(x["panelsGoneAtPress"] == 2 for x in both)
            and all(x["panelsGoneAtPress"] == 1 for x in alone))
    c = {"id": "E:★★ 共活要多按一次", "ok": e_ok, "n": len(detail),
         "detail": detail,
         "claim": "★ 两个 `sIP` 主人**单独**时：第 1 次按压就把两样都清了、"
                  "第 3 次把整张桌关掉；**共活**时：面板要第 2 次才清、"
                  "**已观测的 3 次里桌始终没关** ⟹ **多按一次**。"
                  "这正是 D1i 那条成本线的延伸（784 是 `sIP`+bubble，"
                  "本批是 `sIP`+`sIP`）"}
    assert e_ok, "★ 「多按一次」不成立：%r" % detail
    checks.append(c)

    out = {
        "batch": 789,
        "claims": {
            "P789-1_被否": "★ 我预测「谁**后**被打开谁赢」⟹ **被否**："
                           "实测 `draftThenLib` 第 1 次按 Escape 关掉的是"
                           "**先打开的草稿**",
            "真机制": "★ 两个 effect 都是「状态非空才注册」⟹ 注册顺序 = 打开顺序；"
                      "同 target 同相位下**先注册**的那个 `sIP` 把后面全部截断",
            "P789-2_成立": "★ `libThenDraft` **两轮都结构上不可达**"
                           "（C785-2 的直接推论）",
            "★ UX 结论": "★★ 两个 `sIP` 共活 ⟹ **要按的次数多一次**"
                         "（D1i 那条成本线的延伸）",
        },
        "pressBudget": {a: {"panelsGone": [x.get("panelsGoneAtPress")
                                           for x in v],
                           "deskClosed": [x.get("deskClosedAtPress")
                                          for x in v]}
                        for a, v in detail.items()},
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(x.get("n", 0) for x in checks),
                   "failed": sum(0 if x["ok"] else 1 for x in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ P789-1 **被否**：赢家是**先打开的**那个（`draftThenLib` P1 = "
          "`draft=false, lib=true`）")
    print("★ P789-2 成立：`libThenDraft` 结构上不可达（两轮一致）")
    for a in ("draftOnly", "libOnly", "draftThenLib"):
        seq = got.get(a, [{}])[0]
        print("   %-16s %s" % (a, " → ".join(
            "草稿%s/库%s/导出%s" % (s["draft"], s["lib"], s["exportOpen"])
            for s in seq)))
    print("★ UX：单独臂第 1 次清面板、第 3 次关桌；共活臂第 2 次才清面板、"
          "**3 次里桌没关** ⟹ 多按一次")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

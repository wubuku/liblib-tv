#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 813 验收器 —— 「**重新选中源节点**再点一次」是**完全可达**的第二条路径

## ★ 本批推翻的是 812 自己写下的结论

812 测「连点两下」时，第二下是在第一次触发**之后立刻**点的，而第一次触发把
**选区迁到新建的节点上** ⟹ 812 据此写下「store 层『又建了一遍』那条路径
**用户走不到**」。

★ **那条推理漏了一条路**：用户只要**重新选中原来那个源节点**，工具栏就回来了。
本批把它量出来。

## ★ 判据

- **S1 阳性对照**：第一下建了东西、历史 +1，**且「重新选中」本身没改任何东西**
  ⟹ 否则「第二下建的东西」可能其实是「重新选中」带来的。
- **S2 入口**：重新选中之后，**入口回来了**。
- **S3 三态**：第二下的结局落在 {被守卫拦住 / 完全没拦 / 空记录} 之内
  —— 与 812 同一套三态，但在**可达路径**上重做。
- **S4 重复产物**：哪些动作在**可达路径**上**真的建出了第二份**。
"""
import copy
import hashlib
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB813_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch813-2026-10-01"
                    / "raw" / "vb813a.json"))
OUT = pathlib.Path(os.environ.get("VB813_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch813-2026-10-01"
                    / "verify-report.json"))
SRC_DIR = ROOT / "src"
VN = "src/components/nodes/VideoNode.tsx"
CS = "src/store/canvasStore.ts"

KEYS = ["u_firstFrame", "u_firstLast", "u_breakdown", "u_continuation",
        "u_subtitle", "u_audio", "u_shotComplete"]


def run_checks(raw, src_vn, src_cs, call_sites):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": evidence})

    cells = raw["cells"]

    # ── S1 ★★★ 阳性对照：第一下建了东西 + 历史 +1，且「重新选中」本身是 no-op
    ev = []
    for c in cells:
        if c.get("FAILED"):
            continue
        ev.append({"round": c["round"], "动作": c["key"],
                   "第一次之前": c["第一次之前（节点/边/历史）"],
                   "第一次之后": c["第一次之后（节点/边/历史）"],
                   "重新选中之后": c["重新选中之后（节点/边/历史）"],
                   "★ 第一下建了东西": c["★ 第一下建了东西"] is True,
                   "★ 重新选中**没改**任何东西": c["★ 重新选中**没改**任何东西"] is True,
                   "★ 两件同时": c["★ 第一下建了东西"] is True
                                  and c["★ 重新选中**没改**任何东西"] is True})
    add("S1:★★★ 阳性对照：第一下建了东西，且「**重新选中**」本身**没改任何东西**",
        "★★★ 「重新选中没改任何东西」这条不可省 ⟹ 否则「第二下建出来的节点」"
        "可能其实是**选中动作**带来的，而不是第二次触发带来的；"
        "★ 判据盯的是节点 id 集合与边数（探针侧已逐位记录）",
        ev and all(x["★ 两件同时"] for x in ev)
        and {x["动作"] for x in ev} == set(KEYS), ev)

    # ── S2 ★★★ 入口：重新选中之后，入口**回来了**
    ev = []
    for c in cells:
        if c.get("FAILED"):
            continue
        e = c.get("入口（重新选中之后）") or {}
        shot = e.get("shotStart") or []
        # ★ 第一版把 `shotStart` 漏在「入口回来了」之外 ⟹ `completeShotBreakdown`
        #   那一臂明明按钮**回来了**（只是 `disabled` + 文案改成「拉片完成」），
        #   却被判成「入口没回来」⟹ **又是我自己造的假红**。
        #   ⟹ 「回来了」与「回来且**可点**」是**两件事**，分开记。
        back = bool(e.get("breakdown") or e.get("continuation")
                    or e.get("audioTriggers") or e.get("subtitleTriggers")
                    or e.get("attemptChips") or shot)
        usable = bool((e.get("breakdown") or []) and not
                      (e.get("breakdown") or [{}])[0].get("disabled")) or \
                 bool((e.get("continuation") or []) and not
                      (e.get("continuation") or [{}])[0].get("disabled")) or \
                 bool(e.get("audioTriggers")) or bool(e.get("subtitleTriggers")) \
                 or bool(e.get("attemptChips")) or \
                 bool([x for x in shot if not x.get("disabled")])
        ev.append({"round": c["round"], "动作": c["key"],
                   "逐帧拉片": e.get("breakdown"), "智能续写": e.get("continuation"),
                   "音视频触发器": bool(e.get("audioTriggers")),
                   "去字幕触发器": bool(e.get("subtitleTriggers")),
                   "attempt 芯片": len(e.get("attemptChips") or []),
                   "拉片按钮": [(x.get("disabled"), x.get("text")) for x in shot],
                   "★ 入口回来了": back,
                   "★ 回来且**可点**": usable})
    add("S2:★★★ 重新选中源节点之后，**入口回来了**",
        "★★★ 这条直接推翻 812 的推理：812 看到的是「入口消失」，"
        "而那只是**选区迁到新节点**的暂时结果 ⟹ ★ "
        "**「条件渲染的入口不见了」不等于「这条路走不到」** —— "
        "重新选中原节点它就回来了（806 那条纪律要这么用：记两个状态，别只记动作后）",
        ev and all(x["★ 入口回来了"] for x in ev), ev)

    # ── S3 ★★★ 三态（与 812 同一套，但在**可达路径**上）
    ev = []
    for c in cells:
        if c.get("FAILED"):
            continue
        built = c["★ 第二下建了东西"] is True
        hist = c["★ 第二下历史 +1"] is True
        if built and hist:
            state = "完全没拦（又建了一遍）"
        elif (not built) and (not hist):
            state = "被守卫拦住"
        else:
            state = "★ 空记录（没建东西但历史 +1）"
        ev.append({"round": c["round"], "动作": c["key"],
                   "第一下之后": c["第一次之后（节点/边/历史）"],
                   "第二下之后": c["第二下之后（节点/边/历史）"],
                   "UI 第二下": (c.get("UI 第二下") or {}).get("outcome"),
                   "★ 结局": state,
                   "★ 落在三态之内": state in
                   ("完全没拦（又建了一遍）", "被守卫拦住",
                    "★ 空记录（没建东西但历史 +1）")})
    add("S3:★★★ 第二下的结局落在三态之内（拦住 / 没拦 / 空记录）",
        "★★★ 与 812 用**同一套三态** ⟹ 这样两批可以对照："
        "812 测的是「紧接着点」，813 测的是「重新选中后点」；"
        "★ 本批**只报事实**，不判「不防重」是对是错",
        ev and all(x["★ 落在三态之内"] for x in ev)
        and {x["动作"] for x in ev} == set(KEYS), ev)

    # ── S4 ★★★ 重复产物：哪些动作在**可达路径**上真的建出了第二份
    ev = []
    for c in cells:
        if c.get("FAILED"):
            continue
        d_n = (c["第二下之后（节点/边/历史）"][0]
               - c["第一次之后（节点/边/历史）"][0])
        d_e = (c["第二下之后（节点/边/历史）"][1]
               - c["第一次之后（节点/边/历史）"][1])
        ev.append({"round": c["round"], "动作": c["key"],
                   "第二下的节点 Δ": d_n, "第二下的边 Δ": d_e,
                   "★ 建出了第二份": c["★ 第二下建了东西"] is True and d_n > 0,
                   "★ 或只是塞了空记录": d_n == 0
                       and c["★ 第二下历史 +1"] is True,
                   "★ 或被拦住了": d_n == 0
                       and c["★ 第二下历史 +1"] is False})
    dupes = {x["动作"] for x in ev if x["★ 建出了第二份"]}
    add("S4:★★★ 「重新选中后再点」在**可达路径**上建出了**重复产物**的动作清单",
        "★★★ 这是本批**推翻 812 结论**的那条：812 写「用户走不到」，"
        "实测**走得到**、而且真的建出了第二份；"
        "★ 判据要求每条臂的 Δ 落在 {建出第二份 / 空记录 / 被拦住} 三者之一，"
        "并把「建出第二份」的那几条**显式列出来**（清单本身就是交付物）",
        ev and all(x["★ 建出了第二份"] or x["★ 或只是塞了空记录"]
                   or x["★ 或被拦住了"] for x in ev)
        and dupes, ev)

    # ── S5 ★★ 静态普查：三个动作**各只有一个调用点** ⟹ 没有第二条入口
    #   ★ 第九次提醒：调用点用正则逐文件数，**不靠 grep 的一行输出**。
    # ★ 第一版按「动作名」数调用点，`addDerivedNode` 数出 **4 个** ⟹ 判红。
    #   真因：`ImageNode.tsx:142/162/187` 那三个是**旋转／全景／派生**，
    #   跟逐帧拉片**不是同一个动作**，只是共用同一个 store 动作。
    #   ⟹ 普查必须**按「动作 + 区分参数」**，不是按动作名。
    rows = []
    for label, key in (("逐帧拉片 addDerivedNode(shot-breakdown)",
                        "addDerivedNode|shot-breakdown"),
                       ("智能续写 createVideoContinuation",
                        "createVideoContinuation"),
                       ("音视频分离 createAudioSplit",
                        "createAudioSplit")):
        act = key.split("|")[0]
        sites = call_sites.get(act, [])
        if "|" in key:
            arg = key.split("|")[1]
            # ★ 第一版写成 `arg in call_sites[...]` —— 那是问「字符串
            #   『shot-breakdown』在不在这个位置列表里」，**永远 False**。
            #   要问的是「这些调用点里，哪些的**参数**是它」⟹ 集合交集。
            keep = set(call_sites.get("_arg_" + arg, []))
            sites = [x for x in sites if x in keep]
        rows.append({"UI 动作": label, "调用点数": len(sites), "位置": sites,
                     "★ 只有一个": len(sites) == 1})
    add("S5:★★ 静态普查：那三个动作**各只有一个调用点**",
        "★★ 这条是 813 的前提：812 说「用户走不到」时，我需要先知道"
        "**是不是根本没有别的入口** ⟹ 普查结论是「没有第二条入口，"
        "但**同一条入口可以被走第二次**」；"
        "★ 调用点数由验收器**自己逐文件数**（不抄探针的输出）；"
        "★ ★ **按「动作 + 区分参数」数**，不是按动作名 —— 第一版按动作名数，"
        "`addDerivedNode` 数出 **4 个**（`ImageNode.tsx:142/162/187` 那三个"
        "是**旋转／全景／派生**，跟逐帧拉片不是同一个动作），⟹ 那是**我自己造的假红**",
        rows and all(r["★ 只有一个"] for r in rows)
        and all(any("VideoNode" in x for x in r["位置"]) for r in rows), rows)

    # ── S6 ★★ 静态锚点：两个守卫仍在实现里（`rfind` —— 第十次提醒）
    i_sub = src_cs.rfind("const requestFingerprint")
    seg_sub = src_cs[i_sub:i_sub + 2600] if i_sub >= 0 else ""
    i_sb = src_cs.rfind("if (existingResults.length > 0) return state;")
    add("S6:★★ 静态锚点：两个**防重守卫**仍在实现里（`rfind` 取实现）",
        "★ 静态证据**不能**替代 S3／S4 的行为证据（794 的硬规矩）；"
        "它的作用是把 S3 里「被拦住」的那两条**归因**到具体代码；"
        "★ 一律 `rfind`",
        i_sub >= 0 and "if (existingTarget)" in seg_sub and i_sb >= 0,
        {"指纹去重位置": i_sub, "「existingTarget」在段内": "if (existingTarget)" in seg_sub,
         "拉片守卫位置": i_sb})

    return checks


def count_call_sites():
    """★ 验收器**自己**数调用点，不抄任何外部输出"""
    out = {}
    for act in ("addDerivedNode", "createVideoContinuation", "createAudioSplit"):
        sites = []
        for f in SRC_DIR.rglob("*.ts*"):
            txt = f.read_text(encoding="utf-8")
            for m in re.finditer(r"[\.\s]" + act + r"\s*\(", txt):
                line = txt[:m.start()].count("\n") + 1
                rel = "%s:%d" % (f.relative_to(ROOT), line)
                sites.append(rel)
                # ★ 记下这个调用点**后面 120 个字符**的参数 ⟹ 验收器据此
                #   区分「同一个 store 动作、不同 UI 动作」的不同调用点
                out.setdefault("_arg_around", {})[rel] = txt[m.start():m.start() + 120]
        out[act] = sites
    # 把带参数的调用点按参数名归类
    for arg in ("shot-breakdown", "image"):
        out["_arg_" + arg] = [
            k for k, v in out.get("_arg_around", {}).items() if ('"%s"' % arg) in v]
    return out


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src_vn = (ROOT / VN).read_text(encoding="utf-8")
    src_cs = (ROOT / CS).read_text(encoding="utf-8")
    checks = run_checks(raw, src_vn, src_cs, count_call_sites())
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src_vn, src_cs, count_call_sites())
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        hit_expect = any(f.startswith(expect) for f in flipped)
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped, "ok": hit_expect}

    def reselect_changed(d):
        """★ 伪造「重新选中改了东西」⟹ S1 必须翻红
        （否则「第二下建的东西」可能其实是选中动作带来的）"""
        n = 0
        for c in d["cells"]:
            if c.get("FAILED"):
                continue
            c["★ 重新选中**没改**任何东西"] = False
            n += 1
        return n

    def entry_not_back(d):
        """★ 伪造「入口没回来」⟹ S2 必须翻红（这正是 812 当时的观察）"""
        n = 0
        for c in d["cells"]:
            if c.get("FAILED"):
                continue
            c["入口（重新选中之后）"] = {
                "breakdown": [], "continuation": [], "audioTriggers": [],
                "subtitleTriggers": [], "attemptChips": []}
            n += 1
        return n

    def dupe_claim_gone(d):
        """★ 伪造「可达路径上建不出第二份」⟹ S3／S4 必须翻红"""
        n = 0
        for c in d["cells"]:
            if c.get("FAILED"):
                continue
            a = c["第一次之后（节点/边/历史）"]
            c["第二下之后（节点/边/历史）"] = list(a)
            c["★ 第二下建了东西"] = False
            c["★ 第二下历史 +1"] = False
            n += 1
        return n

    def first_did_nothing(d):
        """伪造「第一下压根没发生」⟹ S1 翻红"""
        n = 0
        for c in d["cells"]:
            if c.get("FAILED"):
                continue
            c["★ 第一下建了东西"] = False
            n += 1
        return n

    def unrelated(d):
        n = 0
        for c in d["cells"]:
            c["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "★ 伪造「重新选中改了东西」⟹ S1 翻红",
            reselect_changed, "S1"),
        neg("N2", "★ 伪造「入口没回来」⟹ S2 翻红（这正是 812 当时的观察）",
            entry_not_back, "S2"),
        neg("N3", "★ 伪造「可达路径上建不出第二份」⟹ S3／S4 翻红",
            dupe_claim_gone, "S4"),
        neg("N4", "伪造「第一下压根没发生」⟹ S1 翻红",
            first_did_nothing, "S1"),
        neg("N5", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 813, "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": nOk, "negativesTotal": len(negs),
              "callSites": count_call_sites(),
              "rawSha": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print(("  PASS " if c["ok"] else "  FAIL ") + c["id"])
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for x in negs:
        print(("  PASS " if x["ok"] else "  FAIL ") + x["name"] + " ｜ 翻红：" +
              str([f[:10] for f in x["flipped"]]))
    print("★ 阴性对照 %d/%d" % (nOk, len(negs)))
    return 0 if (nPass == len(checks) and nOk == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())

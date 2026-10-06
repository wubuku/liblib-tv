#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 806 验收器 —— 独立实现，不 import 探针

## 本批要回答的

759 ③ / 755 ④：`purgeRemovedCanvas` **零调用点** ⟹ 回收站没有「彻底删除」。
那只回答了「渲染层没接」。★ 本批把三件事分开，因为处置完全不同：

  ① **能力**在不在、好不好 —— 绕过 UI 直接调 `purgeRemovedCanvas`（S3）
  ② **入口**有没有 —— 面板动作面普查，两个状态都查（S1）
  ③ 普查本身可不可信 —— 阳性对照 + 覆盖完整性（S2、S4）

## 两条判据纪律

- ★ **普查必须记两个状态**：批量恢复按钮是**条件渲染**的（勾选后才出现）。
  只在「未勾选」下普查会**少算一个入口** ⟹ 而那正是「普查器没看进去」的自证。
  S2 专门要求「勾选后元素数增加」。
- ★ **「入口为 0」不能只靠普查**：若面板本身是个空壳，普查出 0 也不说明什么。
  S4 要求面板里现存的每个动作**真的有效果**（单条恢复、批量恢复都验）。
"""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
D = ROOT / "docs/research/liblib-canvas-batch806-2026-10-01"
RAW = D / "raw/vb806a.json"
REPORT = D / "verify-report.json"
STORE = "src/store/canvasStore.ts"
PROJ = "src/app/project/page.tsx"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


PURGE_RE = ("删除", "移除", "清理", "purge", "delete", "remove", "永久", "彻底")


def matches(row):
    blob = " ".join([str(row.get("text") or ""), str(row.get("ariaLabel") or ""),
                     str(row.get("title") or ""),
                     " ".join((row.get("data") or {}).keys()),
                     " ".join((row.get("data") or {}).values())]).lower()
    return any(k.lower() in blob for k in PURGE_RE)


def named(row):
    """★ 「能命名」= 自身有身份，**或** 它的 data-* 里带了目标。"""
    return bool(row.get("text") or row.get("ariaLabel") or row.get("title")
                or row.get("data"))


def run_checks(raw, store_src, proj_src):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    rs = raw.get("rounds", [])

    # ── S1 ★★ 面板动作面普查：每个元素独立点名，删除类命中 0（两个状态）
    ev = []
    for r in rs:
        for key in ("census", "censusAfterSelect"):
            c = r.get(key) or {}
            if c.get("FAILED") or not c.get("open"):
                continue
            rows = c.get("rows", [])
            # ★ 独立重算「删除类命中」，不复述探针自报的 purgeLike
            hits = [{"i": x["i"], "text": x.get("text"), "data": x.get("data")}
                    for x in rows if matches(x)]
            ev.append({"round": r["round"], "状态": key,
                       "可交互数": len(rows),
                       "逐个": [{"i": x["i"], "tag": x["tag"],
                                 "data": x["data"], "text": x.get("text"),
                                 "★ 能命名": named(x),
                                 "宽高为正": x["rect"]["w"] > 0 and x["rect"]["h"] > 0}
                                for x in rows],
                       "独立重算的删除类命中": hits,
                       "★ 命中 0": len(hits) == 0})
    add("S1:★★ 面板动作面普查：每个元素独立点名，**删除类命中 0**（两个状态）",
        "★★ 命中判定**独立重算**（文本/title/aria/属性名/属性值五条路），"
        "不复述探针自报的那个列表 ⟹ 否则「探针说它查了」等于没查",
        ev and len(ev) >= 4 and all(x["★ 命中 0"] and x["可交互数"] >= 2 for x in ev),
        ev)

    # ── S2 ★★ 覆盖完整性：勾选后元素数**增加**（条件渲染的按钮被看到了）
    ev = []
    for r in rs:
        a = (r.get("census") or {}).get("total")
        b = (r.get("censusAfterSelect") or {}).get("total")
        has_batch = any("data-recycle-restore-selected" in (x.get("data") or {})
                        for x in (r.get("censusAfterSelect") or {}).get("rows", []))
        ev.append({"round": r["round"], "未勾选": a, "已勾选": b,
                   "勾选后新增了批量恢复按钮": has_batch,
                   "★ 覆盖完整": isinstance(b, int) and isinstance(a, int)
                               and b > a and has_batch})
    add("S2:★★ 普查覆盖完整：勾选后**元素数增加**，条件渲染的按钮被看到了",
        "★★ 批量恢复按钮只在 `selectedRemoved.length > 0` 时渲染 ⟹ 只普查"
        "「未勾选」会**少算一个入口**，而那恰好是「普查器没看进去」的自证",
        ev and all(x["★ 覆盖完整"] for x in ev), ev)

    # ── S3 ★★★ 能力验算：purgeRemovedCanvas 有效且**不可逆**，且销毁的是非空快照
    ev = []
    for r in rs:
        p = r.get("purgeViaStore") or {}
        ev.append({"round": r["round"],
                   "调用前在回收站里": p.get("wasRemoved"),
                   "销毁的快照节点数": p.get("snapshotNodes"),
                   "调用后还在回收站": p.get("stillInRemoved"),
                   "调用后回到画布": p.get("appearedInLive"),
                   "回收站条数": [p.get("removedCountBefore"),
                                  p.get("removedCountAfter")],
                   "★ 调用成功": p.get("ok") is True,
                   "★ 确实销毁了非空快照": (p.get("snapshotNodes") or 0) > 0,
                   "★ 不可逆": p.get("stillInRemoved") is False
                                and p.get("appearedInLive") is False,
                   "★ 三件同时": p.get("ok") is True
                                and (p.get("snapshotNodes") or 0) > 0
                                and p.get("stillInRemoved") is False
                                and p.get("appearedInLive") is False})
    add("S3:★★★ 能力验算：`purgeRemovedCanvas` **真的有效、且真的不可逆**",
        "★★★ 这条把「能力」与「入口」分开 ⟹ 结论才能写成「能力在、入口无」"
        "而不是「功能没做」；★ 还要确认销毁的**不是空快照**（否则「不可逆」没意义）",
        ev and all(x["★ 三件同时"] for x in ev), ev)

    # ── S4 ★★ 阳性对照：面板里现存的每个动作**真的有效果**
    ev = []
    for r in rs:
        s0 = r.get("state0") or {}
        one = r.get("restoreSingle") or {}
        one_after = one.get("stateAfter") or {}
        batch = r.get("batchRestore") or {}
        batch_after = batch.get("stateAfter") or {}
        ids0 = ((r.get("items0") or {}).get("ids")) or []
        ev.append({"round": r["round"],
                   "回收站初始": s0.get("removed"), "画布初始": s0.get("canvases"),
                   "单条恢复": {"点了": one.get("clicked"),
                                "点完回收站": one_after.get("removed"),
                                "点完画布": one_after.get("canvases"),
                                "★ 真的恢复了": one_after.get("removed") == 0
                                              and one_after.get("canvases")
                                              == (s0.get("canvases") or 0) + 1},
                   "批量恢复": {"选中文案": batch.get("selectionText"),
                                "点击": batch.get("click"),
                                "点完回收站": batch_after.get("removed"),
                                "点完画布": batch_after.get("canvases"),
                                "★ 真的恢复了": batch_after.get("removed") == 0
                                              and batch_after.get("canvases")
                                              == (s0.get("canvases") or 0) + 1},
                   "★ 起始真有东西": len(ids0) >= 1})
        ev[-1]["★ 两个动作都有效"] = (ev[-1]["单条恢复"]["★ 真的恢复了"]
                                     and ev[-1]["批量恢复"]["★ 真的恢复了"]
                                     and ev[-1]["★ 起始真有东西"])
    add("S4:★★ 阳性对照：面板里现存的**每个动作真的有效果**",
        "★★ 若面板本身是空壳，「删除类命中 0」什么也说明不了 ⟹ 必须先证明"
        "「恢复」与「批量恢复」**真的把条目拿回来了**（回收站 1→0、画布 1→2）",
        ev and all(x["★ 两个动作都有效"] for x in ev), ev)

    # ── S5 ★★ 文案矛盾：确认框说「不可恢复」，实现却是软删除 + 30 天保留
    ev = [{"round": r["round"],
           "确认框原文": (r.get("deleteConfirmCopy") or {}).get("text"),
           "★ 写了不可恢复": (r.get("deleteConfirmCopy") or {}).get("saysUnrecoverable"),
           "★ 而删除后进了回收站": ((r.get("state0") or {}).get("removed") or 0) >= 1,
           "★ 矛盾成立": (r.get("deleteConfirmCopy") or {}).get("saysUnrecoverable")
                         is True
                         and ((r.get("state0") or {}).get("removed") or 0) >= 1}
          for r in rs]
    add("S5:★★ 文案与实现矛盾：确认框写「此操作不可恢复」，而删除后条目**进了回收站**",
        "★ 755 ④ 记过这条矛盾；805 把那句「30 天」变成真的之后它**更尖锐** —— "
        "用户被告知不可恢复，实际可恢复 30 天，而恢复入口在**另一个路由**",
        ev and all(x["★ 矛盾成立"] for x in ev), ev)

    # ── S6 静态锚点：能力实现存在，但渲染层**零调用点**
    decl = "purgeRemovedCanvas: (id: string) => void;" in store_src
    impl = "purgeRemovedCanvas: (id: string) => {" in store_src
    in_proj = "purgeRemovedCanvas" in proj_src
    add("S6:★★ 静态锚点：`purgeRemovedCanvas` 有类型声明也有实现，但**渲染层零调用点**",
        "★ 这是「能力在、入口无」的静态侧证据，与 S3 的运行时证据配对；"
        "★ 它只说明**渲染层**没接，不替 S3 判断能力好坏",
        decl and impl and not in_proj,
        {"类型声明": decl, "实现": impl, "/project 里出现": in_proj})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    store_src = (ROOT / STORE).read_text(encoding="utf-8")
    proj_src = (ROOT / PROJ).read_text(encoding="utf-8")

    checks = run_checks(raw, store_src, proj_src)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, store_src, proj_src)
        flipped = [x["id"] for x in c if not x["ok"]]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": expect in flipped}

    def inject_purge_entry(d):
        """★ 往普查读数里塞一个「彻底删除」按钮 ⟹ S1 必须翻。"""
        n = 0
        for r in d["rounds"]:
            for key in ("census", "censusAfterSelect"):
                c = r.get(key)
                if not c or not c.get("rows"):
                    continue
                c["rows"].append({"i": 99, "tag": "BUTTON", "type": "button",
                                  "ariaLabel": "彻底删除", "title": None,
                                  "disabled": False,
                                  "data": {"data-recycle-purge": "true"},
                                  "text": "彻底删除",
                                  "rect": {"w": 56, "h": 27}})
                c["total"] = len(c["rows"])
                n += 1
        return n

    def flatten_census(d):
        """★ 把勾选后的元素数改成与未勾选相同 ⟹ S2 必须翻。"""
        n = 0
        for r in d["rounds"]:
            a = r.get("census") or {}
            b = r.get("censusAfterSelect") or {}
            if a.get("total") and b.get("rows") is not None:
                b["total"] = a["total"]
                b["rows"] = [x for x in b["rows"]
                             if "data-recycle-restore-selected" not in (x.get("data") or {})]
                n += 1
        return n

    def purge_reversible(d):
        """★ 声称 purge 后还在回收站里 ⟹ S3 必须翻。"""
        n = 0
        for r in d["rounds"]:
            p = r.get("purgeViaStore") or {}
            if p:
                p["stillInRemoved"] = True
                n += 1
        return n

    def restore_broken(d):
        """★ 声称「恢复」没把条目拿回来 ⟹ S4 必须翻。"""
        n = 0
        for r in d["rounds"]:
            one = r.get("restoreSingle") or {}
            after = one.get("stateAfter")
            if after:
                after["removed"] = 1
                after["canvases"] = 1
                n += 1
        return n

    def copy_fixed(d):
        """★ 声称确认框不再说「不可恢复」 ⟹ S5 必须翻。"""
        n = 0
        for r in d["rounds"]:
            c = r.get("deleteConfirmCopy") or {}
            if c:
                c["saysUnrecoverable"] = False
                c["text"] = "删除画布确定要删除画布吗？"
                n += 1
        return n

    def touch_unrelated(d):
        for r in d["rounds"]:
            r["note"] = "touched"
        return True

    negs = [
        neg("N1 ★★★ raw：往普查读数里塞一个「彻底删除」按钮",
            "★★★ 验证 S1 的「命中 0」不是普查器压根没找 —— 塞一个进去必须立刻命中",
            inject_purge_entry,
            "S1:★★ 面板动作面普查：每个元素独立点名，**删除类命中 0**（两个状态）"),
        neg("N2 ★★ raw：把勾选后的元素数改成与未勾选相同",
            "★★ 验证 S2 真的在要求「条件渲染的入口也被看到了」",
            flatten_census,
            "S2:★★ 普查覆盖完整：勾选后**元素数增加**，条件渲染的按钮被看到了"),
        neg("N3 ★★★ raw：声称 purge 之后条目还在回收站里（可逆）",
            "★★★ 验证 S3 抓的是「不可逆」这件事",
            purge_reversible,
            "S3:★★★ 能力验算：`purgeRemovedCanvas` **真的有效、且真的不可逆**"),
        neg("N4 ★★ raw：声称「恢复」没把条目拿回来",
            "★★ 验证 S4 的阳性对照不是空转",
            restore_broken,
            "S4:★★ 阳性对照：面板里现存的**每个动作真的有效果**"),
        neg("N5 ★★ raw：声称确认框不再说「不可恢复」",
            "★★ 验证 S5 抓的是那条文案矛盾本身",
            copy_fixed,
            "S5:★★ 文案与实现矛盾：确认框写「此操作不可恢复」，而删除后条目**进了回收站**"),
        neg("N6 ★★ 反向对照：只动与判据无关的字段（note）",
            "★ 证明判据锚的是读数、不是某段文本",
            touch_unrelated, "__NO_FLIP__"),
    ]

    report = {"batch": 806,
              "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": sum(1 for n in negs if n["ok"]),
              "negativesTotal": len(negs), "rawSha": sha(RAW)}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    for c in checks:
        print("  %s %s" % ("PASS" if c["ok"] else "FAIL", c["id"]))
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for n in negs:
        print("  %s %s ｜ 翻红：%s" % ("PASS" if n["ok"] else "FAIL", n["name"],
                                      n["flipped"] or "无"))
    print("★ 阴性对照 %d/%d" % (sum(1 for n in negs if n["ok"]), len(negs)))
    return 0 if (nPass == len(checks) and all(n["ok"] for n in negs)) else 1


if __name__ == "__main__":
    sys.exit(main())
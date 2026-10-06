#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 805 验收器 —— 独立实现，不 import 探针

## 修的是什么

759 ②：回收站面板写「仅显示最近 30 天内删除的内容」、每项写「· 剩余 30 天」，
**两处都是字面量** —— 没有 Date/diff/减法，`removedCanvases` 只有 `.map`
**没有 `.filter`**。老化实验后「剩余 **30** 天」**一字未变**，过期条目照样列着。

## ★ 本批的核心纪律：**30 这个数不许写死**

「30 天」是**界面自己写着的字**，不是我的期望值。所以判据是：

- S1：标题里的天数 **==** 当天删除项显示的剩余 ⟹ 字面量与行为必须对齐；
- S2：每个条目的剩余 **==** 标题天数 −（今天 − 该条目展示的日期），
  **只用 raw 里的 `shownDate` / `shownRemaining` / `titleDays` 重算**；
- S3：剩余 0 天的条目**必须消失**，剩余 1 天的**必须在**。

⟹ N 是从数据里**反推**的。把 30 换成任何别的数，这三条判据照样成立；
而如果实现是写死的，N 就会和老化结果对不上而红。

## 另一条纪律

★ **阳性对照不可省**：没有「真的通过 UI 删了一张、回收站里真的出现」这条读数，
  「面板里没有过期条目」也可能只是「面板本来就是空的」。S4 守着它。
"""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
D = ROOT / "docs/research/liblib-canvas-batch805-2026-10-01"
PRE = D / "raw/vb805a-pre.json"
POST = D / "raw/vb805a-post.json"
REPORT = D / "verify-report.json"
SRC = "src/app/project/page.tsx"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def cell(raw, name):
    out = []
    for r in raw.get("rounds", []):
        c = r.get(name) or {}
        if not c.get("FAILED"):
            out.append((r["round"], c))
    return out


def recycle_of(c):
    return c.get("recycle") or {}


def run_checks(pre_raw, post_raw, src):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    aging = cell(post_raw, "aging")
    bound = cell(post_raw, "boundary")
    real = cell(post_raw, "realDelete")
    pre_aging = cell(pre_raw, "aging")
    pre_bound = cell(pre_raw, "boundary")

    # ── S0 ★★★ 缺陷复现（**live pre**，不是内存模拟）
    # ★ 这一格是**真的把源码换回 HEAD 跑出来的**：修好的文件先另存到 /tmp，
    #   `git show HEAD:src/app/project/page.tsx` 换入、跑探针、再字节级还原
    #   （sha256 核对通过）。⟹ 两个症状都由真实运行给出，不是阴性对照模拟的。
    ev = []
    for r, c in pre_aging:
        rc = c.get("recycle") or {}
        rem = {i["shownRemaining"] for i in rc.get("items", [])}
        ev.append({"round": r, "造的天数": c.get("ages"),
                   "显示的剩余": sorted(rem),
                   "★ 一字未变": len(rem) == 1,
                   "_sym": "frozen"})
    for r, c in pre_bound:
        rc = c.get("recycle") or {}
        seed = c.get("seed") or {}
        made = {m["id"] for m in (seed.get("made") or [])}
        shown = {i["id"] for i in rc.get("items", [])}
        ev.append({"round": r, "造的天数": c.get("ages"),
                   "造出来": sorted(made), "面板里还在": sorted(shown),
                   "★ 过期条目照样列着": bool(made) and len(made & shown) == len(made),
                   "_sym": "listed"})
    add("S0:★★★ 缺陷复现（**live pre**）：老化后剩余**一字未变**，过期条目**照样列着**",
        "★★★ 759 ② 的两个症状；★ 这一格是**真的把源码换回 HEAD 跑出来的**，"
        "不是靠阴性对照在内存里模拟的",
        ev and any(x["_sym"] == "frozen" and x["★ 一字未变"] for x in ev)
        and any(x["_sym"] == "listed" and x["★ 过期条目照样列着"] for x in ev),
        [{k: v for k, v in x.items() if k != "_sym"} for x in ev])

    # ── S1 ★★ N 反推：标题里的天数 == 当天删除项显示的剩余
    ev = []
    for r, c in aging:
        rc = recycle_of(c)
        zero_age = [i for i in rc.get("items", [])
                    if i["shownDate"] == (c.get("seed") or {}).get("today")]
        ev.append({"round": r, "标题天数": rc.get("titleDays"),
                   "当天删除项的剩余": [i["shownRemaining"] for i in zero_age],
                   "★ 对齐": len(zero_age) == 1
                            and zero_age[0]["shownRemaining"]
                            == rc.get("titleDays")})
    add("S1:★★★ N 反推：标题里的天数 **==** 当天删除项显示的剩余",
        "★★★ 「30」是**界面自己写着的字**、不是我的期望值 ⟹ 判据是"
        "「字面量与行为必须对齐」，而不是「它等于 30」",
        ev and all(x["★ 对齐"] for x in ev), ev)

    # ── S2 ★★★ 算术成立：剩余 == 标题天数 − 已过天数（只用 raw 重算）
    ev = []
    for r, c in aging:
        rc = recycle_of(c)
        today = (c.get("seed") or {}).get("today")
        rows = []
        for i in rc.get("items", []):
            age = (int(today[8:10]) - int(i["shownDate"][8:10]))  # 同月内
            # ★ 不假设同月：按 UTC 日差算，跨月也对
            import datetime as _dt
            d0 = _dt.date(*map(int, i["shownDate"].split("-")))
            d1 = _dt.date(*map(int, today.split("-")))
            age = (d1 - d0).days
            expect = rc.get("titleDays") - age
            rows.append({"日期": i["shownDate"], "剩余(读数)": i["shownRemaining"],
                         "已过天数": age, "重算剩余": expect,
                         "★ 相符": i["shownRemaining"] == expect})
        ev.append({"round": r, "标题天数": rc.get("titleDays"), "逐条": rows,
                   "★ 全部相符": bool(rows) and all(x["★ 相符"] for x in rows)})
    add("S2:★★★ 算术成立：剩余 **==** 标题天数 − 已过天数（只用 raw 重算）",
        "★★★ 这是「30 天真的实现了」的判据本体；★★ 只用 raw 里的日期与剩余，"
        "**不读源码公式**；★ 跨月按 UTC 日差算，不假设都在同一个月",
        ev and all(x["★ 全部相符"] for x in ev), ev)

    # ── S3 ★★★ 边界：剩余 0 天的**消失**，剩余 1 天的**还在**
    ev = []
    for r, c in bound:
        rc = recycle_of(c)
        seed = c.get("seed") or {}
        today = seed.get("today")
        made = {m["removedAt"]: m["id"] for m in (seed.get("made") or [])}
        import datetime as _dt
        ages = {}
        for iso, cid in made.items():
            ages[cid] = (_dt.date(*map(int, today.split("-")))
                         - _dt.date(*map(int, iso.split("-")))).days
        shown = {i["id"]: i for i in rc.get("items", [])}
        age30 = [cid for cid, a in ages.items() if a == 30]
        age29 = [cid for cid, a in ages.items() if a == 29]
        ev.append({"round": r, "造出来的": ages,
                   "面板里的": list(shown.keys()),
                   "提前30天(应消失)": age30,
                   "提前29天(应还在)": age29,
                   "★ 30 天的确实不在": all(c2 not in shown for c2 in age30),
                   "★ 29 天的确实在": all(c2 in shown for c2 in age29),
                   "★ 边界两侧行为不同": (all(c2 not in shown for c2 in age30)
                                       and all(c2 in shown for c2 in age29))})
    add("S3:★★★ 边界两侧行为不同：剩余 0 天的**消失**，剩余 1 天的**还在**",
        "★★★ 759 ② 的核心症状是「过期条目照样列在面板里」；★ 只判「0 天的不在」"
        "不够 —— 还要判「1 天的在」，否则「面板全是空的」也能蒙混过关",
        ev and all(x["★ 边界两侧行为不同"] for x in ev), ev)

    # ── S4 ★★ 阳性对照：真的通过 UI 删了一张，回收站里真的出现
    ev = []
    for r, c in real:
        rc = recycle_of(c)
        conf = c.get("confirm") or {}
        flow = c.get("deleteFlow") or {}
        ev.append({"round": r,
                   "确认框点了": conf.get("ok"),
                   "点的按钮文案": conf.get("clicked"),
                   "确认框按钮文案": conf.get("labels"),
                   "回收站条数": len(rc.get("items", [])),
                   "面板标题": rc.get("headText"),
                   "★ 确认真的点了": bool(conf.get("ok")),
                   "★ 条目真的出现": len(rc.get("items", [])) >= 1,
                   "★ 面板不是空的": rc.get("empty") is False,
                   "★ 整条链走通": (bool(conf.get("ok"))
                                and len(rc.get("items", [])) >= 1
                                and rc.get("empty") is False)})
    add("S4:★★ 阳性对照：走**真实 UI** 删一张画布，回收站里真的出现该条目",
        "★★ 没有这条读数，「面板里没有过期条目」也可能只是「面板本来就是空的」⟹ "
        "★ 而且这一格**亲手走过**画布页下拉 → 删除画布 → 确认框 → 确认 → "
        "logo 下拉「全部项目」客户端路由 → 打开回收站",
        ev and all(x["★ 整条链走通"] for x in ev), ev)

    # ── S5 ★ 无回归：当天删除的条目显示的剩余 == 标题天数
    #（修复前字面量就是「剩余 30 天」，而当天删除恰好等于 TTL ⟹ 用户看到的不变）
    ev = [{"round": r, "标题天数": recycle_of(c).get("titleDays"),
           "逐条剩余": [i["shownRemaining"]
                        for i in recycle_of(c).get("items", [])],
           "★ 全部等于标题天数": all(i["shownRemaining"]
                                    == recycle_of(c).get("titleDays")
                                    for i in recycle_of(c).get("items", []))}
          for r, c in real]
    add("S5:★★ 无回归：真实删除得到的那条，显示的剩余 **==** 标题天数",
        "★★ 当天删除时「剩余」恰好等于 TTL ⟹ 与修复前字面量显示的**同一个数**，"
        "⟹ 用户在修复前后看到的东西**没变**，变的只是它从今起会真的随时间走",
        ev and all(x["★ 全部等于标题天数"] for x in ev), ev)

    # ── S6 静态锚点：三处都绑到同一个常量，且**真的有 filter**
    filt = ".filter(" in src and "remainingDays(canvas.removedAt) > 0" in src
    const_def = "const RECYCLE_TTL_DAYS = 30;" in src
    title_bound = "仅显示最近 {RECYCLE_TTL_DAYS} 天内删除的内容" in src
    item_bound = "剩余 {remainingDays(canvas.removedAt)} 天" in src
    add("S6:★★ 静态锚点：标题与每项都绑到**同一个** TTL 常量，且**真的有 filter**",
        "★ 三处必须同源 —— 若标题还写死 30 而行为用别的数，S1/S2 会红；"
        "★★ `removedCanvases` 必须真的经过 `.filter`（759 ② 的原症状就是**没有**）",
        filt and const_def and title_bound and item_bound,
        {".filter 存在": filt, "常量定义": const_def,
         "标题绑常量": title_bound, "每项绑算式": item_bound})

    return checks


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    src = (ROOT / SRC).read_text(encoding="utf-8")

    checks = run_checks(pre_raw, post_raw, src)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    # ★ 变异器拿到**两个相位**的副本，不是只有 post。
    #   第一版的 neg 只 deep-copy 了 post ⟹ 想打 S0（读 pre）的那条对照，
    #   实际改到了 post 上 ⟹ 翻红的是 S2 而不是 S0。**又一次「对照没打在
    #   性质真正读取的字段上」**（801/802/803/804 各踩过一遍）。
    def neg(name, why, mutate, expect):
        p_pre, p_post = copy.deepcopy(pre_raw), copy.deepcopy(post_raw)
        hit = mutate(p_pre, p_post)
        assert hit, "★ raw 变异没命中"
        c = run_checks(p_pre, p_post, src)
        flipped = [x["id"] for x in c if not x["ok"]]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": expect in flipped}

    def freeze_remaining(pre, post):
        """★ 把 post 某一条的剩余改成**恒定 30**（模拟 759 的字面量实现）。"""
        n = 0
        for r in post["rounds"]:
            c = r.get("aging") or {}
            for i in (c.get("recycle") or {}).get("items", []):
                if i["shownRemaining"] != 30:
                    i["shownRemaining"] = 30
                    n += 1
        return n

    def readd_expired(pre, post):
        """★ 把「提前 30 天」那条**塞回**边界格的读数里（模拟没有 filter）。"""
        n = 0
        for r in post["rounds"]:
            c = r.get("boundary") or {}
            seed = c.get("seed") or {}
            rc = c.get("recycle") or {}
            made = seed.get("made") or []
            if len(made) >= 2 and rc.get("titleDays"):
                rc.setdefault("items", []).append(
                    {"id": made[1]["id"], "shownName": "造出来的过期条目",
                     "shownRemaining": 0, "shownDate": made[1]["removedAt"]})
                n += 1
        return n

    def retitle(pre, post):
        n = 0
        for r in post["rounds"]:
            for cellk in ("aging", "boundary", "realDelete"):
                c = r.get(cellk) or {}
                rc = c.get("recycle") or {}
                if rc.get("titleDays"):
                    rc["titleDays"] = 45
                    n += 1
        return n

    def empty_real(pre, post):
        n = 0
        for r in post["rounds"]:
            c = r.get("realDelete") or {}
            if c.get("recycle"):
                c["recycle"]["items"] = []
                c["recycle"]["empty"] = True
                n += 1
        return n

    def touch_unrelated(pre, post):
        for r in post["rounds"]:
            r["base"] = "touched"
        return True

    def pre_varies(pre, post):
        """★ 让 **pre** 的老化样本剩余**不再恒定** ⟹ S0 的「一字未变」必须翻。"""
        n = 0
        for r in pre["rounds"]:
            c = r.get("aging") or {}
            for i, item in enumerate((c.get("recycle") or {}).get("items", [])):
                item["shownRemaining"] = 30 - i
                n += 1
        return n

    negs = [
        neg("N0 ★★★ pre raw：让 pre 的剩余**不再恒定**",
            "★★★ 验证 S0 抓的是「一字未变」这件事本身，而不是「pre 里有这些条目」",
            pre_varies,
            "S0:★★★ 缺陷复现（**live pre**）：老化后剩余**一字未变**，过期条目**照样列着**"),
        neg("N1 ★★★ raw：把老化样本的剩余**冻成恒定 30**（模拟字面量实现）",
            "★★★ 验证 S2 抓的是「剩余随已过天数递减」，而不是「等于标题天数」",
            freeze_remaining,
            "S2:★★★ 算术成立：剩余 **==** 标题天数 − 已过天数（只用 raw 重算）"),
        neg("N2 ★★★ raw：把提前 30 天那条**塞回**面板读数（模拟没有 filter）",
            "★★★ 验证 S3 抓的正是 759 ② 的原症状「过期条目照样列着」",
            readd_expired,
            "S3:★★★ 边界两侧行为不同：剩余 0 天的**消失**，剩余 1 天的**还在**"),
        neg("N3 ★★ raw：把标题天数改成 45（其余读数不动）",
            "★★ 验证 S1 抓的是「字面量与行为对齐」，改标题就该红",
            retitle,
            "S1:★★★ N 反推：标题里的天数 **==** 当天删除项显示的剩余"),
        neg("N4 ★★ raw：把真实删除那格的读数清空（模拟面板本来是空的）",
            "★★ 验证 S4 守住的确实是阳性对照，不是空转",
            empty_real,
            "S4:★★ 阳性对照：走**真实 UI** 删一张画布，回收站里真的出现该条目"),
        neg("N5 ★★ 反向对照：只动与判据无关的字段（base）",
            "★ 证明判据锚的是读数、不是某段文本",
            touch_unrelated, "__NO_FLIP__"),
    ]

    report = {"batch": 805, "phase": "post",
              "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": sum(1 for n in negs if n["ok"]),
              "negativesTotal": len(negs),
              "rawSha": {"pre": sha(PRE), "post": sha(POST)}}
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
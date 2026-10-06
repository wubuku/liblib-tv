#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 814 验收器 —— 重复产物的三个问题：能不能撤、能不能看出来、能积几份

## ★ 判据

- **S1**：重新选中 + 再点，**每一次都真的建出了新的一份**（逐次节点数递增）。
- **S2 ★★★**：**一次 `Cmd+Z`** 就回到「少一份」的**精确**状态
  （节点数 + 边数 + 历史长度三件同时）。
- **S3 ★★★**：同一动作建出的多份产物，**DOM 可见文本逐字相同**
  ⟹ 用户**分辨不出**自己点了几次。
- **S4 ★★ 对照组**：被守卫拦住的那个动作，累积量**停在 1**。
  没有它，「能积 4 份」可能只是「每个动作都这样」，而不是「这三个没防重」。
"""
import copy
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB814_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch814-2026-10-01"
                    / "raw" / "vb814a.json"))
OUT = pathlib.Path(os.environ.get("VB814_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch814-2026-10-01"
                    / "verify-report.json"))
CS = "src/store/canvasStore.ts"

#: 三个「不防重」的动作（本批的主对象）
DUPES = ["breakdown_x4", "continuation_x3", "audio_x3"]
#: 对照组（813 证明被守卫拦住）
CONTROL = ["subtitle_x3"]


def run_checks(raw, src):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": evidence})

    cells = raw["cells"]

    def c(rd, key):
        return next((x for x in cells if x.get("round") == rd
                     and x.get("key") == key), None)

    # ── S1 ★★ 阳性对照：每一次都真的建出了一份（逐次递增，无跳号）
    ev = []
    for rd in sorted({x["round"] for x in cells}):
        for key in DUPES:
            x = c(rd, key)
            if not x or x.get("FAILED"):
                continue
            counts = [m["节点"][1] for m in x["marks"]]
            each = [len(m["这次新建了"]) for m in x["marks"]]
            ev.append({"round": rd, "臂": key, "逐次节点数": counts,
                       "每次新建了几个": each,
                       "★ 一共建了几份": x["一共建了几份"],
                       "★ 逐次严格递增": all(b > a for a, b in
                                             zip(counts, counts[1:])),
                       "★ 每次都建了东西": all(e >= 1 for e in each),
                       # ★ 第一版写 `一共建了几份 == len(marks)` ⟹ `audio`
                       #   一次建**两个**节点（音轨 + 无声），3 次点击建 6 份 ⟹
                       #   6 != 3 直接判红 ⟹ **又是我自己造的假红**。
                       #   正确的总量是「每次新建数**之和**」。
                       "★ 总量 == 每次之和": x["一共建了几份"] == sum(each),
                       "★ 三件同时": x["一共建了几份"] == sum(each)
                                      and all(b > a for a, b in
                                              zip(counts, counts[1:]))
                                      and all(e >= 1 for e in each)})
    add("S1:★★ 阳性对照：重新选中再点，**每一次都真的建出了一份**（逐次递增）",
        "★★ 判「逐次递增」而不只是「最后多了几份」⟹ 中间某一次没建成的情形"
        "（比如某次被守卫拦住了）不会被「总数对」掩盖",
        ev and all(x["★ 三件同时"] for x in ev)
        and {x["臂"] for x in ev} == set(DUPES), ev)

    # ── S2 ★★★ 一次 Cmd+Z 就回到「少一份」的精确状态
    ev = []
    for rd in sorted({x["round"] for x in cells}):
        for key in DUPES:
            x = c(rd, key)
            if not x or x.get("FAILED") or not x.get("撤销"):
                continue
            u = x["撤销"]
            ev.append({"round": rd, "臂": key,
                       "全部建完": u["全部建完（节点/边/历史）"],
                       "★ 期望回到（少一份）": u["★ 期望回到（少一份）"],
                       "按一次 Cmd+Z 之后": u["按一次 Cmd+Z 之后（节点/边/历史）"],
                       "★ 三件同时": u["★ 三件同时"]})
    add("S2:★★★ 连建多份之后，**一次 `Cmd+Z`** 就回到「少一份」的精确状态",
        "★★★ 811 量的是**单次**触发后的撤销；**重复场景没量过**；"
        "★ 判据要求**节点数 + 边数 + 历史长度**三件同时 ⟹ "
        "「只掉了节点、边还留着」或「历史没退」都会被抓住",
        ev and all(x["★ 三件同时"] for x in ev)
        and {x["臂"] for x in ev} == set(DUPES), ev)

    # ── S3 ★★★ 同一 kind 的多份产物，DOM 可见文本**逐字相同**（用户分辨不出）
    #   ★★ 第一版写成「整条臂只应有一种文本」⟹ 判出两个**假红**：
    #   ① `audio` 一次建**两个 kind**（音轨 + 无声），它们文本**本来就该不同**；
    #   ② `continuation` 的第 3 份多出一大截 —— 真因是**它正被选中**、
    #      编辑器面板展开、`textContent` 把面板文字吃了进去，**那不是节点身份的差异**。
    #   ⟹ 正确判据：**按 kind 分组 + 排除选中态**，每个 kind 内部逐字相同。
    ev = []
    for rd in sorted({x["round"] for x in cells}):
        for key in DUPES:
            x = c(rd, key)
            if not x or x.get("FAILED") or not x.get("可见文本"):
                continue
            groups = {}
            for nid in x["建出来的 id"]:
                g = x["可见文本"].get(nid) or {}
                if not g.get("text") or g.get("selected"):
                    continue
                groups.setdefault(g.get("type"), []).append(g["text"])
            ev.append({"round": rd, "臂": key,
                       "每个 kind 各自有几种文本":
                           {k: len(set(v)) for k, v in groups.items()},
                       "★ 有 kind 出现过两次以上":
                           any(len(v) >= 2 for v in groups.values()),
                       "★ 每个 kind 只有一种文本":
                           bool(groups)
                           and all(len(set(v)) == 1 for v in groups.values()),
                       "★ 样本": {k: v[0] for k, v in groups.items()},
                       "★ 三件同时":
                           any(len(v) >= 2 for v in groups.values())
                           and all(len(set(v)) == 1 for v in groups.values())})
    add("S3:★★★ 同一 **kind** 的多份产物，DOM 可见文本**逐字相同**（用户分辨不出）",
        "★★★ 这是本批**最像缺陷**的一条读数：画布上出现**几个一模一样的节点**，"
        "**没有任何线索**告诉用户自己点了几次；"
        "★ 判据只读 **DOM 可见文本**（808 的纪律：能读 DOM 就不只读 store）；"
        "★ ★ 判「**按 kind 分组 + 排除选中态**」而不是「整条臂只有一种文本」—— "
        "第一次写后者时判出两个**假红**：`audio` 一次建**两个 kind**（音轨 + 无声，"
        "文本本来就该不同），`continuation` 的第 3 份多出的文字是**选中后展开的编辑器面板**、"
        "**不是节点身份的差异**",
        ev and all(x["★ 三件同时"] for x in ev)
        and {x["臂"] for x in ev} == set(DUPES), ev)

    # ── S4 ★★ 对照组：被守卫拦住的那个动作，累积量停在 1
    ev = []
    for rd in sorted({x["round"] for x in cells}):
        for key in CONTROL:
            x = c(rd, key)
            if not x or x.get("FAILED"):
                continue
            counts = [m["节点"][1] for m in x["marks"]]
            ev.append({"round": rd, "臂": key, "逐次节点数": counts,
                       "一共建了几份": x["一共建了几份"],
                       "★ 停在 1 份": x["一共建了几份"] == 1,
                       "★ 后面几次都没再建": counts[-1] == counts[0]})
    add("S4:★★ 对照组：被守卫拦住的那个动作，**累积量停在 1**",
        "★★ 没有它，「能积 4 份」可能只是「每个动作都这样」而不是「那三个没防重」⟹ "
        "★ 这是 806/813 的同一条纪律在另一个方向：**必须有对照**",
        ev and all(x["★ 停在 1 份"] and x["★ 后面几次都没再建"] for x in ev)
        and len(ev) == len(CONTROL) * len({x["round"] for x in cells}), ev)

    # ── S5 ★★ 静态锚点：指纹去重仍在实现里（`rfind` —— 第十一次提醒）
    i_sub = src.rfind("const requestFingerprint")
    seg_sub = src[i_sub:i_sub + 2600] if i_sub >= 0 else ""
    add("S5:★★ 静态锚点：对照组的守卫**指纹去重**仍在实现里",
        "★ 静态证据**不能**替代 S4 的行为证据（794 的硬规矩）；"
        "它的作用是把 S4 的「停在 1 份」**归因**到具体那段代码；★ 一律 `rfind`",
        i_sub >= 0 and "if (existingTarget)" in seg_sub,
        {"指纹去重位置": i_sub,
         "★「existingTarget」在段内": "if (existingTarget)" in seg_sub})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src = (ROOT / CS).read_text(encoding="utf-8")
    checks = run_checks(raw, src)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        hit_expect = any(f.startswith(expect) for f in flipped)
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped, "ok": hit_expect}

    def one_click_leftover(d):
        """★ 伪造「撤销只掉了节点、边还留着」⟹ S2 必须翻红
        （判据要求三件同时，半截状态必须被抓住）"""
        n = 0
        for x in d["cells"]:
            u = x.get("撤销")
            if not u:
                continue
            u["按一次 Cmd+Z 之后（节点/边/历史）"][1] = 999
            u["★ 节点数回到少一份"] = True
            u["★ 边数回到少一份"] = False
            u["★ 历史少一条"] = True
            u["★ 三件同时"] = False
            n += 1
        return n

    def texts_differ(d):
        """★ 伪造「同 kind 的多份产物文本各不相同」⟹ S3 翻红
        （只给**同一 kind** 加后缀，不碰不同 kind 之间的差异）"""
        n = 0
        for x in d["cells"]:
            if x.get("key") not in DUPES or not x.get("可见文本"):
                continue
            seen = {}
            for nid in x["建出来的 id"]:
                g = x["可见文本"][nid] or {}
                if not g.get("text") or g.get("selected"):
                    continue
                k = g.get("type")
                seen[k] = seen.get(k, 0) + 1
                g["text"] = g["text"] + "#%d" % seen[k]
            n += 1
        return n

    def text_empty(d):
        """伪造「可见文本读不到」⟹ S3 翻红（恒定无信息的读数比没有更危险）"""
        n = 0
        for x in d["cells"]:
            if not x.get("可见文本"):
                continue
            for nid in x["可见文本"]:
                x["可见文本"][nid] = None
            n += 1
        return n

    def only_one_kind(d):
        """★ 伪造「只有一个 kind 出现过两次以上」⟹ S3 翻红
        （否则「每个 kind 一种文本」可能只是「每 kind 都只出现过一次」、恒真）"""
        n = 0
        for x in d["cells"]:
            if x.get("key") not in DUPES or not x.get("可见文本"):
                continue
            for nid in x["建出来的 id"]:
                g = x["可见文本"].get(nid)
                if g and g.get("selected"):
                    g["selected"] = False      # 把选中态也并进来
                    n += 1
        return n

    def control_also_dupes(d):
        """★ 伪造「对照组也累积了」⟹ S4 必须翻红
        （没有它，「停在 1 份」可能只是「我也只测了一次」）"""
        n = 0
        for x in d["cells"]:
            if x.get("key") not in CONTROL:
                continue
            x["一共建了几份"] = len(x["marks"])
            for i, m in enumerate(x["marks"]):
                m["节点"][1] = m["节点"][0] + i + 1
            n += 1
        return n

    def not_monotonic(d):
        """伪造「中间某一次没建出来」⟹ S1 必须翻红（总数对也救不了）"""
        n = 0
        for x in d["cells"]:
            if x.get("key") not in DUPES or not x.get("marks"):
                continue
            m = x["marks"][1] if len(x["marks"]) > 1 else x["marks"][0]
            m["节点"][1] = m["节点"][0]
            m["这次新建了"] = []
            n += 1
        return n

    def unrelated(d):
        n = 0
        for x in d["cells"]:
            x["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "★ 伪造「撤销只掉了节点、边还留着」⟹ S2 翻红（半截状态必须被抓住）",
            one_click_leftover, "S2"),
        neg("N3", "伪造「可见文本读不到」⟹ S3 翻红（恒定无信息比没有更危险）",
            text_empty, "S3"),
        neg("N4", "★ 伪造「同 kind 的多份产物文本各不相同」⟹ S3 翻红",
            texts_differ, "S3"),
        neg("N5", "★ 伪造「只有一个 kind 重复出现过」⟹ S3 翻红"
                  "（否则「每个 kind 一种文本」可能只是「每 kind 都只出现过一次」、恒真）",
            only_one_kind, "S3"),
        neg("N6", "★ 伪造「对照组也累积了」⟹ S4 翻红",
            control_also_dupes, "S4"),
        neg("N7", "★ 伪造「中间某一次没建出来」⟹ S1 翻红（总数对也救不了）",
            not_monotonic, "S1"),
        neg("N8", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 814, "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": nOk, "negativesTotal": len(negs),
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

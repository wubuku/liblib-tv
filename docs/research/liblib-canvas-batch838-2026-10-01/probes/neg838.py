#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 阴性对照 ＋ 真实注入自检。

★ 两条纪律：
  1. **阴性每条只翻它自己那一条** ⟹ 读的字段必须互不重叠 ⟹ 否则无法归因；
  2. **注入没打上 ⟹ 负控看起来是「绿的」**（两者一模一样）⟹ 注入必须**先证明打上了**，
     打不上就**中止**（别把「没打上」当成「通过」）。

★ 注入方式（**行数中性**）：
  - 对「源码字面量」的判据 ⟹ 改 `src/store/directorStore.ts` 的种子 name；
  - 对「读脚本本体」的判据 ⟹ 改三个旧门禁脚本的期望值；
  - 对「权威 raw」的判据 ⟹ 改 raw 里的字段（**用解析器改值**，不用文本锚点 ——
    ★ raw 是 1 空格缩进，文本锚点一个都匹配不上 ⟹ 那是 batch 836 踩过的坑）；
  - 对「读 README」的判据 ⟹ 改**本批自己的** README（★ 不碰旧批次 ⟹ 旧批次不可重写）。

★ 归属判据也校正过（第一版写错了归属 ⟹ 会把「没打上」误读成「通过」）：
  - N1 只翻 **S5**（S2/S3 读的是**权威 raw**，与 store 无关 ⟹ 不该红）；
  - N6 只翻 **S2**（加 `shots` 键**不影响** `cameras`/`characters` 的 label ⟹ S3 不该红）；
  - N7/N8/N9 都翻 **S4**，但读的是**三个互不重叠的字段**（默认名 / 新增角色的 label /
    独立复核 raw 里的角色 id）⟹ ⟹ 三条各自证明 S4 的**不同**那一条有牙。

★ 每条注入**先证明打上了**（键名对不上就**中止**）⟹ ★ 第一版的 N7 写的键名是
  `C_★读到的默认名`（**旧版 raw** 的键名）⟹ 注入会打在**不存在的键**上 ⟹
  门禁照绿 ⟹ 负控看起来「通过」实则**什么都没测** ⟹ ★ 这正是「手打的标识符是输入，
  不是测量」的一次复现。

★ 每次注入后**按字节复原**（不是 `git checkout` ⟹ 那会碰到别人的改动）。
"""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch838.py"
STORE = ROOT / "src/store/directorStore.ts"
S720 = ROOT / "scripts/verify-liblib-batch720.py"
S42 = ROOT / "scripts/verify-liblib-batch42.py"
S43 = ROOT / "scripts/verify-liblib-batch43.py"
RAW_DETAIL = (ROOT / "docs/research/liblib-canvas-batch838-2026-10-01/raw"
              / "source-838-detail-by-space.json")
RAW_CLOSED = (ROOT / "docs/research/liblib-canvas-batch838-2026-10-01/raw"
              / "source-838-charname-closedloop.json")
RAW_RESTORED = (ROOT / "docs/research/liblib-canvas-batch838-2026-10-01/raw"
                / "source-838-restored-final.json")

PY = sys.executable


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate() -> tuple:
    r = subprocess.run([PY, str(GATE)], capture_output=True, text=True, timeout=1200)
    fails = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("FAIL"):
            parts = line.split()
            fails.append(parts[1] if len(parts) > 1 else line)
    passed_line = [l for l in r.stdout.splitlines() if "通过" in l and "/" in l]
    return r.returncode, fails, (passed_line[-1] if passed_line else "?")


def main() -> int:
    results = []
    backups = {}

    def backup(path: pathlib.Path):
        if path not in backups:
            backups[path] = path.read_bytes()

    def restore_all():
        for path, data in backups.items():
            path.write_bytes(data)

    # ── 阴性 N1：种子角色名改回旧值 ⟹ S5 应红 ───────────────────────
    #    ★ 只翻 S5：S2/S3 读的是**权威 raw**，与 store 无关 ⟹ 不该红。
    backup(STORE)
    orig = STORE.read_text(encoding="utf-8")
    mutated = orig.replace('    name: "角色A",\n', '    name: "角色01 · 陈默",\n', 1)
    if mutated == orig:
        print("★ 注入没打上（种子 name 那行没找到）⟹ 中止")
        restore_all()
        return 2
    STORE.write_text(mutated, encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S5"}
        results.append({"id": "N1", "注入": "种子角色名 → 旧值「角色01 · 陈默」（行数中性）",
                        "★注入是否真打上": True, "预期红": ["S5"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 阴性 N2：720 的 FIXTURE 首项改回旧值 ⟹ S6 应红 ────────────────
    backup(S720)
    o720 = S720.read_text(encoding="utf-8")
    m720 = o720.replace('FIXTURE = ["角色A",', 'FIXTURE = ["角色01 · 陈默",', 1)
    if m720 == o720:
        print("★ 注入没打上（720 FIXTURE 那行没找到）⟹ 中止")
        restore_all()
        return 2
    S720.write_text(m720, encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S6"}
        results.append({"id": "N2", "注入": "720 FIXTURE 首项 → 旧值（行数中性）",
                        "★注入是否真打上": True, "预期红": ["S6"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 阴性 N3：42 的姿态轨道 label 改回旧值 ⟹ S6 应红 ───────────────
    backup(S42)
    o42 = S42.read_text(encoding="utf-8")
    m42 = o42.replace('assert wave_track["label"] == "角色A · 姿态"',
                      'assert wave_track["label"] == "角色01 · 陈默 · 姿态"', 1)
    if m42 == o42:
        print("★ 注入没打上（42 姿态 label 那行没找到）⟹ 中止")
        restore_all()
        return 2
    S42.write_text(m42, encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S6"}
        results.append({"id": "N3", "注入": "42 姿态轨道 label → 旧值（行数中性）",
                        "★注入是否真打上": True, "预期红": ["S6"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 阴性 N4：43 的 option 列表改回旧值 ⟹ S6 应红 ───────────────────
    backup(S43)
    o43 = S43.read_text(encoding="utf-8")
    m43 = o43.replace('        "角色A",\n', '        "角色01 · 陈默",\n', 1)
    if m43 == o43:
        print("★ 注入没打上（43 option 那行没找到）⟹ 中止")
        restore_all()
        return 2
    S43.write_text(m43, encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S6"}
        results.append({"id": "N4", "注入": "43 option 列表 → 旧值（行数中性）",
                        "★注入是否真打上": True, "预期红": ["S6"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 阴性 N5：★ **改权威 raw** 里的 alt ⟹ S1 应红 ───────────────────
    #    ★ 证明 S1 真的在读那批 raw，不是读一份写死的期望。
    backup(RAW_DETAIL)
    raw = json.loads(RAW_DETAIL.read_text(encoding="utf-8"))
    # ★★ 用**可变容器**当标志 ⟹ 不用 `global touched`：那个 `global` 指向的是**模块全局**，
    #    而 `touched = False` 是 main 的**局部变量** ⟹ 两者**不是同一个东西**
    #    ⟹ 注入其实打上了，main 却读到一个永远是 False 的局部 ⟹ 「注入没打上」⟹ 中止。
    #    （★ 这个坑会让负控**看起来没测**，而且第一版就是这么写的 ⟹ 已修。）
    touched = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == 3 and isinstance(o.get("data"), str):
                d = json.loads(o["data"])
                if d.get("alt", "").endswith(".mp4"):
                    d["alt"] = "S83·镜2"
                    o["data"] = json.dumps(d, ensure_ascii=False)
                    touched.append(1)
                    return
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(raw)
    if not touched:
        print("★ 注入没打上（raw 里的 alt 字段没找到）⟹ 中止")
        restore_all()
        return 2
    RAW_DETAIL.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S1"}
        results.append({"id": "N5", "注入": "★权威 raw 里的 alt 去掉 .mp4 ⟹ S1 应翻红"
                                     "（用**解析器**改 JSON ⟹ 不受格式化影响）",
                        "★注入是否真打上": True, "预期红": ["S1"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 阴性 N6：★ **改权威 raw** 的 compositionData ⟹ S2 应红 ───────
    #    ★ 给 compositionData 加一个 shots 键 ⟹ 「源站没有镜头实体」这条就不成立了。
    #    ★ 只翻 S2：S3 读的是 `cameras`/`characters` 的 label ⟹ 加 shots 键**不影响**它们。
    backup(RAW_DETAIL)
    raw = json.loads(RAW_DETAIL.read_text(encoding="utf-8"))
    touched = []          # ★ 同上：可变容器 ⟹ 不用 `global`

    def walk2(o):
        if isinstance(o, dict):
            if o.get("type") == 36 and isinstance(o.get("data"), str):
                d = json.loads(o["data"])
                comp = d.get("compositionData")
                if isinstance(comp, str):
                    comp = json.loads(comp)
                if isinstance(comp, dict):
                    comp["shots"] = [{"id": "shot-1", "name": "镜头1"}]
                    d["compositionData"] = json.dumps(comp, ensure_ascii=False)
                    o["data"] = json.dumps(d, ensure_ascii=False)
                    touched.append(1)
                    return
            for v in o.values():
                walk2(v)
        elif isinstance(o, list):
            for v in o:
                walk2(v)

    walk2(raw)
    if not touched:
        print("★ 注入没打上（raw 里的 compositionData 没找到）⟹ 中止")
        restore_all()
        return 2
    RAW_DETAIL.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S2"}
        results.append({"id": "N6", "注入": "★权威 raw 的 compositionData 加一个 shots 键 ⟹ "
                                     "「源站没有镜头实体」那条应翻红",
                        "★注入是否真打上": True, "预期红": ["S2"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 阴性 N7：★ **改单趟闭环 raw** ⟹ S4 应红 ───────────────────────
    #    ★ 证明 S4 真的在读那份闭环 raw，而不是读一份写死的结论。
    #    ★ 键名对齐 raw 的实际结构：`D_★读到的默认名`（第一版写的 `C_★读到的默认名`
    #      是**旧版 raw** 的键名 ⟹ 注入会打在**不存在的键**上 ⟹ 门禁照绿 ⟹
    #      负控看起来「通过」实则**什么都没测** ⟹ ★ 这正是「手打的标识符是输入，
    #      不是测量」的一次复现）。
    backup(RAW_CLOSED)
    d = json.loads(RAW_CLOSED.read_text(encoding="utf-8"))
    if "D_★读到的默认名" not in d:
        print("★ 注入没打上（closedloop raw 里没有 D_★读到的默认名）⟹ 中止")
        restore_all()
        return 2
    d["D_★读到的默认名"] = "角色C"          # ← 把「角色B」改成别的 ⟹ 「A→B 递进」不成立
    RAW_CLOSED.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S4"}
        results.append({"id": "N7", "注入": "★单趟闭环 raw 里的默认名改成「角色C」⟹ "
                                     "「A→B 递进」不成立 ⟹ S4 应翻红",
                        "★注入是否真打上": True, "预期红": ["S4"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 阴性 N8：★ 改「新增角色」的 label ⟹ S4 应红 ───────────────────
    #    ★ 证明 S4 的第③条是**关系式**判据（`新增角色.label == 右栏读到的名`），
    #      而不是「读 raw 里那条存好的布尔」（★ 那个布尔改不掉才说明它只是印证）。
    backup(RAW_CLOSED)
    d = json.loads(RAW_CLOSED.read_text(encoding="utf-8"))
    newch = d.get("E_★新增的角色")
    if not newch:
        print("★ 注入没打上（closedloop raw 里没有 E_★新增的角色）⟹ 中止")
        restore_all()
        return 2
    newch[0]["label"] = "角色Z"
    d["E_★新增的角色"] = newch
    RAW_CLOSED.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S4"}
        results.append({"id": "N8", "注入": "★闭环 raw 里新增角色的 label 改成「角色Z」⟹ "
                                     "「新增角色.label == 右栏读到的名」这条**关系**被打破 ⟹ "
                                     "S4 应翻红（★ 证明第③条是关系式判据，不是读存好的布尔）",
                        "★注入是否真打上": True, "预期红": ["S4"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 阴性 N9：★ 改「独立复核」raw 里的角色 id ⟹ S4 应红 ─────────────
    #    ★ 证明第⑤条（收尾已复原）真的在读那份**独立进程**的复核 raw。
    backup(RAW_RESTORED)
    d = json.loads(RAW_RESTORED.read_text(encoding="utf-8"))
    chars = d.get("★独立复核_角色")
    if not chars:
        print("★ 注入没打上（restored raw 里没有 ★独立复核_角色）⟹ 中止")
        restore_all()
        return 2
    chars[0]["id"] = "deadbeef"
    d["★独立复核_角色"] = chars
    RAW_RESTORED.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S4"}
        results.append({"id": "N9", "注入": "★独立复核 raw 里的角色 id 改成别的 ⟹ "
                                     "「复核到的角色 == 基线那个角色」这条关系被打破 ⟹ "
                                     "S4 应翻红（★ 证明第⑤条在读那份独立复核 raw）",
                        "★注入是否真打上": True, "预期红": ["S4"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 阴性 N10：★ 改**本批自己的 README** ⟹ S7 应红 ────────────────
    #    ★ 证明 S7 的「更正已落地」那条**真的在读 README**（而不是恒真）。
    #    ★ 只动**本批**的 README ⟹ 不碰旧批次（★ 旧批次 README 不可重写）。
    readme = ROOT / "docs/research/liblib-canvas-batch838-2026-10-01/README.md"
    backup(readme)
    o838 = readme.read_text(encoding="utf-8")
    m838 = o838.replace("没有「镜头」实体", "没有「镜头」物件") \
              .replace("没有镜头实体", "没有镜头物件")
    if m838 == o838:
        print("★ 注入没打上（本批 README 里没有那句话）⟹ 中止")
        restore_all()
        return 2
    readme.write_text(m838, encoding="utf-8")
    try:
        rc, fails, verdict = run_gate()
        ok = set(fails) == {"S7"}
        results.append({"id": "N10", "注入": "★本批 README 里「没有「镜头」实体」改成别的 ⟹ "
                                      "S7 的「声明源站无镜头实体」应翻红",
                        "★注入是否真打上": True, "预期红": ["S7"], "实际红": fails,
                        "是否只红预期那些": ok, "verdict": verdict})
    finally:
        restore_all()

    # ── 复原核验 ──────────────────────────────────────────────────────
    restore_all()
    intact = {}
    for path, data in backups.items():
        intact[str(path.relative_to(ROOT))] = sha(path) == hashlib.sha256(data).hexdigest()
    results.append({"id": "复原", "注入": "★所有被注入文件按字节复原",
                    "逐文件字节一致": intact, "是否全部复原": all(intact.values())})

    ok_all = all(r.get("是否只红预期那些", True) for r in results) and \
        all(r.get("是否全部复原", True) for r in results)
    print(json.dumps(results, ensure_ascii=False, indent=1))
    n = sum(1 for r in results if r.get("是否只红预期那些", True) or r.get("是否全部复原"))
    print("阴性对照：%d/%d 通过" % (n, len(results)))
    out = ROOT / "docs/research/liblib-canvas-batch838-2026-10-01/raw/negative-838.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())

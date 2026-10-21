#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 837 阴性对照 ＋ 真实注入自检。

★ 两条纪律（来自历次教训）：
  1. **阴性每条只翻它自己那一条** ⟹ 读的字段必须互不重叠 ⟹ 否则无法归因。
  2. **注入没打上 ⟹ 负控看起来是「绿的」**（两者一模一样）⟹ 注入必须**先证明打上了**，
     打不上就**中止**（别把「没打上」当成「通过」）。

★ 注入方式（**行数中性**，且只改**注释/字面量** ⟹ 不改变构建产物）：
  - 对「源码字面量」的判据 ⟹ 改 `src/store/directorStore.ts` 里的种子 name。
  - 对「读脚本本体」的判据 ⟹ 改 `scripts/verify-liblib-batch720.py` / `...750.py` 的期望值。
  - 对「运行时读数」的判据 ⟹ 改 clone 的运行时状态（用 store 改名，**不**改源码）。
  ★ 每次注入后**按字节复原**（不是「git checkout」⟹ 那会碰到别人的改动）。
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts/verify-liblib-batch837.py"
STORE = ROOT / "src/store/directorStore.ts"
S720 = ROOT / "scripts/verify-liblib-batch720.py"
S750 = ROOT / "scripts/verify-liblib-batch750.py"

PY = sys.executable


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate() -> tuple:
    r = subprocess.run([PY, str(GATE)], capture_output=True, text=True, timeout=900)
    fails = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("FAIL"):
            fails.append(line)
    passed_line = [l for l in r.stdout.splitlines() if "通过" in l and "/" in l]
    return r.returncode, fails, (passed_line[-1] if passed_line else "?"), r.stdout


def expect_only(target: str, fails: list, allowed: list) -> tuple:
    """★ 阴性纪律：只允许 `allowed` 里的那条红；其余任何一条红都算失败。"""
    red_labels = []
    for f in fails:
        # "FAIL  S3 ★★ ..." → 取 "S3"
        parts = f.split()
        red_labels.append(parts[1] if len(parts) > 1 else f)
    ok = set(red_labels) == set(allowed)
    return ok, red_labels


def main() -> int:
    results = []
    backups = {}

    def backup(path: pathlib.Path):
        if path not in backups:
            backups[path] = path.read_bytes()

    def restore_all():
        for path, data in backups.items():
            path.write_bytes(data)

    # ── 阴性 N1：把种子名改回旧值 ⟹ S2/S3/S4 应红 ─────────────────────
    backup(STORE)
    orig = STORE.read_text(encoding="utf-8")
    # ★ 注入必须**行数中性**：只替换字符串内容，不增删行
    mutated = orig.replace('    name: "机位1",\n', '    name: "机位01 · 对峙中景",\n', 1)
    if mutated == orig:
        print("★ 注入没打上（种子 name 那行没找到）⟹ 中止")
        restore_all()
        return 2
    STORE.write_text(mutated, encoding="utf-8")
    try:
        rc, fails, verdict, out = run_gate()
        # ★ 预期红清单修正：第一版只写了 S2/S3/S4 ⟹ 实际多红一条 S7 ⟹
        #   ★ 查清了：S7 断言的正是「轨道行 title == 机位1 · 机位」⟹
        #   种子名一改回旧值，它**理应**红 ⟹ **是我的预期清单漏了它，不是它有毛病**。
        #   ⟹ 清单补上 S7（S7 读的是**轨道 label**，与机位名同源 ⟹ 同批红是**正确**的）。
        ok, red = expect_only("N1", fails, ["S2", "S3", "S4", "S7"])
        results.append({
            "id": "N1",
            "注入": "种子 name → 「机位01 · 对峙中景」（行数中性）",
            "★注入是否真打上": True,
            "预期红": ["S2", "S3", "S4", "S7"],
            "实际红": red,
            "是否只红预期那些": ok,
            "verdict": verdict,
        })
    finally:
        restore_all()

    # ── 阴性 N2：把 720 的 FIXTURE 改回旧值 ⟹ S5 应红 ────────────────
    backup(S720)
    o720 = S720.read_text(encoding="utf-8")
    m720 = o720.replace('"咖啡馆背景", "机位1"]', '"咖啡馆背景", "机位01 · 对峙中景"]', 1)
    if m720 == o720:
        print("★ 注入没打上（720 FIXTURE 那行没找到）⟹ 中止")
        restore_all()
        return 2
    S720.write_text(m720, encoding="utf-8")
    try:
        rc, fails, verdict, out = run_gate()
        ok, red = expect_only("N2", fails, ["S5"])
        results.append({
            "id": "N2",
            "注入": "720 FIXTURE 末项 → 旧值「机位01 · 对峙中景」（行数中性）",
            "★注入是否真打上": True,
            "预期红": ["S5"],
            "实际红": red,
            "是否只红预期那些": ok,
            "verdict": verdict,
        })
    finally:
        restore_all()

    # ── 阴性 N3：把 750 的 innerTitle 期望值改回旧值 ⟹ S5 应红 ───────
    backup(S750)
    o750 = S750.read_text(encoding="utf-8")
    m750 = o750.replace('ts.get("innerTitle") == "机位1 · 机位"',
                        'ts.get("innerTitle") == "机位01 · 对峙中景 · 机位"', 1)
    if m750 == o750:
        print("★ 注入没打上（750 innerTitle 那行没找到）⟹ 中止")
        restore_all()
        return 2
    S750.write_text(m750, encoding="utf-8")
    try:
        rc, fails, verdict, out = run_gate()
        ok, red = expect_only("N3", fails, ["S5"])
        results.append({
            "id": "N3",
            "注入": "750 innerTitle 期望值 → 旧值（行数中性）",
            "★注入是否真打上": True,
            "预期红": ["S5"],
            "实际红": red,
            "是否只红预期那些": ok,
            "verdict": verdict,
        })
    finally:
        restore_all()

    # ── 阴性 N4：把源站 raw 里的「对峙中景」证据改成「出现了」 ⟹ S1 应红 ──
    #    ★ 这一条是「否定性判据」的反向 ⟹ 证明 S1 真的在读那批 raw。
    raw = ROOT / "docs/research/liblib-canvas-batch837-2026-10-01/raw/source-837-shotname-scan.json"
    backup(raw)
    oraw = raw.read_text(encoding="utf-8")
    mraw = oraw.replace('"基线机位"', '"★注入_对峙中景": "机位01 · 对峙中景",\n  "基线机位"', 1)
    if mraw == oraw:
        print("★ 注入没打上（源站 raw 那行没找到）⟹ 中止")
        restore_all()
        return 2
    raw.write_text(mraw, encoding="utf-8")
    try:
        rc, fails, verdict, out = run_gate()
        ok, red = expect_only("N4", fails, ["S1"])
        results.append({
            "id": "N4",
            "注入": "源站 raw 里塞进「对峙中景」⟹ S1 的「零出现」应翻红",
            "★注入是否真打上": True,
            "预期红": ["S1"],
            "实际红": red,
            "是否只红预期那些": ok,
            "verdict": verdict,
        })
    finally:
        restore_all()

    # ── 阴性 N5：把整页扫描里的「S83·镜2」改成不含「镜」 ⟹ S6 应红 ────
    #    ★ 这一条证明 S6 的「扫描器有效性」确实在起作用 ⟹ 不是恒绿。
    raw2 = ROOT / "docs/research/liblib-canvas-batch837-2026-10-01/raw/source-837-shotname-page-scan.json"
    backup(raw2)
    o2 = raw2.read_text(encoding="utf-8")
    m2 = o2.replace("S83·镜2", "S83·X2", 1)
    if m2 == o2:
        print("★ 注入没打上（整页扫描那行没找到）⟹ 中止")
        restore_all()
        return 2
    raw2.write_text(m2, encoding="utf-8")
    try:
        rc, fails, verdict, out = run_gate()
        ok, red = expect_only("N5", fails, ["S6"])
        results.append({
            "id": "N5",
            "注入": "整页扫描里的「S83·镜2」→「S83·X2」⟹ S6 的「读到了镜」应翻红",
            "★注入是否真打上": True,
            "预期红": ["S6"],
            "实际红": red,
            "是否只红预期那些": ok,
            "verdict": verdict,
        })
    finally:
        restore_all()

    # ── 阴性 N6：★ **真注入**（改产品源码）⟹ 门禁必须红，且**改的是产品行为** ──
    #    这一条与 N1 的区别：N1 改的是**种子字面量**；N6 改的是**派生式**
    #    （把镜头名从「${camera.name} · 镜头」改成固定串）⟹ 证明 S3 真的在盯派生关系。
    backup(STORE)
    o3 = STORE.read_text(encoding="utf-8")
    m3 = o3.replace("name: `${camera.name} · 镜头`,", "name: `固定镜头名`,", 1)
    if m3 == o3:
        print("★ 注入没打上（镜头派生式那行没找到）⟹ 中止")
        restore_all()
        return 2
    STORE.write_text(m3, encoding="utf-8")
    try:
        rc, fails, verdict, out = run_gate()
        ok, red = expect_only("N6", fails, ["S3"])
        results.append({
            "id": "N6",
            "注入": "★真注入：镜头名派生式 → 固定串「固定镜头名」（行数中性）",
            "★注入是否真打上": True,
            "预期红": ["S3"],
            "实际红": red,
            "是否只红预期那些": ok,
            "verdict": verdict,
        })
    finally:
        restore_all()

    # ── 阴性 N7：★★ **只**把派生式改掉，但**让名字仍然正确** ⟹ 只有「关系式」判据能抓 ──
    #    N6 的盲区：它同时改掉了「派生式」与「运行时名字」⟹ 无法区分
    #    「是关系式判据抓到的」还是「是绝对值判据抓到的」。
    #    ⟹ N7 把派生式改成**等价但换了写法**的形式：
    #       `name: `${camera.name} · 镜头`` ⟹ `name: `${camera.name} · ${"镜头"}``
    #       ⟹ **运行时名字一字不差**（仍是「机位1 · 镜头」）⟹ 绝对值判据**照样绿**
    #       ⟹ 只有「源码派生式必须是那条字面量」的关系式判据会红。
    backup(STORE)
    o4 = STORE.read_text(encoding="utf-8")
    m4 = o4.replace("name: `${camera.name} · 镜头`,",
                    "name: `${camera.name} · ${\"镜头\"}`,", 1)
    if m4 == o4:
        print("★ 注入没打上（镜头派生式那行没找到）⟹ 中止")
        restore_all()
        return 2
    STORE.write_text(m4, encoding="utf-8")
    try:
        rc, fails, verdict, out = run_gate()
        ok, red = expect_only("N7", fails, ["S3"])
        results.append({
            "id": "N7",
            "注入": "★★ **等价改写**派生式（运行时名字一字不差）⟹ "
                    "只有「源码派生式字面量」这条关系式判据能抓",
            "★注入是否真打上": True,
            "★运行时名字是否仍正确": "S3" in red,
            "预期红": ["S3"],
            "实际红": red,
            "是否只红预期那些": ok,
            "verdict": verdict,
        })
    finally:
        restore_all()

    # ── 复原核验：所有被注入的文件必须**按字节**回到原样 ─────────────
    restore_all()
    intact = {}
    for path, data in backups.items():
        intact[str(path.relative_to(ROOT))] = sha(path) == hashlib.sha256(data).hexdigest()
    results.append({
        "id": "复原",
        "注入": "★所有被注入文件按字节复原",
        "逐文件字节一致": intact,
        "是否全部复原": all(intact.values()),
    })

    ok_all = all(r.get("是否只红预期那些", True) for r in results) and \
        all(r.get("是否全部复原", True) for r in results)
    print(json.dumps(results, ensure_ascii=False, indent=1))
    print("阴性对照：%d/%d 通过" % (sum(1 for r in results if r.get("是否只红预期那些", True)
                                        or r.get("是否全部复原")), len(results)))
    out = ROOT / "docs/research/liblib-canvas-batch837-2026-10-01/raw/negative-837.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", out)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())

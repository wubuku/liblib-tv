#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★ batch 868 负控：★ 证明门禁 `868` 的判据**有牙**。

## ★ 每条负控都必须**复原源码**（★ 字节级）

★ Batch 866 记过的坑：★ 变异层失败时源码不复原 ⟹ ⟹ 门禁带着污染退出。
★ ⇒ 本脚本用 `try/finally` ⟹ ⟹ **无条件**复原 ⟹ ⟹ 且复原后做**字节级**自检。

## ★ ★★ 变异必须落在【被断言读的那个量】上

★ Batch 866／867 记过的坑：★ 负控没打红 ⟹ ⟹ **先查变异落点** ⟹ ⟹ 再怀疑判据。
★ 本脚本每条都**写明**：★ 门禁的**哪一条判据**读**哪个量** ⟹ ⟹ 变异就动那里。

## ★ 负控清单

| # | 变异 | 被测判据 | 读的是哪个量 |
| --- | --- | --- | --- |
| N1 | 删掉「生成其他年龄版本」的 `onClick` | S2 | 该标签属性表里**有没有** `onClick` |
| N2 | 删掉导演台「预设运镜」的 `onClick` | S2 | 同上 |
| N3 | 往导演台组件里塞一枚**没有行为**的 `<button>` | S3 | `src/components/director/**` 里的死控件候选数 |
| N4 | 把清单里的一条删掉 | S4 | 「放宽口径命中 ∖ 清单」 |
| N5 | 把运行时读数文件挪走 | S1 | `raw/runtime-868.json` 是否在库 |
| N6 | 在**注释里**写 `onClick` ⟹ ⟹ 判据**不得**变绿 | S2 | ★ 剥注释后属性表里**有没有** `onClick` |
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
BATCH = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
OUT = BATCH / "raw/negative-audit.json"
GATE = ROOT / "scripts/verify-liblib-batch867.py"  # ★ 占位（下面用 868）
GATE = ROOT / "scripts/verify-liblib-batch868.py"
RUNTIME = BATCH / "raw/runtime-868.json"
REGRESS = BATCH / "probes/regress868.py"

# ★ ★★ 本批改过的源文件（★ 负控结束后必须**逐字节**回到这里的样子）
MUTATED_FILES = [
    "src/components/CharacterLibraryPanel.tsx",
    "src/components/director/DirectorCameraMotionTab.tsx",
]


def run_gate() -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True,
                       text=True, timeout=900, cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    results: list[dict] = []
    # ★ ★★ **负控开始前**的基线 sha（★ 复原自检拿它当基准）
    baseline_sha = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
                    for rel in MUTATED_FILES}
    # ★ ★★ `src/` 全量快照（★ 用来抓「负控期间别的文件被改」）
    src_snapshot = {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
                    for f in sorted(ROOT.glob("src/**/*.tsx"))}

    # ── 基线：门禁必须是绿的 ─────────────────────────────────────
    rc, out = run_gate()
    results.append({"name": "基线：门禁 868 必须是绿的", "gate": "868",
                    "applied": True, "rc": rc, "red": rc != 0,
                    "verdict": "★ 基线绿" if rc == 0 else "★ ★ 基线就红（后面没法判）"})
    if rc != 0:
        print(out[-2000:])
        return 1

    # ── N1：删掉角色库那枚按钮的 onClick ─────────────────────────
    p = ROOT / "src/components/CharacterLibraryPanel.tsx"
    orig = p.read_bytes()
    text = orig.decode("utf-8")
    needle = '                    onClick={handleQuickAge}\n'
    try:
        assert text.count(needle) == 1, "★ 锚点不唯一：%d" % text.count(needle)
        p.write_text(text.replace(needle, "", 1), encoding="utf-8")
        rc, out = run_gate()
        red = rc != 0
        hit = "the-fixed-control-quick-age-has-an-onclick" in out
        results.append({"name": "N1: 删掉「生成其他年龄版本」的 onClick",
                        "gate": "868", "applied": True, "rc": rc, "red": red,
                        "expectLabelSeen": hit,
                        "verdict": "★ 判据有牙" if red and hit else "★ ★ 没打红"})
    finally:
        p.write_bytes(orig)
        assert p.read_bytes() == orig, "★ N1 复原失败"

    # ── N2：删掉导演台「预设运镜」的 onClick ───────────────────────
    p = ROOT / "src/components/director/DirectorCameraMotionTab.tsx"
    orig = p.read_bytes()
    text = orig.decode("utf-8")
    needle = "          onClick={() => setPresetListOpen((open) => !open)}\n"
    try:
        assert text.count(needle) == 1, "★ 锚点不唯一：%d" % text.count(needle)
        p.write_text(text.replace(needle, "", 1), encoding="utf-8")
        rc, out = run_gate()
        red = rc != 0
        hit = "the-fixed-control-motion-preset-has-an-onclick" in out
        results.append({"name": "N2: 删掉导演台「预设运镜」的 onClick",
                        "gate": "868", "applied": True, "rc": rc, "red": red,
                        "expectLabelSeen": hit,
                        "verdict": "★ 判据有牙" if red and hit else "★ ★ 没打红"})
    finally:
        p.write_bytes(orig)
        assert p.read_bytes() == orig, "★ N2 复原失败"

    # ── N3：往导演台塞一枚**没有行为**的按钮 ───────────────────────
    p = ROOT / "src/components/director/DirectorCameraMotionTab.tsx"
    orig = p.read_bytes()
    text = orig.decode("utf-8")
    anchor = "      <section className=\"space-y-2 border-t border-white/[0.07] pt-3\">\n"
    try:
        assert text.count(anchor) == 1, "★ 锚点不唯一：%d" % text.count(anchor)
        injected = (anchor
                    + '        <button type="button" className="h-9 w-full">注入的死按钮</button>\n')
        p.write_text(text.replace(anchor, injected, 1), encoding="utf-8")
        rc, out = run_gate()
        red = rc != 0
        hit = "the-director-desk-has-no-dead-buttons" in out
        results.append({"name": "N3: 往导演台注入一枚没有行为的按钮",
                        "gate": "868", "applied": True, "rc": rc, "red": red,
                        "expectLabelSeen": hit,
                        "verdict": "★ 判据有牙" if red and hit else "★ ★ 没打红"})
    finally:
        p.write_bytes(orig)
        assert p.read_bytes() == orig, "★ N3 复原失败"

    # ── N4：把清单里的一条删掉（★ S4 缺口检测）──────────────────
    # ★ ★★ Batch 868：**第一版这里写的是 `p.write_text(...)`** ⟹ ⟹ ⟹ ⟹ ⇒
    #   ★ 而 `p` 是 **N3 段残留的变量**（★ 指向 `DirectorCameraMotionTab.tsx`！）
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 于是「删清单里一条」这个变异
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ **把回归脚本的内容写进了源文件** ⟹ ⟹ ⟹ ⟹ ⇒
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而且 `finally` 只复原了 `REGRESS`
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 源文件**留在污染态**
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 症状极具欺骗性：
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 「跑完了、负控也报了、但源文件已经是别的东西」
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 通则：★ 负控里**每条**
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 都要**自己声明**它改哪个文件（★ 不许靠残留变量）
    orig = REGRESS.read_bytes()
    text = orig.decode("utf-8")
    import re as _re
    mm = _re.search(r'\("(\d+)", "py"\),\n', text)
    try:
        assert mm is not None, "★ 清单里找不到可删的条目"
        target = mm.group(0)
        # ★ ★★ 显式用 `REGRESS`（★ **不用**残留的 `p`）
        REGRESS.write_text(text.replace(target, "", 1), encoding="utf-8")
        rc, out = run_gate()
        red = rc != 0
        hit = "every-gate-touching-the-tracked-sources-is-listed" in out
        results.append({"name": "N4: 从回归清单里删掉一条（%s）" % target.strip(),
                        "gate": "868", "applied": True, "rc": rc, "red": red,
                        "expectLabelSeen": hit,
                        "verdict": "★ 判据有牙" if red and hit else "★ ★ 没打红"})
    finally:
        REGRESS.write_bytes(orig)
        assert REGRESS.read_bytes() == orig, "★ N4 复原失败"

    # ── N5：把运行时读数挪走（★ S1 证据在库）─────────────────────
    backup = RUNTIME.with_suffix(".json.bak868")
    try:
        shutil.move(str(RUNTIME), str(backup))
        rc, out = run_gate()
        red = rc != 0
        hit = "the-runtime-evidence-is-in-the-repo" in out
        results.append({"name": "N5: 把运行时读数挪走",
                        "gate": "868", "applied": True, "rc": rc, "red": red,
                        "expectLabelSeen": hit,
                        "verdict": "★ 判据有牙" if red and hit else "★ ★ 没打红"})
    finally:
        if backup.exists():
            shutil.move(str(backup), str(RUNTIME))
        assert RUNTIME.exists(), "★ N5 复原失败"

    # ── N6：★ 在**注释里**写 onClick ⟹ ⟹ 判据**不得**变绿 ────────
    # ★ ★★ Batch 868：**第一版这条的期望是反的** ⟹ ⟹ ⟹ ⟹ ⇒
    #   ★ 第一版：★ 只在注释里**加**一枚 onClick ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而**真的**那枚还在
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ 判据**理应仍然绿** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 但它写的是
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 「期望：仍然**红**」⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 期望与事实矛盾
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 这条负控**证明不了它想证明的事**
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 正确做法：★ **同时**① 删掉真的 onClick
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ② 在**注释里**补一枚同名的 onClick
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ 判据**必须红**
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ （★ 若它绿 ⟹ ⟹ ⟹ ⟹ ⇒
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ 说明注释里的 onClick 被当成了真的
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ 剥注释没生效）
    p = ROOT / "src/components/director/DirectorCameraMotionTab.tsx"
    orig = p.read_bytes()
    text = orig.decode("utf-8")
    anchor = "          data-director-motion-preset-button\n"
    real_onclick = ("          onClick={() => setPresetListOpen((open) => !open)}\n")
    try:
        assert text.count(anchor) == 1, "★ 锚点不唯一：%d" % text.count(anchor)
        assert text.count(real_onclick) == 1, \
            "★ 真 onClick 不唯一：%d" % text.count(real_onclick)
        # ① 删掉真的 onClick
        stripped = text.replace(real_onclick, "", 1)
        # ② 在注释里补一枚同名的
        injected = (anchor
                    + "          {/* onClick={() => setPresetListOpen((open) => !open)} */}\n")
        stripped = stripped.replace(anchor, injected, 1)
        p.write_text(stripped, encoding="utf-8")
        rc, out = run_gate()
        # ★ 期望：**红**（★ 真 onClick 已被删 ⟹ ⟹ 注释里那个**不算数**）
        red = rc != 0
        results.append({"name": "N6: 删掉真 onClick ＋ 在注释里补一枚 ⟹ 判据必须红",
                        "gate": "868", "applied": True, "rc": rc, "red": red,
                        "expectLabelSeen": "the-fixed-control-motion-preset-has-an-onclick" in out,
                        "verdict": "★ 剥注释生效（注释不算接线）" if red
                                   else "★ ★ ★ 注释里的 onClick 被当成了真的 ⟹ 判据有洞"})
    finally:
        p.write_bytes(orig)
        assert p.read_bytes() == orig, "★ N6 复原失败"

    # ── 复原自检：★ 全部源码必须**字节级**回到「负控开始前」 ──────────
    # ★ ★★ Batch 868：**第一版这里用 `git diff --stat`** ⟹ ⟹ ⟹ ⟹ ⇒
    #   ★ 而**本批本来就改了这两个源文件** ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒
    #   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 所以那个判据**恒为脏** ⟹ ⟹ ⟹ ⟹ ⇒
    #   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 换句话说：★ 它**永远报脏** ⟹ ⟹ ⟹ ⟹ ⇒
    #   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 判据**恒红** ⟹ ⟹ ⟹ ⟹ ⇒
    #   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 等于**没有判据**
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ （★ 这正是本仓记过的那个形状：
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 「**判据自己先自检**」）
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 修法：★ 拿**负控开始前**的 sha 做基线
    dirty = []
    for rel, want in baseline_sha.items():
        got = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if got != want:
            dirty.append("%s（★ 与负控开始前不一致）" % rel)
    results.append({"复原自检": "字节级干净（★ 与负控开始前一致）" if not dirty else dirty})
    # ★ ★★ 跨文件污染守卫：★ 负控**跑的过程中** ⟹ ⟹ ⟹ ⟹ ⇒
    #   ★ 有没有**别的**文件被意外改掉
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 口径：★ **不用** `git diff`（★ 别人在 `src/` 里的
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ WIP 会**误报**）⟹ ⟹ ⟹ ⟹ ⇒ ★ 而是拿**负控开始前的快照**比
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 而**判定**分两档：
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ① **本批改过的两个文件** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 必须与基线**逐字节**相同
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ② **任何** `.tsx` 里出现了**回归脚本的特征**
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ （★ `GATES = [` ／ `KNOWN_RED`）
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 这条直接抓 N4 那个「残留变量」
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 型的污染（★ 回归脚本被写进 .tsx）
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 且**不**受别人并发改 jimeng 的影响
    touched = []
    for rel, want in src_snapshot.items():
        f = ROOT / rel
        if not f.exists():
            touched.append(rel + "（★ 消失了）")
            continue
        got = hashlib.sha256(f.read_bytes()).hexdigest()
        if got != want:
            touched.append(rel)
    # ② 直接检测「回归脚本被写进 .tsx」
    script_leak = []
    for f in sorted(ROOT.glob("src/**/*.tsx")):
        try:
            head = f.read_text(encoding="utf-8")[:4000]
        except Exception:  # noqa: BLE001
            continue
        if "GATES = [" in head or "KNOWN_RED" in head:
            script_leak.append(str(f.relative_to(ROOT)))
    results.append({"跨文件污染守卫": {
        "负控期间变动的文件": touched or "无",
        "★ 回归脚本特征泄漏进 .tsx": script_leak or "无",
    }})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    nred = sum(1 for r in results if r.get("red"))
    ntot = sum(1 for r in results if "applied" in r)
    print("\n★ 负控 %d 条，打红 %d 条" % (ntot, nred))
    for r in results:
        if "applied" in r:
            print("  %-58s rc=%-4s %s" % (r["name"][:58], r.get("rc"),
                                          r.get("verdict", "")))
    print("★ 复原自检：%s" % next(r["复原自检"] for r in results if "复原自检" in r))
    print("★ 读数已落盘：%s" % OUT)
    return 0 if nred == ntot and not dirty else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 23「截图布局漂移」的反向验证（Batch 189）。

用例清单：
  1  注入一处**未登记**的漂移              → 必报（方向一）
  2  删掉一条 DRIFT 登记（漂仍在）          → 必报（方向一：无人认领）
  3  删掉就地说明（漂移仍在、登记仍在）      → 必报（方向二之二）
  4  登记一条**已经不漂移**的               → 必报过期（方向二，防免死金牌）
  5  **紧邻要求**：把就地说明挪到 20 行之外  → 必报（**全页搜不算数**）
  6  自检探针失配（ref 指到没有探针的树）    → 必须 rc=2「未能核对」
  7  真实现状                                → 不报

**用例 5 是本文件最要紧的一条**。纪律 121 的原话是「**全页出现该版本号不算数，
读者未必读到那里**」——而如果判据用全页搜索来核「就地说明在不在」，
**它就恰好犯了自己要防的那个错，并且恒真**。所以判据只看图片引用行之后 8 行内
有没有引用块开头，用例 5 把说明挪到 20 行外，**全页搜照样找得到、紧邻判据必须报**。

**用例 4 钉的是「登记只增不减」的老毛病**：免检表一旦只增不减，几年后就是一张
没人敢碰的清单（闸 5 方向二、闸 10 的 `EXEMPT` 都是同一个教训）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-shot-drift.py")
GATE_SRC = os.path.join(ROOT, "scripts", "verify-shot-drift.py")
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")
DIRECTOR = os.path.join(ROOT, "10-tasks", "director-basics.md")

results = []


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def run(env=None):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True, env=e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def snapshot():
    return {MANIFEST: read(MANIFEST), DIRECTOR: read(DIRECTOR), GATE_SRC: read(GATE_SRC)}


def restore(s):
    for p, t in s.items():
        write(p, t)


def _note_span(lines, name):
    """返回 (图片嵌入行下标, 紧随其后的整段 `>` 引用块的行号区间)。"""
    i = next(k for k, l in enumerate(lines) if ("![" in l) and (name in l))
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    k = j
    while k < len(lines) and lines[k].lstrip().startswith(">"):
        k += 1
    return i, j, k


def check_anchor():
    g = read(GATE_SRC)
    assert "DRIFT = {" in g, "前提失配：闸门里没有 DRIFT 登记表"
    assert "33-director-workbench.png" in g, "前提失配：DRIFT 里少了 33 那条"
    m = read(MANIFEST)
    assert "visible_text:" in m, "前提失配：manifest 里没有 visible_text"
    d = read(DIRECTOR)
    assert "33-director-workbench.png" in d, "前提失配：director-basics.md 里引用不到 33 那张图"


# ── 1 注入未登记的漂移 → 必报 ────────────────────────────────────────
def m_unregistered_must_report():
    check_anchor()
    snap = snapshot()
    try:
        # 把 33 的文案换成「摄像机检查器」——它在 v1.6.14 有、基线里那行已不在
        # （Batch 188 核实过变的只是一行注释，故本闸会跳过它；**换成它测不出东西**）
        # 所以这里改用**确定会漂**的那条：把 33 的 visible_text 改成「选择镜头模板」
        g = read(GATE_SRC)
        g2 = g.replace('"33-director-workbench.png":', '"zzz-unregistered.png":', 1)
        assert g2 != g, "前提失配：注入没生效（DRIFT 键名未替换）"
        write(GATE_SRC, g2)
        m = read(MANIFEST)
        m2 = m.replace("visible_text: '3D导演台'", "visible_text: '选择镜头模板'", 1)
        assert m2 != m, "前提失配：manifest 注入没生效"
        write(MANIFEST, m2)
        rc, out = run()
        ok = rc == 1 and "33-director-workbench.png" in out and "方向一" in out
        record("1 未登记的漂移 → 必报", ok, f"rc={rc}")
    finally:
        restore(snap)


# ── 2 删掉一条登记 → 必报（漂仍在、无人认领）─────────────────────────
def m_missing_registry_must_report():
    check_anchor()
    snap = snapshot()
    try:
        g = read(GATE_SRC)
        g2 = re.sub(r'\n    "33-director-workbench\.png":\n        "[^"]*"(?:\n        "[^"]*")*,', "", g)
        assert g2 != g, "前提失配：注入没生效（没能删掉 33 那条登记）"
        write(GATE_SRC, g2)
        rc, out = run()
        ok = rc == 1 and "33-director-workbench.png" in out
        record("2 漂仍在但无人认领 → 必报", ok, f"rc={rc}")
    finally:
        restore(snap)


# ── 3 删掉就地说明 → 必报 ───────────────────────────────────────────
def m_missing_note_must_report():
    check_anchor()
    snap = snapshot()
    try:
        ls = read(DIRECTOR).split("\n")
        i, j, k = _note_span(ls, "33-director-workbench.png")
        assert k > j, "前提失配：图片后面没有引用块（就地说明已不在？)"
        write(DIRECTOR, "\n".join(ls[:j] + ls[k:]))     # **整段删掉**
        rc, out = run()
        ok = rc == 1 and "就地说明" in out
        record("3 漂移有登记但就地说明被删 → 必报", ok, f"rc={rc}")
    finally:
        restore(snap)


# ── 4 登记一条已经不漂移的 → 必报过期 ───────────────────────────────
def m_stale_registry_must_report():
    check_anchor()
    snap = snapshot()
    try:
        # 拿一张确定不漂移的截图去登记（34-camera-inspector 在 Batch 188 核实过是假阳性）
        g = read(GATE_SRC)
        anchor = '    "33-director-workbench.png":'
        i = g.index(anchor)
        g2 = g[:i] + '    "34-camera-inspector.png":\n        "反验注入：登记一条并不漂移的截图",\n' + g[i:]
        write(GATE_SRC, g2)
        rc, out = run()
        ok = rc == 1 and "已经不漂移" in out
        record("4 登记已不漂移的 → 必报过期", ok, f"rc={rc}")
    finally:
        restore(snap)


# ── 5 紧邻要求：把说明挪到 20 行外 → 必报 ───────────────────────────
def m_note_must_be_adjacent():
    check_anchor()
    snap = snapshot()
    try:
        ls = read(DIRECTOR).split("\n")
        i, j, k = _note_span(ls, "33-director-workbench.png")
        block = ls[j:k]                                  # **整段挪走**
        rest = ls[:j] + ls[k:]
        # 挪到**文件末尾**——必然离引用处超过 8 行，且**仍在同一页里**
        # （全页搜照样找得到，这正是这一例要测的东西）
        rest2 = rest + [""] + block
        write(DIRECTOR, "\n".join(rest2))
        # 关键前提：说明**仍在这一页里**（全页搜照样找得到）——这正是用例的意义
        assert "33-director-workbench.png" in read(DIRECTOR)
        rc, out = run()
        ok = rc == 1 and "紧邻" in out
        record("5 说明挪远（全页仍搜得到）→ 必报", ok, f"rc={rc}")
    finally:
        restore(snap)


# ── 6 自检探针失配 → 必须 rc=2 ──────────────────────────────────────
def m_probe_mismatch_must_be_rc2():
    check_anchor()
    snap = snapshot()
    try:
        g = read(GATE_SRC)
        g2 = g.replace('aria-label=\\"摄像机检查器', 'aria-label=\\"这段探针在上游任何一棵树里都不存在', 1)
        assert g2 != g, "前提失配：注入没生效"
        write(GATE_SRC, g2)
        rc, out = run()
        ok = rc == 2 and "未能核对" in out
        record("6 自检探针失配 → 必须 rc=2 未能核对", ok, f"rc={rc}")
    finally:
        restore(snap)


# ── 7 真实现状 ──────────────────────────────────────────────────────
def m_clean_pass():
    check_anchor()
    rc, out = run()
    record("7 真实现状 → 不报", rc == 0, f"rc={rc}")


def main():
    tests = [m_unregistered_must_report, m_missing_registry_must_report,
             m_missing_note_must_report, m_stale_registry_must_report,
             m_note_must_be_adjacent, m_probe_mismatch_must_be_rc2, m_clean_pass]
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", f"前提失配：{exc}")
    failed = 0
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print(f"  {mark} {name}  {detail}")
        if status != "通过":
            failed += 1
    print(f"闸 23 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

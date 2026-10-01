#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 16「截图版本登记」的反向验证（Batch 177）。

用例清单：
  1  删掉某张图的 captured_version      → 必报（方向一）
  2  captured_version 形态非法          → 必报（方向一）
  3  登记了失效但引用页正文没写版本说明  → 必报（方向二，**本批核心**）
  4  登记了失效但没人引用这张图          → 必报（方向二）
  5  误登记：上游顶端其实还有那个文件    → 必报（方向三）
  6  **方向三必须核上游顶端而非基线**    → 用 BEEFTV_REF 指向基线时**不得**报错
  7  真实现状                          → 不报

**用例 6 是本文件最要紧的一条**：判据上线首跑就因为拿基线核而误报，
反验必须把「修法」钉住，否则下一个人会以为那是误报而改回去。
"""

import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-shot-version.py")
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")
PAGE = os.path.join(ROOT, "10-tasks", "director-basics.md")
GATE_SRC = os.path.join(ROOT, "scripts", "verify-shot-version.py")

results = []


def run(env=None):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True, env=e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def snapshot():
    return {MANIFEST: read(MANIFEST), PAGE: read(PAGE), GATE_SRC: read(GATE_SRC)}


def restore(s):
    for p, t in s.items():
        write(p, t)


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def check_anchor():
    t = read(MANIFEST)
    assert "captured_version:" in t, "前提失配：manifest 里没有 captured_version 字段"
    g = read(GATE_SRC)
    assert "STALE = {" in g, "前提失配：闸门里没有 STALE 登记表"


# ── 1 缺 captured_version ────────────────────────────────────────────
def m_missing_version():
    check_anchor()
    s = snapshot()
    try:
        t = s[MANIFEST]
        new = re.sub(r"^\s*captured_version: 'v1\.6\.14'\n", "", t, count=1, flags=re.M)
        assert new != t, "注入未生效：captured_version 没被删掉"
        write(MANIFEST, new)
        rc, out = run()
        record("1 缺 captured_version→必报", rc == 1 and "方向一" in out, f"rc={rc}")
    finally:
        restore(s)


# ── 2 形态非法 ──────────────────────────────────────────────────────
def m_bad_version_shape():
    check_anchor()
    s = snapshot()
    try:
        t = s[MANIFEST]
        new = t.replace("captured_version: 'v1.6.14'", "captured_version: '1.6'", 1)
        assert new != t, "注入未生效：版本号没被改"
        write(MANIFEST, new)
        rc, out = run()
        record("2 版本形态非法→必报", rc == 1 and "方向一" in out, f"rc={rc}")
    finally:
        restore(s)


# ── 3 引用页没写版本说明 ─────────────────────────────────────────────
def m_page_missing_note():
    check_anchor()
    s = snapshot()
    try:
        t = s[PAGE]
        # 删掉紧跟该截图之后的三行说明（用行首锚点，不靠脆弱的多行正则）
        lines = t.split("\n")
        idx = next((i for i, l in enumerate(lines)
                    if "31-director-templates.png" in l), None)
        assert idx is not None, "前提失配：页面里找不到该截图的引用"
        # 图片与说明块之间可能隔着空行，所以从**下方**向上找最近的引用块起点
        probe = idx + 1
        while probe < len(lines) and not lines[probe].strip():
            probe += 1
        assert probe < len(lines) and lines[probe].startswith(">"), \
            f"前提失配：截图下方没有引用块（下一非空行是 {lines[probe][:30]!r}）"
        end = probe + 1
        while end < len(lines) and lines[end].startswith(">"):
            end += 1
        new = "\n".join(lines[:probe] + lines[end:])
        assert "这张截图拍的是" not in new, "注入未生效：说明仍在"
        write(PAGE, new)
        assert "这张截图拍的是" not in read(PAGE), "注入未生效：写回后说明仍在"
        rc, out = run()
        record("3 引用页缺说明→必报", rc == 1 and "方向二" in out, f"rc={rc}")
    finally:
        restore(s)


# ── 4 登记失效但没人引用 ─────────────────────────────────────────────
def m_stale_not_referenced():
    check_anchor()
    s = snapshot()
    try:
        t = s[PAGE]
        write(PAGE, t.replace("31-director-templates.png", "31-director-templates-OLD.png"))
        rc, out = run()
        record("4 失效图无人引用→必报", rc == 1 and "方向二" in out, f"rc={rc}")
    finally:
        restore(s)


# ── 5 误登记（上游顶端仍有该文件）→ 必报 ─────────────────────────────
def m_false_stale():
    check_anchor()
    s = snapshot()
    try:
        g = s[GATE_SRC]
        # 指向一个在上游顶端确实存在的文件
        new = g.replace(
            '"removed_file": "web/src/components/canvas/director/canvas-director-template-modal.tsx",',
            '"removed_file": "web/src/lib/canvas/director/director-templates.ts",', 1)
        assert new != g, "注入未生效：removed_file 没被改"
        write(GATE_SRC, new)
        rc, out = run()
        record("5 误登记失效→必报", rc == 1 and "方向三" in out, f"rc={rc}")
    finally:
        restore(s)


# ── 6 方向三必须核上游顶端，**不得**因基线里还有该文件而误报 ────────
def m_direction_three_uses_upstream_tip():
    check_anchor()
    rc, out = run(env={"BEEFTV_REF": "3a74793"})
    ok = rc == 0 and "方向三" not in out
    record("6 基线版本下方向三不得误报", ok, f"rc={rc}")


# ── 7 真实现状 ──────────────────────────────────────────────────────
def m_clean_pass():
    check_anchor()
    rc, out = run()
    record("7 真实现状→不报", rc == 0, f"rc={rc}")


def main():
    tests = [m_missing_version, m_bad_version_shape, m_page_missing_note,
             m_stale_not_referenced, m_false_stale, m_direction_three_uses_upstream_tip,
             m_clean_pass]
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
    print(f"闸 16 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

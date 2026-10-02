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
  8  方向四：manifest 改一张的版本（分布变）→ 必报
  9  方向四：正文三个数不自洽            → 必报
  10 方向四：正文把整个分布删掉          → 必报
  11 **输入范围必须跟着 `config.mjs` 的 srcExclude 走** → 必报
  12 **方向二必须认 README.md**（它是发布首页）→ 必报
  13 不误伤：把失效截图写进**不发布**的 `PUBLISH.md` → 不得报

**用例 6 是本文件最要紧的一条**：判据上线首跑就因为拿基线核而误报，
反验必须把「修法」钉住，否则下一个人会以为那是误报而改回去。

**用例 11/12 是 Batch 217 加的，而它们验的不是「判据能抓缺陷」，是「修法真的生效」**——
这两件事很容易混：修法写了但没接上，判据照样能抓已知缺陷、看起来一切正常。
用例 11 把 `20-reference.md` 加进 `config.mjs` 的 `srcExclude`，
**方向四必须立刻改口说「没有任何发布页声明」**——
它证明输入范围不是脚本里抄的常量，而是从配置文件读的。
用例 12 往 `README.md` 里塞一个无说明的失效截图引用，方向二必须点名 README——
**而修法之前 `README.md` 被硬编码表排除了**，`config.mjs` 里明写着
`'README.md': 'index.md'`、产物里也确实有 `index.html`：
**读者第一眼看到的页面，判据当时不认。**

**用例 13 钉住相反的一侧**：`PUBLISH.md` **不发布**（它在 `srcExclude` 里），
拿它当「引用页」等于让一个内部文件冒充读者可见的说明——
而方向二当年正是硬编码漏了它。**两类错误方向相反，必须同时钉住。**
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
#: Batch 217：方向四的核对对象，以及「范围锚在 config.mjs」要动的那两个文件
REF_PAGE = os.path.join(ROOT, "20-reference.md")
VITEPRESS = os.path.join(ROOT, ".vitepress", "config.mjs")
README = os.path.join(ROOT, "README.md")
PUBLISH = os.path.join(ROOT, "PUBLISH.md")

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
    return {p: read(p) for p in
            (MANIFEST, PAGE, GATE_SRC, REF_PAGE, VITEPRESS, README, PUBLISH)}


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
    r = read(REF_PAGE)
    assert "**截图拍于**" in r, "前提失配：20-reference.md 里没有「截图拍于」声明"
    assert re.search(r"（\d+\s*张中有\s*\d+\s*张", r), \
        "前提失配：20-reference.md 里的截图分布形态变了"
    c = read(VITEPRESS)
    assert "srcExclude" in c, "前提失配：config.mjs 里没有 srcExclude"
    assert "README.md" in c and "index.md" in c, \
        "前提失配：config.mjs 里 README→index 的重命名规则没了，用例 12 的前提不成立"


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


# ── 8 方向四：manifest 改一张的版本 → 分布变而正文没跟上 → 必报 ─────
def m_manifest_version_drift():
    check_anchor()
    s = snapshot()
    try:
        t = s[MANIFEST]
        new, n = re.subn(r"(captured_version:\s*')v1\.6\.14(')", r"\1v1.6.15\2", t, count=1)
        assert n == 1, "注入未生效：没找到 v1.6.14 的 captured_version"
        write(MANIFEST, new)
        rc, out = run()
        record("8 分布变而正文没跟上→必报", rc == 1 and "方向四" in out, f"rc={rc}")
    finally:
        restore(s)


# ── 9 方向四：正文三个数不自洽 → 必报 ───────────────────────────────
def m_distribution_inconsistent():
    check_anchor()
    s = snapshot()
    try:
        t = s[REF_PAGE]
        new = re.sub(r"另\s*\d+\s*张更早", "另 5 张更早", t, count=1)
        assert new != t, "注入未生效：没找到「另 N 张更早」"
        write(REF_PAGE, new)
        rc, out = run()
        record("9 三个数不自洽→必报",
               rc == 1 and "方向四" in out and "不自洽" in out, f"rc={rc}")
    finally:
        restore(s)


# ── 10 方向四：正文把整个分布删掉 → 必报 ─────────────────────────────
def m_distribution_deleted():
    check_anchor()
    s = snapshot()
    try:
        t = s[REF_PAGE]
        new = re.sub(r"（\d+\s*张中有[^）]*）", "", t, count=1)
        assert new != t, "注入未生效：分布括号没被删掉"
        write(REF_PAGE, new)
        assert "**截图拍于**" in read(REF_PAGE), "注入把整行删掉了，形态变了"
        rc, out = run()
        record("10 分布被删掉→必报",
               rc == 1 and "方向四" in out and "没有分布" in out, f"rc={rc}")
    finally:
        restore(s)


# ── 11 输入范围必须跟着 config.mjs 的 srcExclude 走（验的是修法）────
def m_scope_follows_config():
    check_anchor()
    s = snapshot()
    try:
        c = s[VITEPRESS]
        new = c.replace("srcExclude: [", "srcExclude: ['**/20-reference.md', ", 1)
        assert new != c, "注入未生效：srcExclude 那一行没找到"
        write(VITEPRESS, new)
        rc, out = run()
        ok = rc == 1 and "没有任何发布页声明" in out
        record("11 输入范围跟着 config.mjs 走→必报", ok, f"rc={rc}")
    finally:
        restore(s)


# ── 12 方向二必须认 README.md（它被 config.mjs 重命名成 index.md）────
def m_readme_is_published():
    check_anchor()
    s = snapshot()
    try:
        write(README, s[README] +
              "\n顺带提一句 `screenshots/31-director-templates.png` 这个界面。\n")
        rc, out = run()
        hit = [l for l in out.split("\n") if "方向二" in l and "README" in l]
        record("12 方向二认发布首页 README.md→必报", rc == 1 and bool(hit), f"rc={rc}")
    finally:
        restore(s)


# ── 13 不误伤：PUBLISH.md 不发布，不该被当成「引用页」 ────────────────
def m_unpublished_page_ignored():
    check_anchor()
    s = snapshot()
    try:
        write(PUBLISH, "试发一张 `screenshots/31-director-templates.png`。\n" + s[PUBLISH])
        rc, out = run()
        ok = rc == 0 and "方向二" not in out
        record("13 不发布的 PUBLISH.md→不得报", ok, f"rc={rc}")
    finally:
        restore(s)


def main():
    tests = [m_missing_version, m_bad_version_shape, m_page_missing_note,
             m_stale_not_referenced, m_false_stale, m_direction_three_uses_upstream_tip,
             m_clean_pass,
             m_manifest_version_drift, m_distribution_inconsistent,
             m_distribution_deleted, m_scope_follows_config,
             m_readme_is_published, m_unpublished_page_ignored]
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

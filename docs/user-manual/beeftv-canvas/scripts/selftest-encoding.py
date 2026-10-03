#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 20「文本文件编码完整性」的反向验证（Batch 183）。

用例清单：
  1  文本文件里注入 U+FFFD 替换字符   → 必报（方向二，本闸要抓的那件事）
  2  文本文件写成非法 UTF-8 字节      → 必报（方向一）
  3  文本文件里塞 NUL 字节            → 必报（方向三）
  4  **非白名单扩展名的二进制不得误报** → 必报的反面：`.DS_Store` 里有 0x80 也**不得**报
  5  判据源码里写着它要找的那个字面量 → 必报（**上线首跑就抓到了闸 20 自己**）
  6  真实现状                          → 不报
  7  文本文件里塞字面 C0 控制字符      → 必报（方向四，Batch 254 新增）
  8  换行与制表符                      → **不得**报（7 的不误伤那一半）

**用例 4 是本文件最要紧的一条**：闸 20 第一版想用「试着解码一次」来划定输入范围，
而真实手册树里就有一个 `screenshots/.DS_Store`，它含 `0x80` 字节——**试解码必然误报**。
判据把不相干的东西报成异常，人就会学会忽略它，所以输入范围必须是白名单。

**用例 5 记的是一次真实的自伤**：闸 20 上线首跑报的就是 `verify-encoding.py` 自己
（源码里直接写了 U+FFFD 字面量）。**修法不是把自己排除掉**——那等于开一道后门、
文件别处坏了照样看不见；而是改用 `\\ufffd` 转义写法，让源码里根本不出现那个字面量。
**一条判据会在自己身上触发，而正确的修法是让那个字面量消失，不是给自己发豁免。**

**为什么用例 1–4 在临时手册根里跑，不改真实手册**：闸 20 的输入范围是
`dirname(dirname(__file__))`，所以把闸门脚本放进一个临时目录，它就只扫那个目录。
**注入真实文件一旦中途被打断，损坏就留在手册里了**——而本批修的恰恰就是这类残留。
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-encoding.py")
GATE_SRC = os.path.join(ROOT, "scripts", "verify-encoding.py")
PROBE_DIRNAME = "encselftest"

results = []


def run(gate=GATE):
    r = subprocess.run([sys.executable, gate], capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def make_probe_root(files):
    """建一个临时「手册根」：scripts/verify-encoding.py + 若干样本文件。"""
    d = tempfile.mkdtemp(prefix=PROBE_DIRNAME)
    os.mkdir(os.path.join(d, "scripts"))
    shutil.copy2(GATE_SRC, os.path.join(d, "scripts", "verify-encoding.py"))
    for name, payload in files.items():
        p = os.path.join(d, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if isinstance(payload, bytes):
            with open(p, "wb") as fh:
                fh.write(payload)
        else:
            with io.open(p, "w", encoding="utf-8") as fh:
                fh.write(payload)
        # **注入必须自证生效**：文件没写成时，用例照样会「通过」，
        # 而通过的原因与被测行为无关（Batch 178：断言查的不是被改后的真实状态，
        # 它就只是一句自我确认）。逐字节数一遍，不对就地作废。
        want = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        got = open(p, "rb").read()
        assert got == want, f"注入没生效：{name} 写了 {len(got)} 字节，应为 {len(want)}"
    return d


def run_in_probe(files):
    """在临时根上跑一次闸门，返回 (rc, out, 根目录)。调用方负责删。"""
    d = make_probe_root(files)
    try:
        rc, out = run(os.path.join(d, "scripts", "verify-encoding.py"))
        return rc, out
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ── 1 U+FFFD 替换字符 → 必报 ─────────────────────────────────────────
def m_fffd_must_report():
    # **源码里一律用转义写这个字面量**，否则注入脚本自己就是坏的
    rc, out = run_in_probe({"a.md": "正常内容\n这里坏了：非\uFFFD法字符\n"})
    ok = rc == 1 and "a.md" in out and "U+FFFD" in out
    record("1 文本文件含 U+FFFD → 必报", ok, f"rc={rc}")


# ── 2 非法 UTF-8 字节 → 必报 ─────────────────────────────────────────
def m_bad_utf8_must_report():
    # 裸 0xFF 在 UTF-8 里任何位置都非法；0x80 单独出现同理
    rc, out = run_in_probe({"b.md": b"\xe6\x89\x8b\xe5\x86\x8c\n\xff\xfe\n"})
    ok = rc == 1 and "b.md" in out and "UTF-8" in out
    record("2 文本文件不是合法 UTF-8 → 必报", ok, f"rc={rc}")


# ── 3 NUL 字节 → 必报 ────────────────────────────────────────────────
def m_nul_must_report():
    rc, out = run_in_probe({"c.md": b"\xe6\x89\x8b\xe5\x86\x8c\n\x00\n"})
    ok = rc == 1 and "c.md" in out and "NUL" in out
    record("3 文本文件含 NUL 字节 → 必报", ok, f"rc={rc}")


# ── 4 非白名单扩展名的二进制里有坏字节 → **不得**报 ──────────────────
def m_binary_must_not_report():
    payload = {"ok.md": "正常\n",
               "screenshots/.DS_Store": b"\x00\x01\x80\xff\xfe",   # 真有非法字节
               "img.png": b"\x89PNG\r\n\x1a\n\x80\xff"}
    rc, out = run_in_probe(payload)
    ok = rc == 0 and "DS_Store" not in out
    record("4 二进制/非白名单文件含坏字节 → 不得误报", ok, f"rc={rc}")


# ── 5 判据源码里写着它要找的字面量 → 必报 ────────────────────────────
def m_gate_own_literal_must_report():
    rc, out = run_in_probe({"d.md": "源码里带着字面量：\uFFFD\uFFFD\n"})
    ok = rc == 1 and "d.md" in out
    record("5 判据自身源码含字面量 → 必报（上线首跑抓到的就是它）", ok, f"rc={rc}")


# ── 6 真实现状 ──────────────────────────────────────────────────────
def m_clean_pass():
    rc, out = run()
    record("6 真实现状 → 不报", rc == 0, f"rc={rc}")


# ── 7 C0 控制字符 → 必报（Batch 254 方向四）──────────────────────────
def m_c0_control_must_report():
    # **这里刻意用 `chr(3)` 而不是写进一个转义**——
    # 本批最大的一个坑就是：反向引用 `\\1` 穿过两层字符串后被解成了 **U+0001**，
    # **而文件完全合法、Python 照常编译、闸 20 照常报绿**。
    # **而这个用例自己就是那个坑的对照组**：
    # 注入必须靠 `chr()` 现算，**不能让注入代码本身再穿一层字符串**。
    rc, out = run_in_probe({"e.md": "正常内容\n这里有个控制字符：" + chr(3) + "\n"})
    ok = rc == 1 and "e.md" in out and "U+0003" in out
    record("7 文本文件含 C0 控制字符 → 必报（并点名码位）", ok, f"rc={rc}")


# ── 8 换行与制表符 → **不得**报（不误伤那一半）────────────────────────
def m_newline_tab_must_not_report():
    payload = {"f.md": "第一行\n\t缩进的第二行\n\n\n第四行\n"}
    rc, out = run_in_probe(payload)
    # **断言「一条都没报」，而不是断言某个词不出现**——
    # 第一版写的是 `"C0" not in out`，而**闸的通过语里恰恰写着「无 C0 控制字符」**，
    # **于是这条用例红在一个与被测行为完全无关的地方**。
    # **判据的输出里出现了某个词，不等于它判了这件事**——
    # 与纪律 14 的老教训同形：**要问的是「它判的是什么」，不是「它字面上提了什么」**。
    ok = rc == 0 and "✗" not in out
    record("8 换行/制表符 → 不得误报", ok, f"rc={rc}")


def main():
    tests = [m_fffd_must_report, m_bad_utf8_must_report, m_nul_must_report,
             m_binary_must_not_report, m_gate_own_literal_must_report, m_clean_pass,
             m_c0_control_must_report, m_newline_tab_must_not_report]
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
    print(f"闸 20 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

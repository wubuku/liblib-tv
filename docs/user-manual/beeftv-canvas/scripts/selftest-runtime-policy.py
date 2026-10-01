#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十二道闸（`verify-runtime-policy.py`）的反向验证。

**它与别的闸最不一样的地方**：手册登记的**不是「一个数」，而是「同一个常量的两套取值」**
（默认部署 / 本地部署 `localMode`）。所以反验的核心是——
**只改其中一套而另一套正确时，闸门必须仍然报错**。
如果它只核了默认那一列，本地模式那一半就等于没看守，而那恰恰是本手册读者的主要场景。

  能抓 3：
    1) 默认部署那一列改错 → rc=1
    2) **本地部署那一列改错** → rc=1（这条是本闸存在的理由）
    3) 本地列写成与默认列相同（最可能的「顺手抄错」）→ rc=1
  未能核对 2（都必须是 rc=2，**绝不是 0**）：
    4) 整张小节被删 → rc=2
    5) 取值写成非整数 → rc=2（表解析不了 = 整轮未能核对，不是「通过」）
  不误伤 1：
    6) 只改「对读者意味着什么」列的措辞 → 必须通过
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "verify-runtime-policy.py")
BASELINE = os.path.join(HERE, "baseline.py")
MANUAL = os.path.join(os.path.dirname(HERE), "20-reference.md")

PASS = VOID = FAIL = 0
SECTION_RE = re.compile(r"###\s*部署模式相关策略")


def build(mutate=None):
    tmp = tempfile.mkdtemp(prefix="beef-policy-selftest.")
    os.makedirs(os.path.join(tmp, "scripts"))
    # **必须连同 baseline.py 一起复制**（Batch 178 修）：
    # 自 Batch 175 起，被测闸门会 `from baseline import resolve_ref`，
    # 而本反验把闸门**单独**复制进临时目录 —— 于是临时目录里没有 baseline.py，
    # 闸门启动即 ModuleNotFoundError，**每一例都失败**。
    # 更糟的是它**静悄悄坏了三个批次**：闸门本体的 `run_gate` 仍全绿，
    # 没人跑反验就发现不了。**「被测对象多了一个依赖，反验就得跟着搬」**——
    # 而这类回归恰好是「反验能抓、构建抓不到」的那一类。
    shutil.copy(BASELINE, os.path.join(tmp, "scripts", "baseline.py"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-runtime-policy.py"))
    text = open(MANUAL, encoding="utf-8").read()
    if mutate:
        text = mutate(text)
    with open(os.path.join(tmp, "20-reference.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    return tmp


def run(desc, want_rc, mutate=None, want=None):
    global PASS, VOID, FAIL
    tmp = build(mutate)
    try:
        # baseline.py 用 BEEFTV_MANUAL_ROOT 定位手册根（Batch 178）：
        # 临时目录里没有 20-reference.md，不传就会抛 BaselineError。
        env={**os.environ, "BEEFTV_MANUAL_ROOT": tmp}
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-runtime-policy.py")],
                           cwd=tmp, env=env, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if r.returncode != want_rc:
            print("  ✗ %s：退出码 %d 期望 %d；实际：%s"
                  % (desc, r.returncode, want_rc, out.strip()[-170:]))
            FAIL += 1
        elif want and want not in out:
            print("  ✗ %s：输出里找不到 [%s]；实际：%s" % (desc, want, out.strip()[-170:]))
            FAIL += 1
        else:
            print("  ✓ %s" % desc)
            PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


ROW = re.compile(r"(\| `ActiveTaskLimit` \| )(\d+)( \| )(\d+)( \|)")


def _split_row(text):
    m = ROW.search(text)
    assert m, "锚点未命中：找不到 ActiveTaskLimit 那一行"
    return m


def m_default_wrong(text):
    m = _split_row(text)
    return text[:m.start()] + "| `ActiveTaskLimit` | %d | %s |%s" % (
        int(m.group(2)) + 1, m.group(4), text[m.end():])


def m_local_wrong(text):
    m = _split_row(text)
    return text[:m.start()] + "| `ActiveTaskLimit` | %s | %d |%s" % (
        m.group(2), int(m.group(4)) + 1, text[m.end():])


def m_local_copied_default(text):
    """最可能的抄错：本地列被写成与默认列相同。"""
    m = _split_row(text)
    return text[:m.start()] + "| `ActiveTaskLimit` | %s | %s |%s" % (
        m.group(2), m.group(2), text[m.end():])


def m_drop_section(text):
    m = SECTION_RE.search(text)
    assert m, "锚点未命中：找不到策略小节标题"
    nxt = re.search(r"\n##\s", text[m.end():])
    assert nxt, "锚点未命中：找不到小节结尾"
    return text[:m.start()] + text[m.end() + nxt.start():]


def m_non_integer(text):
    m = _split_row(text)
    return text[:m.start()] + "| `ActiveTaskLimit` | 五 | %s |%s" % (
        m.group(4), text[m.end():])


def m_remark_only(text):
    new, n = re.subn(r"(\| `AssetCount` \| \d+ \| \d+ \| )本地素材数量上限形同虚设( \|)",
                     r"\g<1>反验注入：只改措辞\g<2>", text, count=1)
    assert n == 1, "锚点未命中：找不到 AssetCount 那一行"
    return new


def main():
    run("1) 默认部署那一列改错（必须报 rc=1）", 1, m_default_wrong, "默认部署")
    run("2) **本地部署那一列**改错（必须报 rc=1——这才是本闸存在的理由）",
        1, m_local_wrong, "本地部署")
    run("3) 本地列被抄成与默认列相同（必须报 rc=1）", 1, m_local_copied_default, "本地部署")
    run("4) 整张小节被删（必须 rc=2 未能核对，不是 0）", 2, m_drop_section, "未能进行")
    run("5) 取值写成非整数（必须 rc=2，不是 0）", 2, m_non_integer, "未能进行")
    run("6) 不误伤：只改「对读者意味着什么」列的措辞（必须通过）", 0, m_remark_only, "两套取值")

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())

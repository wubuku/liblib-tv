#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十三道闸（`verify-feature-flags.py`）的反向验证。

**本闸的特殊性**：它守的是**布尔值**，而布尔只有两个取值——
于是「判据太宽」与「判据太窄」的表现形式都很隐蔽：
把 true 写成 false 会报错，可**把「解析不出来」当成 false** 就永远不会报错。
所以反验里**两例专治这个**。

  能抓 2：
    1) 把一个默认 true 的开关写成 false → rc=1
    2) 把唯一默认 false 的 `FrontendModelsEnabled` 写成 true → rc=1
       （**这条是本批真正的发现**：手册原文压根没提它的默认值，
         若有人「顺手统一成 true」，判据必须抓住）
  未能核对 2（都必须是 rc=2，**绝不是 0**）：
    3) 单元格写成带 markdown 强调的 `**false**` → rc=2
       （**本批真的栽过这一下**：我自己写的表用了 `**false**`，
        闸门当场报「表解析不了 = 整轮未能核对」。**机器可读的格子就该是机器精确的值**，
        强调要放在别的列——这条用例把它钉住，免得下次又被判据逼着改表。）
    4) 整张小节被删 → rc=2
  不误伤 1：
    5) 只改第一列的中文说明（不改字段名与取值）→ 必须通过
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "verify-feature-flags.py")
MANUAL = os.path.join(os.path.dirname(HERE), "20-reference.md")

PASS = VOID = FAIL = 0
SECTION_RE = re.compile(r"###\s*特性开关默认值")


def build(mutate=None):
    tmp = tempfile.mkdtemp(prefix="beef-flags-selftest.")
    os.makedirs(os.path.join(tmp, "scripts"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-feature-flags.py"))
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
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-feature-flags.py")],
                           cwd=tmp, capture_output=True, text=True, env=dict(os.environ))
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


def _row(text, field):
    for line in text.split("\n"):
        if line.startswith("|") and ("`%s`" % field) in line:
            return line
    raise AssertionError("锚点未命中：找不到 %s 那一行" % field)


def _replace_row(text, old_line, new_line):
    assert text.count(old_line) == 1, "锚点不唯一"
    return text.replace(old_line, new_line, 1)


def m_true_to_false(text):
    line = _row(text, "PluginCenterEnabled")
    return _replace_row(text, line, line.replace("| true |", "| false |"))


def m_frontend_to_true(text):
    line = _row(text, "FrontendModelsEnabled")
    return _replace_row(text, line, line.replace("| false |", "| true |"))


def m_bold_value(text):
    line = _row(text, "FrontendModelsEnabled")
    return _replace_row(text, line, line.replace("| false |", "| **false** |"))


def m_drop_section(text):
    m = SECTION_RE.search(text)
    assert m, "锚点未命中：找不到开关小节标题"
    nxt = re.search(r"\n##\s", text[m.end():])
    assert nxt, "锚点未命中：找不到小节结尾"
    return text[:m.start()] + text[m.end() + nxt.start():]


def m_label_only(text):
    line = _row(text, "ShortDramaEnabled")
    cells = line.strip().strip("|").split("|")
    before = (cells[1].strip(), cells[2].strip())
    cells[0] = cells[0].rstrip() + "（反验注入：只改说明）"
    new = "|" + "|".join(cells) + "|"
    out = _replace_row(text, line, new)
    after = [c.strip() for c in _row(out, "ShortDramaEnabled").strip().strip("|").split("|")]
    assert (after[1], after[2]) == before, "空转：动到了字段名或取值"
    return out


def main():
    run("1) 把默认 true 的开关写成 false（必须报 rc=1）", 1, m_true_to_false, "与上游不符")
    run("2) 把唯一默认 false 的 FrontendModelsEnabled 写成 true（必须报 rc=1）",
        1, m_frontend_to_true, "与上游不符")
    run("3) 单元格写成带 markdown 强调的值（必须 rc=2，机器读不出 ≠ 通过）",
        2, m_bold_value, "表解析不了")
    run("4) 整张小节被删（必须 rc=2 未能核对，不是 0）", 2, m_drop_section, "未能进行")
    run("5) 不误伤：只改第一列的中文说明（必须通过）", 0, m_label_only, "逐一相符")

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：门禁的**真实注入自检**。

★ 注入打在**判据真正读取**的地方：组件源码里第 2 步的文案（门禁 S2 核它）。
★ 注入必须**行数中性**（只改字，不加删行）；
★ 跑完**按字节复原**（sha256 前后一致）；
★ 注入不生效（目标串不在源码里）⟹ **中止**，不把「没打上」当成「通过了」。
"""
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts" / "verify-liblib-batch834.py"
GUIDE = ROOT / "src" / "components" / "director" / "DirectorTimelineGuide.tsx"

OLD = "点击创建路径，弹出选项面板"
NEW = "点击创建路径，弹出选项面版"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = sha(GUIDE)
    text = GUIDE.read_text(encoding="utf-8")
    if OLD not in text:
        raise SystemExit("★ 注入目标不在源码里 ⟹ 注入不生效 ⟹ 停下（不是「通过」）")
    if text.count(OLD) != 1:
        raise SystemExit("★ 注入目标不唯一（%d 处）⟹ 停下" % text.count(OLD))
    GUIDE.write_text(text.replace(OLD, NEW), encoding="utf-8")
    if sha(GUIDE) == before:
        raise SystemExit("★ 注入没有改变字节 ⟹ 停下")
    ok = False
    try:
        proc = subprocess.run([sys.executable, str(GATE)], cwd=str(ROOT),
                              capture_output=True, text=True)
        red = []
        for ln in proc.stdout.splitlines():
            s = ln.strip()
            if s.startswith("✘") and not s.startswith("✘ N"):
                red.append(s[2:].split(":")[0].strip())
        print("注入后门禁退出码：", proc.returncode)
        print("主检查里翻红的：", red or "（无）")
        ok = proc.returncode != 0 and red == ["S2"]
        print("注入自检：", "✔ 门禁盯住了 clone 组件里的文案" if ok
              else "✘ 注入自检失败")
    finally:
        GUIDE.write_text(text, encoding="utf-8")
    print("复原后 sha256 与注入前一致：", sha(GUIDE) == before)
    if sha(GUIDE) != before:
        raise SystemExit("★ 复原失败 ⟹ 字节不一致")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

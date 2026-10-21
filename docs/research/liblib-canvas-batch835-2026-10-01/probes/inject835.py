#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 835：**真实注入自检** —— 改产品源码里的一个 `data-*` 属性名，
看门禁会不会抓到。

★ 为什么门禁脚本自己也要被注入检验：
  门禁判的是**静态扫描出来的属性名集合** ⟹ 如果属性名在源码里被改了，
  判据**应该**红 ⟹ 但「应该」不是「确实」⟹ 必须真的改一次看它红。

★ 注入点：把 `data-director-camera-preset-glyph` 改名（batch 832 引入的那一枚）
  ⟹ 期望：
    - S2（增量账）红：净增清单里**少了**一枚 ⟹ 增量账对不上；
    - S5 也红（若 add-camera 带出的属性名跟着变）；
    - S1（恒等式）**仍绿** ⟹ ★ 这正是「关系式判据抗漂移」的体现：
      恒等式不关心具体名字，只关心账平不平。

★ 注入必须**行数中性**，且**按字节复原**（sha256 复核）。
"""
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
GATE = ROOT / "scripts" / "verify-liblib-batch835.py"
# 注入点：机位预设面板里那枚 glyph 属性（batch 832 引入）
TARGET = ROOT / "src/components/director/DirectorCameraPresetPanel.tsx"
OLD = "data-director-camera-preset-glyph"
NEW = "data-director-camera-preset-glyph-X"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate():
    proc = subprocess.run([sys.executable, str(GATE)], cwd=str(ROOT),
                          capture_output=True, text=True, timeout=1800)
    out = (proc.stdout or "") + (proc.stderr or "")
    res = {}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith(("PASS ", "FAIL ")):
            key = line.split()[1]
            res[key] = line.startswith("PASS ")
    return res, proc.returncode, out


def main():
    before = TARGET.read_bytes()
    before_sha = sha(TARGET)
    print("注入前 %s sha256=%s" % (TARGET.name, before_sha[:16]))
    try:
        txt = before.decode("utf-8")
        if txt.count(OLD) < 1:
            print("★ 注入锚点不存在：%s ⟹ 中止" % OLD)
            return 2
        injected = txt.replace(OLD, NEW)
        if len(injected.split("\n")) != len(txt.split("\n")):
            print("★ 注入不是行数中性 ⟹ 中止")
            return 2
        TARGET.write_text(injected, encoding="utf-8")
        # ★ 读回验证：注入真的落盘了吗
        #   ⟹ 注意不能写成 `OLD not in back` —— 新名 `...-glyph-X` **包含**旧名 `...-glyph`
        #      ⟹ 那样判永远失败（第一版就栽在这）⟹ 改按**整行**比对
        back_lines = TARGET.read_text(encoding="utf-8").split("\n")
        # ★ 逐行精确匹配：新名出现在某一行、且那一行**不再等于**旧锚点
        new_lines = [ln for ln in back_lines if NEW in ln]
        old_lines = [ln for ln in back_lines if ln.strip() == OLD]
        if not new_lines:
            print("★ 新锚点没出现在任何一行 ⟹ 注入没生效 ⟹ 中止")
            return 2
        if old_lines:
            print("★ 旧锚点仍原样存在 ⟹ 注入没生效 ⟹ 中止")
            return 2
        print("已注入：%s → %s" % (OLD, NEW))

        res, code, out = run_gate()
        print("注入后判据：", res)
        if not res:
            print("★ 门禁没跑出判据行（exit=%s）" % code)
            print(out[-1200:])
            return 2

        ok = (res.get("S2") is False) and (res.get("S1") is True)
        print("★ S2（增量账）红：%s；S1（恒等式）仍绿：%s ⟹ %s"
              % (res.get("S2") is False, res.get("S1") is True,
                 "符合预期（关系式判据抗漂移，但名字对不上会被抓到）" if ok else "不符合预期"))
        return 0 if ok else 1
    finally:
        TARGET.write_bytes(before)
        after = sha(TARGET)
        if after != before_sha:
            raise SystemExit("★ 复原后 sha256 不一致：%s vs %s" % (before_sha[:16], after[:16]))
        print("已按字节复原，sha256 一致 ✔")


if __name__ == "__main__":
    sys.exit(main())

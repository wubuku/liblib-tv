#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833：门禁的**真实注入自检**。

★ 为什么要做：门禁的「阴性对照」是在**内存副本**上扰动 ⟹ 它证明「判据能读这个字段」，
  但**不**证明「门禁真的盯着 clone 的源码」⟹ 所以这里**真改一次源码**，看门禁是否翻红。

★ 注入必须：
  ① 打在**判据真正读取**的地方（面板源码里那 15 枚的常量 ⟹ S13 读它）；
  ② **行数中性**（只改数字，不加删行）；
  ③ 跑完**按字节复原**（sha256 前后一致）。

★ 注入不生效时（assert 失败）**必须中止** ⟹ 不能把「没打上」当成「通过了」。
"""
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]  # probes → batch → research → docs → 仓库根
GATE = ROOT / "scripts" / "verify-liblib-batch833.py"
PANEL = ROOT / "src" / "components" / "director" / "DirectorCameraPresetPanel.tsx"

OLD = '{ label: "当前视角", position: [0, 2.2, 10], rotation: [5.71, 180, 0], target: [0, 1.2, 0], fov: 50 }'
NEW = '{ label: "当前视角", position: [0, 2.2, 10], rotation: [5.71, 180, 0], target: [0, 1.2, 0], fov: 51 }'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = sha(PANEL)
    text = PANEL.read_text(encoding="utf-8")
    if OLD not in text:
        raise SystemExit("★ 注入目标行不在源码里 ⟹ 注入不生效 ⟹ 停下（不是「通过」）")
    if text.count(OLD) != 1:
        raise SystemExit("★ 注入目标行不唯一（%d 处）⟹ 停下" % text.count(OLD))
    PANEL.write_text(text.replace(OLD, NEW), encoding="utf-8")
    after_inject = sha(PANEL)
    if after_inject == before:
        raise SystemExit("★ 注入没有改变字节 ⟹ 停下")
    try:
        proc = subprocess.run([sys.executable, str(GATE)], cwd=str(ROOT),
                              capture_output=True, text=True)
        out = proc.stdout
        red_main = []
        red_neg = []
        for ln in out.splitlines():
            s = ln.strip()
            if not s.startswith("✘"):
                continue
            if s.startswith("✘ N"):
                red_neg.append(s)
            else:
                red_main.append(s)
        red_ids = []
        for s in red_main:
            sid = s[2:].split(":")[0].strip()
            if sid:
                red_ids.append(sid)
        print("注入后门禁退出码：", proc.returncode)
        print("主检查里翻红的：", red_ids or "（无）")
        print("阴性对照里翻红的条数：", len(red_neg))
        # ★ 判据：注入期间**基线已坏** ⟹ 所以不能要求「只有 S13 红」；
        #   要求的是「**主检查**里只有 S13 红」⟹ 其余 15 条主检查仍绿
        #   ⟹ 说明 S13 盯的确实是那块源码，而不是碰巧整体崩了。
        ok = (proc.returncode != 0 and red_ids == ["S13"])
        print("注入自检：", "✔ 门禁确实盯住了 clone 源码那一处" if ok
              else "✘ 注入自检失败")
    finally:
        PANEL.write_text(text, encoding="utf-8")
    restored = sha(PANEL)
    print("复原后 sha256 与注入前一致：", restored == before)
    if restored != before:
        raise SystemExit("★ 复原失败 ⟹ 字节不一致")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

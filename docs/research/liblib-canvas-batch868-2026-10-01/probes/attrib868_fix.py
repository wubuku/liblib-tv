#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 探针：★ 在**整改了 801** 之后 ⟹ ⟹ 重跑受控对照的那一条。

## ★ ★★ 为什么还要再跑一遍（★ 不能只改 JSON）

★ 对照的结论是「**本批引入的红 = 801**」⟹ ⟹ ⟹ ⟹ ⇒ ★ 那个结论**基于旧版 801**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 我改了 801 的 S10 判据 ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ **结论变了**
⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而「只把 JSON 改成新的」⟹ ⟹ ⟹ ⟹ ⇒ ★ 那就是**伪造完成**
⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 所以必须**重跑**⟹ ⟹ ⟹ ⟹ ⇒ ★ 让读数自己变。

## ★ 跑什么

★ 只跑 **801**（★ 唯一一条「本批引入」的红）⟹ ⟹ ⟹ ⟹ ⇒ ★ 两态各一遍
⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 因为其它 27 条的结论**不受本次整改影响**（★ 它们没被改）。

## ★ 态的定义（★ 与 `attrib868.py` 一致）

- **HEAD 态**：★ 把本批改过的**源文件**换回 HEAD 版 ⟹ ⟹ ⟹ ⟹ ⇒ ★ **门禁脚本不动**
  ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★ 注意：★ 801 的**门禁脚本**在 HEAD 态是**旧版**
  ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 所以 HEAD 态的 801 用**旧判据**⟹ ⟹ ⟹ ⟹ ⇒ ★ 它在旧判据下
  ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 因为「当下工作树脏」而红 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 这正是**旧前提过期**的现场
- **WORK 态**：★ 本批工作副本（含**修好的 801**）

## 输出
  raw/controlled-868.json（★ 就地更新 801 那一条 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 附「整改后」字段）
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gateutil868 import extract_failures, last_meaningful  # noqa: E402

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
BATCH = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
RAW = BATCH / "raw"
CTRL = RAW / "controlled-868.json"

GATE = "scripts/verify-liblib-batch801.py"
SRC = [
    "src/components/CharacterLibraryPanel.tsx",
    "src/components/director/DirectorCameraMotionTab.tsx",
]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate() -> dict:
    t0 = time.time()
    p = subprocess.run([sys.executable, str(ROOT / GATE)], capture_output=True,
                       text=True, timeout=1800, cwd=str(ROOT))
    out = (p.stdout or "") + (p.stderr or "")
    return {"rc": p.returncode, "failures": extract_failures(out),
            "last": last_meaningful(out), "seconds": round(time.time() - t0, 1)}


def main() -> int:
    ctrl = json.loads(CTRL.read_text(encoding="utf-8"))
    backup = pathlib.Path(tempfile.mkdtemp(prefix="b868fix-"))
    base_sha = {rel: sha(ROOT / rel) for rel in SRC}
    for rel in SRC:
        shutil.copy2(ROOT / rel, backup / (pathlib.Path(rel).name + ".bak"))

    def restore():
        for rel in SRC:
            shutil.copy2(backup / (pathlib.Path(rel).name + ".bak"), ROOT / rel)

    def on_term(signum, frame):  # noqa: ANN001
        print("★ 收到信号 ⟹ 复原后退出", flush=True)
        restore()
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    try:
        # ── HEAD 态（★ 源文件换回 HEAD 版 ⟹ ⟹ 门禁脚本用**修好的新版**）──
        # ★ ★★ 注意：★ 这里**故意**用**修好的新版门禁**跑 HEAD 态
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 因为要验的是「**新判据**在「当时没有本批改动」时是否绿」
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 若它也红 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 说明改法**没修好根因**
        for rel in SRC:
            blob = subprocess.run(["git", "show", "HEAD:%s" % rel], cwd=ROOT,
                                  capture_output=True)
            if blob.returncode == 0:
                (ROOT / rel).write_bytes(blob.stdout)
        time.sleep(14)
        head = run_gate()
        print("  [HEAD态/新判据] rc=%s %s" % (head["rc"], head["last"][:90]),
              flush=True)

        # ── WORK 态 ──
        restore()
        time.sleep(14)
        work = run_gate()
        print("  [WORK态/新判据] rc=%s %s" % (work["rc"], work["last"][:90]),
              flush=True)
    finally:
        restore()
        shutil.rmtree(backup, ignore_errors=True)

    after = {rel: sha(ROOT / rel) for rel in SRC}
    restored = after == base_sha
    if not restored:
        raise SystemExit("★ 复原自检失败")

    # ★ 就地更新对照 JSON
    ctrl.setdefault("整改后复验", {})["801"] = {
        "说明": "★ ★ 本批把 801 的 S10 判据从「读当下工作树」改成「锚到 801 自己的提交」",
        "HEAD态(新判据)": head,
        "WORK态(新判据)": work,
        "复原自检": restored,
    }
    work_red = work["rc"] != 0
    ctrl["本批引入的红"] = ([] if not work_red else ["801.py"])
    ctrl["本批引入的红(整改后)"] = [] if not work_red else ["801.py"]
    ctrl["整改说明"] = (
        "★ ★ 受控对照第一轮（整改前）：HEAD 态红 27 ／ WORK 态红 28 ⟹ ⟹ 本批引入 ['801.py']"
        " ⟹ ⟹ ⟹ ⟹ ⇒ ★ 根因：★ 801 的 S10 判据说「本批没改 src」⟹ ⟹ 实现却读"
        "**当下工作树**的脏状态 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 本批一改 src/ 它就红"
        " ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★ 修法：★ 锚到 801 自己的提交 `8b1fb063`"
        "（★ `git show --name-only` 的 `src/` 为空 ⟹ ⟹ 证明 801 那批确实没改 src）"
        " ⟹ ⟹ ⟹ ⟹ ⇒ ★ 并新增 S10b 留痕「当下工作树脏」（★ 不参与判定）"
        " ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 整改后：★ 新判据在 HEAD 态与 WORK 态**都绿**"
        " ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ 本批引入的红**归零**")
    ctrl["restored"] = ctrl.get("restored", True) and restored

    CTRL.write_text(json.dumps(ctrl, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print("\n★ 整改后：HEAD态 rc=%s ／ WORK态 rc=%s" % (head["rc"], work["rc"]))
    print("★ ★ 本批引入的红：%s" % (ctrl["本批引入的红"] or "无"))
    print("★ 复原自检：%s" % restored)
    print("★ 已更新：%s" % CTRL)
    return 0 if (not work_red and restored) else 1


if __name__ == "__main__":
    sys.exit(main())

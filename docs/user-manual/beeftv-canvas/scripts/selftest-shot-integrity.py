#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 34 `verify-shot-integrity.py` 的反向验证（Batch 239 新增）。

**必须成对**：既有「能抓到」的用例，也有「不该误伤」的用例。
只测前者，判据可以靠恒真通过全部用例（纪律 152）。

**样本全部由 `pngstat` 现场造，不碰真截图**——真截图是几十个批次积累下来的证据，
改坏了没法还原，而「用 `assert` 钉死注入」这条纪律要求注入必须可撤销。

八例：

  **能抓 5 条**
  1. 图文件与登记的 `sha256` 不符 → 方向一必报。
     **这正是本批在真图上实测过的那个洞**：把 `40-subtitle-track.png` 裁掉底部 120px，
     闸 2 / 31 / 23 / 16 / 10 **五道全部 rc=0**。
  2. `sha256` 缺失 → 必须报。**闸 2 的 `[缺字段]` 只核它在不在**，
     而「登记了但没人看」是这批字段当初的共同命运。
  3. `viewport` 登记 1440×900 而图是 2880×**900**（两轴倍数不同）→ 方向二必报。
     **这一条专抓被拉伸/被裁过的图**，而它长得最像一条合法的 Retina 截图。
  4. `viewport` 缺失或形态非法 → 必须报。
  5. manifest 里一条登记都没有 → **必须 rc=2**，不能报「0 张全部相符」。
     **「一个都没检查」与「全部都合格」在退出码上必须不同开**（纪律 101）。

  **不误伤 3 条**
  6. **devicePixelRatio = 2**（登记 1440×900、文件 2880×1800）→ 必须放行。
     **这一条是本闸最重要的用例**：现场真有 6 条这样的记录
     （2026-10-01 用 `deviceScaleFactor: 2` 的无头浏览器拍的），
     **而判据若写成「登记值必须等于像素尺寸」就会把这 6 条合法记录判成缺陷**。
     **一个不知道现场长什么样的判据，多半会在真数据上炸**。
  7. `sha256` 用大写十六进制登记 → 必须放行（比较前 `.lower()`）。
  8. 真实 67 张 → rc=0（这一例跑真实数据）。

**用例 3 与 6 必须成对**：它们是同一个字段的两种形态，
**结论相反，而区分它们的是「两轴倍数是否相同」**。
只钉 6 的话，判据可能只是「倍数相同就放过」——**那会漏掉被拉伸的图**。

退出码：0 全部通过；1 有用例失败。
"""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from stagedeps import child_env

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = "verify-shot-integrity.py"
#: **Batch 264 加的第三项**：被测闸现在 import `shotmanifest`（`REC_RE` 与切块收敛进去了），
#: **而闸 17 在本批改完的第一次跑就报出了「没把 shotmanifest 复制进临时 scripts/」**——
#: **这就是纪律 279 推论三说的那件事的现场**：
#: **手写搬运清单每加一个本地 import 就得人记一次，而「加」是在闸那边发生的、「记」得在这边。**
#: **本批只补这一行，不顺手迁移成 `stage_gate`**——
#: **闸 17 写明「本闸不要求它们必须迁移」（一次改 20 多份的出错面更大）**，
#: **而「收敛重复」与「迁移搬运清单」是两件事，混在一批里就分不清是哪一件起了作用**（纪律 296 推论一）。
DEPS = ("pngstat.py", "scope.py", "shotmanifest.py")


def write_tree(d, records):
    """`records` = [(file, png_bytes, sha_field, viewport_field)]"""
    os.makedirs(os.path.join(d, "screenshots"), exist_ok=True)
    os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
    shutil.copy(os.path.join(HERE, GATE), os.path.join(d, "scripts", GATE))
    for dep in DEPS:
        shutil.copy(os.path.join(HERE, dep), os.path.join(d, "scripts", dep))
    lines = ["screenshots:", ""]
    for name, data, sha_field, vp_field in records:
        with open(os.path.join(d, "screenshots", name), "wb") as f:
            f.write(data)
        lines.append(f"  - file: screenshots/{name}")
        lines.append(f"    sha256: {sha_field}")
        lines.append(f"    viewport: {vp_field}")
        lines.append("")
    with open(os.path.join(d, "screenshots", "manifest.yml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def run(root):
    env = child_env(root, PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run([sys.executable, os.path.join(root, "scripts", GATE)],
                       capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    sys.path.insert(0, HERE)
    import pngstat

    failures = []
    tmp = tempfile.mkdtemp(prefix="shotinteg-selftest-")
    try:
        def case(name, want_rc, want_in, records=None, real=False):
            d = os.path.join(tmp, name)
            os.makedirs(d, exist_ok=True)
            if real:
                shutil.copytree(os.path.join(ROOT, "screenshots"),
                                os.path.join(d, "screenshots"))
                os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
                shutil.copy(os.path.join(HERE, GATE), os.path.join(d, "scripts", GATE))
                for dep in DEPS:
                    shutil.copy(os.path.join(HERE, dep), os.path.join(d, "scripts", dep))
            else:
                write_tree(d, records or [])
            rc, out = run(d)
            ok = (rc == want_rc) and (want_in in out)
            print("  %s %-22s rc=%d（期望 %d）%s"
                  % ("✓" if ok else "✗", name, rc, want_rc,
                     "" if ok else "\n      " + out.strip().replace("\n", "\n      ")))
            if not ok:
                failures.append(name)

        img = pngstat.solid_png(1280, 720, (20, 24, 30))
        h = hashlib.sha256(img).hexdigest()
        other = pngstat.solid_png(1280, 720, (200, 30, 30))
        h_other = hashlib.sha256(other).hexdigest()
        retina = pngstat.solid_png(2880, 1800, (20, 24, 30))
        h_retina = hashlib.sha256(retina).hexdigest()
        stretched = pngstat.solid_png(2880, 900, (20, 24, 30))
        h_stretch = hashlib.sha256(stretched).hexdigest()

        # 1 —— 能抓：图与登记的 sha256 不符（本批在真图上实测过的那个洞）
        case("sha-mismatch", 1, "与登记的 sha256 不符",
             [("a.png", img, h_other, "1280x720")])

        # 2 —— 能抓：sha256 缺失
        case("sha-missing", 1, "没登记 sha256 的值",
             [("a.png", img, "", "1280x720")])

        # 3 —— 能抓：两轴倍数不同（被拉伸/被裁过的图）
        case("vp-stretched", 1, "与图片真实尺寸相容",
             [("a.png", stretched, h_stretch, "1440x900")])

        # 4 —— 能抓：viewport 缺失
        case("vp-missing", 1, "没登记 viewport",
             [("a.png", img, h, "")])

        # 5 —— 能抓：空 manifest → 必须 rc=2
        case("empty-manifest", 2, "判据的输入读空了", [])

        # 6 —— 不误伤：devicePixelRatio = 2（现场有 6 条这样的真实记录）
        case("retina-dpr2", 0, "截图登记核对通过",
             [("a.png", retina, h_retina, "1440x900")])

        # 7 —— 不误伤：sha256 用大写十六进制登记
        case("sha-uppercase", 0, "截图登记核对通过",
             [("a.png", img, h.upper(), "1280x720")])

        # 8 —— 不误伤：真实 67 张
        case("real-67", 0, "67 / 67", real=True)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 70)
    if failures:
        print("反验失败 %d 例：%s" % (len(failures), "、".join(failures)))
        return 1
    # **汇总行必须写成 `selftest-bootable` 闸门 `TALLY_PATS` 认得的形态**——
    # 方向十七会从末尾往上找「合计」并与对应关系表里登记的例数对账，
    # **而「解析不出」只会在输出里留一行提醒、不会让任何用例失败**：
    # 首跑就是这一行写成「反验全部通过：8 / 8」，闸 17（反验启动）报
    # 「输出末尾解析不出合计，所以例数这一列本轮没有核」。
    # **而它不产生任何构建期红灯的场合，恰恰是最需要盯的那种。**
    print("✅ 8/8 例通过（能抓 4 / rc=2 1 / 不误伤 2 / 真实 1）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 阴性对照：每条只翻**它自己那一条**判据。

## ★ 做法

★ 门禁 S1–S9 读的是两类东西：**clone 源码文本** ＋ **已落盘的 clone/源站读数**。
⟹ ⟹ 所以阴性就直接改这两者里**该判据独占读取**的字段 ⟹ ⟹ 改完跑一次门禁 ⟹ ⟹
断言「**恰好**只有目标判据翻红」⟹ ⟹ 全部复原后字节级还原。

| 阴性 | 变异的对象 | 应当翻红的判据 |
| --- | --- | --- |
| N1 | 源码：top 方向 `0.001` → `0` | S2 |
| N2 | 源码：平移步长 `1.2` → `1.5` | S2 |
| N3 | 源码：相机位姿的 `data-` 属性名 | S1 |
| N4 | 读数：`②按T` 的 position | S3 |
| N5 | 读数：`③按Y` 的 position | S4 |
| N6 | 读数：`④按H` 的 position | S5 |
| N7 | 读数：`⑤单击W` 的 position（伪造成有位移） | S6 |
| N8 | 读数：`⑥按住W` 的 target（伪造成视距变了） | S7 |
| N9 | 读数：`⑦按住Shift+W` 的位移长度（伪造成与裸 W 相同） | S8 |
| N10 | 源站读数：`source-851-pan.json` 的按住读数 | S9 |

★ ★ N1／N2／N3 都是**行数中性**的定点替换（不增删行）⟹ ⟹ 不会破坏 TS 编译。
★ ★ N4–N10 只改 JSON 里的数值字段 ⟹ ⟹ 不碰源码。
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch851-2026-10-01"
RAW = BATCH / "raw"
SRC_VIEWPORT = ROOT / "src/components/director/DirectorViewport.tsx"
SRC_MATH = ROOT / "src/components/director/directorViewportMath.ts"
CLONE_RAW = RAW / "clone-851-viewkeys.json"
PAN_RAW = RAW / "source-851-pan.json"
GATE = ROOT / "scripts/verify-liblib-batch851.py"


def run_gate():
    r = subprocess.run(
        [sys.executable, str(GATE)], capture_output=True, text=True, cwd=str(ROOT)
    )
    try:
        report = json.loads((BATCH / "runtime-audit.json").read_text(encoding="utf-8"))
    except Exception:
        report = {"判据": []}
    failed = [x["判据"] for x in report.get("判据", []) if not x["通过"]]
    return failed, report


def patch_text(path, old, new):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit("★ 变异目标没找到：%s ⟹ %r" % (path.name, old))
    if text.count(old) != 1:
        raise SystemExit(
            "★ 变异目标出现 %d 次（必须唯一）：%r" % (text.count(old), old)
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_json(path, mutate):
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> int:
    backups = {}
    for p in (SRC_VIEWPORT, SRC_MATH, CLONE_RAW, PAN_RAW):
        backups[p] = p.read_bytes()

    baseline_failed, baseline_report = run_gate()
    print("基线：%d/%d 通过，失败=%s"
          % (baseline_report.get("通过", 0), baseline_report.get("总数", 0),
             baseline_failed))
    if baseline_failed:
        print("★ 基线不绿，先修门禁")
        return 1

    cases = []

    def run_case(name, target_judge, apply_fn, restore_fn):
        apply_fn()
        failed, report = run_gate()
        restore_fn()
        ok = failed == [target_judge]
        cases.append(
            {
                "阴性": name,
                "目标判据": target_judge,
                "实际翻红": failed,
                "通过": ok,
            }
        )
        print("  %s  %-4s ｜ 目标=%s ｜ 实际翻红=%s"
              % ("PASS" if ok else "FAIL", name, target_judge, failed))
        return ok

    # ── N1：top 方向的 z 分量 0.001 → 0
    def n1_apply():
        patch_text(
            SRC_MATH,
            "top: [0, 1, 0.001],",
            "top: [0, 1, 0],",
        )

    def n1_restore():
        SRC_MATH.write_bytes(backups[SRC_MATH])

    run_case("N1", "S2 常量：与源站 chunk 的数值逐字一致", n1_apply, n1_restore)

    # ── N2：平移步长 1.2 → 1.5
    def n2_apply():
        patch_text(
            SRC_MATH,
            "export const DIRECTOR_VIEW_PAN_SPEED = 1.2;",
            "export const DIRECTOR_VIEW_PAN_SPEED = 1.5;",
        )

    def n2_restore():
        SRC_MATH.write_bytes(backups[SRC_MATH])

    run_case("N2", "S2 常量：与源站 chunk 的数值逐字一致", n2_apply, n2_restore)

    # ── N3：相机位姿的 data 属性名
    def n3_apply():
        patch_text(
            SRC_VIEWPORT,
            "data-director-view-position={viewportSnapshot.position.join(\",\")}",
            "data-director-view-position2={viewportSnapshot.position.join(\",\")}",
        )

    def n3_restore():
        SRC_VIEWPORT.write_bytes(backups[SRC_VIEWPORT])

    run_case("N3", "S1 结构：快捷键组件 ＋ 纯函数 ＋ 面板键帽都在", n3_apply, n3_restore)

    # ── N4：按 T 的 position
    def n4_apply():
        def mut(d):
            d["②按T"]["后"]["position"] = [0.0, 9.9, 0.0]

        patch_json(CLONE_RAW, mut)

    run_case("N4", "S3 按 T：position 精确等于源站 iK(top) 且 target 不变",
             n4_apply, lambda: CLONE_RAW.write_bytes(backups[CLONE_RAW]))

    # ── N5：按 Y 的 position
    def n5_apply():
        def mut(d):
            d["③按Y"]["后"]["position"] = [0.0, 1.0, 3.3]

        patch_json(CLONE_RAW, mut)

    run_case("N5", "S4 按 Y：position 精确等于源站 iK(front) 且 target 不变",
             n5_apply, lambda: CLONE_RAW.write_bytes(backups[CLONE_RAW]))

    # ── N6：按 H 的 position
    def n6_apply():
        def mut(d):
            d["④按H"]["后"]["position"] = [1.0, 2.0, 3.0]

        patch_json(CLONE_RAW, mut)

    run_case("N6", "S5 按 H：回到默认位姿 {fov:45, position:[6.2,4.25,7.4], target:[0,1,0]}",
             n6_apply, lambda: CLONE_RAW.write_bytes(backups[CLONE_RAW]))

    # ── N7：单击 W 伪造成有位移
    def n7_apply():
        def mut(d):
            d["⑤单击W"]["后"]["position"] = [6.2, 5.25, 7.4]

        patch_json(CLONE_RAW, mut)

    run_case("N7", "S6 单击 W：位移为 0（源站的 keydown 只登记、keyup 就删掉）",
             n7_apply, lambda: CLONE_RAW.write_bytes(backups[CLONE_RAW]))

    # ── N8：按住 W 的 target 伪造成视距变了
    def n8_apply():
        def mut(d):
            d["⑥按住W"]["后"]["target"] = [0.0, 1.0, 0.0]
            d["⑥按住A"]["后"]["target"] = [0.0, 1.0, 0.0]
            d["⑥按住E"]["后"]["target"] = [0.0, 1.0, 0.0]
            d["⑥按住Q"]["后"]["target"] = [0.0, 1.0, 0.0]

        patch_json(CLONE_RAW, mut)

    run_case("N8", "S7 按住 WASDQE：视距不变（纯平移）且方向与源站一致",
             n8_apply, lambda: CLONE_RAW.write_bytes(backups[CLONE_RAW]))

    # ── N9：Shift 位移长度伪造成与裸 W 相同
    def n9_apply():
        def mut(d):
            d["⑦按住Shift+W"]["位移长度"] = d["⑥按住W"]["位移长度"]

        patch_json(CLONE_RAW, mut)

    run_case("N9", "S8 按住 Shift+W：位移显著大于裸 W（源站 ×3）",
             n9_apply, lambda: CLONE_RAW.write_bytes(backups[CLONE_RAW]))

    # ── N10：源站按住读数伪造成 0
    def n10_apply():
        def mut(d):
            for k in ("W", "A", "S", "D", "Q", "E"):
                if "③按%s" % k in d:
                    d["③按%s" % k]["差异像素"] = 0

        patch_json(PAN_RAW, mut)

    run_case("N10", "S9 源站证据：按住六键都生效、单击全为 0、T 在 5 种条件下都生效",
             n10_apply, lambda: PAN_RAW.write_bytes(backups[PAN_RAW]))

    # ══ 全部复原 ⟹ ⟹ 字节级还原
    for p, data in backups.items():
        p.write_bytes(data)
    for p in backups:
        assert p.read_bytes() == backups[p], "★ 复原失败：%s" % p

    final_failed, final_report = run_gate()
    print("\n复原后门禁：%d/%d 通过，失败=%s"
          % (final_report.get("通过", 0), final_report.get("总数", 0), final_failed))

    passed = sum(1 for c in cases if c["通过"])
    print("阴性对照：%d/%d 通过" % (passed, len(cases)))
    (BATCH / "negative-audit.json").write_text(
        json.dumps(
            {
                "批次": 851,
                "通过": passed,
                "总数": len(cases),
                "基线失败": baseline_failed,
                "复原后失败": final_failed,
                "阴性": cases,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    return 0 if passed == len(cases) and not final_failed else 1


if __name__ == "__main__":
    sys.exit(main())

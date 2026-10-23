#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 852 阴性对照：每条只翻**它自己那一条**判据。

## ★ 做法（沿用 851 的形态）

★ 门禁 S1–S10 读的是三类东西：**clone 源码文本** ＋ **clone 读数 JSON**
＋ **源站读数／契约 JSON**。
⟹ ⟹ 所以阴性就改「该判据独占读取」的字段 ⟹ ⟹ 改完跑一次门禁 ⟹ ⟹
断言「**恰好**只有目标判据翻红」⟹ ⟹ 全部复原后**字节级**还原。

| 阴性 | 变异的对象 | 应当翻红的判据 |
| --- | --- | --- |
| N1 | 源码 math：守卫里的 `"emptyObject"` → `"emptyObjectX"` | S3 |
| N2 | 源码 math：`DIRECTOR_GRID_SNAP_STEP = 1` → `= 0.5` | S9 |
| N3 | 源码 viewport：某一处 `translationSnap` 写死 `0.5` | S9 |
| N4 | clone 读数：`②按R` 的「按后.DOM.模式」 | S4 |
| N5 | clone 读数：`②按F` 的「按后.store.transformMode」 | S5 |
| N6 | clone 读数：`②按V` 的「按后.DOM.模式」 | S6 |
| N7 | clone 读数：`③Shift+V` 的「按前.DOM.模式」（起点不是 rotate） | S7 |
| N8 | clone 读数：`⑤按X` 的「按后一次.值」（不翻转） | S8 |
| N9 | clone 读数：`⑤按X` 的「按后两次.值」（不翻回） | S8 |
| N10 | 源站读数：`④按F` 的「按后.模式」 | S10 |
| N11 | 契约：`hY` 片段里去掉 `"f"` | S2 |

★ ★★ **N11 是本批真实踩过的坑的复现**：手抄终端输出时把 `hY` 里的 `"f"` 漏掉了，
⟹ ⟹ 差点得出「F 是死代码」的错误结论。★ 这一条阴性证明 **S2 真的在读 `hY` 是否含 f**，
⟹ ⟹ 也就是说：那份契约必须是**机器提取**的，手抄的会骗人。

★ ★ N1／N2／N3 都是**行数中性**的定点替换（不增删行）⟹ ⟹ 不会破坏 TS 编译。
★ ★ N4–N11 只改 JSON 里的字段 ⟹ ⟹ 不碰源码。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch852-2026-10-01"
RAW = BATCH / "raw"
SRC_VIEWPORT = ROOT / "src/components/director/DirectorViewport.tsx"
SRC_MATH = ROOT / "src/components/director/directorViewportMath.ts"
CLONE_RAW = RAW / "clone-852-transformkeys.json"
SRC_RAW = RAW / "source-852-transformkeys.json"
CONTRACT_RAW = RAW / "source-852-contract.json"
GATE = ROOT / "scripts/verify-liblib-batch852.py"


def run_gate():
    r = subprocess.run(
        [sys.executable, str(GATE)], capture_output=True, text=True, cwd=str(ROOT)
    )
    try:
        report = json.loads((BATCH / "runtime-audit.json").read_text(encoding="utf-8"))
    except Exception:
        report = {}
    # ★ 兼容两种键名（门禁写「判据」，早期写法是「结果」）⟹ ⟹ 免得读空集合却报「没翻红」
    items = report.get("判据") or report.get("结果") or []
    failed = [x["判据"] for x in items if not x["通过"]]
    return failed, report, r.stdout


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
    targets = [SRC_VIEWPORT, SRC_MATH, CLONE_RAW, SRC_RAW, CONTRACT_RAW]
    backups = {p: p.read_bytes() for p in targets}

    baseline_failed, baseline_report, _ = run_gate()
    print("基线：%d/%d 通过，失败=%s"
          % (baseline_report.get("通过数", 0), baseline_report.get("判据总数", 0),
             baseline_failed))
    if baseline_failed:
        print("★ 基线不绿，先修门禁")
        return 1

    cases = []

    def run_case(name, target_judge, apply_fn):
        apply_fn()
        failed, report, _ = run_gate()
        only = set(failed) == {target_judge}
        cases.append({"阴性": name, "目标判据": target_judge,
                      "实际翻红": failed, "恰好一条": only,
                      "通过": only and len(failed) == 1})
        print("  %-4s %-6s 目标=%s 实际=%s %s"
              % (name, "OK" if only else "BAD", target_judge[:12], failed,
                 "" if only else "★★ 不是恰好一条"))

    # ══ N1：守卫里的 emptyObject 改名 ⟹ 纯函数行为变 ⟹ S3
    def n1():
        patch_text(
            SRC_MATH,
            'if (selectedCategory === "emptyObject" && requested !== "translate") {',
            'if (selectedCategory === "emptyObjectX" && requested !== "translate") {',
        )
    run_case("N1", "S3 纯函数：emptyObject 守卫的 6 条用例（node 实跑）", n1)
    _restore(SRC_MATH, backups[SRC_MATH])

    # ══ N2：吸附步长改成 0.5 ⟹ S9
    def n2():
        patch_text(SRC_MATH, "export const DIRECTOR_GRID_SNAP_STEP = 1;",
                   "export const DIRECTOR_GRID_SNAP_STEP = 0.5;")
    run_case("N2", "S9 吸附步长 = 1（源站 p7 逐字），clone 三处 TransformControls 都用它", n2)
    _restore(SRC_MATH, backups[SRC_MATH])

    # ══ N3：viewport 里某一处 translationSnap 写死 0.5 ⟹ S9
    def n3():
        # ★ 该串在文件里出现 **3 次**（对象／分组 rig／路径锚点）⟹ ⟹ 用 `size={0.72}`
        #   把它**唯一化**；只改一处 ⟹ ⟹ S1 的「DIRECTOR_GRID_SNAP_STEP 出现在 viewport 里」
        #   仍然成立 ⟹ ⟹ 翻红的**只有** S9。
        patch_text(
            SRC_VIEWPORT,
            "translationSnap={snapToGrid ? DIRECTOR_GRID_SNAP_STEP : null}\n"
            "          size={0.72}",
            "translationSnap={snapToGrid ? 0.5 : null}\n"
            "          size={0.72}",
        )
    run_case("N3", "S9 吸附步长 = 1（源站 p7 逐字），clone 三处 TransformControls 都用它", n3)
    _restore(SRC_VIEWPORT, backups[SRC_VIEWPORT])

    # ══ N4：按 R 的 DOM 模式
    def n4():
        def m(d):
            d["②按R"]["按后"]["DOM"]["模式"] = "translate"
        patch_json(CLONE_RAW, m)
    run_case("N4", "S4 clone 按 R ⟹ 变换模式**等于** rotate", n4)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N5：按 F 的 **store 那一路**（★ 证明 S5 真的读了 store，不只是 DOM）
    def n5():
        def m(d):
            d["②按F"]["按后"]["store"]["transformMode"] = "translate"
        patch_json(CLONE_RAW, m)
    run_case("N5", "S5 clone 按 F ⟹ 变换模式**等于** scale", n5)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N6：按 V 的 DOM 模式
    def n6():
        def m(d):
            d["②按V"]["按后"]["DOM"]["模式"] = "rotate"
        patch_json(CLONE_RAW, m)
    run_case("N6", "S6 clone 按 V ⟹ 变换模式**等于** translate", n6)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N7：Shift+V 的**起点**不是 rotate
    def n7():
        def m(d):
            d["③Shift+V"]["按前"]["DOM"]["模式"] = "translate"
        patch_json(CLONE_RAW, m)
    run_case("N7", "S7 clone Shift+V ⟹ 从 rotate 切到 translate（★ 源站对 v 无修饰键限制）", n7)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N8：按 X 不翻转
    def n8():
        def m(d):
            d["⑤按X"]["按后一次"]["值"] = "false"
        patch_json(CLONE_RAW, m)
    run_case("N8", "S8 clone 按 X ⟹ 网格吸附 false→true→false（DOM 开关 ＋ store 两条路）", n8)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N9：按 X 不翻回（★ 单独打「再按翻回」这一条）
    def n9():
        def m(d):
            d["⑤按X"]["按后两次"]["值"] = "true"
        patch_json(CLONE_RAW, m)
    run_case("N9", "S8 clone 按 X ⟹ 网格吸附 false→true→false（DOM 开关 ＋ store 两条路）", n9)
    _restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N10：源站读数（按 F 的模式）
    def n10():
        def m(d):
            d["④按F"]["按后"]["模式"]["模式"] = "rotate"
        patch_json(SRC_RAW, m)
    run_case("N10", "S10 源站实测：R/F/V 三步成链 ＋ Shift+V ＋ X 翻转 ＋ 吞按键", n10)
    _restore(SRC_RAW, backups[SRC_RAW])

    # ══ N11：★★ 契约里的 hY 去掉 "f" ⟹ S2（本批真实踩过的坑的复现）
    def n11():
        def m(d):
            frag = d["片段"]["键集合 hY（字母快捷键白名单）"]
            frag["原文"] = frag["原文"].replace('"f",', "")
        patch_json(CONTRACT_RAW, m)
    run_case("N11", "S2 契约：源站原文里 V/R/F/X 的实现逐字对得上", n11)
    _restore(CONTRACT_RAW, backups[CONTRACT_RAW])

    # ══ 复原验证（★ 字节级）
    restore_ok = all(p.read_bytes() == backups[p] for p in targets)
    print("\n复原（字节级）：%s" % ("OK" if restore_ok else "★ 失败"))
    ok_count = sum(1 for c in cases if c["通过"])
    print("== batch 852 阴性对照：%d/%d 通过 ==" % (ok_count, len(cases)))

    audit = {
        "批次": 852,
        "阴性总数": len(cases),
        "通过数": ok_count,
        "复原字节级一致": restore_ok,
        "结果": cases,
    }
    (BATCH / "negative-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")

    if ok_count != len(cases) or not restore_ok:
        return 1
    # ★ 复原后必须把门禁跑回绿（★ runtime-audit.json 也要留下**绿**的那份）
    failed, report, _ = run_gate()
    print("复原后门禁：%d/%d 通过，失败=%s"
          % (report.get("通过数", 0), report.get("判据总数", 0), failed))
    return 1 if failed else 0


def _restore(path, data: bytes):
    path.write_bytes(data)


if __name__ == "__main__":
    sys.exit(main())

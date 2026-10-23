#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 857 阴性对照：每条只翻**它自己那一条**判据（或者让**被迁移的老门禁**翻红）。

## ★ 做法（沿用 851–856 的形态）

★ 门禁 S1–S12 读的是四类东西：**契约 JSON** ＋ **源站实测 JSON**
＋ **clone 实测 JSON** ＋ **clone 源码** ⟹ ⟹ 阴性就改「该判据
**独占读取**的那一处」⟹ ⟹ 改完跑一次门禁 ⟹ ⟹ 断言「**恰好**只有
目标判据翻红」⟹ ⟹ 全部复原后**字节级**还原。

| 阴性 | 变异的对象 | 应当翻红的判据 |
| --- | --- | --- |
| N1 | 契约：「间距 onChange」的逐字被改 | S1 |
| N2 | 源站读数：间距填 1.55 后读回 **1.55**（不是 1.6） | S3 |
| N3 | 源站读数：同 aria 元素 **count ＝ 2**（源站有第二个入口） | S4 |
| N4 | clone 读数：落点 **不再**等于按钮 right+8 | S6 |
| N5 | clone 读数：间距填 1.55 后读回 **1.55** | S7 |
| N6 | clone 读数：再点一次后**对话框仍可见**（没实现开关） | S8 |
| N7 | clone 读数：桌面可见入口 **＝ 2** | S9 |
| N8 | clone 读数：移动端可见入口 **＝ 2** | S10 |
| N9 | clone 读数：移动端**再点一次**后对话框仍可见（那枚不是开关） | S10 |
| N10 | clone 源码：间距**不再**保留 1 位小数 | S11 |
| N11 | clone 源码：视口里**加回** legacy 选择器 | S11 |
| N12 | clone 源码：store 的 `addCrowdArray` **加回** `Math.min(` 夹取 | S11 |
| N13 | clone 源码：落点**改回**写死偏移 | ★ **老门禁 `625.py` 直接跑会红** |
| N14 | clone 源码：**去掉开关**（再点一次不关） | ★ **重跑 clone 探针 ⟹ S8 红** |

★ ★★ **N12 是本批最重要的一条**：625 门禁里「crowd-dialog 的落点」
  在本批**被迁移过**（旧的写死坐标 `[294,52,220,208]` ⟹ 改成「按源站
  公式 ＋ 实测锚点」推导）⟹ ⟹ 光跑本批门禁证明不了「迁移后的判据还有牙」
  ⟹ ⟹ 必须**直接跑 625**、看它**会不会红**。

★ ★★ **N13 证明的是「探针本身有牙」**：S7/S8 读的是**探针跑出来的 JSON**
  ⟹ ⟹ 只变异 JSON 只能证明「判据读的是它声称的那个字段」
  ⟹ ⟹ 要证明「探针真的能测出行为不对」，必须**改源码 → 重跑探针 → 门禁红**。

## ★ ★★ **行数中性**：所有源码变异都是**同一行内**的等长替换
   （或同行替换 ⟹ 行数不变）⟹ ⟹ 复原时能**字节级**校验。
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch857-2026-10-01"
RAW = BATCH / "raw"
SRC_RAIL = ROOT / "src/components/director/DirectorIconRail.tsx"
SRC_VIEWPORT = ROOT / "src/components/director/DirectorViewport.tsx"
SRC_STORE = ROOT / "src/store/directorStore.ts"
CONTRACT_RAW = RAW / "source-857-contract.json"
SRC_CROWD_RAW = RAW / "source-857-crowd.json"
CLONE_RAW = RAW / "clone-857-crowd.json"
GATE = ROOT / "scripts/verify-liblib-batch857.py"
GATE625 = ROOT / "scripts/verify-liblib-batch625.py"
PROBE = BATCH / "probes/clone857_crowd.py"

TARGET = {
    "N1": "S1", "N2": "S3", "N3": "S4", "N4": "S6", "N5": "S7",
    "N6": "S8", "N7": "S9", "N8": "S10", "N9": "S10", "N10": "S11",
    "N11": "S11", "N12": "S11",
}


def run_gate():
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True,
                       text=True, cwd=str(ROOT))
    try:
        report = json.loads((BATCH / "runtime-audit.json").read_text(encoding="utf-8"))
    except Exception:
        report = {}
    items = report.get("判据") or []
    failed = [x["判据"] for x in items if not x["通过"]]
    return failed, report, r.stdout


def gate_fail_keys(failed):
    """把「判据名」压成判据号（S1/S3/…）⟹ ⟹ 便于精确比较。"""
    return sorted({f.split()[0] for f in failed})


def patch_text(path, old, new):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit("★ 变异目标出现 %d 次（必须唯一）：%r"
                         % (text.count(old), old))
    before_lines = text.count("\n")
    blob = path.read_bytes()
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    after_lines = path.read_text(encoding="utf-8").count("\n")
    if before_lines != after_lines:
        path.write_bytes(blob)
        raise SystemExit("★ 变异不是行数中性（已回滚）：%d → %d 行"
                         % (before_lines, after_lines))


def patch_json(path, mutate):
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def restore(path, blob):
    path.write_bytes(blob)
    if path.read_bytes() != blob:
        raise SystemExit("★ 复原失败（字节级校验没过）：%s" % path.name)


def run_gate625():
    r = subprocess.run([sys.executable, str(GATE625)], capture_output=True,
                       text=True, cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def run_probe():
    r = subprocess.run([sys.executable, str(PROBE)], capture_output=True,
                       text=True, cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    audit = {"批次": 857, "阴性": []}
    blobs = {p: p.read_bytes() for p in
             (CONTRACT_RAW, SRC_CROWD_RAW, CLONE_RAW,
              SRC_RAIL, SRC_VIEWPORT, SRC_STORE)}

    def record(name, ok, detail):
        audit["阴性"].append({"阴性": name, "通过": bool(ok), "详情": detail})
        print(("  PASS  " if ok else "  FAIL  ") + name + " ｜ " + detail)

    # ══════════ 阶段 A：raw / 源码层变异 ⟹ 本批门禁的**恰好一条**翻红 ══════════
    def n_json(name, path, mutate, target):
        blob = blobs[path]
        try:
            patch_json(path, mutate)
            failed, _report, _out = run_gate()
            keys = gate_fail_keys(failed)
            ok = keys == [target]
            record(name, ok, "翻红判据 %s（期望恰好 [%s]）｜ 全部翻红 %s"
                   % (keys, target, failed))
        finally:
            restore(path, blob)

    def n_source(name, path, old, new, target):
        blob = blobs[path]
        try:
            patch_text(path, old, new)
            failed, _report, _out = run_gate()
            keys = gate_fail_keys(failed)
            ok = keys == [target]
            record(name, ok, "翻红判据 %s（期望恰好 [%s]）" % (keys, target))
        finally:
            restore(path, blob)

    # N1：契约里「间距 onChange」的逐字被改 ⟹ S1 红（只 S1：S5 读的是别的片段）
    def m1(d):
        d["片段"]["间距 onChange（夹 [0.1,10] ＋ 保留 1 位小数）"]["原文"] = \
            "Math.min(10,Math.max(.1,t))"
    n_json("N1 契约：「间距 onChange」逐字被改", CONTRACT_RAW, m1, "S1")

    # N2：源站读数里「间距填 1.55 后」改成 1.55 ⟹ S3 红（S7 读 clone 那边）
    def m2(d):
        d["⑥间距填1.55后"] = "1.55"
    n_json("N2 源站读数：间距填 1.55 后读回 1.55", SRC_CROWD_RAW, m2, "S3")

    # N3：源站读数里同 aria 元素 count 改成 2 ⟹ S4 红
    def m3(d):
        d["⑤同aria元素"]["count"] = 2
    n_json("N3 源站读数：同 aria 元素 count ＝ 2", SRC_CROWD_RAW, m3, "S4")

    # N4：clone 读数里落点 left 不再相等 ⟹ S6 红
    def m4(d):
        d["③落点是否符合源站公式"]["left相等"] = False
    n_json("N4 clone 读数：落点不等于按钮 right+8", CLONE_RAW, m4, "S6")

    # N5：clone 读数里间距读回 1.55 ⟹ S7 红（S3 读源站那边）
    def m5(d):
        d["④间距填1.55后"]["间距"]["value"] = "1.55"
    n_json("N5 clone 读数：间距填 1.55 后读回 1.55", CLONE_RAW, m5, "S7")

    # N6：clone 读数里「再点一次后」对话框仍可见 ⟹ S8 红
    def m6(d):
        d["⑤再点一次后"]["对话框可见"] = True
    n_json("N6 clone 读数：再点一次后对话框仍可见", CLONE_RAW, m6, "S8")

    # N7：clone 读数里桌面可见入口改成 2 ⟹ S9 红
    def m7(d):
        d["⑧桌面可见入口数"] = 2
    n_json("N7 clone 读数：桌面可见入口 ＝ 2", CLONE_RAW, m7, "S9")

    # N8：clone 读数里移动端可见入口改成 2 ⟹ S10 红
    def m8(d):
        d["⑩移动端点开对话框"]["可见入口数"] = 2
    n_json("N8 clone 读数：移动端可见入口 ＝ 2", CLONE_RAW, m8, "S10")

    # N9：clone 读数里「移动端再点一次后」对话框仍可见 ⟹ S10 红
    #   （★ 这是本批**补录**的一条：移动端那枚也得是**开关**）
    def m9(d):
        d["⑪移动端再点一次"]["对话框可见"] = True
    n_json("N9 clone 读数：移动端再点一次后对话框仍可见", CLONE_RAW, m9, "S10")

    # N10：源码里间距不再保留 1 位小数 ⟹ S11 红
    n_source("N10 clone 源码：间距不再保留 1 位小数", SRC_RAIL,
             "Math.round(next * 10) / 10", "next", "S11")

    # N10：视口里加回 legacy 选择器 ⟹ S11 红
    n_source("N11 clone 源码：视口加回 legacy 选择器", SRC_VIEWPORT,
             "data-director-crowd-mobile-trigger", "data-director-crowd-panel", "S11")

    # N11：store 的 addCrowdArray 加回 Math.min( 夹取 ⟹ S11 红
    n_source("N12 clone 源码：store 加回 Math.min( 夹取", SRC_STORE,
             "const safeSpacing = spacing ?? 1.6;",
             "const safeSpacing = Math.min(3, spacing ?? 1.6);", "S11")

    # ══════════ N12：★ 落点改回写死 ⟹ **直接跑老门禁 625** ══════════
    #   ★ 变异目标是**带上下文**的那一处（`anchor.right + 8` 在文件里出现 2 次：
    #   `placeCrowdDialog` 与 `openCrowdDialog` 各一次）⟹ ⟹ 必须唯一命中。
    #   ★ 改 `placeCrowdDialog` 就够：它是**挂载后**再算一遍的那次（layout effect），
    #   ⟹ ⟹ 最终落点由它决定。
    blob = blobs[SRC_RAIL]
    try:
        patch_text(SRC_RAIL,
                   "Math.min(anchor.right + 8, window.innerWidth - width - 8)",
                   "Math.min(anchor.right + 294, window.innerWidth - width - 8)")
        code, out = run_gate625()
        red = code != 0
        record("N13 ★ 老门禁 625 直接跑：落点改回写死偏移 ⟹ 625 翻红",
               red, "625 退出码 %s ｜ 输出尾部 %s"
               % (code, out.strip().splitlines()[-1] if out.strip() else ""))
    finally:
        restore(SRC_RAIL, blob)

    # ══════════ N13：★ 去掉开关 ⟹ 重跑探针 ⟹ S8 红 ══════════
    blob = blobs[SRC_RAIL]
    raw_blob = blobs[CLONE_RAW]
    try:
        # ★ 变异目标必须**唯一** ⟹ ⟹ 「开关块」现在有**两处**
        #   （rail 的「群众 (3x3)」按钮 ＋ 移动端事件处理器）⟹ ⟹ 要带上下文。
        patch_text(SRC_RAIL,
                   "      if (crowdDialogOpen) {\n"
                   "        setCrowdDialogOpen(false);\n"
                   "        return;\n"
                   "      }\n"
                   "      const rect = crowdButtonRef.current?.getBoundingClientRect();",
                   "      if (false) {\n"
                   "        setCrowdDialogOpen(false);\n"
                   "        return;\n"
                   "      }\n"
                   "      const rect = crowdButtonRef.current?.getBoundingClientRect();")
        pcode, pout = run_probe()
        failed, _report, _out = run_gate()
        keys = gate_fail_keys(failed)
        record("N14 ★ 重跑探针：去掉开关 ⟹ S8 红（探针本身有牙）",
               pcode == 0 and keys == ["S8"],
               "探针退出码 %s ｜ 翻红判据 %s（期望恰好 [S8]）" % (pcode, keys))
    finally:
        restore(SRC_RAIL, blob)
        restore(CLONE_RAW, raw_blob)

    # ── 复原自检：所有被改过的文件都要**字节级**回到原样 ──
    intact = all(p.read_bytes() == b for p, b in blobs.items())
    record("复原自检：6 个文件字节级回到原样", intact,
           "全部一致 %s" % intact)

    out_path = BATCH / "negative-audit.json"
    out_path.write_text(json.dumps(audit, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    passed = sum(1 for r in audit["阴性"] if r["通过"])
    print("\n%d/%d 条通过" % (passed, len(audit["阴性"])))
    return 0 if passed == len(audit["阴性"]) else 1


if __name__ == "__main__":
    sys.exit(main())

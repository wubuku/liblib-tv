#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 856 阴性对照：每条只翻**它自己那一条**判据。

## ★ 做法（沿用 851–855 的形态）

★ 门禁 S1–S9 读的是四类东西：**契约 JSON** ＋ **源站实测 JSON** ×2
＋ **clone 实测 JSON** ＋ **clone 源码** ⟹ ⟹ 所以阴性就改「该判据
**独占读取**的那一处」⟹ ⟹ 改完跑一次门禁 ⟹ ⟹ 断言「**恰好**只有
目标判据翻红」⟹ ⟹ 全部复原后**字节级**还原。

| 阴性 | 变异的对象 | 应当翻红的判据 |
| --- | --- | --- |
| N1 | 契约：组对象字面量里**加上** `transform` | S1 |
| N2 | 源站读数：组检查器**多一个**字段 | S2 |
| N3 | 源站读数：角色检查器**少一个**字段（让阳性对照失效） | S3 |
| N4 | 源站读数：选中组后的**包围盒右缘**改到画布上 | S4 |
| N5 | 源站读数：选中角色的**包围盒右缘**改到树面板内 | S5 |
| N6 | clone 读数：组检查器**多一个**变换字段 | S6 |
| N7 | clone 读数：组轨道数**改成 0** | S7 |
| N8 | clone 源码：组检查器**加回**一个变换字段容器 | S8 |
| N9 | clone 源码：Inspector **加回** `cloneDirectorTransform` 定义 | S9 |
| N10 | clone 源码：组 rig 里**加回** `<TransformControls>`（源站没有组 gizmo） | 老门禁 `86.mjs` 红 ＋ S8 |
| N11 | clone 源码：路径 gizmo **去掉** `onPointerCancel` | 老门禁 `86.mjs` 红 |
| N12 | clone 源码：**多一个不带** `onPointerCancel` 的 gizmo | 老门禁 `86.mjs` 红（★ 旧的「只看个数」判据看不见） |
| N13 | clone 源码：一处 gizmo **不用**吸附步长 | 老门禁 `852.py` 红 |

★ ★★ **字段互不重叠**是这套阴性能成立的前提 ⟹ ⟹ 所以：
  - S2 读源站的 `⑤组检查器面板字段`，S3 读 `③选中角色后面板字段`
    ⟹ ⟹ 两个不同的键 ⟹ ⟹ 互不影响；
  - S4 读 `④选中组后 vs 未选中任何`，S5 读 `②选中角色后 vs 未选中`
    ⟹ ⟹ 两个不同的键；
  - S6 读 clone 的 `⑤组检查器`，S7 读 clone 的 `⑦组轨道数`／`⑧复原后组数`
    ⟹ ⟹ 两个不同的键；
  - S8 读 **Inspector 源码**，S9 读 **Inspector 源码里的另一个函数**
    ⟹ ⟹ N8 加的是 `data-director-group-transform-field` 容器，
    N9 加的是 `function cloneDirectorTransform(` ⟹ ⟹ 两个不同的字符串。

★ ★ **行数中性**：所有源码变异都是**同一行内**的等长替换 ⟹ ⟹
  文件行数不变 ⟹ ⟹ 复原时能**字节级**校验。
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch856-2026-10-01"
RAW = BATCH / "raw"
SRC_INSPECTOR = ROOT / "src/components/director/DirectorInspector.tsx"
SRC_VIEWPORT = ROOT / "src/components/director/DirectorViewport.tsx"
CONTRACT_RAW = RAW / "source-856-contract.json"
SRC_INSPECTOR_RAW = RAW / "source-856-groupinspector.json"
SRC_GIZMO_RAW = RAW / "source-856-groupgizmo.json"
CLONE_RAW = RAW / "clone-856-groupinspector.json"
GATE = ROOT / "scripts/verify-liblib-batch856.py"
GATE86 = ROOT / "scripts/verify-liblib-batch86.mjs"
GATE852 = ROOT / "scripts/verify-liblib-batch852.py"

J = {
    "S1": "S1 契约：6 个片段唯一命中 ＋ 3 条关键逐字 ＋ 任意值自检",
    "S2": "S2 源站实测：组检查器只有「名称」一个字段",
    "S3": "S3 源站阳性对照：角色检查器 13 个字段（含位置／旋转／缩放）",
    "S4": "S4 源站实测：选中组后画布无 gizmo（像素差只落在左侧树面板）",
    "S5": "S5 源站阳性对照：选中角色时画布**有** gizmo（像素差延伸到右侧）",
    "S6": "S6 clone 实测：组检查器 0 个变换字段 ＋ 只有名称输入框",
    "S7": "S7 clone 实测：组轨道仍在 ＋ 解组能复原",
    "S8": "S8 clone 源码：组检查器无变换字段 ＋ 组 gizmo 组件无 TransformControls",
    "S9": "S9 clone 源码：死代码已清（Inspector 里没有 cloneDirectorTransform 的定义／调用）",
}


def run_gate():
    r = subprocess.run(
        [sys.executable, str(GATE)], capture_output=True, text=True, cwd=str(ROOT)
    )
    try:
        report = json.loads((BATCH / "runtime-audit.json").read_text(encoding="utf-8"))
    except Exception:
        report = {}
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
    before_lines = text.count("\n")
    blob = path.read_bytes()
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    after_lines = path.read_text(encoding="utf-8").count("\n")
    if before_lines != after_lines:
        # ★★ **当场回滚** ⟹ ⟹ 变异不是行数中性时，**不能把变异留在仓库里**
        path.write_bytes(blob)
        raise SystemExit(
            "★ 变异不是行数中性（已回滚）：%d → %d 行" % (before_lines, after_lines)
        )


def patch_json(path, mutate):
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def restore(path, blob):
    path.write_bytes(blob)
    if path.read_bytes() != blob:
        raise SystemExit("★ 复原失败（字节级校验没过）：%s" % path.name)


def run_node_gate(path):
    """跑一条**外部**门禁（`.mjs` 走 node，`.py` 走 python）⟹ ⟹ 返回 (exit code, 输出)。

    ★ 这批有三条老门禁（`84.mjs`／`86.mjs`／`852.py`）的**判据被迁移过**
    ⟹ ⟹ 光跑本批门禁证明不了「迁移后的判据还有牙」
    ⟹ ⟹ 必须**直接跑那几条老门禁**、看它们**会不会红**。
    """
    if path.suffix == ".mjs":
        cmd = ["node", str(path)]
    else:
        cmd = [sys.executable, str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def viewport_gizmo_readings():
    """读出视口里的两个量：gizmo 挂点数 ＋ `onPointerCancel={cancelTransform}` 计数。

    ★ 这两个量的**组合**就是「结构性断言」的全部依据 ⟹ ⟹
    ★ N12 要用它们证明「只看 count 的旧式判据」看不见某个变异。
    """
    src = SRC_VIEWPORT.read_text(encoding="utf-8")
    live = re.sub(r"/\*[\s\S]*?\*/", "", src)
    live = re.sub(r"(^|[^:])//.*$", r"\1", live, flags=re.M)
    tc = "<TransformControls"
    blocks = []
    at = live.find(tc)
    while at != -1:
        close_at = live.find("/>", at)
        next_at = live.find(tc, at + len(tc))
        if next_at != -1 and (close_at == -1 or next_at < close_at):
            end = next_at
        else:
            end = close_at
        blocks.append(live[at:] if end == -1 else live[at:end])
        at = next_at
    cancels = len(re.findall(r"onPointerCancel=\{cancelTransform\}", live))
    return len(blocks), cancels


def main() -> int:
    targets = [SRC_INSPECTOR, SRC_VIEWPORT, CONTRACT_RAW, SRC_INSPECTOR_RAW,
               SRC_GIZMO_RAW, CLONE_RAW]
    backups = {p: p.read_bytes() for p in targets}

    baseline_failed, baseline_report, _ = run_gate()
    total = len(baseline_report.get("判据", []))
    print("基线：%d/%d 通过，失败=%s" % (total - len(baseline_failed), total,
                                       baseline_failed))
    if baseline_failed:
        print("★ 基线不绿，先修门禁")
        return 1

    cases = []

    def run_case(name, key, apply_fn):
        apply_fn()
        failed, _, _ = run_gate()
        target = J[key]
        only = set(failed) == {target}
        cases.append({"阴性": name, "目标判据": target, "实际翻红": failed,
                      "恰好一条": only, "通过": only and len(failed) == 1})
        print("  %-4s %-4s 目标=%s 实际=%s %s"
              % (name, "OK" if only else "BAD", key, failed,
                 "" if only else "★★ 不是恰好一条"))

    # ══ N1：契约里给组对象加上 transform ⟹ S1 ═════════════════════════
    def n1():
        def m(d):
            k = "组对象字面量（无 transform 字段）"
            d["片段"][k]["原文"] = d["片段"][k]["原文"].replace(
                "members:r}", "members:r,transform:null}")
        patch_json(CONTRACT_RAW, m)
    run_case("N1", "S1", n1)
    restore(CONTRACT_RAW, backups[CONTRACT_RAW])

    # ══ N2：源站读数里给组检查器多一个字段 ⟹ S2 ══════════════════════
    def n2():
        def m(d):
            d["⑤组检查器面板字段"].append({
                "type": "number", "x": 1656, "y": 200, "w": 80, "h": 28,
                "value": "1", "aria": "", "placeholder": "", "label": "位置",
                "min": None, "max": None, "step": None})
        patch_json(SRC_INSPECTOR_RAW, m)
    run_case("N2", "S2", n2)
    restore(SRC_INSPECTOR_RAW, backups[SRC_INSPECTOR_RAW])

    # ══ N3：源站读数里让角色检查器少一个字段 ⟹ S3 ════════════════════
    def n3():
        def m(d):
            d["③选中角色后面板字段"] = d["③选中角色后面板字段"][:-1]
        patch_json(SRC_INSPECTOR_RAW, m)
    run_case("N3", "S3", n3)
    restore(SRC_INSPECTOR_RAW, backups[SRC_INSPECTOR_RAW])

    # ══ N4：源站读数里让「选中组」的像素差落到画布上 ⟹ S4 ════════════
    def n4():
        def m(d):
            d["④选中组后 vs 未选中任何"]["变化包围盒"][2] = 820
        patch_json(SRC_GIZMO_RAW, m)
    run_case("N4", "S4", n4)
    restore(SRC_GIZMO_RAW, backups[SRC_GIZMO_RAW])

    # ══ N5：源站读数里让「选中角色」的像素差缩回树面板 ⟹ S5 ══════════
    def n5():
        def m(d):
            d["②选中角色后 vs 未选中"]["变化包围盒"][2] = 260
        patch_json(SRC_GIZMO_RAW, m)
    run_case("N5", "S5", n5)
    restore(SRC_GIZMO_RAW, backups[SRC_GIZMO_RAW])

    # ══ N6：clone 读数里给组检查器加回一个变换字段 ⟹ S6 ══════════════
    def n6():
        def m(d):
            d["⑤组检查器"]["变换字段"] = ["position"]
            d["⑤组检查器"]["变换字段数"] = 1
        patch_json(CLONE_RAW, m)
    run_case("N6", "S6", n6)
    restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N7：clone 读数里把组轨道数改成 0 ⟹ S7 ════════════════════════
    def n7():
        def m(d):
            d["⑦组轨道数"] = 0
        patch_json(CLONE_RAW, m)
    run_case("N7", "S7", n7)
    restore(CLONE_RAW, backups[CLONE_RAW])

    # ══ N8：clone 源码里给组检查器加回变换字段容器 ⟹ S8 ═════════════
    def n8():
        # ★ 行数中性：**同行替换**（不是插一行）⟹ ⟹ 行数不变。
        # ★ ★ 上一版插了一行 ⟹ ⟹ 被「行数中性」检查当场回滚（脚本自己救了自己）。
        patch_text(
            SRC_INSPECTOR,
            "      {/* ★★★ Batch 856：组**没有变换字段**。",
            "      <div data-director-group-transform-field=\"position\" />{/* ★★★ Batch 856：组**没有变换字段**。",
        )
    run_case("N8", "S8", n8)
    restore(SRC_INSPECTOR, backups[SRC_INSPECTOR])

    # ══ N9：clone 源码里加回 cloneDirectorTransform 定义 ⟹ S9 ═════════
    def n9():
        # ★ 行数中性：**同行替换**（把 axisLabels 那行改成两段 ⟹ ⟹ 还是 1 行）
        patch_text(
            SRC_INSPECTOR,
            "const axisLabels = [\"X\", \"Y\", \"Z\"] as const;",
            "function cloneDirectorTransform() { return null; } const axisLabels = [\"X\", \"Y\", \"Z\"] as const;",
        )
    run_case("N9", "S9", n9)
    restore(SRC_INSPECTOR, backups[SRC_INSPECTOR])

    # ══ N10/N11/N12：★ **迁移后的老门禁**必须**还能红** ═══════════════
    #
    # ★ ★ 背景：本批迁移了 `86.mjs` 的判据（写死个数 ⟹ 结构性断言）
    #   ⟹ ⟹ 光跑本批门禁（S1–S11）证明不了「迁移后的判据还有牙」
    #   ⟹ ⟹ 必须**直接跑那条老门禁**、看它**会不会红**。
    # ★ ★ 三条各测一处：
    #   N10 ⟹ 组 rig 的**负向断言**（源站没有组 gizmo）有牙；
    #   N11 ⟹ **逐挂点**断言（每个 gizmo 都必须带 pointer cancel）有牙；
    #   N12 ⟹ **挂点数一致性**断言有牙，
    #        且同时证明「只看 count 的旧式判据**看不见**这个变异」。
    # ★ ★ 变异对象统一是 **viewport 源码** ⟹ ⟹ 所以只动一个文件。
    def run_external_case(name, apply_fn, expect_flipped=(), gate=None,
                          label="86.mjs"):
        gate = gate or GATE86
        apply_fn()
        rc, out = run_node_gate(gate)
        failed_gate, _, _ = run_gate()
        restore(SRC_VIEWPORT, backups[SRC_VIEWPORT])
        rc2, _ = run_node_gate(gate)
        red = rc != 0
        back_green = rc2 == 0
        only_expected = set(failed_gate) == set(expect_flipped)
        ok = red and back_green and only_expected
        cases.append({
            "阴性": name,
            "目标判据": "老门禁 %s（判据已迁移）" % label,
            "老门禁是否翻红": red,
            "复原后老门禁回绿": back_green,
            "本批门禁同时翻红": failed_gate,
            "期望同时翻红": list(expect_flipped),
            "通过": ok,
        })
        print("  %-4s %-4s %s 翻红=%s 复原回绿=%s 本批同时翻红=%s（期望 %s）"
              % (name, "OK" if ok else "BAD", label, red, back_green, failed_gate,
                 list(expect_flipped)))
        return ok

    # ══ N10：组 rig 里加回一个 gizmo ⟹ 86.mjs 红（组 rig 负向断言有牙）══
    def n10():
        # ★ 行数中性：**同行替换**（在组 rig 的根 group 上挂一个 gizmo）
        patch_text(
            SRC_VIEWPORT,
            "    <group data-director-group-rig={group.id}>",
            "    <group data-director-group-rig={group.id}><TransformControls object={anchor} mode=\"translate\" />",
        )
    run_external_case("N10", n10, expect_flipped=(J["S8"],))

    # ══ N11：路径 gizmo 去掉 onPointerCancel ⟹ 86.mjs 红 ═══════════════
    def n11():
        # ★ 行数中性：**同行替换**（锚点两行 ⟹ ⟹ 换成两行）
        patch_text(
            SRC_VIEWPORT,
            "          onPointerCancel={cancelTransform}\n        />",
            "          onPointerCancel={cancelTransformAlt}\n        />",
        )
    run_external_case("N11", n11)

    # ══ N12：多一个**不带** pointerCancel 的 gizmo ⟹ 86.mjs 红 ═════════
    base_blocks, base_cancels = viewport_gizmo_readings()
    mut_readings = {}
    def n12():
        # ★ 行数中性：**同行替换**（锚点四行 ⟹ ⟹ 换成四行）
        patch_text(
            SRC_VIEWPORT,
            "          onPointerCancel={cancelTransform}\n"
            "        />\n"
            "      ) : null}\n"
            "      {content}",
            "          onPointerCancel={cancelTransform}\n"
            "        />\n"
            "      ) : null}\n"
            "      {content}      <TransformControls object={transformTarget} mode=\"translate\" size={0.5} />",
        )
        # ★ ★ 变异后的读数必须**在复原前**采集（否则读到的是复原后的基线）
        mut_readings["blocks"], mut_readings["cancels"] = viewport_gizmo_readings()
    ok12 = run_external_case("N12", n12)
    mut_blocks = mut_readings.get("blocks")
    mut_cancels = mut_readings.get("cancels")
    # ★ ★★ **关键证据**：这个变异**不改变 count**（pointerCancel 计数不变）⟹ ⟹
    #   ★ 任何「只依赖 count」的判据（旧写法 `count === 写死的 K`）
    #   ★ 在这个变异前后**输出逐字相同** ⟹ ⟹ 它**看不见**这个变异；
    #   ★ 而新判据「count == gizmo 挂点数」⟹ ⟹ 挂点数变了 ⟹ ⟹ 立刻变红。
    count_unchanged = base_cancels == mut_cancels
    blocks_changed = base_blocks != mut_blocks
    print("  ★ N12 证据：pointerCancel 计数 %d → %d（%s）｜ gizmo 挂点数 %d → %d（%s）"
          % (base_cancels, mut_cancels, "不变 ⟹ 旧式『只看个数』判据看不见",
             base_blocks, mut_blocks, "变了 ⟹ 新式结构性判据能抓住"))
    cases[-1]["pointerCancel计数"] = [base_cancels, mut_cancels]
    cases[-1]["gizmo挂点数"] = [base_blocks, mut_blocks]
    cases[-1]["count不变旧判据看不见"] = count_unchanged and blocks_changed
    if not (count_unchanged and blocks_changed):
        cases[-1]["通过"] = False
        ok12 = False

    # ══ N13：让一处 gizmo 不用吸附步长 ⟹ 852.py 红 ═══════════════════
    # ★ 背景：852.py 的 S9 原来写死「**三处** TransformControls 都用吸附步长」
    #   ⟹ ⟹ 本批删掉组 gizmo ⟹ ⟹ 前提过期 ⟹ ⟹ 已迁移成「**每处** gizmo 都用」。
    # ★ 这条阴性证明**迁移后的那条**有牙（不是只证明「852.py 整体是红的」）。
    def n13():
        # ★ 行数中性：**同行替换**（锚点两行 ⟹ ⟹ 换成两行）
        patch_text(
            SRC_VIEWPORT,
            "          translationSnap={snapToGrid ? DIRECTOR_GRID_SNAP_STEP : null}\n"
            "          size={0.62}",
            "          translationSnap={null}\n"
            "          size={0.62}",
        )
    run_external_case("N13", n13, gate=GATE852, label="852.py")

    # ── 全部复原后必须回绿 ────────────────────────────────────────────
    for p in targets:
        restore(p, backups[p])
    final_failed, final_report, _ = run_gate()
    green = not final_failed
    passed = sum(1 for c in cases if c["通过"])
    print("\n阴性 %d/%d 条「恰好翻一条」" % (passed, len(cases)))
    print("复原后门禁：%s" % ("回绿" if green else "★ 没回绿 %s" % final_failed))
    if not green:
        return 1
    for p in targets:
        if p.read_bytes() != backups[p]:
            print("★ 字节级复原失败：%s" % p.name)
            return 1
    out = BATCH / "negative-audit.json"
    out.write_text(
        json.dumps({"批次": 856, "阴性": cases,
                    "复原后回绿": green,
                    "字节级复原": True},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print("已落盘：", out)
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())

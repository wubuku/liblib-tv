#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 856 门禁：导演台**组的检查器与画布 gizmo**（对齐源站逐字）。

## ★ 这批要守住的东西

★ 855 登记的 D1 是「源站交互路径的组变换语义未取证」⟹ ⟹ 本批**取证完���**
⟹ ⟹ ★ **结论与当初的假设相反**：

| | 源站 | clone（整改前） | clone（整改后） |
| --- | --- | --- | --- |
| 组检查器的**变换字段** | **0**（只有「名称」） | 3（位置／旋转／缩放） | **0** |
| 组检查器的**输入框** | **1**（名称，248×28） | 10 | **1**（名称，248×32） |
| 画布上的**组 gizmo** | **没有** | 有（可拖拽） | **没有** |

★ 源站逐字（机器提取见 `raw/source-856-contract.json`，6/6 唯一命中）：
  建组 `a={id:lM(),label:lT(e.characterGroups),characterIds:n,members:r}`
  ⟹ ⟹ 组**只有 4 个字段**，**没有 transform**。
★ 源站实测（`raw/source-856-groupinspector.json`）：
  选中**角色** ⟹ 检查器 **13 个字段**（名称／位置xyz／旋转xyz／缩放xyz／
  统一缩放／颜色）；选中**组** ⟹ 检查器 **1 个字段**（**只有「名称」**）。
★ 源站实测（`raw/source-856-groupgizmo.json`）：
  选中组后画布**像素差只落在左侧树面板**（包围盒右缘 x=271）；
  ★ **阳性对照**＝选中角色时画布右下角出现**红色箭头**（包围盒延伸到 x=896）。
  ⟹ ⟹ 源站里 gizmo **只注册具体对象**，**没有「组」这一类**。

## ★ ★ 判据分工（★ 各条读的字段互不重叠 ⟹ ⟹ 阴性每条只翻它自己那一条）

| 判据 | 读什么 | 阴性 |
| --- | --- | --- |
| S1 | 契约：6 个片段**唯一命中** ＋ 关键逐字 | N1 |
| S2 | 源站实测：**组检查器只有 1 个字段**，且**没有**变换字段 | N2 |
| S3 | 源站实测：**角色检查器有 13 个字段**（★ 阳性对照 ⟹ 证明探针**看得见**变换字段） | N3 |
| S4 | 源站实测：选中组后画布**像素差只落在树面板**（无 gizmo） | N4 |
| S5 | 源站实测：**阳性对照**选中角色时画布像素差**延伸到右侧**（有 gizmo） | N5 |
| S6 | clone 实测：**组检查器 0 个变换字段 ＋ 1 个输入框** | N6 |
| S7 | clone 实测：**组轨道仍在**（组唯一的移动路径没被删掉） | N7 |
| S8 | clone 源码：组检查器**没有**变换字段、视口**没有** TransformControls | N8 |
| S9 | clone 源码：**死代码已清**（`cloneDirectorTransform` 不在 Inspector 里） | N9 |
| S10 | 老门禁 `84.mjs`：**判据已迁移**（组锁定守卫改认 store ＋ 旧写法清零） | N10 |
| S11 | 老门禁 `86.mjs`：**判据已迁移**（写死个数 ⟹ 结构性断言 ＋ 旧写法清零） | N11／N12 |
| S12 | 老门禁 `852.py`：**判据已迁移**（写死三处 ⟹ 每处 gizmo 都用吸附步长） | N13 |

## ★ ★★ **S2/S3/S4/S5 是「源站 ↔ clone 交叉」的关键**

★ 只断言 clone 是 0 个字段 ⟹ ⟹ 那可能只是「探针瞎了」⟹ ⟹
★ 所以必须**同时**断言「**同一个探针**在角色上能看见 13 个字段」（S3）
★ 与「在组上只能看见 1 个」（S2）⟹ ⟹ **对照组的读数证明探针有分辨力**。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch856-2026-10-01"
RAW = BATCH / "raw"

SRC_INSPECTOR = ROOT / "src/components/director/DirectorInspector.tsx"
SRC_VIEWPORT = ROOT / "src/components/director/DirectorViewport.tsx"

results = []


def record(name, ok, detail):
    results.append({"判据": name, "通过": bool(ok), "详情": detail})
    print(("  PASS  " if ok else "  FAIL  ") + name + " ｜ " + detail)


def main() -> int:
    for p in (RAW / "source-856-contract.json",
              RAW / "source-856-groupinspector.json",
              RAW / "source-856-groupgizmo.json",
              RAW / "clone-856-groupinspector.json"):
        if not p.exists():
            print("★★ 缺产物：%s" % p)
            return 2

    contract = json.loads((RAW / "source-856-contract.json").read_text(encoding="utf-8"))
    src_insp = json.loads((RAW / "source-856-groupinspector.json").read_text(encoding="utf-8"))
    src_giz = json.loads((RAW / "source-856-groupgizmo.json").read_text(encoding="utf-8"))
    clone = json.loads((RAW / "clone-856-groupinspector.json").read_text(encoding="utf-8"))
    inspector_src = SRC_INSPECTOR.read_text(encoding="utf-8")
    viewport_src = SRC_VIEWPORT.read_text(encoding="utf-8")

    # ══════════════════════════════════════════════════════════════════
    # S1 契约：6 个片段唯一命中 ＋ 关键逐字
    # ══════════════════════════════════════════════════════════════════
    frags = contract.get("片段", {})
    uniq = [k for k, v in frags.items() if v.get("锚点命中数") == 1 and v.get("原文")]
    key_verbatim = [
        ("组对象字面量（无 transform 字段）",
         "a={id:lM(),label:lT(e.characterGroups),characterIds:n,members:r}"),
        ("reducer SELECT_CHARACTER_GROUP（选中组 ⟹ lQ(n) ＋ selectedGroupId）",
         "case\"SELECT_CHARACTER_GROUP\":{let r=e.characterGroups.find(e=>e.id===t.id)"),
        ("组的锚点 H(e,t)（全部成员位置均值 ⟹ 组位置永远是派生的）",
         "function H(e,t){var r=O(e).map(t).filter(e=>!!e)"),
    ]
    verbatim_ok = all(
        needle in frags.get(name, {}).get("原文", "")
        for name, needle in key_verbatim
    )
    arb_ok = contract.get("★任意值类名自检", {}).get("通过") is True
    record("S1 契约：6 个片段唯一命中 ＋ 3 条关键逐字 ＋ 任意值自检",
           len(uniq) == 6 and verbatim_ok and arb_ok,
           "唯一命中 %d/6 ｜ 关键逐字 %s ｜ 任意值自检 %s"
           % (len(uniq), verbatim_ok, arb_ok))

    # ══════════════════════════════════════════════════════════════════
    # S2 源站实测：组检查器只有 1 个字段（只有「名称」）
    # ══════════════════════════════════════════════════════════════════
    grp_fields = src_insp.get("⑤组检查器面板字段") or []
    grp_labels = sorted({f.get("label") for f in grp_fields})
    grp_values = [f.get("value") for f in grp_fields]
    s2_ok = (
        len(grp_fields) == 1
        and grp_labels == ["名称"]
        and len(grp_values) == 1
        and str(grp_values[0]).startswith("分组")
    )
    record("S2 源站实测：组检查器只有「名称」一个字段",
           s2_ok,
           "字段数 %d ｜ label %s ｜ 值 %s"
           % (len(grp_fields), grp_labels, grp_values))

    # ══════════════════════════════════════════════════════════════════
    # S3 ★ 阳性对照：角色检查器有 13 个字段（证明探针**看得见**变换字段）
    # ══════════════════════════════════════════════════════════════════
    chr_fields = src_insp.get("③选中角色后面板字段") or []
    chr_labels = sorted({f.get("label") for f in chr_fields})
    chr_has_transform = all(
        any(f.get("label") == lab for f in chr_fields)
        for lab in ("位置", "旋转", "缩放")
    )
    s3_ok = len(chr_fields) == 13 and chr_has_transform
    record("S3 源站阳性对照：角色检查器 13 个字段（含位置／旋转／缩放）",
           s3_ok,
           "字段数 %d（期望 13）｜ 含位置/旋转/缩放 %s ｜ label 集 %s"
           % (len(chr_fields), chr_has_transform, chr_labels))

    # ══════════════════════════════════════════════════════════════════
    # S4 源站实测：选中组后画布**没有** gizmo（像素差只落在树面板）
    # ══════════════════════════════════════════════════════════════════
    gz = src_giz.get("④选中组后 vs 未选中任何") or {}
    bbox = gz.get("变化包围盒") or [0, 0, 0, 0]
    changed = gz.get("不同像素数") or 0
    # ★ 树面板右缘 ≈ x=271（源站实测：树在左 0–280 区间）⟹ ⟹
    #   画布上**没有**任何像素变化 ⟹ ⟹ 包围盒右缘必须**小于** 400
    s4_ok = changed > 0 and len(bbox) == 4 and bbox[2] < 400
    record("S4 源站实测：选中组后画布无 gizmo（像素差只落在左侧树面板）",
           s4_ok,
           "不同像素 %d ｜ 包围盒 %s（右缘 %s < 400 ⟹ 画布无变化）"
           % (changed, bbox, bbox[2] if len(bbox) == 4 else "?"))

    # ══════════════════════════════════════════════════════════════════
    # S5 ★ 阳性对照：选中**角色**时画布**有** gizmo（包围盒延伸到右侧）
    # ══════════════════════════════════════════════════════════════════
    gz2 = src_giz.get("②选中角色后 vs 未选中") or {}
    bbox2 = gz2.get("变化包围盒") or [0, 0, 0, 0]
    s5_ok = len(bbox2) == 4 and bbox2[2] > 400
    record("S5 源站阳性对照：选中角色时画布**有** gizmo（像素差延伸到右侧）",
           s5_ok,
           "包围盒 %s（右缘 %s > 400 ⟹ 画布上有 gizmo）"
           % (bbox2, bbox2[2] if len(bbox2) == 4 else "?"))

    # ══════════════════════════════════════════════════════════════════
    # S6 clone 实测：组检查器 0 个变换字段 ＋ 1 个输入框
    # ══════════════════════════════════════════════════════════════════
    c_insp = clone.get("⑤组检查器") or {}
    c_fields = c_insp.get("变换字段") or []
    c_inputs = c_insp.get("输入框") or []
    s6_ok = (
        len(c_fields) == 0
        and len(c_inputs) == 1
        and c_inputs[0].get("name") == "group-name"
    )
    record("S6 clone 实测：组检查器 0 个变换字段 ＋ 只有名称输入框",
           s6_ok,
           "变换字段 %s（期望 0）｜ 输入框数 %d（期望 1）｜ 名称框 %s"
           % (c_fields, len(c_inputs),
              c_inputs[0].get("name") if c_inputs else None))

    # ══════════════════════════════════════════════════════════════════
    # S7 clone 实测：**组轨道仍在**（组唯一的移动路径没被删掉）
    # ══════════════════════════════════════════════════════════════════
    track_count = clone.get("⑦组轨道数")
    ungroup_ok = clone.get("⑧复原后组数") == 0
    s7_ok = track_count == 1 and ungroup_ok
    record("S7 clone 实测：组轨道仍在 ＋ 解组能复原",
           s7_ok,
           "组轨道数 %s（期望 1）｜ 复原后组数 %s（期望 0）"
           % (track_count, clone.get("⑧复原后组数")))

    # ══════════════════════════════════════════════════════════════════
    # S8 clone 源码：组检查器没有变换字段、视口没有 TransformControls
    # ══════════════════════════════════════════════════════════════════
    inspector_block = inspector_src
    # ★ 组检查器组件那一段（从 function GroupInspector 到下一个 function）
    m = re.search(r"function GroupInspector\(.*?\n\}\n", inspector_src, re.S)
    if m:
        inspector_block = m.group(0)
    has_field_attr = "data-director-group-transform-field" in inspector_block
    # ★ 视口里那个组件**不应**再有 TransformControls
    m2 = re.search(r"function DirectorGroupTransformRig\(.*?\n\}\n", viewport_src, re.S)
    rig_block = m2.group(0) if m2 else ""
    has_controls = "TransformControls" in rig_block
    s8_ok = not has_field_attr and not has_controls
    record("S8 clone 源码：组检查器无变换字段 ＋ 组 gizmo 组件无 TransformControls",
           s8_ok,
           "组检查器里还有 data-director-group-transform-field %s ｜ "
           "组 gizmo 组件里还有 TransformControls %s"
           % (has_field_attr, has_controls))

    # ══════════════════════════════════════════════════════════════════
    # S9 clone 源码：死代码已清（Inspector 里不再**定义** cloneDirectorTransform）
    # ★ ★ 判据要查「**函数定义**」而不是「名字出现过」——
    #   ⟹ ⟹ 否则注释里提一句这个名字就会假红（★ 本批第一次跑就假红了）。
    # ══════════════════════════════════════════════════════════════════
    dead_def = re.search(r"function\s+cloneDirectorTransform\s*\(", inspector_src)
    dead_use = re.search(r"(?<!function\s)\bcloneDirectorTransform\s*\(",
                          inspector_src)
    s9_ok = dead_def is None and dead_use is None
    record("S9 clone 源码：死代码已清（Inspector 里没有 cloneDirectorTransform 的定义／调用）",
           s9_ok,
           "定义 %s ｜ 调用 %s"
           % (bool(dead_def), bool(dead_use)))

    # ══════════════════════════════════════════════════════════════════
    # S10 ★ **老门禁 84.mjs 的判据迁移**（本批引入的一条回归 ⟹ ⟹ 必须钉住）
    #
    # ★ ★ 背景：老门禁 `84.mjs` 断言 `viewportSource` 含 `hasLockedMember`
    #   ⟹ ⟹ 那道守卫的**前提**是「视口里有组 gizmo、且组里有锁定成员就隐藏它」
    #   ⟹ ⟹ 本批按源站逐字**删掉组 gizmo** ⟹ ⟹ 视口层不再需要这道守卫
    #   ⟹ ⟹ 旧断言的前提**过期**（它守的是一个源站不存在的交互）。
    # ★ ★ 处理（按仓库先例：854 改 `45.py`、855 改 `87.mjs`）：
    #   正向改成「组锁定守卫在 store 里（定义 ＋ 调用点）」，
    #   另加**负向断言**保证旧的视口层写法清零（否则「新旧都写」就能蒙混过关）。
    # ★ ★ 本条判据钉的是「**迁移这件事本身**」⟹ ⟹ 免得以后有人把老门禁改回旧写法。
    # ══════════════════════════════════════════════════════════════════
    gate84 = ROOT / "scripts/verify-liblib-batch84.mjs"
    if gate84.exists():
        g84 = gate84.read_text(encoding="utf-8")
        # ★ ★ 查的是**活代码行**（去掉整行注释）⟹ ⟹ 注释里提到旧名字也不算数
        g84_code = "\n".join(
            ln for ln in g84.splitlines() if not ln.lstrip().startswith("//")
        )
        s10_def = "function directorGroupHasLockedMember\\(" in g84_code
        s10_call = "directorGroupHasLockedMember\\(state, group\\)" in g84_code
        s10_neg = "doesNotMatch" in g84_code
        s10_neg_watch = "const hasLockedMember\\s*=" in g84_code
        # ★ ★ 旧的正向断言必须**清零**
        s10_old_cleared = "assert.match(viewportSource, /hasLockedMember/)" not in g84_code
        s10_ok = (s10_def and s10_call and s10_neg
                  and s10_neg_watch and s10_old_cleared)
        s10_detail = ("活代码里新写法：定义 %s ｜ 调用点 %s ｜ 有负向断言 %s ｜ "
                      "负向断言盯旧写法 %s ｜ 旧正向断言已清零 %s"
                      % (s10_def, s10_call, s10_neg, s10_neg_watch, s10_old_cleared))
    else:
        s10_ok = False
        s10_detail = "★ 缺 scripts/verify-liblib-batch84.mjs"
    record("S10 老门禁 84.mjs：判据已迁移（组锁定守卫改认 store ＋ 旧写法清零）",
           s10_ok, s10_detail)

    # ══════════════════════════════════════════════════════════════════
    # S11 ★ **老门禁 86.mjs 的判据迁移**（本批引入的第二条回归 ⟹ ⟹ 必须钉住）
    #
    # ★ ★ 背景：老门禁 `86.mjs` 写死了「`onPointerCancel={cancelTransform}` 出现 3 次、
    #   `onLostPointerCapture={cancelTransform}` 出现 2 次」
    #   ⟹ ⟹ 那 3 个挂点里有一个**就是组 gizmo**
    #   ⟹ ⟹ 本批按源站逐字删掉组 gizmo ⟹ ⟹ 写死的个数**前提过期**。
    # ★ ★ 而且「写死个数」这种判据**本身就有洞**：
    #   少一个 gizmo ⟹ 假红；多一个**不带** pointer cancel 的 gizmo ⟹ 照样绿。
    # ★ ★ 处理：改成**结构性**断言（每个 `<TransformControls>` 都必须带 pointer cancel；
    #   主变换 gizmo 唯一且带 lostPointerCapture；路径控制点 gizmo 唯一；
    #   组 rig 组件里**不允许**有 gizmo）。
    # ══════════════════════════════════════════════════════════════════
    gate86 = ROOT / "scripts/verify-liblib-batch86.mjs"
    if gate86.exists():
        g86 = gate86.read_text(encoding="utf-8")
        g86_code = "\n".join(
            ln for ln in g86.splitlines() if not ln.lstrip().startswith("//")
        )
        s11_blocks = "gizmoBlocks" in g86_code and "for (const block of gizmoBlocks)" in g86_code
        s11_main = "mainGizmos" in g86_code and "pathGizmos" in g86_code
        s11_neg = "assert.doesNotMatch" in g86_code and "DirectorGroupTransformRig" in g86_code
        # ★ ★ 旧的「写死个数」判据必须**清零**
        s11_old_cleared = "viewportSource.match(/onPointerCancel" not in g86_code
        s11_ok = s11_blocks and s11_main and s11_neg and s11_old_cleared
        s11_detail = ("活代码里结构性断言：逐挂点检查 %s ｜ 主/路径 gizmo 唯一性 %s ｜ "
                      "组 rig 负向断言 %s ｜ 旧的写死个数判据已清零 %s"
                      % (s11_blocks, s11_main, s11_neg, s11_old_cleared))
    else:
        s11_ok = False
        s11_detail = "★ 缺 scripts/verify-liblib-batch86.mjs"
    record("S11 老门禁 86.mjs：判据已迁移（写死个数 ⟹ 结构性断言 ＋ 旧写法清零）",
           s11_ok, s11_detail)

    # ══════════════════════════════════════════════════════════════════
    # S12 ★ **老门禁 852.py 的判据迁移**（本批引入的第三条回归 ⟹ ⟹ 必须钉住）
    #
    # ★ ★ 背景：老门禁 `852.py` 的 S9 写死了「**三处** TransformControls 都用
    #   `DIRECTOR_GRID_SNAP_STEP`」⟹ ⟹ 那个「三」的前提是「视口里有 3 个 gizmo
    #   （对象／组／路径控制点）」⟹ ⟹ ★ 本批按源站逐字**删掉了组 gizmo**
    #   ⟹ ⟹ 只剩 2 处 ⟹ ⟹ 旧断言的前提**过期** ⟹ ⟹ 旧断言红。
    # ★ ★ 处理：改成**结构性**断言「**每处** gizmo 都用它」
    #   （gizmo 挂点数 == 用步长的处数 ⟹ ⟹ 不再写死个数）
    #   ⟹ ⟹ 并**在计数前剥注释**（否则注释里那句
    #   「`<TransformControls mode={transformMode}>`」会被算成一处挂点）。
    # ══════════════════════════════════════════════════════════════════
    gate852 = ROOT / "scripts/verify-liblib-batch852.py"
    if gate852.exists():
        g852 = gate852.read_text(encoding="utf-8")
        g852_code = "\n".join(
            ln for ln in g852.splitlines() if not ln.lstrip().startswith("#")
        )
        s12_struct = ("gizmo_count" in g852_code
                      and "snap_count == gizmo_count" in g852_code)
        s12_strip = "live_viewport" in g852_code
        # ★ ★ 旧的「写死三处」必须**清零**
        s12_old_cleared = 'DIRECTOR_GRID_SNAP_STEP : null}") == 3' not in g852_code
        s12_ok = s12_struct and s12_strip and s12_old_cleared
        s12_detail = ("活代码里结构性断言 %s ｜ 计数前剥注释 %s ｜ "
                      "旧的写死三处已清零 %s"
                      % (s12_struct, s12_strip, s12_old_cleared))
    else:
        s12_ok = False
        s12_detail = "★ 缺 scripts/verify-liblib-batch852.py"
    record("S12 老门禁 852.py：判据已迁移（写死三处 ⟹ 每处 gizmo 都用吸附步长）",
           s12_ok, s12_detail)

    # ── 汇总 ──────────────────────────────────────────────────────────
    out_path = BATCH / "runtime-audit.json"
    out_path.write_text(
        json.dumps({"批次": 856, "判据": results}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    passed = sum(1 for r in results if r["通过"])
    print("\n%d/%d 条通过" % (passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 853 门禁：导演台的**打组／解组快捷键**（⌘G／⌘⇧G／⌘⇧D）。

## ★ 这批要守住的东西

★ 源站 chunk（`0fmehki05gkzw.js.js`）的**逐字实现**（机器提取，见
`raw/source-853-contract.json`，**16 个片段全部唯一命中**）：

```js
hY=new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])
&&("g"!==n||e.ctrlKey||e.metaKey)&&("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))
else if("g"===n||"d"===n)if(e.shiftKey){
  let e=nf.current.selectedGroupId;e&&rY(e)}else"g"===n&&rW()
function sg(e){return"character"===e||"prop"===e||"emptyObject"===e||"camera"===e}
function lT(e){return`${(0,tS.V)("canvas:nodeTypeGroup")}${e.length+1}`}
```

★ 源站实测（`raw/source-853-groupkeys.json`）：

- 只选 1 个 ⟹ 按 ⌘G **行数不变**（reducer 逐字 `r.length<2 ⟹ return e`）
- 选 2 个（⌘+点击 ⟹ additive）⟹ 按 ⌘G **树上多一行**（组行，带 lucide Group 图标）
- 成组后**成员缩进**（x 变大）⟹ 组是父子结构
- 按 ⌘D ⟹ **无变化**（`d` 要求 ⇧ ＋ ⌘）
- 按 ⌘⇧D ⟹ **解组** ⟹ 逐字回到基线

★ ★ 本门禁的 **S3 是「第二套独立实现」**：
★ 提取器用**递归下降**解析布尔表达式 ⟹ 门禁用**把 minified 条件翻译成 Python
★ 再 `eval`** 的办法**重算一遍**矩阵 ⟹ ⟹ 两条独立路径必须给出同一张表。
★ ⇒ 这是对「提取器自己算对了」的交叉验证，而不是自证。

## ★ 判据分工（★ 各条读的字段互不重叠 ⟹ 阴性每条只翻它自己那一条）

| 判据 | 读什么 | 阴性 |
| --- | --- | --- |
| S1 | clone 源码里的**结构**（纯函数／接线／依赖数组） | N1／N2 |
| S2 | 契约里**除两段 keydown 原文之外**的片段 | N8 |
| S3 | 契约里的**修饰键条件 ＋ 分支体 ＋ 矩阵**（门禁自己重算） | N9 |
| S4 | clone 纯函数 `resolveDirectorGroupShortcutAction` 的**运行时** | N3 |
| S5 | clone 读数 `③⌘D`（无变化） | N4 |
| S6 | clone 读数 `④⌘⇧D`（解组） | N5 |
| S7 | clone 读数 `⑦⌘G`（打组） | N6 |
| S8 | clone 读数 `⑧裸G`／`⑨裸D`（无变化） | N7 |
| S9 | clone 读数 `⑩⌘⇧G`（解组） | N10 |
| S10 | **源站**读数（`raw/source-853-groupkeys.json`） | N11 |
| S11 | clone 快捷键面板的两行 ＋ 源站面板片段 | N12 |
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch853-2026-10-01"
RAW = BATCH / "raw"

SRC_RULES = ROOT / "src/components/director/directorShortcutRules.ts"
SRC_DESK = ROOT / "src/components/director/DirectorDesk.tsx"
SRC_DIALOG = ROOT / "src/components/director/DirectorShortcutsDialog.tsx"

NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

results = []


def record(name, ok, detail):
    results.append({"判据": name, "通过": bool(ok), "详情": detail})
    print(("  PASS  " if ok else "  FAIL  ") + name + " ｜ " + detail)


# ══════════════════════════════════════════════════════════════════════════
# ★ S3 的**第二套独立实现**：把 minified 的条件**翻译成 Python** 再 eval
#   （提取器走的是递归下降解析器 ⟹ ⟹ 两条路径互相独立）
# ══════════════════════════════════════════════════════════════════════════
def derive_matrix_independently(gate: str, branch: str) -> list:
    """★ 输入＝契约里那两段**原文**；输出＝16 格矩阵。

    ★ 与提取器**不同的实现路线**：
      提取器 ＝ 手写递归下降解析器（自己处理括号与优先级）
      本函数 ＝ 把 `&&`/`||`/`!==` 翻译成 Python 的 `and`/`or`/`!=` 后直接 `eval`
    ⟹ ⟹ 两条路线对同一份原文必须给出同一张表。
    """
    if not re.search(r'if\(e\.shiftKey\)\{.*?\}else"g"===n&&rW\(\)', branch):
        raise ValueError("★ 分支体形状与预期不符：%r" % branch[:120])
    if '"g"===n||"d"===n' not in branch:
        raise ValueError("★ 分支体没有 g/d 双字母守卫")

    py = gate.strip()
    if py.startswith("&&"):
        py = py[2:]
    py = py.replace("&&", " and ").replace("||", " or ")
    py = py.replace("!==", " != ").replace("===", " == ")
    py = py.replace("e.ctrlKey", "ctrl").replace("e.metaKey", "meta")
    py = py.replace("e.shiftKey", "shift")
    py = re.sub(r"\bn\b", "key", py)
    py = "(" + py + ")"

    out = []
    for key in ("g", "d"):
        for ctrl in (False, True):
            for meta in (False, True):
                for shift in (False, True):
                    gate_ok = bool(eval(py, {"key": key, "ctrl": ctrl,
                                             "meta": meta, "shift": shift}))
                    if not gate_ok:
                        action = None
                    else:
                        # 分支体：带 ⇧ 一律解组；不带 ⇧ 时只有 g 打组
                        action = "ungroup" if shift else ("group" if key == "g" else None)
                    out.append({"按键": key, "Ctrl": ctrl, "Cmd": meta,
                                "Shift": shift, "动作": action})
    return out


def extract_function(source: str, name: str) -> str:
    """★ 从 TS 源码里抽出纯函数并**去掉类型标注** ⟹ 变成可执行的 JS。"""
    sig = "export function %s(" % name
    i = source.find(sig)
    if i < 0:
        raise SystemExit("★ 源码里找不到函数 %s" % name)
    j = source.find("{", source.find(")", i))
    if j < 0:
        raise SystemExit("★ 找不到函数体起点")
    depth = 0
    end = -1
    for k in range(j, len(source)):
        if source[k] == "{":
            depth += 1
        elif source[k] == "}":
            depth -= 1
            if depth == 0:
                end = k
                break
    if end < 0:
        raise SystemExit("★ 函数体花括号不配平")
    head = source[i:end + 1]
    head = head.replace("export function", "function", 1)
    head = re.sub(r":\s*DirectorGroupShortcutInput", "", head)
    head = re.sub(r"\)\s*:\s*DirectorGroupShortcutAction\s*\|\s*null", ")", head)
    head = re.sub(r":\s*DirectorGroupShortcutAction\s*\|\s*null", "", head)
    return head


def run_func_cases(js_text: str, cases: list):
    """★ 真正跑一次这些用例（node）⟹ ⟹ 不是「看代码像对的」。"""
    script = (
        js_text
        + "\nconst cases = " + json.dumps(cases, ensure_ascii=False) + ";\n"
        + "const out = cases.map(([k,m,s,e])=>"
          "[resolveDirectorGroupShortcutAction({key:k, modifier:m, shift:s}), e]);\n"
        + "console.log(JSON.stringify(out));\n"
    )
    tmp = RAW / ".func-cases.tmp.js"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(script, encoding="utf-8")
    try:
        proc = subprocess.run([str(NODE), str(tmp)], capture_output=True,
                              text=True, timeout=60)
    finally:
        if tmp.exists():
            tmp.unlink()
    if proc.returncode != 0:
        return None, (proc.stderr or "")[-500:]
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1]), None
    except Exception as exc:  # noqa: BLE001
        return None, "解析 node 输出失败：%s / %r" % (exc, proc.stdout[-300:])


def main() -> int:
    clone = json.loads((RAW / "clone-853-groupkeys.json").read_text(encoding="utf-8"))
    src = json.loads((RAW / "source-853-groupkeys.json").read_text(encoding="utf-8"))
    contract = json.loads((RAW / "source-853-contract.json").read_text(encoding="utf-8"))
    rules = SRC_RULES.read_text(encoding="utf-8")
    desk = SRC_DESK.read_text(encoding="utf-8")
    dialog = SRC_DIALOG.read_text(encoding="utf-8")
    frag = contract.get("片段", {})

    # ══ S1 结构
    need_rules = [
        "export type DirectorGroupShortcutAction",
        "export interface DirectorGroupShortcutInput",
        "export function resolveDirectorGroupShortcutAction",
    ]
    miss_r = [k for k in need_rules if k not in rules]
    need_desk = [
        'from "@/components/director/directorShortcutRules"',
        "resolveDirectorGroupShortcutAction",
        "groupSelectedCharacters",
        "ungroupSelectedCharacters",
        # ★ 判定必须真的走纯函数 ⟹ ⟹ 不能只是把 action 绑上就完事
        "const groupShortcut = resolveDirectorGroupShortcutAction({",
        'if (groupShortcut === "group") groupSelectedCharacters();',
        "else ungroupSelectedCharacters();",
    ]
    miss_d = [k for k in need_desk if k not in desk]
    record(
        "S1 结构：打组/解组纯函数 ＋ DirectorDesk 接线 ＋ 依赖数组都在",
        not miss_r and not miss_d,
        "rules缺=%s desk缺=%s" % (miss_r, miss_d),
    )

    # ══ S2 契约（★ 只读**除两段 keydown 原文之外**的片段 ⟹ 与 S3 互不重叠）
    checks = []
    for name in frag:
        checks.append(("片段唯一命中：%s" % name, frag[name].get("命中数") == 1))
    sg = (frag.get("可分组类别 sg(e)（character/prop/emptyObject/camera）") or {}).get("原文") or ""
    lt = (frag.get("组名 lT(e)＝ i18n(canvas:nodeTypeGroup) ＋ N") or {}).get("原文") or ""
    cg = (frag.get("右键菜单的 canGroup 判定式") or {}).get("原文") or ""
    menu = (frag.get("右键菜单「打组」项（disabled:!e.canGroup）") or {}).get("原文") or ""
    treeclick = (frag.get("树行的 onClick：⇧／⌘／Ctrl ＝ additive（且仅对 sg 类别）") or {}).get("原文") or ""
    hY = (frag.get("键集合 hY（字母快捷键白名单）") or {}).get("原文") or ""
    checks += [
        ("sg 可分组类别含 camera", '"camera"===e' in sg),
        ("sg 含 character/prop/emptyObject",
         all(('"%s"===e' % k) in sg for k in ("character", "prop", "emptyObject"))),
        ("lT 组名用 i18n(canvas:nodeTypeGroup)", '"canvas:nodeTypeGroup"' in lt),
        ("canGroup 要求 >1 且每项都 sg",
         "s.length>1&&s.every(e=>sg(e.category))" in cg),
        ("右键菜单打组项 disabled:!e.canGroup", "disabled:!e.canGroup" in menu),
        ("树行 additive 条件是 ⇧/⌘/Ctrl 三者之一",
         "t.shiftKey||t.metaKey||t.ctrlKey" in treeclick),
        ("树行 additive 只对 sg 类别生效",
         "sg(e.category)?{additive:r" in treeclick),
        ("hY 白名单含 g 与 d", '"g"' in hY and '"d"' in hY),
    ]
    bad = [n for n, v in checks if not v]
    record(
        "S2 契约：16 个片段唯一命中 ＋ 源站原文逐字对得上",
        not bad,
        "不符=%s（共 %d 项）" % (bad, len(checks)),
    )

    # ══ S3 矩阵（★ 门禁**自己重算** ⟹ ⟹ 与提取器交叉验证）
    gate_txt = (frag.get("keydown 里 hY 块的修饰键条件（g / d 两段）") or {}).get("原文") or ""
    branch_txt = (frag.get("keydown 里的 g/d 分支") or {}).get("原文") or ""
    stored = contract.get("★行为矩阵（由提取串推导）") or {}
    stored_rows = stored.get("组合") or []
    try:
        mine = derive_matrix_independently(gate_txt, branch_txt)
    except Exception as exc:  # noqa: BLE001
        mine = None
        err = str(exc)
    if mine is None:
        record("S3 矩阵：两套独立实现给出同一张表", False, "重算失败：%s" % err)
        mine = []
    else:
        def key_of(row):
            return (row["按键"], row["Ctrl"], row["Cmd"], row["Shift"])
        mine_map = {key_of(r): r["动作"] for r in mine}
        stored_map = {key_of(r): r["动作"] for r in stored_rows}
        diff = [k for k in mine_map if mine_map[k] != stored_map.get(k)]
        expect = {
            ("g", False, True, False): "group",
            ("g", False, True, True): "ungroup",
            ("d", False, True, True): "ungroup",
            ("d", False, True, False): None,
            ("g", False, False, False): None,
            ("d", False, False, False): None,
        }
        bad_expect = [k for k, v in expect.items() if mine_map.get(k) != v]
        ok3 = (not diff and len(stored_map) == len(mine_map)
               and not bad_expect)
        record(
            "S3 矩阵：提取器与门禁两套独立实现给出同一张表",
            ok3,
            "格数=%d/%d 两实现不一致=%s 关键格不符=%s"
            % (len(mine_map), len(stored_map), diff, bad_expect),
        )

    # ══ S4 纯函数运行时（期望值＝**契约矩阵**⟹ ⟹ 不是手打）
    cases = []
    for row in stored_rows:
        cases.append([row["按键"], bool(row["Ctrl"]) or bool(row["Cmd"]),
                      bool(row["Shift"]), row["动作"]])
    try:
        js = extract_function(rules, "resolveDirectorGroupShortcutAction")
        got, err = run_func_cases(js, cases)
    except SystemExit as exc:
        got, err = None, str(exc)
    if got is None:
        record("S4 纯函数：16 格动作表（node 实跑）", False, "跑不起来：%s" % err)
    else:
        mism = [{"用例": c[:3], "期望": c[3], "实得": g[0]}
                for c, g in zip(cases, got) if g[0] != c[3]]
        record(
            "S4 纯函数：16 格动作表（node 实跑，期望值取自契约矩阵）",
            not mism and len(got) == len(cases),
            "共 %d 条，不符=%s" % (len(cases), mism),
        )

    # ══ S5 ⌘D 必须**什么都不做**（★ 逐字段比较「按前／按后」）
    s5 = clone.get("③⌘D 不做") or {}
    b5, a5 = s5.get("按前") or {}, s5.get("按后") or {}
    same5 = bool(b5) and b5 == a5
    record(
        "S5 clone 按 ⌘D ⟹ **什么都不做**（逐字段比对按前/按后）",
        same5 and s5.get("实测动作") is None,
        "前后相同=%s 实测动作=%s 期望=%s"
        % (same5, s5.get("实测动作"), s5.get("期望动作")),
    )

    # ══ S6 ⌘⇧D 解组
    s6 = clone.get("④⌘⇧D 解组") or {}
    b6, a6 = s6.get("按前") or {}, s6.get("按后") or {}
    cmd6 = (a6.get("最后命令") or {})
    ok6 = (
        b6.get("DOM组数") == 1 and a6.get("DOM组数") == 0
        and b6.get("store选中组") is not None and a6.get("store选中组") is None
        and b6.get("store组数") == 1 and a6.get("store组数") == 0
        and cmd6.get("kind") == "DELETE_GROUP"
        and cmd6.get("disposition") == "COMMITTED"
        and s6.get("实测动作") == "ungroup"
    )
    record(
        "S6 clone 按 ⌘⇧D ⟹ 解组（DOM 组数 1→0 ＋ store 选中组清空 ＋ DELETE_GROUP）",
        ok6,
        "DOM组数=%s→%s store选中组=%s→%s 最后命令=%s"
        % (b6.get("DOM组数"), a6.get("DOM组数"), b6.get("store选中组"),
           a6.get("store选中组"), cmd6.get("kind")),
    )

    # ══ S7 ⌘G 打组
    s7 = clone.get("⑦⌘G 打组") or {}
    b7, a7 = s7.get("按前") or {}, s7.get("按后") or {}
    cmd7 = (a7.get("最后命令") or {})
    ok7 = (
        b7.get("DOM组数") == 0 and a7.get("DOM组数") == 1
        and b7.get("store选中组") is None and a7.get("store选中组") is not None
        and b7.get("store选中数") == 2 and a7.get("store选中数") == 2
        and a7.get("选择类别") == "group"
        and cmd7.get("kind") == "GROUP_CHARACTERS"
        and cmd7.get("disposition") == "COMMITTED"
        and s7.get("实测动作") == "group"
    )
    record(
        "S7 clone 按 ⌘G ⟹ 打组（DOM 组数 0→1 ＋ 选中组指向新组 ＋ GROUP_CHARACTERS）",
        ok7,
        "DOM组数=%s→%s store选中组=%s→%s 选中数=%s 最后命令=%s/%s"
        % (b7.get("DOM组数"), a7.get("DOM组数"), b7.get("store选中组"),
           a7.get("store选中组"), a7.get("store选中数"),
           cmd7.get("kind"), cmd7.get("disposition")),
    )

    # ══ S8 裸 G ／ 裸 D 必须**什么都不做**（★ 两组各读各的字段）
    s8g = clone.get("⑧裸G 不做") or {}
    s8d = clone.get("⑨裸D 不做") or {}
    bg, ag = s8g.get("按前") or {}, s8g.get("按后") or {}
    bd, ad = s8d.get("按前") or {}, s8d.get("按后") or {}
    ok8 = (bool(bg) and bg == ag and s8g.get("实测动作") is None
           and bool(bd) and bd == ad and s8d.get("实测动作") is None)
    record(
        "S8 clone 裸 G ／ 裸 D ⟹ **什么都不做**（两组各逐字段比对）",
        ok8,
        "裸G前后相同=%s(%s) 裸D前后相同=%s(%s)"
        % (bg == ag, s8g.get("实测动作"), bd == ad, s8d.get("实测动作")),
    )

    # ══ S9 ⌘⇧G 解组（★ 源站**未在面板列出**的别名）
    s9 = clone.get("⑩⌘⇧G 解组") or {}
    b9, a9 = s9.get("按前") or {}, s9.get("按后") or {}
    cmd9 = (a9.get("最后命令") or {})
    ok9 = (
        b9.get("DOM组数") == 1 and a9.get("DOM组数") == 0
        and b9.get("store选中组") is not None and a9.get("store选中组") is None
        and cmd9.get("kind") == "DELETE_GROUP"
        and s9.get("实测动作") == "ungroup"
    )
    record(
        "S9 clone 按 ⌘⇧G ⟹ 解组（★ 源站面板没列这个别名，但逐字行为成立）",
        ok9,
        "DOM组数=%s→%s store选中组=%s→%s 最后命令=%s"
        % (b9.get("DOM组数"), a9.get("DOM组数"), b9.get("store选中组"),
           a9.get("store选中组"), cmd9.get("kind")),
    )

    # ══ S10 源站实测（★ 读**源站** raw ⟹ 与 clone 各判据互不重叠）
    base_labels = src.get("①基线标签") or []
    single_delta = src.get("②单选按⌘G行数变化")
    group_labels = src.get("③双选按⌘G后标签") or []
    group_rows = src.get("③双选按⌘G后行") or []
    base_rows = src.get("①基线行") or []
    delta = src.get("③行数变化")
    d_noop = src.get("④⌘D有变化")
    ungroup_delta = src.get("⑤行数变化")
    back_to_base = src.get("⑤回到基线")
    end_labels = src.get("⑥结束时标签") or []

    new_labels = [x for x in group_labels if x not in base_labels]
    # ★ 缩进：**不写死 16px** ⟹ ⟹ 断言「**被点的那两行**都朝同一个方向偏移，
    #   偏移量彼此相等且 > 0」＋「**没被点的行**偏移量 == 0」
    #   ⟹ ⟹ 这才是在断言「组是父子结构、且只有成员被缩进」。
    picked = src.get("③选中的两行标签") or []
    base_x = {r["label"]: r["x"] for r in base_rows}
    after_x = {r["label"]: r["x"] for r in group_rows}
    member_indent = [after_x[l] - base_x[l] for l in picked
                     if l in base_x and l in after_x]
    others = [l for l in base_labels if l not in picked]
    other_indent = [after_x[l] - base_x[l] for l in others
                    if l in base_x and l in after_x]
    new_row = next((r for r in group_rows if r["label"] in new_labels), None)
    base_icons = {r["icon"] for r in base_rows}
    ok10 = (
        len(base_labels) >= 2
        and len(picked) == 2
        and single_delta == 0
        and delta == 1
        and len(new_labels) == 1
        and new_row is not None
        and new_row["icon"] not in base_icons
        and len(member_indent) == 2
        and len(set(member_indent)) == 1
        and member_indent[0] > 0
        and len(other_indent) == len(others)
        and all(x == 0 for x in other_indent)
        and d_noop is False
        and ungroup_delta == 0
        and back_to_base is True
        and end_labels == base_labels
    )
    record(
        "S10 源站实测：⌘G 建组（只有成员被缩进）＋ ⌘D 无 ＋ ⌘⇧D 解组回到基线",
        ok10,
        "单选⌘GΔ=%s 双选⌘GΔ=%s 新行=%s 成员缩进=%s 非成员缩进=%s "
        "⌘D有变化=%s 解组Δ=%s 回基线=%s"
        % (single_delta, delta, new_labels, member_indent, other_indent,
           d_noop, ungroup_delta, back_to_base),
    )

    # ══ S11 面板文案（★ clone 的两行 ＋ 源站面板片段逐字比对）
    panel_src = (frag.get("快捷键面板：打组 ⌘G ＋ 解组 ⌘⇧D 两行") or {}).get("原文") or ""
    src_tuples = re.findall(
        r'\{id:"([^"]+)"(?:,icon:"([^"]*)")?(?:,label:"([^"]*)")?\}', panel_src)
    src_tuples = [(a, b or c) for (a, b, c) in src_tuples]

    def clone_rows(label):
        m = re.search(r'label: "%s",\s*keys: \[(.*?)\]' % label, dialog, re.S)
        if not m:
            return None
        out = []
        for mm in re.finditer(
                r'\{ id: "([^"]+)"(?:, icon: "([^"]*)")?(?:, label: "([^"]*)")? \}',
                m.group(1)):
            out.append((mm.group(1), mm.group(2) or mm.group(3)))
        return out

    clone_group = clone_rows("打组")
    clone_ungroup = clone_rows("解组")
    got_tuples = list(clone_group or []) + list(clone_ungroup or [])

    # ★★ 「打组」那行的字母**不是手打的** ⟹ ⟹ 从**分支体原文**里推出来：
    #    `else"g"===n&&rW()` ⟹ 那个 `g` 就是「不带 ⇧ 时会打组」的字母
    m_letter = re.search(r'else"([a-z])"===n&&\w+\(\)', branch_txt)
    group_letter = (m_letter.group(1).upper() if m_letter else None)
    src_map = dict(src_tuples)
    ok11 = (
        len(src_tuples) == 5
        and group_letter is not None
        and src_map.get("group-key") == group_letter
        and src_map.get("group-command") == "command"
        and src_map.get("ungroup-command") == "command"
        and src_map.get("ungroup-shift") == "⇧"
        and "ungroup-key" in src_map
        and got_tuples == src_tuples
        and 'label: "打组"' in dialog and 'label: "解组"' in dialog
    )
    record(
        "S11 面板：打组 ⌘G ／ 解组 ⌘⇧D 两行与源站逐字一致",
        ok11,
        "打组字母(从分支体推)=%s 源站=%s clone=%s"
        % (group_letter, src_tuples, got_tuples),
    )

    passed = sum(1 for r in results if r["通过"])
    total = len(results)
    report = {
        "批次": 853,
        "通过数": passed,
        "判据总数": total,
        # ★ 键名与 851／852 的门禁**一致**（「判据」）⟹ ⟹ 阴性脚本读同一套键
        "判据": results,
    }
    (BATCH / "runtime-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n== batch 853 门禁：%d/%d 通过 ==" % (passed, total))
    if passed != total:
        print("★ 有判据未通过")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

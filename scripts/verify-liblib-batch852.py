#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 852 门禁：导演台的**变换类快捷键**（V／R／F）与**网格吸附**（X）。

## ★ 这批要守住的东西

★ 源站 chunk（`0fmehki05gkzw.js.js`）的**逐字实现**（机器提取，见
`raw/source-852-contract.json`，17 个片段全部唯一命中）：

```js
hY=new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])
...
else if("v"===n)iW("translate");
else if("r"===n)iW("rotate");
else if("f"===n)iW("scale");
else if("x"===n)eT(e=>!e);
...
let iW=(0,o.useCallback)(e=>{
  if(t4&&im(),
     "emptyObject"===nf.current.selectedCategory&&"translate"!==e){
    tl("translate"),af.setMode("translate");return}
  tl(e),af.setMode(e)},[im,t4,af]);
...
function p7(e,t){e.translationSnap=t?1:null}
```

★ 源站实测（`raw/source-852-transformkeys.json`）：

- 按 R ⟹ 下拉里 active 项从「移动/V」变成「旋转/R」⟹ 模式 translate→rotate
- 按 F ⟹ rotate→scale（「缩放/F」）
- 按 V ⟹ scale→translate
- Shift+V ⟹ rotate→translate（★ 源站对 `v` **没有**修饰键限制）
- 按 X ⟹ 右栏「网格吸附」`aria-checked` false→true；再按 ⟹ true→false（是**翻转**不是置位）
- ★ 装在 document 冒泡阶段的监听器**一个键都没收到** ⟹ 源站在 window 捕获阶段
  `stopPropagation()+stopImmediatePropagation()` ⟹ **导演台吞掉所有按键**

## ★ 判据分工（★ 各条读的字段互不重叠）

| 判据 | 读什么 |
| --- | --- |
| S1 | clone 源码里的**结构**（组件／函数／常量／data 属性） |
| S2 | **源站原文**契约（`raw/source-852-contract.json` 的 17 个片段） |
| S3 | clone 纯函数 `resolveDirectorTransformShortcutMode` 的**运行时**行为 |
| S4 | clone 读数 `②按R` 的 DOM 模式 |
| S5 | clone 读数 `②按F` 的 DOM 模式 |
| S6 | clone 读数 `②按V` 的 DOM 模式 |
| S7 | clone 读数 `③Shift+V` 的 DOM 模式 |
| S8 | clone 读数 `⑤按X` 的 DOM 开关 |
| S9 | clone 源码里的**吸附步长**（源站 `p7` 逐字 = 1） |
| S10 | **源站**读数（`raw/source-852-transformkeys.json`） |
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch852-2026-10-01"
RAW = BATCH / "raw"

SRC_VIEWPORT = ROOT / "src/components/director/DirectorViewport.tsx"
SRC_MATH = ROOT / "src/components/director/directorViewportMath.ts"

NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

# ★ 纯函数的 6 条用例（期望值来自**源站 chunk 的守卫规则**，不是我自己编的）
FUNC_CASES = [
    ("rotate", "emptyObject", "translate"),
    ("scale", "emptyObject", "translate"),
    ("translate", "emptyObject", "translate"),
    ("rotate", "character", "rotate"),
    ("scale", None, "scale"),
    ("translate", "prop", "translate"),
]

results = []


def record(name, ok, detail):
    results.append({"判据": name, "通过": bool(ok), "详情": detail})
    print(("  PASS  " if ok else "  FAIL  ") + name + " ｜ " + detail)


def extract_function(source: str, name: str):
    """★ 从 TS 源码里抽出纯函数并**去掉类型标注** ⟹ 变成可执行的 JS。

    ★ 只做**两处**精确替换（参数标注 ＋ 返回类型）⟹ 替换前先核对函数签名逐字存在，
    签名对不上就抛错 ⟹ 不会「悄悄抽出一段别的代码」。
    """
    sig = "export function %s(" % name
    i = source.find(sig)
    if i < 0:
        raise SystemExit("★ 源码里找不到函数 %s" % name)
    # 找函数体：从第一个 `{`（参数列表之后）开始按花括号配平
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
    head = re.sub(r":\s*DirectorTransformMode", "", head)
    head = re.sub(r":\s*DirectorTransformShortcutCategory", "", head)
    return head


def run_func_cases(js_text: str):
    """★ 真正跑一次这 6 条用例（node）⟹ ⟹ 不是「看代码像对的」"""
    cases = json.dumps(FUNC_CASES, ensure_ascii=False)
    script = (
        js_text
        + "\nconst cases = "
        + cases
        + ";\nconst out = cases.map(([r,c,e])=>[resolveDirectorTransformShortcutMode(r,c),e]);\n"
        + "console.log(JSON.stringify(out));\n"
    )
    tmp = BATCH / "raw" / ".func-cases.tmp.js"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(script, encoding="utf-8")
    try:
        proc = subprocess.run(
            [str(NODE), str(tmp)],
            capture_output=True, text=True, timeout=60,
        )
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
    clone = json.loads((RAW / "clone-852-transformkeys.json").read_text(encoding="utf-8"))
    src = json.loads((RAW / "source-852-transformkeys.json").read_text(encoding="utf-8"))
    contract = json.loads((RAW / "source-852-contract.json").read_text(encoding="utf-8"))
    viewport = SRC_VIEWPORT.read_text(encoding="utf-8")
    math = SRC_MATH.read_text(encoding="utf-8")

    # ══ S1 结构
    need_viewport = [
        "DirectorViewShortcutController",
        "resolveDirectorTransformShortcutMode",
        "DIRECTOR_TRANSFORM_SHORTCUT_MODES",
        "DIRECTOR_GRID_SNAP_STEP",
        "applyTransformShortcut",
        # ★ 带等号 ⟹ ⟹ 精确到「属性赋值」⟹ ⟹ 否则 `data-director-transform-mode2`
        #   仍会被子串匹配命中 ⟹ ⟹ 阴性就没有牙了。
        "data-director-transform-mode={mode}",
        "updateScene({ snapToGrid: !snapToGrid })",
    ]
    miss_v = [k for k in need_viewport if k not in viewport]
    need_math = [
        "DIRECTOR_TRANSFORM_SHORTCUT_MODES",
        "DIRECTOR_GRID_SNAP_STEP",
        "resolveDirectorTransformShortcutMode",
        "DirectorTransformShortcutCategory",
    ]
    miss_m = [k for k in need_math if k not in math]
    record(
        "S1 结构：变换快捷键 ＋ 吸附步长 ＋ 纯函数都在 clone 源码里",
        not miss_v and not miss_m,
        "viewport缺=%s math缺=%s" % (miss_v, miss_m),
    )

    # ══ S2 源站原文契约（★ 期望值来自**入库的源站原文**，不是手打）
    frag = contract.get("片段", {})
    hY = (frag.get("键集合 hY（字母快捷键白名单）") or {}).get("原文") or ""
    branch = (frag.get("keydown 里的分支链（v/r/f/x）") or {}).get("原文") or ""
    iw = (frag.get("iW：变换模式切换（含 emptyObject 守卫）") or {}).get("原文") or ""
    p7 = (frag.get("p7：把吸附写进 gizmo（translationSnap）") or {}).get("原文") or ""
    toolbar = (frag.get("底部工具栏的变换模式表 R") or {}).get("原文") or ""
    eT = (frag.get("吸附 state：[eI,eT]=useState(false)") or {}).get("原文") or ""
    checks = [
        ("hY 白名单含 f（★ F 可达）", '"f"' in hY),
        ("hY 白名单含 v/r/x", all('"%s"' % k in hY for k in ("v", "r", "x"))),
        ("分支链有 iW(\"translate\")", 'iW("translate")' in branch),
        ("分支链有 iW(\"rotate\")", 'iW("rotate")' in branch),
        ("分支链有 iW(\"scale\")", 'iW("scale")' in branch),
        ("分支链有 eT(e=>!e)", "eT(e=>!e)" in branch),
        ("iW 含 emptyObject 守卫", '"emptyObject"===nf.current.selectedCategory' in iw),
        ("iW 含 t4&&im() 前置", "t4&&im()" in iw),
        ("p7 吸附步长 = 1", "e.translationSnap=t?1:null" in p7),
        ("吸附 state 是 useState(false)", "[eI,eT]=(0,o.useState)(!1)" in eT),
        ("工具栏键位表 translate/V", 'mode:"translate"' in toolbar and 'shortcut:"V"' in toolbar),
        ("工具栏键位表 rotate/R", 'mode:"rotate"' in toolbar and 'shortcut:"R"' in toolbar),
        ("工具栏键位表 scale/F", 'mode:"scale"' in toolbar and 'shortcut:"F"' in toolbar),
    ]
    bad = [n for n, v in checks if not v]
    record(
        "S2 契约：源站原文里 V/R/F/X 的实现逐字对得上",
        not bad,
        "不符=%s（共 %d 项）" % (bad, len(checks)),
    )

    # ══ S3 纯函数运行时
    try:
        js = extract_function(math, "resolveDirectorTransformShortcutMode")
        got, err = run_func_cases(js)
    except SystemExit as exc:
        got, err = None, str(exc)
    if got is None:
        record("S3 纯函数：emptyObject 守卫的 6 条用例", False, "跑不起来：%s" % err)
    else:
        mism = [
            {"用例": [r, c, e], "实得": g}
            for (r, c, e), (g, _) in zip(FUNC_CASES, got)
            if g != e
        ]
        record(
            "S3 纯函数：emptyObject 守卫的 6 条用例（node 实跑）",
            not mism,
            "共 %d 条，不符=%s" % (len(FUNC_CASES), mism),
        )

    # ══ S4／S5／S6 三条变换模式（★ 各读一条 clone 读数，字段互不重叠）
    for key, mode, label in [("R", "rotate", "S4"), ("F", "scale", "S5"), ("V", "translate", "S6")]:
        rec = clone.get("②按%s" % key) or {}
        dom = ((rec.get("按后") or {}).get("DOM") or {})
        store = (rec.get("按后") or {}).get("store") or {}
        ok = (
            rec.get("期望模式") == mode
            and dom.get("模式") == mode
            and store.get("transformMode") == mode
            and rec.get("两条一致") is True
        )
        record(
            "%s clone 按 %s ⟹ 变换模式**等于** %s" % (label, key, mode),
            ok,
            "DOM=%s store=%s 期望=%s 两条一致=%s"
            % (dom.get("模式"), store.get("transformMode"), rec.get("期望模式"),
               rec.get("两条一致")),
        )

    # ══ S7 Shift+V
    s7 = clone.get("③Shift+V") or {}
    dom7 = ((s7.get("按后") or {}).get("DOM") or {})
    before7 = ((s7.get("按前") or {}).get("DOM") or {})
    ok7 = (
        before7.get("模式") == "rotate"
        and dom7.get("模式") == "translate"
        and s7.get("DOM模式对") is True
    )
    record(
        "S7 clone Shift+V ⟹ 从 rotate 切到 translate（★ 源站对 v 无修饰键限制）",
        ok7,
        "按前=%s 按后=%s DOM模式对=%s"
        % (before7.get("模式"), dom7.get("模式"), s7.get("DOM模式对")),
    )

    # ══ S8 X 翻转网格吸附
    s8 = clone.get("⑤按X") or {}
    b8 = s8.get("按前") or {}
    m8 = s8.get("按后一次") or {}
    a8 = s8.get("按后两次") or {}
    ok8 = (
        b8.get("值") == "false"
        and m8.get("值") == "true"
        and a8.get("值") == "false"
        and s8.get("★首次翻转") is True
        and s8.get("★再按翻回") is True
        and s8.get("★往返一致") is True
        and s8.get("★两条通路一致") is True
    )
    record(
        "S8 clone 按 X ⟹ 网格吸附 false→true→false（DOM 开关 ＋ store 两条路）",
        ok8,
        "值=%s→%s→%s 来源=%s 两条路一致=%s"
        % (b8.get("值"), m8.get("值"), a8.get("值"), b8.get("来源"),
           s8.get("★两条通路一致")),
    )

    # ══ S9 吸附步长（源站 p7 逐字 = 1）
    # ★ ★ ★ Batch 856 **判据迁移**：原来写死「**三处** TransformControls 都用它」
    #   ⟹ ⟹ 那个「三」的前提是「视口里有 3 个 gizmo（对象／组／路径控制点）」
    #   ⟹ ⟹ ★ 本批按源站逐字**删掉了组 gizmo**（源站没有组 gizmo）
    #   ⟹ ⟹ 只剩 2 处 ⟹ ⟹ 旧断言的前提**过期** ⟹ ⟹ 旧断言红。
    # ★ ★ 改成**结构性**断言：「**每处** gizmo 都用 `DIRECTOR_GRID_SNAP_STEP`」
    #   ⟹ ⟹ 不再写死个数 ⟹ ⟹ 以后再加／减 gizmo 都不用改这条。
    # ★ ★ 计数**必须先剥注释** ⟹ ⟹ 否则注释里那句
    #   「`<TransformControls mode={transformMode}>`」会被算成一处挂点 ⟹ ⟹ 假红。
    live_viewport = re.sub(r"/\*[\s\S]*?\*/", "", viewport)
    live_viewport = re.sub(r"(^|[^:])//.*$", r"\1", live_viewport, flags=re.M)
    gizmo_count = live_viewport.count("<TransformControls")
    snap_count = live_viewport.count(
        "translationSnap={snapToGrid ? DIRECTOR_GRID_SNAP_STEP : null}")
    step_ok = (
        "DIRECTOR_GRID_SNAP_STEP = 1" in math
        and gizmo_count >= 1
        and snap_count == gizmo_count
        and "snapToGrid ? 0.5" not in live_viewport
    )
    record(
        "S9 吸附步长 = 1（源站 p7 逐字），clone 每处 TransformControls 都用它",
        step_ok,
        "math里=%s viewport里 gizmo 挂点=%d 处 用步长的=%d 处 相等=%s 残留0.5=%s"
        % ("DIRECTOR_GRID_SNAP_STEP = 1" in math,
           gizmo_count, snap_count, snap_count == gizmo_count,
           "snapToGrid ? 0.5" in live_viewport),
    )

    # ══ S10 源站侧证据
    src_checks = []
    for key, frm, to in [("R", "translate", "rotate"), ("F", "rotate", "scale"),
                         ("V", "scale", "translate")]:
        rec = src.get("④按%s" % key) or {}
        bf = (rec.get("按前") or {}).get("模式") or {}
        af = (rec.get("按后") or {}).get("模式") or {}
        src_checks.append(
            ("源站按%s ⟹ %s→%s" % (key, frm, to),
             bf.get("模式") == frm and af.get("模式") == to
             and bf.get("两条一致") is True and af.get("两条一致") is True
             and rec.get("svg变了") is True)
        )
    s5 = src.get("⑤Shift+V") or {}
    src_checks.append(
        ("源站 Shift+V ⟹ rotate→translate",
         ((s5.get("按前模式") or {}).get("模式")) == "rotate"
         and ((s5.get("按后模式") or {}).get("模式")) == "translate")
    )
    s6 = src.get("⑥按X") or {}
    src_checks.append(
        ("源站按 X ⟹ 「网格吸附」false→true→false",
         s6.get("翻转项数") == 1
         and ((s6.get("翻转项") or [{}])[0]).get("文本") == "网格吸附"
         and ((s6.get("翻转项") or [{}])[0]).get("前") == "false"
         and ((s6.get("翻转项") or [{}])[0]).get("后") == "true"
         and len(s6.get("再按翻转项") or []) == 1)
    )
    src_checks.append(
        ("源站在 window 捕获阶段掐断所有按键（冒泡阶段收到 0 个）",
         src.get("⑦冒泡阶段收到数") == 0)
    )
    bad_src = [n for n, v in src_checks if not v]
    record(
        "S10 源站实测：R/F/V 三步成链 ＋ Shift+V ＋ X 翻转 ＋ 吞按键",
        not bad_src,
        "不符=%s（共 %d 项）" % (bad_src, len(src_checks)),
    )

    passed = sum(1 for r in results if r["通过"])
    total = len(results)
    report = {
        "批次": 852,
        "通过数": passed,
        "判据总数": total,
        # ★ 键名与 batch 851 的门禁**一致**（「判据」）⟹ ⟹ 阴性脚本读同一套键
        "判据": results,
    }
    (BATCH / "runtime-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n== batch 852 门禁：%d/%d 通过 ==" % (passed, total))
    if passed != total:
        print("★ 有判据未通过")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

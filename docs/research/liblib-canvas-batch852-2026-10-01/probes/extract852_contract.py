#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 852 契约提取器：**从源站 chunk 机器提取**变换类快捷键（V/R/F/X）的逐字实现。

## 为什么要有这一步

★ 本批要复刻的是**行为**，而行为写死在源站 chunk（`0fmehki05gkzw.js.js`）里。
★ 只靠「面板上印着 V/R/F/X」去实现 = **拿 UI 文字当规格**，那是推断不是测量。
★ 所以先逐字取出源站实现，**入库**成 `raw/source-852-contract.json`，
★ 后面的门禁与 README 都引用这份**源站原文**（而不是我手写的期望值）。

## ★ 提取纪律

1. 每个片段用**锚点**（唯一子串）定位 ⟹ 命中数**必须恰好 1** ⟹ 否则记 `命中数` 并置空。
   ★ 「命中数 != 1」不许静默取第一条 —— 那是把「猜到的」当「测到的」。
2. 片段**逐字**复制（含标点），不改写、不省略（除非片段本身很短）。
3. 记录**字节偏移**，便于回溯。
4. ★ 提取出的文本**不允许含截断的 Tailwind 任意值类名**（`xxx-[…`）⟹
   本文件的锚点都选在**逻辑代码**上，不选 JSX 里的 className 长串。

## 输出

  raw/source-852-contract.json
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch852-2026-10-01"
RAW = BATCH / "raw"
CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")

# ★ 锚点 → (键名, 锚点后面要取多少字符)
#   ★ 锚点都是**逻辑代码**里的唯一子串；取长固定 ⟹ 便于逐字核对。
SPECS = [
    ("keydown 里 hY 块的修饰键条件",
     'if(hY.has(n)&&("z"!==n||e.ctrlKey||e.metaKey)',
     240),
    ("keydown 里的分支链（v/r/f/x）",
     'else if("v"===n)iW("translate");',
     200),
    ("iW：变换模式切换（含 emptyObject 守卫）",
     'let iW=(0,o.useCallback)(e=>{if(t4&&im(),',
     200),
    ("变换模式 state：[ts,tl]=useState(\"translate\")",
     '[ts,tl]=(0,o.useState)("translate")',
     0),
    ("吸附 state：[eI,eT]=useState(false)",
     '[eI,eT]=(0,o.useState)(!1)',
     0),
    ("吸附 state 接到 3D 场景：snapEnabled:eI",
     '{snapEnabled:eI,gaussianGroundSnapEnabled:',
     0),
    ("p7：把吸附写进 gizmo（translationSnap）",
     'function p7(e,t){e.translationSnap=t?1:null}',
     0),
    ("ha：gizmo setMode + scale 时隐藏 Y 轴",
     'function ha(e,t,r){e.setMode(t),e.showY=!(r&&"scale"===t)}',
     0),
    ("gizmo 管理器 setMode：eh",
     'eh=(0,o.useCallback)(e=>{m.current=e,',
     120),
    ("底部工具栏的变换模式表 R",
     'R=[{mode:"translate",label:k("canvas:directorTransformMove"),shortcut:"V"},',
     220),
    ("工具栏下拉的 active 判定（class）",
     'e===n.mode&&"bg-white/8 text-white"',
     0),
    ("工具栏折叠按钮：aria-haspopup=menu",
     '"aria-haspopup":"menu","aria-expanded":S',
     0),
    ("环境面板开关 lb：role=switch + aria-checked",
     'function lb({label:e,checked:t,onToggle:r,compact:n=!1}){return(0,i.jsxs)("button",{type:"button",role:"switch","aria-checked":t',
     0),
    ("t4：正在编辑的运动路径状态",
     '[t4,t8]=(0,o.useState)(null)',
     0),
    ("im：提交正在编辑的运动路径",
     'im=(0,o.useCallback)(()=>{t8(e=>{if(!e)return null;',
     120),
]

# ★ 正则提取：**键集合**这种「元素列表」必须用正则整段取，
#   绝不能手抄 —— ★★ 手抄终端输出时**漏过一个字符**就会得出相反的结论
#   （本批就真踩到了：手抄的 hY 少了 "f" ⟹ 差点误判「F 是死代码」）。
REGEX_SPECS = [
    ("键集合 hY（字母快捷键白名单）", r'hY=new Set\(\[[^\]]*\]\)'),
    ("键集合 hX（视口平移键）", r'hX=new Set\(\[[^\]]*\]\)'),
]


def main() -> int:
    if not CHUNK.exists():
        print("★ 源站 chunk 不存在：", CHUNK)
        return 2
    text = CHUNK.read_text(encoding="utf-8", errors="replace")
    out = {
        "来源": {
            "chunk": str(CHUNK),
            "字节数": len(text.encode("utf-8")),
        },
        "片段": {},
    }
    bad = []
    for name, anchor, tail in SPECS:
        hits = [m.start() for m in re.finditer(re.escape(anchor), text)]
        rec = {
            "锚点": anchor,
            "命中数": len(hits),
            "偏移": hits[0] if len(hits) == 1 else None,
            "原文": None,
        }
        if len(hits) == 1:
            start = hits[0]
            rec["原文"] = text[start:start + len(anchor) + tail]
        else:
            bad.append((name, len(hits)))
        out["片段"][name] = rec

    for name, pattern in REGEX_SPECS:
        hits = list(re.finditer(pattern, text))
        rec = {
            "正则": pattern,
            "命中数": len(hits),
            "偏移": hits[0].start() if len(hits) == 1 else None,
            "原文": hits[0].group(0) if len(hits) == 1 else None,
        }
        if len(hits) != 1:
            bad.append((name, len(hits)))
        out["片段"][name] = rec

    # ★ 自检：提取出的片段里不许出现**截断**的 Tailwind 任意值类名
    #   （`xxx-[` 后面没有闭合的 `]`）⟹ 文档/JSON 入库后不会生成坏 CSS。
    arb = []
    for name, rec in out["片段"].items():
        src = rec["原文"] or ""
        for m in re.finditer(r"[A-Za-z0-9_:/\[\]().,#%!-]*-\[[^\]\s\"']*", src):
            frag = m.group(0)
            if not frag.endswith("]"):
                arb.append((name, frag))
    out["★任意值类名自检"] = {
        "疑似截断": arb,
        "通过": not arb,
    }

    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "source-852-contract.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print("已落盘：", path)
    ok = 0
    for name, rec in out["片段"].items():
        flag = "OK " if rec["命中数"] == 1 else "BAD"
        if rec["命中数"] == 1:
            ok += 1
        print("  [%s] %-46s 命中=%d" % (flag, name, rec["命中数"]))
    print("唯一命中：%d / %d" % (ok, len(SPECS)))
    print("任意值类名自检：", "通过" if not arb else ("★ 疑似截断 %r" % (arb,)))
    if bad:
        print("★★ 锚点未唯一命中：", bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

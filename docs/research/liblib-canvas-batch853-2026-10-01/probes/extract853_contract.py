#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 853 契约提取器：**从源站 chunk 机器提取**打组／解组快捷键的逐字实现。

## ★ 为什么要机器提取（★ 852 已经吃过一次亏）

★ 852 我把 `hY` 键位白名单**手抄**进提取脚本 ⟹ ⟹ 漏掉了 `"f"` ⟹ ⟹ 一度得出
「F 是死代码」的错误结论 ⟹ ⟹ 是「锚点必须恰好命中 1 次」这条纪律当场拦住。
★ 所以本批的契约**一律整段机器提取** ⟹ ⟹ 不手抄任何字面量。

## ★ 提取纪律（沿用 852）

1. 每个锚点**必须恰好命中 1 次** ⟹ 否则记 `命中数` 并置空（不许静默取第一条）。
2. 片段**逐字**复制，记录**字节偏移**。
3. 片段里不许出现**截断**的 Tailwind 任意值类名（缺右方括号的形式）。

## ★★ 本批新增：**行为矩阵由提取串推导**，不是手打

★ 关键的两段（修饰键条件 ＋ 分支体）是**从 chunk 里逐字取出来**的；
★ 下面的 `derive_behavior_matrix()` 是一个**通用的小解释器**：
★   输入 ＝ 那两段**提取出来的字符串**，输出 ＝ 12 种按键组合各自的动作。
★ ⇒ 也就是说：矩阵是**算出来的**，不是人写上去的。
★ ⇒ 而源站探针（`source853_groupkeys.py`）是**独立**的实测通路 ⟹ 两条路互相印证。

## 输出

  raw/source-853-contract.json
"""
import itertools
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch853-2026-10-01"
RAW = BATCH / "raw"
CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")

# ── 逐字锚点：(名字, 锚点串, 追加尾巴长度) ─────────────────────────────────
SPECS = [
    ("hook 返回值里的绑定：createCharacterGroup→rW / ungroupCharacterGroup→rY",
     "createCharacterGroup:rW,selectCharacterGroup:r$,ungroupCharacterGroup:rY",
     0),
    ("reducer 回调 u：CREATE_CHARACTER_GROUP",
     'u=(0,o.useCallback)(e=>r({type:"CREATE_CHARACTER_GROUP",members:e}),[])',
     0),
    ("reducer 回调 h：UNGROUP_CHARACTER_GROUP",
     'h=(0,o.useCallback)(e=>r({type:"UNGROUP_CHARACTER_GROUP",id:e}),[])',
     0),
    ("reducer case：CREATE_CHARACTER_GROUP",
     'case"CREATE_CHARACTER_GROUP":', 520),
    ("reducer case：UNGROUP_CHARACTER_GROUP",
     'case"UNGROUP_CHARACTER_GROUP":', 560),
    ("keydown 里的 g/d 分支",
     'else if("g"===n||"d"===n)if(e.shiftKey)', 150),
    ("keydown 里 hY 块的修饰键条件（g / d 两段）",
     '&&("g"!==n||e.ctrlKey||e.metaKey)&&("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))',
     0),
    ("keydown 里 z 的条件（撤销／重做同族）",
     'else if("z"===n)e.shiftKey?nu():nd();',
     0),
    ("可分组类别 sg(e)（character/prop/emptyObject/camera）",
     'function sg(e){return"character"===e||"prop"===e||"emptyObject"===e||"camera"===e}',
     0),
    ("组名 lT(e)＝ i18n(canvas:nodeTypeGroup) ＋ N",
     'function lT(e){return`${(0,tS.V)("canvas:nodeTypeGroup")}${e.length+1}`}',
     0),
    ("右键菜单的 canGroup 判定式",
     'X(e,s,!l&&s.length>1&&s.every(e=>sg(e.category)),l?.id)',
     0),
    ("右键菜单「打组」项（disabled:!e.canGroup）",
     'disabled:!e.canGroup,className:v,onClick:()=>{r(),t()},children:'
     '[(0,i.jsx)("span",{className:b,children:(0,i.jsx)(u.p.Group,{width:14,height:14})}),'
     'p("canvas:directorContextMenuGroup")]',
     0),
    ("树行的 onClick：⇧／⌘／Ctrl ＝ additive（且仅对 sg 类别）",
     'onClick:t=>{if("motionPath"===e.category)return void s?.(e.id);'
     'let r=t.shiftKey||t.metaKey||t.ctrlKey;'
     'a(e.id,e.category,sg(e.category)?{additive:r,individual:!0}:void 0)}',
     0),
    ("快捷键面板：打组 ⌘G ＋ 解组 ⌘⇧D 两行",
     '{label:e("canvas:directorShortcutGroup"),'
     'keys:[{id:"group-command",icon:"command"},{id:"group-key",label:"G"}]},'
     '{label:e("canvas:directorShortcutUngroup"),'
     'keys:[{id:"ungroup-command",icon:"command"},{id:"ungroup-shift",label:"⇧"},'
     '{id:"ungroup-key",label:"D"}]}',
     0),
]

REGEX_SPECS = [
    ("键集合 hY（字母快捷键白名单）", r'hY=new Set\(\[[^\]]*\]\)'),
    # ★★ 「组树条目」＝ 树里那一支 Group 图标 ⟹ 必须**唯一**。
    #   源站 chunk 里 `u.p.Group` 共 3 处：右键菜单「解组」／右键菜单「打组」／**树条目**。
    #   树条目那一处的前置特征是「展开／收起组」的 title ⟹ 用它把正则锚到唯一。
    ("组树条目：带 Group 图标的那一支（树，非右键菜单）",
     r'title:h\(r\?"canvas:directorCollapseGroup":"canvas:directorExpandGroup"\)'
     r'.{0,520}?\(0,i\.jsx\)\(u\.p\.Group[^)]*\)'),
]


# ══════════════════════════════════════════════════════════════════════════
# ★ 行为矩阵推导：一个**通用**的小解释器，输入是上面**提取出来的字符串**
# ══════════════════════════════════════════════════════════════════════════

def split_top_level(s: str, sep: str = "&&") -> list:
    """★ 只在**括号深度为 0** 的地方切分。

    ★ 为什么必须这样做：`&&("g"!==n||e.ctrlKey||e.metaKey)&&("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))`
    里那个 `&&` **在括号内** ⟹ 用 `str.split("&&")` 会把条件切成三段（实测报
    「无法解析 gate 片段」）。
    """
    out, depth, cur = [], 0, ""
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and s.startswith(sep, i):
            out.append(cur)
            cur = ""
            i += len(sep)
            continue
        cur += ch
        i += 1
    out.append(cur)
    return out


def strip_outer_parens(s: str) -> str:
    """剥掉**包住整串**的那一层括号（不动内部的括号）。"""
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        depth = 0
        balanced = True
        for idx, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and idx != len(s) - 1:
                    balanced = False
                    break
        if not balanced:
            break
        s = s[1:-1].strip()
    return s


# ── 布尔表达式求值：**递归下降**，保留优先级 ──────────────────────────────
# ★ 关键：`e.shiftKey&&(e.ctrlKey||e.metaKey)` 里的括号**不能**直接去掉 ⟹
#   去掉就变成 `(shift&&ctrl)||meta` ⟹ **优先级被改掉** ⟹ 判定结果会错。
_LEAVES = ("e.ctrlKey", "e.metaKey", "e.shiftKey")


def _eval_bool(expr: str, env: dict) -> bool:
    """求值只含 `||`／`&&`／括号／三个叶子（e.ctrlKey|e.metaKey|e.shiftKey）的表达式。"""
    tokens = re.findall(r"\(|\)|\|\||&&|e\.(?:ctrlKey|metaKey|shiftKey)", expr)
    pos = [0]

    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def take():
        tok = tokens[pos[0]]
        pos[0] += 1
        return tok

    def parse_or():
        val = parse_and()
        while peek() == "||":
            take()
            right = parse_and()
            val = val or right
        return val

    def parse_and():
        val = parse_primary()
        while peek() == "&&":
            take()
            right = parse_primary()
            val = val and right
        return val

    def parse_primary():
        tok = take()
        if tok == "(":
            val = parse_or()
            close = take()
            if close != ")":
                raise ValueError("★ 括号不配对：%r" % expr)
            return val
        if tok in _LEAVES:
            return bool(env[tok])
        raise ValueError("★ 无法解析的记号：%r（整串 %r）" % (tok, expr))

    result = parse_or()
    if pos[0] != len(tokens):
        raise ValueError("★ 表达式尾部有多余记号：%r" % tokens[pos[0]:])
    return result


def _parse_gate_segment(seg: str):
    """把 `&&` 切出来的一段修饰键条件，解析成 (适用字母 or None, 条件表达式)。

    ★ 源站只有两种形状：
      `"g"!==n||e.ctrlKey||e.metaKey`      ⟹ 字母 g 时要求 (ctrl 或 meta)
      `"d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey)` ⟹ 字母 d 时要求 (shift 且 (ctrl 或 meta))
    ★ 通用做法：把 `X!==n||` 开头的那一段**当作前缀**剥掉，
      剩下的就是「该字母必须满足的附加条件」。
    """
    seg = strip_outer_parens(seg)
    m = re.match(r'^"([a-z])"!==n\|\|(.+)$', seg)
    if not m:
        return None, None
    return m.group(1), m.group(2).strip()


def _eval_req(req: str, ctrl: bool, meta: bool, shift: bool) -> bool:
    """把**由提取串得到的**布尔表达式求值。"""
    env = {"e.ctrlKey": ctrl, "e.metaKey": meta, "e.shiftKey": shift}
    return _eval_bool(req, env)


def _format_combo(meta: bool, ctrl: bool, shift: bool) -> str:
    """把 (Cmd / Ctrl / Shift) 格式成一个**无歧义**的前缀串。

    ★ 源站的条件里 ctrl 与 meta 是「或」关系（`e.ctrlKey||e.metaKey`），
    ★ 但两者**同时**按下时也要能区分 ⟹ 所以这里不合并成一个符号。
    """
    parts = []
    if meta:
        parts.append("Cmd")
    if ctrl:
        parts.append("Ctrl")
    if shift:
        parts.append("⇧")
    return "+".join(parts)


def derive_behavior_matrix(gate_cond: str, branch_body: str) -> list:
    """★ 用**提取到的**两段字符串，推出 12 种组合各自的动作。

    gate_cond 形如：
      &&("g"!==n||e.ctrlKey||e.metaKey)&&("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))
    branch_body 形如：
      else if("g"===n||"d"===n)if(e.shiftKey){let e=...;e&&rY(e)}else"g"===n&&rW();
    """
    # ── 1) 解析 gate：每个字母一条附加条件 ──
    body = gate_cond.strip()
    body = body[2:] if body.startswith("&&") else body
    per_letter = {}
    for seg in split_top_level(body, "&&"):
        if not seg.strip():
            continue
        letter, req = _parse_gate_segment(seg)
        if letter is None:
            raise ValueError("★ 无法解析 gate 片段：%r" % seg)
        per_letter[letter] = req

    # ── 2) 解析分支体 ──
    #    if(e.shiftKey){ …解组… }else"g"===n&&rW();
    # ★ 注意：源站 chunk 里 `rW()` 后面**没有分号**（压缩代码在 `}` 前省略末尾分号）⟹
    #   正则里不能写 `rW\(\);` ⟹ 否则匹配不上（★ 这是本轮实际踩到的坑）。
    if not re.search(r'if\(e\.shiftKey\)\{.*?\}else"g"===n&&rW\(\)', branch_body):
        raise ValueError("★ 分支体形状与预期不符：%r" % branch_body[:120])
    if not re.search(r'"g"===n\|\|"d"===n', branch_body):
        raise ValueError("★ 分支体没有 g/d 双字母守卫：%r" % branch_body[:120])
    ungroup_call = re.search(r'if\(e\.shiftKey\)\{(.*?)\}else', branch_body).group(1)
    if "rY(" not in ungroup_call:
        raise ValueError("★ ⇧ 分支里没有 rY(（解组调用）：%r" % ungroup_call)

    # ── 3) 枚举 ──
    rows = []
    for key, ctrl, meta, shift in itertools.product(
            ["g", "d"], [False, True], [False, True], [False, True]):
        # gate：只有「命中字母」那一段起作用
        req = per_letter.get(key)
        if req is None:
            action = None
        elif not _eval_req(req, ctrl, meta, shift):
            action = None
        else:
            # 分支体：带 ⇧ 一律解组；不带 ⇧ 时只有 g 打组
            action = "ungroup" if shift else ("group" if key == "g" else None)
        rows.append({
            "按键": key,
            "Ctrl": ctrl,
            "Cmd": meta,
            "Shift": shift,
            # ★ 显示串必须**无歧义**：源站条件里 ctrl 与 meta 是「或」关系，
            #   但两者都按下时也要能区分 ⟹ 所以这里不合并成一个符号。
            "显示": _format_combo(meta, ctrl, shift) + key.upper(),
            "动作": action,
        })
    return rows


def main() -> int:
    if not CHUNK.exists():
        print("★ 源站 chunk 不存在：", CHUNK)
        return 2
    text = CHUNK.read_text(encoding="utf-8", errors="replace")
    out = {"来源": {"chunk": str(CHUNK), "字节数": len(text.encode("utf-8"))}, "片段": {}}
    bad = []
    for name, anchor, tail in SPECS:
        hits = [m.start() for m in re.finditer(re.escape(anchor), text)]
        rec = {"锚点": anchor, "命中数": len(hits),
               "偏移": hits[0] if len(hits) == 1 else None, "原文": None}
        if len(hits) == 1:
            rec["原文"] = text[hits[0]:hits[0] + len(anchor) + tail]
        else:
            bad.append((name, len(hits)))
        out["片段"][name] = rec

    for name, pattern in REGEX_SPECS:
        hits = list(re.finditer(pattern, text))
        rec = {"正则": pattern, "命中数": len(hits),
               "偏移": hits[0].start() if len(hits) == 1 else None,
               "原文": hits[0].group(0) if len(hits) == 1 else None}
        if len(hits) != 1:
            bad.append((name, len(hits)))
        out["片段"][name] = rec

    arb = []
    for name, rec in out["片段"].items():
        src = rec["原文"] or ""
        for m in re.finditer(r"[A-Za-z0-9_:/\[\]().,#%!-]*-\[[^\]\s\"']*", src):
            frag = m.group(0)
            if not frag.endswith("]"):
                arb.append((name, frag))
    out["★任意值类名自检"] = {"疑似截断": arb, "通过": not arb}

    # ★★ 行为矩阵：由上面**提取出来的**两段字符串推导
    gate = out["片段"]["keydown 里 hY 块的修饰键条件（g / d 两段）"]["原文"]
    branch = out["片段"]["keydown 里的 g/d 分支"]["原文"]
    if gate and branch:
        out["★行为矩阵（由提取串推导）"] = {
            "说明": "输入＝上面两段**提取出来的**字符串；输出＝12 种组合的动作",
            "修饰键条件原文": gate,
            "分支体原文": branch,
            "组合": derive_behavior_matrix(gate, branch),
        }
    else:
        bad.append(("行为矩阵推导", "缺片段"))

    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "source-853-contract.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", path)
    ok = 0
    for name, rec in out["片段"].items():
        if rec["命中数"] == 1:
            ok += 1
        print("  [%s] %-58s 命中=%d"
              % ("OK " if rec["命中数"] == 1 else "BAD", name, rec["命中数"]))
    print("唯一命中：%d / %d" % (ok, len(out["片段"])))
    print("任意值类名自检：", "通过" if not arb else ("★ 疑似截断 %r" % (arb,)))
    matrix = out.get("★行为矩阵（由提取串推导）", {}).get("组合", [])
    if matrix:
        print("── 推导出的行为矩阵 ──")
        for r in matrix:
            print("   %-8s ⟹ %s" % (r["显示"], r["动作"] or "无"))
    if bad:
        print("★★ 锚点未唯一命中：", bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

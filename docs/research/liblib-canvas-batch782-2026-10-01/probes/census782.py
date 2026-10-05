#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 782 普查器 —— 键盘主人全量普查（**按挂载域**，不按目录）

## 为什么要有这一批

778–781 四批把 `DirectorDesk.tsx:487` 那道 `isEditable` 守卫的机制钉死了，
但**四批都默认了一件事**：那 6 个非 Escape 键的**主人**只有一个。
★ 本批要把这个默认**测出来** —— 它是 779/780/781 全部归因的地基。

## ★★ 本批推翻了自己：普查域划错了

第一版普查只扫 `src/components/director/` 目录，得出「那 6 个键的主人 = 1」。
★ 而 `DirectorDesk` 是被 **`src/app/page.tsx:1655`** 渲染的 —— 那个文件
**自己就注册了 3 个 window 键盘主人**（`:1400/:1401/:1402`），其中
`:1400` 是 **window + capture + `stopImmediatePropagation`**，
认领 `Escape` / `Delete` / `Backspace` / `Tab` / `Meta+z` / `Meta+y`。

⟹ 「只有一个主人」**在 director 目录内成立，在导演台实际所处的挂载域里不成立**。
⟹ 普查必须**从「目录」改成「挂载域」**：谁渲染了 `DirectorDesk`，谁就是同域。

## ★ 本批自己踩的第二个坑（普查器本身的语义 bug）

第一版 `keys_in()` 把 `key === "X"` 与 `key !== "X"` **收进同一个集合**。
而这两种比较的语义**相反**：

- `if (key !== "X") return;` ⟹ **早退守卫** ⟹ 它**认领** `X`
- `if (key !== "A" && …) { begin(); }` ⟹ **排除清单** ⟹ 它**不认领** `A`

⟹ `useDirectorGestureBoundary.ts:100-104` 那 5 个 `!==`
（Tab/Shift/Alt/Control/Meta）被算成「主人」⟹ `Tab` 主人变成 **2 个**、
`Escape` 的「排他」集合里混进一个 **bubble 相位**的。

★ 判据：**看 `!==` 所在 `if` 的语句体是不是 `return`** ——
是则归属，否则是排除。两类都要单独记（`keys` / `keysExcluded`）。

## 第一个坑（保留，作为方法记录）

普查用「从 `addEventListener` 那一行往上走 N 行」猜函数体，
于是**切掉了** `DirectorViewport.tsx:2702`/`:2744` 的
`event.stopImmediatePropagation()` ⟹ 得出一条**完全相反**的结论。
⟹ 函数体必须用**括号配对**取；验收器再用**另一种方法**独立重算。
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUT = REPO / ("docs/research/liblib-canvas-batch782-2026-10-01"
              "/raw/census782.json")
PLANE = REPO / "src/components/director"
SRC = REPO / "src"

#: 承重的那组键（779/780/781 实测被 `:487` 吞掉的那几个）
MODIFIER_KEYS = ["c", "v", "z", "y", "Delete", "Backspace"]

ADD_RX = re.compile(
    r'addEventListener\(\s*["\'](keydown|keyup)["\']\s*,\s*([A-Za-z0-9_]+)\s*(,\s*true\s*)?\)')
ONKEY_RX = re.compile(r'onKey(Down|Up)\s*[=:]\s*\(')
IF_RX = re.compile(r'\bif\s*\(')


def strip_line_comment(line):
    """★ **只抹行注释**，保留字符串。

    注册行要靠 `addEventListener("keydown", ...)` 里的**引号**来匹配事件名，
    而若先把字符串也抹掉，正则就永远匹配不上 ⟹ 普查只找到 1 个主人。
    ★ 这是 R128 的「加工顺序错了」：同一个函数体需要**两种视图** ——
    数调用用「抹字符串」的，数字面量/键名用「只抹注释」的。
    """
    i = line.find("//")
    return line if i < 0 else line[:i]


def strip_strings_comments(line):
    """★ 只抹**行内**的字符串与注释尾巴 —— 普查要数的是**代码**里的调用，
    而 `// 注释里写 stopImmediatePropagation()` 不算。"""
    out, i, n = [], 0, len(line)
    quote = None
    while i < n:
        c = line[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "\"'`":
            quote = c
            i += 1
            continue
        if c == "/" and i + 1 < n and line[i + 1] == "/":
            break
        out.append(c)
        i += 1
    return "".join(out)


def body_by_brace(lines, decl_idx):
    """★ 从声明行开始**括号配对**取整个函数体 —— 不用「往上/往下 N 行」。"""
    depth, started = 0, False
    for n in range(decl_idx, len(lines) + 1):
        code = strip_strings_comments(lines[n - 1])
        for ch in code:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}":
                depth -= 1
        if started and depth <= 0:
            return "\n".join(lines[decl_idx - 1:n]), n
    return "\n".join(lines[decl_idx - 1:]), len(lines)


def find_decl(lines, name, before_line):
    """找 `name` 的**声明**行（往前找 `const|function name` 或 `name = (`）。"""
    rx = re.compile(r'(const|function|let|var)\s+' + re.escape(name) + r'\b'
                    r'|\b' + re.escape(name) + r'\s*=\s*[\(\w]')
    for n in range(before_line, 0, -1):
        if rx.search(lines[n - 1]):
            return n
    return None


def _close_paren(text, open_idx):
    """从 `(` 处括号配对找它的 `)`；配不上返回 -1。"""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _negatives(body, mstart):
    """保留：`_enclosing_if` 的语义见 keys_in 的注释。"""
    cond, _, close = _enclosing_if(body, mstart)
    return close > 0 and strip_strings_comments(
        body[close + 1:]).lstrip().startswith("return")


#: 比较式：`event.key` / `event.code`，带不带 `toLowerCase()`，=== 还是 !==
CMP_RX = re.compile(
    r'\.(key|code)(\.toLowerCase\(\))?\s*(===|!==)\s*"([^"]+)"')
#: 成员式：`["z","y","d"].includes(event.key.toLowerCase())` —— 第三种形态，
#: 第一版完全漏掉 ⟹ `page.tsx:1400` 的键集少报 3 个（★ 明显偏小的计数
#: 本身就是「匹配写错了」的信号）。
INCL_RX = re.compile(
    r'\[\s*((?:"[^"]+"\s*,\s*)*"[^"]+")\s*\]\s*\.includes\(\s*'
    r'(?:event\.)?(key|code)(\.toLowerCase\(\))?\)')


def _enclosing_if(body, pos):
    """★ 找**包住** `pos` 的最近那个 `if (` 的条件文本。

    不能只取「前面最近的 `if`」—— 若那个 `if` 的 `)` 在 `pos` 之前，
    说明它不包住本次比较（嵌套箭头函数里的 if）。"""
    best = None
    for m in IF_RX.finditer(body, 0, pos):
        op = body.index("(", m.end() - 1)
        cl = _close_paren(body, op)
        if cl > pos and (best is None or m.start() > best[0]):
            best = (m.start(), op, cl)
    if best is None:
        return "", -1, -1
    return body[best[1] + 1:best[2]], best[1], best[2]


def _modality(body, pos, lowercased):
    """★ 修饰键极性 —— 第三种语义。

    `if (modifier && k.toLowerCase() === "v")` ⟹ 认领 **`Meta+v`**；
    `if (!modifier && … === "v")`            ⟹ 认领 **裸 `v`**（无修饰键）。

    ★ 第一版不看这个 ⟹ 把 `page.tsx:1372` 的裸 `v` 报成 `Meta+v`，
    而那正是本批承重的那个 handler ⟹ 会得出「桌不是 `Meta+v` 的唯一主人」
    的**假**结论（方向刚好反：真结论是它也不认领 `Meta+v`）。

    ★★ 门控可以出现在三个位置，`if (...)` 括号**只覆盖其中一个**：
      ① `if (modifier && …)`            —— 在 `if` 括号内
      ② `const x = … || (modifier && …)` —— 同级表达式（`page.tsx:1282`）
      ③ `return ( … || (!modifier && …))` —— 也在同级（`isLibTVCanvasCommandKey`）
    ⟹ 改成**就近取极性**：在同一语句窗口内，比较**最后一次**出现的是
    `modifier` 还是 `!modifier`。（`isLibTVCanvasCommandKey` 的返回体里
    `const modifier = …` 定义在前，而裸 `g/v/h` 的 `!modifier` 在后 ⟹ 就近取到负极性，
    这正是对的。）"""
    if not lowercased:
        return ""                       # `event.key === "Delete"` 永远是裸键
    win = strip_strings_comments(body[max(0, pos - 300):pos])
    cut = max(win.rfind(";"), win.rfind("{"), win.rfind("}"))
    win = win[cut + 1:]
    neg = [m.start() for m in re.finditer(r'!\s*\bmodifier\b', win)]
    pos_ = [m.start() for m in re.finditer(r'(?<![!\w])\bmodifier\b', win)]
    if neg and (not pos_ or neg[-1] > pos_[-1]):
        return ""                       # 显式排除修饰键 ⟹ 裸键
    if pos_ or re.search(r'const\s+modifier\s*=\s*event\.metaKey', body):
        return "Meta+"
    return ""


def keys_in(body_keep_strings):
    """★ 吃**只抹注释、保留字符串**的视图 —— 键名就是字符串字面量。

    ★★★ 本批修的三个语义 bug（全部由「键集看起来不对」逼出来）：
      ① `!==` 有**两种**相反语义 ——
         `if (key !== "X") return;` ⟹ **早退守卫** ⟹ 认领 `X`；
         `if (key !== "A" && …) { … }` ⟹ **排除清单** ⟹ **不**认领。
      ② **修饰键极性**：`!modifier && k === "v"` 是**裸** `v`，不是 `Meta+v`。
      ③ **成员式**：`["z","y","d"].includes(k)` 也是认领，第一版整个漏掉。
    """
    owned, excluded = set(), set()

    def put(k, negated, pos):
        cond, _, close = _enclosing_if(body_keep_strings, pos)
        if not negated:
            owned.add(k)
        elif close > 0 and strip_strings_comments(
                body_keep_strings[close + 1:]).lstrip().startswith("return"):
            owned.add(k)               # 早退守卫 ⟹ 认领
        else:
            excluded.add(k)            # 排除清单 ⟹ 不认领

    for m in CMP_RX.finditer(body_keep_strings):
        put(_modality(body_keep_strings, m.start(), m.group(2)) + m.group(4),
            m.group(3) == "!==", m.start())
    for m in INCL_RX.finditer(body_keep_strings):
        for lit in re.findall(r'"([^"]+)"', m.group(1)):
            put(_modality(body_keep_strings, m.start(), m.group(3)) + lit,
                False, m.start())
    return sorted(owned), sorted(excluded - owned)


DELI_RX = re.compile(r'\b([A-Za-z_]\w*)\s*\(\s*event\s*\)')


def resolve_delegates(body_keep_strings):
    """★ **一层**委托解析。

    `page.tsx:1303` 把判定交给 `isLibTVCanvasCommandKey(event)`，
    键名在 `src/lib/libtvSelectionCommandContext.ts` 里 ⟹ 不解析的话，
    ★ 本批**承重**的那个主人（capture+sIP）键集有个洞。
    只解析 `src/lib/**` 里 `export function` 定义的（不追第二层，
    追到底就不是普查而是编译器了；这一层已经覆盖实际调用）。"""
    got = {}
    for name in sorted(set(DELI_RX.findall(body_keep_strings))):
        for p in sorted((REPO / "src/lib").rglob("*.ts")):
            text = p.read_text(encoding="utf-8")
            m = re.search(r'export function ' + re.escape(name) + r'\b', text)
            if not m:
                continue
            lines = text.split("\n")
            dbody, _ = body_by_brace(lines, text[:m.start()].count("\n") + 1)
            dk, dx = keys_in("\n".join(strip_line_comment(x)
                                       for x in dbody.split("\n")))
            got[name] = {"file": str(p.relative_to(REPO)), "keys": dk,
                         "keysExcluded": dx}
            break
    return got


def make_owner(p, lines, n, ev, fn, cap, decl, scope):
    body, end = body_by_brace(lines, decl)
    code = "\n".join(strip_strings_comments(x) for x in body.split("\n"))
    codeKeep = "\n".join(strip_line_comment(x) for x in body.split("\n"))
    owned, excl = keys_in(codeKeep)
    delegates = resolve_delegates(codeKeep)
    owned = sorted(set(owned) | {k for d in delegates.values() for k in d["keys"]})
    return {
        "file": str(p.relative_to(REPO)), "scope": scope,
        "regLine": n, "handler": fn, "event": ev, "capture": cap,
        "regTarget": "window" if "window." in lines[n - 1] else "root",
        "declLine": decl, "bodyEnd": end,
        "keys": owned, "keysExcluded": excl, "delegates": delegates,
        "preventsDefault": "preventDefault()" in code,
        "stopsPropagation": "stopPropagation()" in code,
        "stopsImmediate": "stopImmediatePropagation()" in code,
        "consultsType": bool(re.search(
            r"HTMLInputElement|tagName|\.type\s*===|getAttribute\(.type.\)", code)),
        # ★ D1h 的两条载荷：**这个主人是不是被导演台的状态挡住的**
        "gatedOnActiveDirector": bool(re.search(
            r"activeDirectorNodeId\s*\)?\s*(?:\|\||&&|return|;)", code)),
        "gatedOnBlockingSurface": "resolveLibTVBlockingForegroundSurface" in code,
    }


def census_file(p, scope):
    lines = p.read_text(encoding="utf-8").split("\n")
    out = []
    for n, ln in enumerate(lines, 1):
        m = ADD_RX.search(strip_line_comment(ln))
        if m:
            decl = find_decl(lines, m.group(2), n)
            out.append(make_owner(p, lines, n, m.group(1), m.group(2),
                                  bool(m.group(3)), decl or n, scope))
            continue
        m2 = ONKEY_RX.search(strip_line_comment(ln))
        if m2:
            out.append(make_owner(p, lines, n, "key" + m2.group(1).lower(),
                                  "inline", False, n, scope))
    return out


def find_mount_hosts():
    """★ 谁渲染了 `<DirectorDesk` ⟹ 谁与它**同域**（共用一个 window）。"""
    hosts = []
    for p in sorted(list(SRC.rglob("*.ts")) + list(SRC.rglob("*.tsx"))):
        if re.search(r"<DirectorDesk[\s/>]", p.read_text(encoding="utf-8")):
            hosts.append(p)
    return hosts


def census():
    owners = []
    for p in sorted(list(PLANE.rglob("*.ts")) + list(PLANE.rglob("*.tsx"))):
        owners += census_file(p, "director-plane")
    hosts = find_mount_hosts()
    for p in hosts:
        owners += census_file(p, "mount-host")
    return owners, hosts


def main():
    owners, hosts = census()
    # ★ D1h 的载荷：导演台**在不在**阻塞面枚举里
    lib = (REPO / "src/lib/libtvSelectionCommandContext.ts").read_text(encoding="utf-8")
    union = lib.split("export type LibTVBlockingForegroundSurface =")[1].split(";")[0]
    payload = {
        "blockingSurfaceUnion": sorted(
            re.findall(r'"([a-z-]+)"', union)),
        "unionMentionsDirector": bool(re.search(r"director", union, re.I)),
        "snapshotMentionsActiveDirectorNodeId":
            "activeDirectorNodeId" in lib.split("export interface "
                                                "LibTVForegroundSurfaceSnapshot")[1]
            .split("}")[0],
        "mountHosts": [str(p.relative_to(REPO)) for p in hosts],
    }
    out = {"batch": 782, "owners": owners, "payload": payload,
           "modifierKeys": MODIFIER_KEYS,
           "method": "★ 函数体用**括号配对**取；普查域 = director 目录 ∪ "
                     "**渲染了 `<DirectorDesk` 的挂载页**（同域共用一个 window）；"
                     "`!==` 按「该 if 的语句体是不是 return」区分**归属/排除**。"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("挂载页：%r" % payload["mountHosts"])
    print("键盘主人：%d 个（director 目录 %d + 挂载页 %d）"
          % (len(owners), sum(1 for o in owners if o["scope"] == "director-plane"),
             sum(1 for o in owners if o["scope"] == "mount-host")))
    print("\n%-30s %-15s %-6s %-7s %-8s %-6s %-5s %-5s %-5s %-6s %s"
          % ("file", "scope", "行", "相位", "目标", "键数", "pD", "sP", "sIP",
             "看type", "键"))
    for o in owners:
        print("%-30s %-15s %-6d %-7s %-8s %-6d %-5s %-5s %-5s %-6s %s"
              % (o["file"].split("src/")[-1], o["scope"], o["regLine"],
                 "capture" if o["capture"] else "bubble", o["regTarget"],
                 len(o["keys"]), o["preventsDefault"], o["stopsPropagation"],
                 o["stopsImmediate"], o["consultsType"], ",".join(o["keys"])[:40]))
        if o["keysExcluded"]:
            print("%30s %-15s %-6s %-7s %-8s 排除：%s"
                  % ("", "", "", "", "", ",".join(o["keysExcluded"])))
    print("\n★ 阻塞面枚举 = %r" % payload["blockingSurfaceUnion"])
    print("★ 枚举里提到 director？ %s   快照里有 activeDirectorNodeId？ %s"
          % (payload["unionMentionsDirector"],
             payload["snapshotMentionsActiveDirectorNodeId"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

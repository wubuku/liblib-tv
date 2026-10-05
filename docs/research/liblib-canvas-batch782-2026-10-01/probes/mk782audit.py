#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 782 汇编器 —— **键盘主人全量普查**：四批的归因前提，测出来了

## 本批验的是 778–781 **四批共同依赖的那个默认**

> 「那 6 个非 Escape 键的主人**只有一个**」

★ 本批把这个默认**测出来** —— 它是全部归因的地基。

## ★★ 而本批把这个默认**推翻了一半**，并给出了它成立的**真正原因**

第一版普查只扫 `src/components/director/` 目录 ⟹ 得出「主人 = 1」。
★ 而 `DirectorDesk` 是被 **`src/app/page.tsx:1655`** 渲染的，那个文件
**自己就注册了 3 个 window 键盘主人**（`:1400/:1401/:1402`）：

| 主人 | 相位 | `sIP` | 认领的承重键 | 运行时门 |
| --- | --- | --- | --- | --- |
| `DirectorDesk.tsx:570` | bubble | ✗ | **全部 6 个** | 无（但唯一看 `target.type`） |
| `src/app/page.tsx:1400` | **capture** | **✓** | `Escape` `Meta+z` `Meta+y` `Delete` `Backspace` `Tab` | 阻塞面门 |
| `src/app/page.tsx:1401` | bubble | ✗ | 同上 | **`activeDirectorNodeId` 门** |

⟹ **`Meta+c`/`Meta+v` 的主人确实唯一**（真·单主人）；
⟹ **`Meta+z`/`Meta+y`/`Delete`/`Backspace` 的主人是 3 个**（默认被推翻）。

## ★ 但四批的归因**仍然成立** —— 成立的原因换了，而且更脆

两个挂载页主人都带**运行时门**，导演台打开时**两道门都是关的**：

- `:1401` 的门**以导演台开着为条件**（`:1312 if (uiState.activeDirectorNodeId) return;`）
  ⟹ **它正是为了「导演台在时让位」而存在的**，可靠。
- `:1400` 的门是一张 `LibTVBlockingForegroundSurface` 枚举
  （`src/lib/libtvSelectionCommandContext.ts`），**那张表里根本没有导演台**
  ⟹ 它休眠是**遗漏**，不是设计。

⟹ 归因从「代码里只有一个主人」变成「另外两个主人都恰好被门挡住了」。
★ 这就是缺陷 **D1h**：把导演台登记为阻塞面（一个很自然的重构 —— 它确实是
`fixed inset-0 z-[100]` 的全屏模态），`:1400` 会**静默接管整个 Escape 阶梯**。

## 本批自己踩的三个坑（普查器本身的语义 bug，全部由「结果看起来太干净」逼出来）

1. **函数体用行数窗口取** ⟹ 切掉 `DirectorViewport:2702/2744` 的
   `stopImmediatePropagation()` ⟹ 得出**完全相反**的结论（R141）。
2. **`!==` 被当成归属** ⟹ `useDirectorGestureBoundary:100-104` 那 5 个
   **排除**条件被算成「主人」⟹ `Tab` 主人变成 2 个、`Escape` 的排他集合
   混进一个 bubble 相位的（R144）。
3. **修饰键极性没看** ⟹ `page.tsx:1372` 的**裸** `v` 被报成 `Meta+v`
   ⟹ 会得出「桌不是 `Meta+v` 唯一主人」的**假**结论（方向刚好反）；
   同批还漏了 `["z","y","d"].includes(...)` 这个**第三种**认领形态（R145）。
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent.parent
BATCH = REPO / "docs/research/liblib-canvas-batch782-2026-10-01"
OUT = BATCH / "runtime-audit.json"
CENSUS = BATCH / "raw/census782.json"
RAW = BATCH / "raw/vb782a.json"
META = {"tries", "retried"}
GESTURE_RX = re.compile(r"director-gesture-\d+-(\d+)")

#: 承重的 6 个键（779/780/781 实测被 `:487` 吞掉的那几个）
BEAR = ["Meta+c", "Meta+v", "Meta+z", "Meta+y", "Delete", "Backspace"]
#: 宿主页那两个主人各自的门（判据取**源码里那行字面量**，且逐个唯一）
GATE_DIRECTOR = "activeDirectorNodeId"
GATE_SURFACE = "resolveLibTVBlockingForegroundSurface"
TREE_BTN = "[data-director-panels-toggle]"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def norm(x):
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, str):
        return GESTURE_RX.sub(r"director-gesture-<TS>-\1", x)
    return x


def strip(rows):
    if isinstance(rows, dict):
        return {k: v for k, v in rows.items() if k not in META}
    return [{k: v for k, v in r.items() if k not in META} for r in (rows or [])]


def reading(row):
    r = {k: v for k, v in row.items() if k not in META}
    r.pop("arm", None)
    return r


# ═══════════════ 1. 静态普查 ═══════════════
cen = json.loads(CENSUS.read_text(encoding="utf-8"))
owners = cen["owners"]
payload = cen["payload"]
plane = [o for o in owners if o["scope"] == "director-plane"]
host = [o for o in owners if o["scope"] == "mount-host"]
print("（阶段一）挂载域键盘主人 %d 个 = director 目录 %d + 挂载页 %d（%r）"
      % (len(owners), len(plane), len(host), payload["mountHosts"]))


def short(o):
    return "%s:%d" % (o["file"].split("src/")[-1], o["regLine"])


def owners_for(keys):
    """某个（或某几个）键的主人。★ `keys` 是**并集**语义。"""
    return [o for o in owners if any(k in o["keys"] for k in keys)]


# ── 预测 A：`Meta+c` / `Meta+v` 的主人在**挂载域**里唯一 ──
#   （这是第一版普查唯一没被推翻的那一半，且它是**真**的单主人）
copyPaste = [k for k in ("Meta+c", "Meta+v")
             if len(owners_for([k])) == 1]
assert copyPaste == ["Meta+c", "Meta+v"], (
    "★ `Meta+c`/`Meta+v` 的主人不是 1 个：%r ⟹ 「单主人」连这一半也不成立"
    % {k: [short(o) for o in owners_for([k])] for k in ("Meta+c", "Meta+v")})
copyPasteOwners = owners_for(["Meta+c", "Meta+v"])
assert {short(o) for o in copyPasteOwners} == {"components/director/"
                                               "DirectorDesk.tsx:570"}, (
    "★ `Meta+c`/`Meta+v` 的主人换人了：%r" % [short(o) for o in copyPasteOwners])

# ── 预测 A-2：★ 分流的落点唯一 —— 桌是挂载域里**唯一**看 `target.type` 的主人 ──
#   ★ 必须连挂载页一起数：若 `page.tsx` 某个主人也看 `target.type`，
#   那「`:487` 是唯一的分流点」就只是 director 面内的局部性质。
typeAware = [short(o) for o in owners if o["consultsType"]]
assert typeAware == ["components/director/DirectorDesk.tsx:570"], (
    "★ 挂载域里有 %d 个键盘主人看 `target.type`（%r），预测是**只有桌一个** "
    "⟹ 「分流的落点是唯一的」这条要重算" % (len(typeAware), typeAware))

# ── 预测 A'：★ `Meta+z`/`Meta+y`/`Delete`/`Backspace` 的主人**不是 1 个** ──
multi = {k: [short(o) for o in owners_for([k])]
         for k in ("Meta+z", "Meta+y", "Delete", "Backspace")}
multiOwnerNames = {tuple(v) for v in multi.values()}
assert len(multiOwnerNames) == 1, (
    "★ 四个键的主人集合彼此不同：%r ⟹ J1 的更正要重写" % multi)
multiOwners = owners_for(["Meta+z", "Meta+y", "Delete", "Backspace"])
assert len(multiOwners) == 3, (
    "★ 那 4 个键的主人是 %d 个（%r），预测是 3 个"
    % (len(multiOwners), [short(o) for o in multiOwners]))
deskOwner = [o for o in multiOwners
             if o["file"].endswith("DirectorDesk.tsx")][0]
hostOwners = [o for o in multiOwners if o["scope"] == "mount-host"]
assert len(hostOwners) == 2 and {o["regLine"] for o in hostOwners} == {1400, 1401}, (
    "★ 宿主页的主人不正好是 `page.tsx:1400/1401`：%r"
    % [short(o) for o in hostOwners])

# ── 预测 A''：★ 两个宿主页主人都带**运行时门**，且导演台打开时都是关的 ──
#   `:1401` 的门**以导演台开着为条件**（可靠）；`:1400` 的门是一张
#   **没提到导演台**的枚举（靠遗漏休眠）⟹ 两者性质不同，要分开说。
gate1401 = [o for o in hostOwners if o["regLine"] == 1401][0]
gate1400 = [o for o in hostOwners if o["regLine"] == 1400][0]
assert gate1401["gatedOnActiveDirector"] is True, (
    "★ `page.tsx:1401` **没有** `%s` 门 ⟹ 它在导演台打开时**会**抢走那 4 个键 "
    "⟹ 779/780/781 的归因要重算" % GATE_DIRECTOR)
assert gate1400["gatedOnBlockingSurface"] is True, (
    "★ `page.tsx:1400` **没有** `%s` 门 ⟹ 它的排他阻断没有任何门 ⟹ "
    "四批的归因要重算" % GATE_SURFACE)
assert payload["unionMentionsDirector"] is False, (
    "★ `LibTVBlockingForegroundSurface` 枚举里**提到**了 director ⟹ "
    "「`:1400` 靠遗漏休眠」这条要重算")
assert payload["snapshotMentionsActiveDirectorNodeId"] is False, (
    "★ `LibTVForegroundSurfaceSnapshot` 里有 `activeDirectorNodeId` ⟹ "
    "门可能已经关着但读法不同 ⟹ 「靠遗漏休眠」这条要重算")
print("（阶段二）`Meta+c`/`Meta+v` 主人 = 1 个（%s）；★ 而 `Meta+z`/`Meta+y`/"
      "`Delete`/`Backspace` 主人 = **%d 个**（%r）⟹ 四批的默认**被推翻一半**"
      % (short(deskOwner), len(multiOwners), multi["Meta+z"]))
print("（阶段二）两个宿主页主人都带运行时门：`:1401` 以 `%s` 为条件（可靠）、"
      "`:1400` 以 `%s` 为条件，而那张枚举**里没有导演台**（靠遗漏）"
      % (GATE_DIRECTOR, GATE_SURFACE))

# ── 预测 B：★ 导演台自己**不写**任何阻塞面开关（否则门当场就开） ──
BLOCK_FLAGS = ["isShortcutsPanelOpen", "isAddNodePanelOpen", "isZoomMenuOpen",
               "isSharePanelOpen", "isNotificationOpen", "isUserMenuOpen",
               "isFollowingSession", "isCanvasDropdownOpen",
               "isStoryboardEditorOpen", "activePrimaryPanel"]
planeHits = {}
for p in sorted((REPO / "src/components/director").rglob("*.ts")) + \
        sorted((REPO / "src/components/director").rglob("*.tsx")):
    txt = p.read_text(encoding="utf-8")
    for fl in BLOCK_FLAGS:
        if fl in txt:
            planeHits.setdefault(fl, []).append(
                "%s:%d" % (p.name, txt[:txt.index(fl)].count("\n") + 1))
assert not planeHits, (
    "★ director 面**写了**阻塞面开关 %r ⟹ 门会被导演台自己打开 ⟹ D1h 的"
    "「当前不可达」这条要重算" % planeHits)

# ── 预测 C：`Escape` 的排他性**分两类**，且两类**不是一回事** ──
escOwners = owners_for(["Escape"])
escSip = [o for o in escOwners if o["stopsImmediate"]]
escSprop = [o for o in escOwners
            if o["stopsPropagation"] and not o["stopsImmediate"]]
escCapture = [o for o in escOwners if o["capture"]]
escBubble = [o for o in escOwners if not o["capture"]]
assert escSip and all(o["capture"] for o in escSip), (
    "★ `stopImmediatePropagation` 的主人里有**冒泡相位**的（%r）⟹ "
    "「sIP 全在 capture 相位」这条要重算" % [short(o) for o in escSip])
# ★ `sP`（`stopPropagation`）与 `sIP` **机制不同**：它在**目标上**，
#   只能挡住「越过目标继续冒泡」，挡不住 capture 相位已经跑过的监听器。
#   ⟹ 第一版把两者合称「排他」，断言「排他的一定在 capture 相位」因此炸了 ——
#   **炸的是断言的分类，不是机制**（R144）。
assert all(o["capture"] for o in escSip), "见上"
assert escSprop, "★ 没有任何 Escape 主人只用 `stopPropagation` ⟹ 两类分法要重算"
print("（阶段三）Escape 主人 %d 个 = capture %d / bubble %d；"
      "★ 阻断强度分**两类**：`sIP`（capture %d 个，挡整条链）/ "
      "`sP`（%r，**只在目标上**、挡越过目标的冒泡）"
      % (len(escOwners), len(escCapture), len(escBubble), len(escSip),
         [short(o) for o in escSprop]))

# ── 预测 D：★ D8 要引入的形状**仓里已经有** ──
alreadyHave = [o for o in plane
               if o["capture"] and o["preventsDefault"] and o["stopsImmediate"]]
assert alreadyHave, (
    "★ director 面**没有**任何 capture+pD+sIP 的键盘主人 ⟹ "
    "D8 是**新机制**而不是照抄 ⟹ J3 翻了")
d8Precedents = [short(o) for o in alreadyHave]
# ★ 先例**只在 director 面**数：挂载页那两个是「页面 chrome 的门」，
#   语义不同（一个管全站命令键、一个管阻塞面），不能算作导演台内的先例。
assert all(o["scope"] == "director-plane" for o in alreadyHave), (
    "★ 先例集合里混进了挂载页的主人 ⟹ 「同仓先例」的语义要限定")
print("（阶段四）D8 的形状（capture + preventDefault + stopImmediatePropagation）"
      "在 director 面**已有 %d 处**：%r ⟹ D8 是**照抄**"
      % (len(alreadyHave), d8Precedents))

# ── 预测 E：`Tab` 的主人，以及桌面端那个实例**不**排他 ──
tabOwners = owners_for(["Tab"])
assert len(tabOwners) == 3, (
    "★ `Tab` 有 %d 个主人（%r），预测是 3 个（1 个焦点容器 + 2 个页面门）"
    % (len(tabOwners), [short(o) for o in tabOwners]))
# ★ 调用点**在 `DirectorDesk.tsx`**，不在 hook 自己的文件里 ——
#   hook 文件里唯一那处 `useDirectorFocusContainment({` 是**函数定义**的解构
#   参数（`:92`），第一版在错误的文件里搜 ⟹ 既漏掉 3 个真调用点、
#   又把定义算成 1 个「调用点」⟹ 计数变成 1。
FC = REPO / "src/components/director/useDirectorFocusContainment.ts"
fc = FC.read_text(encoding="utf-8")
DESK_SRC = REPO / "src/components/director/DirectorDesk.tsx"
deskText = DESK_SRC.read_text(encoding="utf-8")


def _balanced(text, open_idx):
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_idx:i + 1]
    return ""


fcCalls = [_balanced(deskText, m.end() - 1)
           for m in re.finditer(r'useDirectorFocusContainment\s*\(\s*\{', deskText)]
fcWithStop = [c for c in fcCalls if "stopPropagation" in c]
fcDefault = [c for c in fcCalls if "stopPropagation" not in c]
assert len(fcCalls) == 3 and len(fcWithStop) == 2 and len(fcDefault) == 1, (
    "★ `useDirectorFocusContainment` 在 `DirectorDesk.tsx` 里的调用点变成 %d 个"
    "（开 `stopPropagation` 的 %d 个），预测是 3/2 ⟹ "
    "「桌面端 workspace 实例不排他」这条要重算"
    % (len(fcCalls), len(fcWithStop)))
# ★ 三处的焦点域要分清：开 `stopPropagation` 的两个都**只对移动端焦点域启用**
#   （`enabled: activeMobileFocusScope === …`），桌面端那个用默认 `false`。
mobileGated = [c for c in fcWithStop if "activeMobileFocusScope" in c]
assert len(mobileGated) == 2, (
    "★ 开 `stopPropagation` 的两个调用点里只有 %d 个受 `activeMobileFocusScope` "
    "门控 ⟹ 「那两个都是移动端焦点域」这条要重算" % len(mobileGated))
assert 'stopPropagation = false' in fc, (
    "★ `stopPropagation` 的默认值不再是 false ⟹ J6 要重算")
# ★ 关键交叉验证：`:92` 那个**排除**清单里**也有** `Tab` ——
#   第一版把它算成「`Tab` 的第二个主人」，而它恰恰是**不认领** `Tab` 的那个。
GB = REPO / "src/components/director/useDirectorGestureBoundary.ts"
gbOwner = [o for o in plane if o["file"].endswith("useDirectorGestureBoundary.ts")][0]
assert "Tab" in gbOwner["keysExcluded"], (
    "★ `useDirectorGestureBoundary:92` 的**排除**清单里没有 `Tab` ⟹ "
    "「`Tab` 的第二个主人是假的」这条要重算")
print("（阶段四）`Tab` 主人 %d 个：%r（后两个是页面门）｜焦点容器 %d 个调用点、"
      "其中 %d 个开 `stopPropagation`（都是移动端），**桌面端 workspace 用默认 "
      "false**｜★ `:92` 的排除清单里有 `Tab` ⟹ 第一版那个「第二主人」是假的"
      % (len(tabOwners), [short(o) for o in tabOwners], len(fcCalls),
         len(fcWithStop)))

# ═══════════════ 2. 运行时（从源码逐行推出的预测） ═══════════════
raw = json.loads(RAW.read_text(encoding="utf-8"))
rounds = raw["rounds"]
assert len(rounds) == 2, "轮数不是 2"
arms = {}
for rd in rounds:
    for r in strip(rd.get("rows")):
        arms.setdefault(r.get("arm"), []).append(norm(r))
assert set(arms) == set(("captureOwner", "bubbleOwner", "none")), \
    "臂集合不符：%r" % sorted(arms)
bad = [(k, v[0].get("FAILED")) for k, v in arms.items() if v[0].get("FAILED")]
assert not bad, "★ 有 FAILED：%r" % bad
for k, rs in arms.items():
    assert len(rs) == 2 and reading(rs[0]) == reading(rs[1]), \
        "%s 两轮不一致或只跑了一轮" % k
    assert (rs[0].get("stateBefore") or {}).get("exportOpen") is True, \
        "%s 起点导出面板没开 ⟹ 阶梯的 :557 那档没有目标" % k
    # ★ `cap` **不是通用正向对照**：capture 相位上的
    #   `stopImmediatePropagation` 会把 capture 相位的 document 监听器
    #   **一起截断**（capture 顺序 window → document → … → target）⟹
    #   `cap=0` 在 captureOwner 臂**是承重读数**，不是坏测量。
    for p in rs[0]["presses"]:
        if k == "captureOwner" and p["n"] == 1:
            continue
        assert (p["read"].get("cap") or 0) >= 1, (
            "★ %s 第%s次 cap=%r ⟹ 按键没送达浏览器" % (k, p["n"],
                                                     p["read"].get("cap")))
CELLS = sum(len(arms[k]) * 2 for k in arms)
print("（阶段五）%d 轮 × %d 臂 × 2 次按压 = **%d 格**，零 FAILED，两轮逐字段一致"
      % (len(rounds), len(arms), CELLS))


def per(arm):
    return [{"n": p["n"], "cap": p["read"].get("cap"),
             "win": p["read"].get("win"),
             "targetOpen": p["state"].get("targetOpen"),
             "exportOpen": p["state"].get("exportOpen"),
             "deskOpen": p["state"].get("deskOpen"),
             "lastCommand": p["state"].get("lastCommand")}
            for p in arms[arm][0]["presses"]]


capArm, bubArm, noneArm = per("captureOwner"), per("bubbleOwner"), per("none")

# ── 预测 F：排他的主人激活时，**阶梯跑不到** ──
e0 = capArm[0]
assert e0["cap"] == 0 and e0["win"] == 0, (
    "★ captureOwner 第 1 次 cap=%r win=%r，而预测是**双双为 0**"
    "（capture 相位的 `sIP` 把整条链截断）⟹ 「排他性真的发生」这条要重算"
    % (e0["cap"], e0["win"]))
assert e0["targetOpen"] is False, (
    "★ captureOwner 第 1 次后目标浮层**仍开着** ⟹ "
    "`DirectorViewport:2748` 那个排他主人**没跑** ⟹ J2 要重算")
assert e0["exportOpen"] is True, (
    "★ captureOwner 第 1 次后导出面板**也关了** ⟹ "
    "「排他主人会让阶梯跑不到」这条**被否掉** ⟹ J2 翻了")
assert capArm[1]["cap"] >= 1 and capArm[1]["win"] >= 1, (
    "★ captureOwner 第 2 次 cap/win 仍为 0 ⟹ 那个主人卸载后链**没有**恢复 ⟹ J2 要重算")
assert capArm[1]["exportOpen"] is False, (
    "★ captureOwner 第 2 次后导出面板**仍开着** ⟹ 阶梯**第二次**也没跑 ⟹ "
    "「卸载后阶梯能接住」这条要重算")
ladderBlocked = e0["exportOpen"] is True
capAlsoCut = e0["cap"] == 0
print("（阶段五）captureOwner 第 1 次：cap=%d win=%d（**正向对照自己也被截断**）"
      "｜目标浮层**关掉了**（%r）而**导出面板仍开**（%r）⟹ ★ 排他性真的发生；"
      "第 2 次链恢复（cap=%d win=%d）且阶梯跑到了（导出面板关=%r）"
      % (e0["cap"], e0["win"], e0["targetOpen"], e0["exportOpen"],
         capArm[1]["cap"], capArm[1]["win"], capArm[1]["exportOpen"]))

# ── 预测 G：不排他的主人开着时，**一次按压多主并发** ──
assert bubArm[0]["targetOpen"] is False, (
    "★ bubbleOwner 第 1 次后目标浮层**仍开着** ⟹ 那个 bubble 主人没跑 ⟹ J2 要重算")
assert bubArm[0]["exportOpen"] is False, (
    "★ bubbleOwner 第 1 次后导出面板**仍开着** ⟹ "
    "「不排他的主人会与阶梯并发」这条**被否掉** ⟹ J2 翻了")
concurrent = True
print("（阶段五）bubbleOwner 第 1 次：目标浮层关（%r）**且**导出面板也关（%r）"
      "⟹ ★ **一次按压里两个主人同时处理**（不排他 ⟹ 并发）"
      % (bubArm[0]["targetOpen"], bubArm[0]["exportOpen"]))

# ── 预测 H：对照臂（什么都不开）阶梯跑完 ──
assert noneArm[0]["exportOpen"] is False, (
    "★ none 臂第 1 次后导出面板**仍开着** ⟹ 阶梯没跑 ⟹ 判别力为零")
assert noneArm[1]["deskOpen"] is False, (
    "★ none 臂第 2 次后桌**仍开着** ⟹ 阶梯没跑完 ⟹ 判别力为零")
print("（阶段五）none 臂：第 1 次关导出面板（%r）、第 2 次关桌（%r）"
      "⟹ 对照成立" % (noneArm[0]["exportOpen"], noneArm[1]["deskOpen"]))

# ── 预测 I：★★ 阶段二那道门**现在是关着的**（D1h 的「当前」那半） ──
#   ★ 这是**运行时**证据，不是静态推断：若 `page.tsx:1400`（window + capture +
#   `sIP`）当时在跑，它会 `stopImmediatePropagation` ⟹ `cap` 会是 0 且阶梯跑不到。
#   实测两条臂第 1 次都是 `cap>=1` 且**导出面板真的关了** ⟹ `:1400` 没跑。
hostDormant = all(p["cap"] >= 1 and p["exportOpen"] is False
                  for p in (bubArm[0], noneArm[0]))
assert hostDormant, (
    "★ 对照臂第 1 次出现 `cap=0` 或导出面板没关 ⟹ `page.tsx:1400` **当时在跑** ⟹ "
    "「它被门挡住了」这条要重算")
print("（阶段五）★ 宿主页那两个门**此刻是关着的**：对照臂第 1 次 `cap>=1` "
      "**且**导出面板真的关了 ⟹ 若 `page.tsx:1400` 在跑，它会在 window 捕获相位 "
      "`sIP` 掉整条链 ⟹ D1h 的「当前不可达」有运行时证据")

# ═══════════════ 3. 可比性 ═══════════════
r0 = norm(strip(rounds[0].get("rows")))
r1 = norm(strip(rounds[1].get("rows")))
tries = [r.get("tries", 1) for rd in rounds for r in (rd.get("rows") or [])]
comparability = {
    "rounds": len(rounds), "armsPerRound": len(arms), "cells": CELLS,
    "allConsistent": [reading(x) for x in r0] == [reading(x) for x in r1],
    "censusMethod": cen.get("method"),
    "censusSelfJustification": "★ 普查**逐个自证非空**：%d 个监听点全部由"
                               "`addEventListener`/`onKeyDown` 的**代码**匹配到"
                               "（行注释先抹掉），并逐个用**括号配对**取函数体；"
                               "★ 普查域 = director 目录 ∪ **渲染了 `<DirectorDesk` "
                               "的挂载页**（同域共用一个 window）；"
                               "★ 验收器用**另一种方法**独立重算承重三列。"
                               % len(owners),
    "retryPolicy": "每格最多试 3 次（含第一次），900×n 退避；`tries`/`retried` "
                   "记进 raw 但**排除在两轮一致性比较之外**。",
    "retryStats": {"cells": len(tries),
                   "retriedCells": sum(1 for t in tries if t > 1),
                   "maxTries": max(tries) if tries else None},
    "boundary": "★ **本批未改 `src/`，也没有任何注入。** 只开/关浮层与按 Escape，"
                "**不做任何破坏性操作**（不点删除/提交/连接/新增机位/导入导出，"
                "不做付费或真实生图生视频）；每格开头 `fresh()` 清 localStorage "
                "⟹ 不留残留。",
}
assert comparability["allConsistent"] is True, "★ 两轮不一致"

# ═══════════════ 4. 结论 ═══════════════
judgments = [
    {"id": "J1",
     "text": "★ **四批的默认被推翻一半，但归因仍然成立 —— 成立的原因换了。**"
             "在**挂载域**里：`Meta+c`/`Meta+v` 的主人**确实唯一**（%s），"
             "而 `Meta+z`/`Meta+y`/`Delete`/`Backspace` 的主人是 **%d 个**"
             "（多出 `%s` 与 `%s`）。⟹ 「桌的 `:487` 吞了」不是部分归因，"
             "**但它成立是因为另外两个主人都恰好被门挡住了**，"
             "而不是因为代码里只有它一个主人。" % (
                 short(deskOwner), len(multiOwners),
                 short(gate1400), short(gate1401)),
     "evidence": "阶段二 预测 A / A'"},
    {"id": "J2",
     "text": "★ **两个宿主页主人的门性质不同，这正是 D1h 的根据。**"
             "`%s` 的门是 `%s`（`:1312` 的早退）⟹ **它正是为了「导演台在时"
             "让位」而存在**的，可靠；`%s` 的门是 `%s` 返回的那张枚举，"
             "而**那张表里没有导演台**（枚举 %d 个成员，实测 `unionMentionsDirector="
             "False`、`snapshotMentionsActiveDirectorNodeId=False`）⟹ "
             "**它休眠是遗漏，不是设计**。" % (
                 short(gate1401), GATE_DIRECTOR, short(gate1400), GATE_SURFACE,
                 len(payload["blockingSurfaceUnion"])),
     "evidence": "阶段二 预测 A'' + 阶段五 预测 I"},
    {"id": "J3",
     "text": "★ **`Escape` 的阻断强度分两类，不是「排他/不排他」两类。**"
             "`sIP`（`stopImmediatePropagation`）%d 个，**全在 capture 相位**，"
             "它把**整条链**截断（含 capture 相位上更早的监听器）⟹ 实测那条臂 "
             "`cap=0`；而 `sP`（`stopPropagation`）只有 %s 一个，它在**目标上**，"
             "只能挡住「越过目标继续冒泡」⟹ **挡不住 capture 相位已经跑过的监听器**。"
             "★ 第一版把两者合称「排他」，于是断言「排他的一定在 capture 相位」"
             "炸掉 —— **炸的是分类，不是机制**（R144）。" % (
                 len(escSip), short(escSprop[0])),
     "evidence": "阶段三 + 阶段五 预测 F"},
    {"id": "J4",
     "text": "★ **不排他的主人会与阶梯并发**：bubbleOwner 臂第 1 次按压，"
             "**路径菜单关了、导出面板也关了** ⟹ **一次按压里两个主人同时处理**。"
             "⟹ 「层内 Escape 只关层」并不是靠阻断实现的，而是靠"
             "**恰好那个主人的状态是激活的**——不激活时它就是个旁观者。",
     "evidence": "阶段五 预测 G + 774"},
    {"id": "J5",
     "text": "★ **D8 要引入的形状在 director 面已有 %d 处**（%r）⟹ "
             "`DirectorTimeline:570/594` 改 capture+pD+**sIP** "
             "**不是新机制，是照抄** ⟹ C775-2「同仓先例」模式的**第三次**成立。"
             "★ 先例**只在 director 面数**：挂载页那两个是「页面 chrome 的门」，"
             "语义不同，不能算作导演台内的先例。",
     "evidence": "阶段四 预测 D"},
    {"id": "J6",
     "text": "★ **`Tab` 的主人是 3 个**（`%s` + 页面两个门），而焦点容器"
             "**桌面上不排他**（默认值 false，三个调用点里只有两个移动端开了 "
             "`stopPropagation`）。★ 另有一条**假主人**被第一版算进来了："
             "`useDirectorGestureBoundary:92` 的 `:100-104` 是**排除清单**"
             "（`if (key !== \"Tab\" && …) { begin(); }`），它**不认领** `Tab`。" % (
                 short(tabOwners[0])),
     "evidence": "阶段四 预测 E"},
]
corrections = [
    {"id": "C782-1",
     "targets": ["**778–781 四批共同依赖的默认**：「那 6 个非 Escape 键的主人只有一个」"],
     "was": "读作「director 面里那 6 个键的主人**只有** `DirectorDesk.tsx:570` "
            "一个」——该普查只扫了 `src/components/director/` 目录。",
     "now": "★ **普查域划错了**：导演台是被 `src/app/page.tsx:1655` 渲染的，"
            "**那个文件自己就注册了 3 个 window 键盘主人**。⟹ 在**挂载域**里，"
            "`Meta+z`/`Meta+y`/`Delete`/`Backspace` 的主人是 **3 个**"
            "（多出 `page.tsx:1400`（**capture + `sIP`**）与 `page.tsx:1401`）；"
            "只有 `Meta+c`/`Meta+v` 仍是真·单主人。\n"
            "★ **但归因不撤销**：两个宿主页主人都带**运行时门**，导演台打开时"
            "两道门都关着，且**阶段五预测 I 有运行时证据**（对照臂第 1 次 "
            "`cap>=1` 且导出面板真的关了 ⟹ `page.tsx:1400` 当时**没跑**）。\n"
            "⟹ 归因的**依据**从「代码里只有一个主人」变成「另外两个主人都恰好"
            "被门挡住了」—— 结论一样，**性质更脆**（见 D1h）。",
     "evidence": "J1 + J2 + 阶段二 + 阶段五 预测 I"},
    {"id": "C782-2",
     "targets": ["**挂起项 D8**：「`DirectorTimeline.tsx:570/594` 改 window 捕获"
                 "+preventDefault+stopImmediatePropagation」"],
     "was": "读作「把三处**不合规**的监听器改成**合规**形状」（合规 = 与 774 "
            "测到的 2/6 一致）。",
     "now": "★ **两处补充，都要写进授权文本**："
            "① **这个形状在 director 面已经有 %d 处**（%r）⟹ D8 是**照抄**不是"
            "发明，**同仓先例的把握很高**（C775-2 第三次成立）；"
            "② ★ **但它会引入一个 D8 没提的副作用**：照抄之后路径菜单就成了"
            "**第 %d、%d 个 `sIP` 主人** ⟹ **路径菜单开着时按 Escape，"
            "桌的阶梯再也不会跑**（取消手势、关导出面板都失效）"
            "——runtime 已实测 `sIP` **真的**会挡住阶梯（captureOwner 臂）。\n"
            "⟹ **D8 的真实代价是「引入一条层级优先级」**，而 779 的 C779-2 "
            "已经把「层级优先级」标成**产品决定** ⟹ **这两项是同一个待决问题"
            "的两半，不该各自拍板。**" % (
                len(alreadyHave), d8Precedents, len(escSip) + 1, len(escSip) + 2),
     "evidence": "J3 + J5 + 阶段五 预测 F"},
    {"id": "C782-3",
     "targets": ["**第一版普查的键集**（「`Escape` 主人的排他集合」）"],
     "was": "把 `sIP`（`stopImmediatePropagation`）与 `sP`（`stopPropagation`）"
            "**合称「排他」**，并断言「排他的一定在 capture 相位」。",
     "now": "★ **两者机制不同，必须分开**：`sIP` 在 capture 相位会截断**整条链**"
            "（实测那条臂连 capture 相位的 document 监听器一起没跑，`cap=0`）；"
            "`sP` 那个（`useDirectorGestureBoundary.ts:92`）在**目标上**，"
            "只能挡住「越过目标继续冒泡」⟹ 两者对同一次按压的**后果不同**。\n"
            "★ 断言炸掉时**炸的是分类、不是机制** —— 这条是本批最贵的教训之一："
            "**断言必须先定义清楚它在断言哪一类**。",
     "evidence": "阶段三 + R144"},
]
assert [c["id"] for c in corrections] == ["C782-1", "C782-2", "C782-3"]

probeLessons = [
    {"id": "R141", "text": "★ **普查的函数体必须用括号配对取，不能用行数窗口。**"
                            "第一版用「从注册行往上/往下 N 行」猜函数体，"
                            "于是切掉了 `DirectorViewport:2702/2744` 的 "
                            "`stopImmediatePropagation()` ⟹ 得出一条"
                            "**完全相反**的结论（「没有排他主人 ⟹ D8 是新机制」）。"
                            "★ 若照那条写下去，会给出一条"
                            "「别照抄，没有先例」的建议 —— 而先例就在文件里。"},
    {"id": "R142", "text": "★ **同一个函数体要两种视图。** 数**调用**"
                            "（`preventDefault()`）要用「抹掉字符串」的视图，"
                            "而数**键名字面量**（`key === \"Escape\"`）要用"
                            "「只抹注释、保留字符串」的视图。"
                            "★ 两次都用错视图：先是用抹掉字符串的视图去匹配 "
                            "`addEventListener(\"keydown\")` ⟹ 普查只找到 1 个主人；"
                            "再用抹掉字符串的视图去找 `\"Escape\"` ⟹ 键列全空。"
                            "⟹ **加工顺序错了，输出看起来仍像个正常结果。**"},
    {"id": "R143a", "text": "★ **正向对照不是**普遍**的 —— 有一条路径能把它"
                             "自己关掉。** 我把 `cap`（capture 相位的 "
                             "document 监听器）当成了「按键送达了」的通用"
                             "正向对照；可 capture 相位上的 "
                             "`stopImmediatePropagation` 会把**整条链**"
                             "（含它自己）一起截断 ⟹ 那个臂 `cap=0`。"
                             "★ 一开始我差点把它当**坏测量**删掉，"
                             "而它恰恰是**排他性最强的证据**。"
                             "⟹ 正向对照要**逐臂**声明，"
                             "并**显式预测**哪条臂会把它自己关掉。"},
    {"id": "R144", "text": "★ **`!==` 有两种相反语义，混成一个集合就会造出"
                            "**假主人**。** `if (key !== \"X\") return;` 是**早退守卫**"
                            "⟹ 认领 `X`；而 `if (key !== \"A\" && …) { … }` 是"
                            "**排除清单** ⟹ **不**认领。第一版把两者收进同一个集合，"
                            "于是 `useDirectorGestureBoundary:100-104` 那 5 个"
                            "排除条件被算成「主人」⟹ `Tab` 主人变成 2 个、"
                            "`Escape` 的「排他」集合里混进一个 bubble 相位的。\n"
                            "★ **它炸的方式很典型**：断言挂掉时我第一反应是"
                            "「断言的分类写错了，改断言」——方向对，但**只改了一半**："
                            "真正的错在**普查器**，若只改断言就会把假主人固化下来。\n"
                            "⟹ 判据：断言与采集器**谁**先错，要看**炸掉的那一层"
                            "是不是被当成了事实**。"},
    {"id": "R145", "text": "★ **「没找到」与「不存在」在普查里长得一样"
                            "（R104/R112 的新变体）。** 前几次错法都表现为"
                            "「结果很干净」——1 个主人、键列全空、"
                            "`Tab` 恰好 1 个主人 —— 而**一个明显偏小的计数**"
                            "本身就是「我的匹配写错了」的信号。\n"
                            "★ 本批在同一处连踩**三种**认领形态："
                            "`===`、早退 `!==`、以及**成员式**"
                            "`[\"z\",\"y\",\"d\"].includes(k)`；还漏了"
                            "**修饰键极性**（`!modifier && k === \"v\"` 是**裸** `v`，"
                            "不是 `Meta+v`）——而那个 handler 正是本批承重的那个，"
                            "方向刚好反。⟹ 普查结果要带**自证**：逐个自证非空 + "
                            "**用另一种方法独立重算**。"},
]
assert [x["id"] for x in probeLessons] == ["R141", "R142", "R143a", "R144", "R145"]

defects = [
    {"id": "D1h", "severity": "中·潜伏回归（本批新提）",
     "text": "★ **导演台的 Escape 阶梯能工作，靠的是一个「没人登记过」的前提。**"
             "`src/app/page.tsx:1400` 是 **window + capture + `sIP`** 的主人，"
             "认领 `Escape`/`Delete`/`Backspace`/`Meta+z`/`Meta+y`/`Tab`，"
             "而它唯一的门是 `resolveLibTVBlockingForegroundSurface(uiState)`"
             "（`:1294`）—— 那张 `LibTVBlockingForegroundSurface` 枚举"
             "（%d 个成员）**里没有导演台**，`LibTVForegroundSurfaceSnapshot` "
             "里也**没有** `activeDirectorNodeId` ⟹ 门是**关着的**。\n"
             "★ 对照之下 `:1401` 的门是 `:1312` 的 `if (uiState.activeDirectorNodeId) "
             "return;` ⟹ **那正是「导演台在时让位」，是显式的、可靠的**。\n"
             "⟹ **同一个页面两个主人，一个显式让位、一个靠遗漏休眠** —— "
             "而导演台恰恰是 `fixed inset-0 z-[100]` 的全屏模态，"
             "**登记为阻塞面是很自然的重构**。一旦登记：\n"
             "  ① `:1400` 在 **window 捕获相位** `sIP` ⟹ 桌的**整个阶梯**"
             "（`activeGesture`/导出面板/followTarget/closeWorkspace 四档）"
             "**一次都跑不到**，且**没有报错、没有反馈**；\n"
             "  ② `closeTopForegroundSurface()` 会把导演台**当成阻塞面关掉**，"
             "`focusCanvasRoot()` 把焦点甩到**模态后面的画布**上。\n"
             "★ **当前不可达**（有运行时证据）：导演台打开时对照臂 `cap>=1` "
             "且导出面板真的关了 ⟹ `:1400` 当时没跑；且 director 面**不写**任何"
             "阻塞面开关（%d 个标志全 0 命中），画布 chrome 被 `z-[100]` 盖住。\n"
             "⟹ 但**闸门只差一行枚举**，而这一行没有测试守着。" % (
                 len(payload["blockingSurfaceUnion"]), len(BLOCK_FLAGS)),
     "evidence": "J2 + 阶段二 预测 B + 阶段五 预测 I"},
    {"id": "D8a", "severity": "待拍板（本批为其补授权文本）",
     "text": "★ **D8 会引入一条它没提的层级优先级。** `sIP` 在 director 面"
             "**已经存在** %d 处（%r），而 runtime 已实测它**真的**会挡住"
             "桌的阶梯 ⟹ 照抄到 `DirectorTimeline:570/594` 之后，"
             "**路径菜单开着的状态下 Escape 将不再能取消手势或关导出面板**。"
             "⟹ D8 与 779 的 C779-2（「有活动手势时 Escape 要不要也关层」="
             "**产品决定**）是**同一个待决问题的两半**。"
             % (len(alreadyHave), d8Precedents),
     "evidence": "C782-2 + J3 + J5"},
]
audit = {
    "batch": 782,
    "topic": "键盘主人全量普查（**挂载域**）：四批共同依赖的「那 6 个键只有一个主人」"
             "**被推翻一半**；归因仍成立但依据换成了两道运行时门；新缺陷 D1h",
    "generatedBy": "probes/mk782audit.py",
    "sources": {
        "census782.json": {"sha16": sha(CENSUS), "owners": len(owners)},
        "vb782a.json": {"sha16": sha(RAW), "rounds": len(rounds),
                        "armsPerRound": len(arms)},
    },
    "owners": owners,
    "ownership": {
        "domain": {"directorPlane": len(plane), "mountHost": len(host),
                   "mountHosts": payload["mountHosts"],
                   "note": "★ 同域 = 共用同一个 `window`；只扫 director 目录会漏"
                           "掉挂载页上那 3 个主人（C782-1 的成因）"},
        "bearingKeys": BEAR,
        "singleOwnerKeys": copyPaste,
        "multiOwnerKeys": multi,
        "multiOwnerCount": len(multiOwners),
        "deskOwner": short(deskOwner),
        "typeAwareOwners": typeAware,
        "hostGates": {
            short(gate1401): {"gate": GATE_DIRECTOR,
                              "keyedOnDeskBeingOpen": True,
                              "source": "src/app/page.tsx:1312"},
            short(gate1400): {"gate": GATE_SURFACE,
                              "keyedOnDeskBeingOpen": False,
                              "unionMentionsDirector":
                                  payload["unionMentionsDirector"],
                              "blockingSurfaceUnion":
                                  payload["blockingSurfaceUnion"],
                              "source": "src/app/page.tsx:1294"},
        },
        "escapeOwners": [short(o) for o in escOwners],
        "escapeOwnerCount": len(escOwners),
        "escapeCapture": [short(o) for o in escCapture],
        "escapeBubble": [short(o) for o in escBubble],
        "escapeStopImmediate": [short(o) for o in escSip],
        "escapeStopPropagationOnly": [short(o) for o in escSprop],
        "tabOwners": [short(o) for o in tabOwners],
        "falseTabOwner": {"file": short(gbOwner),
                          "keysExcluded": gbOwner["keysExcluded"]},
        "d8ShapePrecedents": d8Precedents,
        "blockingFlagsInDirectorPlane": planeHits,
    },
    "runtime": {
        "captureOwner": capArm,
        "bubbleOwner": bubArm,
        "none": noneArm,
        "ladderBlockedBySip": ladderBlocked,
        "concurrentOwners": concurrent,
        "positiveControlAlsoCut": capAlsoCut,
        "hostGateClosedNow": hostDormant,
    },
    "verdict": {
        "四批共同依赖的默认": "★ **被推翻一半**：`Meta+c`/`Meta+v` 主人唯一；"
                              "`Meta+z`/`Meta+y`/`Delete`/`Backspace` 主人在"
                              "**挂载域**里是 %d 个（director 目录只有 1 个，"
                              "挂载页 `page.tsx` 还有 2 个）" % len(multiOwners),
        "779/780/781的归因": "★ **仍然成立**（不是部分归因）—— 但依据从"
                             "「代码里只有一个主人」换成「另外两个宿主页主人"
                             "**都被门挡住了**」⟹ 结论一样，**性质更脆**",
        "两道门的性质": "★ `page.tsx:1401` 以 `activeDirectorNodeId` 为条件"
                        "（**显式让位**，可靠）；`page.tsx:1400` 以"
                        "`LibTVBlockingForegroundSurface` 为条件，"
                        "而**那张表里没有导演台**（**靠遗漏**）",
        "Escape主人": "%d 个；阻断强度分**两类**：`sIP` %d 个（全在 capture 相位，"
                      "截断整条链）/ `sP` %d 个（%s，**在目标上**，只挡越过目标的冒泡）"
                      % (len(escOwners), len(escSip), len(escSprop),
                         short(escSprop[0])),
        "排他性是否真的发生": "★ **是** —— captureOwner 臂第 1 次：目标浮层关、"
                              "**导出面板仍开** ⟹ 阶梯被挡住；且 `cap` 也为 0 "
                              "⟹ 连 capture 相位上更早的监听器都没跑到",
        "D8": "★ **是照抄**（director 面已有 %d 处），但会**引入一条它没提的"
              "层级优先级" % len(alreadyHave),
        "Tab": "主人 %d 个（焦点容器 + 页面两个门），**桌面上不排他**"
               "（默认值 false，只有两个移动端调用点开了）；"
               "第一版那个「第二主人」是 `useDirectorGestureBoundary:92` 的"
               "**排除清单**，已剔除" % len(tabOwners),
        "新缺陷 D1h": "★ 导演台的 Escape 阶梯靠「导演台没被登记为阻塞面」"
                      "这个**遗漏**才成立；登记后 `:1400` 会在 window 捕获相位"
                      "`sIP` 掉整条链。当前不可达（运行时已证），但只差一行枚举",
    },
    "comparability": comparability,
    "results": {
        "owners": len(owners),
        "directorPlaneOwners": len(plane),
        "mountHostOwners": len(host),
        "singleOwnerKeys": len(copyPaste),
        "multiOwnerKeys": len(multi),
        "typeAwareOwners": len(typeAware),
        "escapeOwners": len(escOwners),
        "escapeStopImmediate": len(escSip),
        "escapeStopPropagationOnly": len(escSprop),
        "d8Precedents": len(alreadyHave),
        "ladderBlocked": ladderBlocked,
        "capAlsoCut": capAlsoCut,
        "hostGateClosedNow": hostDormant,
        "concurrent": concurrent,
        "cells": CELLS,
        "failedCells": 0,
    },
    "judgments": judgments,
    "corrections": corrections,
    "findings": {
        "F1": "★ **四批的默认被推翻一半**：`Meta+c`/`Meta+v` 主人唯一（真·单主人），"
              "而 `Meta+z`/`Meta+y`/`Delete`/`Backspace` 在**挂载域**里是 **3 个**。"
              "⟹ 成因是**普查域划错了**（只扫 director 目录，漏掉挂载页那 3 个）。",
        "F2": "★ **归因仍然成立**，但依据换成「两道运行时门都关着」，"
              "且阶段五预测 I 给了**运行时**证据（对照臂 `cap>=1` + 导出面板真关）"
              "⟹ 结论一样，**性质更脆**。",
        "F3": "★ **两个宿主页主人的门性质不同**：`:1401` 显式以导演台开着为条件"
              "（可靠让位），`:1400` 靠**枚举里没有导演台**（遗漏）⟹ 缺陷 D1h。",
        "F4": "★ **Escape 的阻断强度分两类**：`sIP`（capture，截断整条链，实测 "
              "`cap=0`）与 `sP`（目标上，只挡越过目标的冒泡）⟹ 第一版合称「排他」"
              "是错的分类，**断言炸的是分类不是机制**（R144）。",
        "F5": "★ **不排他的主人会与阶梯并发**（一次按压关掉两个东西）。",
        "F6": "★ **D8 是照抄**（director 面已有 3 处），但会引入一条它没提的"
              "层级优先级。",
        "F7": "★ **`Tab` 有 3 个真主人**，第一版那个「第二主人」是"
              "`useDirectorGestureBoundary:92` 的**排除清单**⟹ 假主人，R144 的"
              "第二个实例。",
    },
    "probeLessons": probeLessons,
    "defects": defects,
    "srcDiff": "**本批未改 `src/`**（工作区 `src/` 干净）；**没有任何注入**。",
    "rawSha": {"census782.json": sha(CENSUS), "vb782a.json": sha(RAW)},
    "retryStats": comparability["retryStats"],
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)

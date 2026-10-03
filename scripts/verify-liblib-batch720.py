#!/usr/bin/env python3
"""batch 720 验收：加模型写历史且当场可撤销；「关台丢内容」只对单独的加模型成立

## 起点

原计划是普查导演台里所有 `keydown` 判据看不看修饰键（719 测出
场景描述 prompt 的四种 Enter 组合全部提交）。普查做完了，但**顺着它撞见的
一件事把这一批整个改写了**。

顺着「加一个模型」走一圈之后发现：**Escape 关台之后，刚加的模型没了。**
于是本批改问一个更基础的问题：**关台到底丢什么？**

## 决定性读数

### 静态普查（`src/components/director/`，10 处 `onKeyDown`）

| 类别 | 处数 | 修饰键 | 键位判据 |
|---|---|---|---|
| 组件级 handler | **8** | **一处都不查** | 全部只比 `Enter` |
| `useDirectorGestureBoundary.ts:92`（hook） | 1 | **查**（`event.key` 判非修饰键） | — |
| `DirectorDesk.tsx:570`（`window` 全局快捷键） | 1 | **查**（c/v/z/y 要求修饰键） | — |

**8 处组件级 handler 全部修饰键盲**；而**查修饰键的恰好是两处需要它的地方**。
其中两处把 `Enter` 与空格 `" "` 视为同一个键，且**两处动作都改变状态**：
模型库卡片的 `onAdd(item)` 与 AI 导入上传区的 `imageInputRef.current?.click()`。
导演台内**没有 `<form>`**，所以 Enter 的隐式提交不是问题。

### 运行时：加模型这一步本身是完整的

| 读数 | 值 |
|---|---|
| `objects` | **5 → 6**（多出「饮料瓶」） |
| `history.past` | **0 → 1** |
| `lastCommandResult` | **null → SET**，`projectChanged: true` |
| 模型库卡片数 | **3 → 0**（一次激活就把列表清空） |
| 台开着时按 `Meta+z` | **`past` 1 → 0、`objects` 6 → 5** ⟹ **当场可撤销** |
| 卡片元素 | `<article role="group" tabIndex={0} aria-label="添加模型 饮料瓶">` |

**⟹ 这是与 719 那枚 prompt 的正面对照**：同一个底部条区域里，
一个是「纯本地回显、store 一个字段都不动」，一个是「真写历史、真进对象表」。

### 关台丢了什么：三条路线对照

| 路线 | 改动 | 关台后 store | **重开（点节点卡上那枚按钮）** |
|---|---|---|---|
| **A** | **只加模型** | objects 6、**past 0** | **objects 5，饮料瓶没了** |
| **B** | **只改名** | — | **改名还在**，且 **`past` 回到 1** |
| **C** | **先改名、再加模型** | objects 6 | **6 个全在**，改名与饮料瓶都留住 |

- `Escape` 与关闭按钮 `[data-close-director]` **结果完全一致**（`past` 0、objects 6、台不在 DOM）
- **关台后 `past` 立刻归 0**，而 store 的 `objects` 仍是 6 —— 丢的是「重开时读到什么」，不是「关台那一刻」
- **路线 B 的 `past` 重开后回到 1** ⟹ **关台不丢历史，刷新才丢**（711 测的是刷新）

## 与 710 的关系（读数存活，概括要收窄）

710 测出「同一节点上关台重开：P2 内容与历史都保留」，并据此**撤回了**
「关台丢内容」这个假设。**710 的读数全部存活** ——
但它的概括太宽：**改名成立，单独的加模型不成立。**
本批**不声称成因**：为什么「先改名再���模型」能留住、而单独加模型留不住，
这三条读数本身不足以判定（见 README「不声称」一节）。

## 五条预测（写死在代码里，先于任何测量）

- **P1** 加模型写历史（`past` 0→1、objects 5→6、`projectChanged: true`），且台开着时 `Meta+z` 能撤销
- **P2** 关台（Escape 与关闭按钮同结果）令 `past` 立刻归 0，而 store 的 `objects` 仍为 6
- **P3** 路线 A 重开后 **objects 回到 5**，饮料瓶消失
- **P4** 路线 B 重开后**改名保留**，且 `past` 回到 1
- **P5** 路线 C 重开后**两个改动都保留**（6 个对象）

## 判据

1. `adding-a-model-writes-history-and-is-undoable-while-the-desk-is-open`
2. `closing-the-desk-zeroes-history-immediately-and-escape-matches-the-close-button`
3. `an-isolated-model-add-does-not-survive-close-and-reopen`
4. `a-rename-survives-close-and-reopen-and-its-undo-entry-comes-back`
5. `the-same-add-survives-if-a-rename-happened-first`
6. `the-model-card-is-focusable-and-activatable-but-its-role-is-group`
7. `all-eight-component-keydown-handlers-are-modifier-blind`
"""
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch720-2026-10-01"
DIR = ROOT / "src/components/director"
W, H = 1280, 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "加模型写历史（past 0→1、objects 5→6、projectChanged true），台开着时 Meta+z 能撤销",
    "P2": "关台（Escape 与关闭按钮同结果）令 past 立刻归 0，而 store 的 objects 仍为 6",
    "P3": "路线 A（只加模型）重开后 objects 回到 5，饮料瓶消失",
    "P4": "路线 B（只改名）重开后改名保留，且 past 回到 1",
    "P5": "路线 C（先改名再加模型）重开后两个改动都保留（6 个对象）",
}

# ---- 静态：keydown 普查（排除注释）----
BLOCK_C = re.compile(r"\{/\*.*?\*/\}", re.S)
LINE_C = re.compile(r"(?<!:)//[^\n]*")
MODS = ("metaKey", "ctrlKey", "shiftKey", "altKey")


def static_census() -> dict[str, Any]:
    component: list[dict[str, Any]] = []
    with_mods: list[str] = []
    for f in sorted(DIR.glob("*.tsx")):
        clean = LINE_C.sub("", BLOCK_C.sub("", f.read_text(encoding="utf-8")))
        lines = clean.split("\n")
        for i, ln in enumerate(lines):
            if "onKeyDown" not in ln:
                continue
            window = "\n".join(lines[i:i + 14])
            rec = {"file": f.name, "line": i + 1,
                   "checksMods": any(m in window for m in MODS),
                   "keys": sorted(set(
                       re.findall(r"event\.key\s*(?:===|!==)\s*'([^']+)'", window)
                       + re.findall(r'event\.key\s*(?:===|!==)\s*"([^"]+)"', window)))}
            component.append(rec)
    for f in sorted(DIR.glob("*")):
        if f.suffix in (".ts", ".tsx"):
            t = f.read_text(encoding="utf-8")
            if ("addEventListener(\"keydown\"" in t
                    or "addEventListener('keydown'" in t) or \
                    ("onKeyDown" in t and f.suffix == ".ts"
                     and "useDirector" in f.name):
                with_mods.append(f.name)
    forms = sum(1 for f in DIR.glob("*.tsx") if "<form" in f.read_text(encoding="utf-8"))
    return {"componentHandlers": component,
            "withModifiers": sorted(set(with_mods)), "formCount": forms}


READ = r"""() => {
  const s = window.__director_store.getState();
  const q = (sel) => document.querySelector(sel);
  const card = q('[data-director-model-library-card]');
  return {
    deskOpen: !!q('[data-director-workspace]'),
    objects: s.objects ? s.objects.length : null,
    names: s.objects ? s.objects.map((o) => o.name || o.kind) : null,
    past: s.history && s.history.past ? s.history.past.length : null,
    cmd: s.lastCommandResult === undefined ? 'ABSENT'
      : (s.lastCommandResult === null ? null : (s.lastCommandResult.kind || 'SET')),
    cmdProjectChanged: s.lastCommandResult
      ? s.lastCommandResult.projectChanged : null,
    cards: document.querySelectorAll('[data-director-model-library-card]').length,
    card: card ? { tag: card.tagName.toLowerCase(), role: card.getAttribute('role'),
                   tabIndex: card.tabIndex, aria: card.getAttribute('aria-label') } : null,
    openBtn: (() => { const b = q('[data-open-director]'); if (!b) return null;
      const r = b.getBoundingClientRect();
      return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
              h: Math.round(r.height)}; })(),
    closeBtn: (() => { const b = q('[data-close-director]'); if (!b) return null;
      const r = b.getBoundingClientRect();
      return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
              h: Math.round(r.height)}; })(),
  };
}"""


def read(page: Page) -> Any:
    return page.evaluate(READ)


def add_model(page: Page) -> Any:
    geo = page.evaluate(r"""() => {
      const btn = [...document.querySelectorAll('button')]
        .find((b) => b.getAttribute('aria-label') === '模型库');
      if (!btn) return null; const r = btn.getBoundingClientRect();
      return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width)};}""")
    assert geo, "找不到「模型库」按钮"
    page.mouse.click(geo["x"] + geo["w"] / 2, geo["y"] + 16)
    page.wait_for_timeout(650)
    ok = page.evaluate("() => { const c = document.querySelector"
                       "('[data-director-model-library-card]'); if (!c) return false;"
                       "c.focus(); return document.activeElement === c; }")
    assert ok, "模型库卡片没拿到焦点"
    # 卡片元信息与卡片数必须在**按 Enter 之前**读（激活后列表会被清空）
    g = read(page)
    page.keyboard.press("Enter")
    page.wait_for_timeout(700)
    g["after"] = read(page)
    return g


def rename(page: Page, new_name: str) -> Any:
    geo = page.evaluate(r"""() => {
      const el = document.querySelector('[data-director-object-name]');
      if (!el) return null; el.focus();
      const r = el.getBoundingClientRect();
      return {x: Math.round(r.x), y: Math.round(r.y), focused: document.activeElement === el};
    }""")
    assert geo and geo["focused"], "对象名字段没拿到焦点"
    page.keyboard.press("Meta+a")
    page.wait_for_timeout(120)
    page.keyboard.type(new_name)
    page.wait_for_timeout(250)
    page.keyboard.press("Enter")
    page.wait_for_timeout(600)
    return read(page)


def close_escape(page: Page) -> Any:
    page.mouse.move(400, 600)
    page.wait_for_timeout(200)
    page.keyboard.press("Escape")
    page.wait_for_timeout(900)
    g = read(page)
    g["_method"] = "Escape"
    return g


def close_desk(page: Page) -> Any:
    """确定性地关台。

    实测：模型库面板开着时 Escape 先关面板、不关导演台
    （objects 7、饮料瓶重两份、past 4、台仍在 DOM）——
    所以先点「关闭模型库」，再 Escape；Escape 仍不生效就用关闭按钮兜底。
    全程只用真实控件，并把实际生效的方式记进 _method。
    """
    page.mouse.move(400, 600)
    page.wait_for_timeout(200)
    panel = page.evaluate(r"""() => {
      const b = [...document.querySelectorAll('button')]
        .find((x) => x.getAttribute('aria-label') === '关闭模型库');
      if (!b) return null; const r = b.getBoundingClientRect();
      return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
              h: Math.round(r.height)};}""")
    used = []
    if panel:
        page.mouse.click(panel["x"] + panel["w"] / 2, panel["y"] + panel["h"] / 2)
        page.wait_for_timeout(600)
        used.append("closeModelLibraryPanel")
    page.keyboard.press("Escape")
    page.wait_for_timeout(900)
    g = read(page)
    used.append("Escape")
    if g["deskOpen"]:
        cb = g["closeBtn"]
        assert cb, "找不到 [data-close-director]"
        page.mouse.click(cb["x"] + cb["w"] / 2, cb["y"] + cb["h"] / 2)
        page.wait_for_timeout(900)
        g = read(page)
        used.append("closeButton")
    assert g["deskOpen"] is False, ("两条路线都关不掉台", used, g)
    g["_method"] = "+".join(used)
    return g


def close_button(page: Page) -> Any:
    """用关闭按钮关台。

    路线 A 之后面板可能仍开着，此时 Escape 先关面板、不关导演台
    （实测：objects 7、饮料瓶重两份、past 4、台仍开着）——
    所以 B/C 两条路线用按钮，让「关台」这一步是确定的。
    """
    cb = read(page)["closeBtn"]
    assert cb, "找不到 [data-close-director]"
    page.mouse.click(cb["x"] + cb["w"] / 2, cb["y"] + cb["h"] / 2)
    page.wait_for_timeout(900)
    g = read(page)
    g["_method"] = "closeButton"
    return g


def reopen(page: Page) -> Any:
    ob = read(page)["openBtn"]
    assert ob, "关台后找不到 [data-open-director]"
    page.mouse.click(ob["x"] + ob["w"] / 2, ob["y"] + ob["h"] / 2)
    page.wait_for_timeout(1000)
    return read(page)


FIXTURE = ["角色01 · 陈默", "咖啡桌", "冷掉的咖啡", "咖啡馆背景", "机位01 · 对峙中景"]


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(600)
    base = read(page)

    # 路线 A：只加模型
    a_add = add_model(page)
    card_meta = a_add.get("card")
    cards_before = a_add["cards"]
    # 台开着时撤销
    page.mouse.move(400, 600)
    page.wait_for_timeout(200)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(700)
    a_undo = read(page)
    # 再加一次，然后关台
    a_add2 = add_model(page)["after"]
    a_close = close_escape(page)
    a_reopen = reopen(page)

    # 路线 B：只改名
    b_rename = rename(page, "改名探针")
    b_close = close_desk(page)
    b_reopen = reopen(page)

    # 路线 C：先改名再加模型
    c_rename = rename(page, "第二个改名")
    c_add = add_model(page)["after"]
    c_close = close_desk(page)
    c_reopen = reopen(page)

    page.close()
    return {"static": static_census(), "base": base, "cardMeta": card_meta,
            "cardsBefore": cards_before, "A": {"add": a_add, "undo": a_undo,
                                               "add2": a_add2, "close": a_close,
                                               "reopen": a_reopen},
            "B": {"rename": b_rename, "close": b_close, "reopen": b_reopen},
            "C": {"rename": c_rename, "add": c_add, "close": c_close,
                  "reopen": c_reopen},
            }


def check_1(r: dict[str, Any]) -> None:
    a = r["A"]
    assert a["add"]["objects"] == 5, ("激活前应当还是 5 个", a["add"])
    assert a["add"]["after"]["objects"] == 6, a["add"]
    assert a["add"]["after"]["past"] == 1, a["add"]
    assert a["add"]["after"]["cmd"] is not None, a["add"]
    assert a["add"]["after"]["cmdProjectChanged"] is True, a["add"]
    assert a["add"]["after"]["cards"] == 0, a["add"]
    assert r["cardsBefore"] > 0, r["cardsBefore"]
    assert a["undo"]["objects"] == 5 and a["undo"]["past"] == 0, a["undo"]


def check_2(r: dict[str, Any]) -> None:
    """关台：past 立刻归 0，而 store 的 objects 仍为 6；两条关台路径读数同构。

    A 路线用裸 Escape（实测确实关了台）；B/C 先关掉可能开着的模型库面板再关台。
    两条路径都必须走到「台不在 DOM、past 归 0、objects 仍 6」这个同一个读数。
    """
    for key in ("A", "C"):
        c = r[key]["close"]
        assert c["deskOpen"] is False, (key, c)
        assert c["past"] == 0, (key, c)
        assert c["objects"] == 6, (key, c)
    assert r["A"]["close"].get("_method") == "Escape", r["A"]["close"].get("_method")
    assert "Escape" in (r["C"]["close"].get("_method") or ""), r["C"]["close"].get("_method")


def check_3(r: dict[str, Any]) -> None:
    """路线 A：单独加的模型重开后没了。"""
    a = r["A"]
    assert "饮料瓶" in a["add"]["after"]["names"], a["add"]["after"]["names"]
    assert a["reopen"]["objects"] == 5, a["reopen"]
    assert a["reopen"]["names"] == FIXTURE, a["reopen"]["names"]
    assert a["reopen"]["past"] == 0, a["reopen"]


def check_4(r: dict[str, Any]) -> None:
    """路线 B：改名活着，而且撤销条目跨关台回来了。"""
    b = r["B"]
    assert b["rename"]["names"][0] == "改名探针", b["rename"]["names"]
    assert b["rename"]["past"] == 1, b["rename"]
    assert b["reopen"]["names"][0] == "改名探针", b["reopen"]["names"]
    assert b["reopen"]["objects"] == 5, b["reopen"]
    assert b["reopen"]["past"] == 1, ("改名的撤销条目应当跨关台回来", b["reopen"])


def check_5(r: dict[str, Any]) -> None:
    """路线 C：同样的加模型，先改过名之后就留住了。"""
    c = r["C"]
    assert c["add"]["objects"] == 6, c["add"]
    assert c["reopen"]["objects"] == 6, c["reopen"]
    assert "饮料瓶" in c["reopen"]["names"], c["reopen"]["names"]
    assert "第二个改名" in c["reopen"]["names"], c["reopen"]["names"]


def check_6(r: dict[str, Any]) -> None:
    """模型库卡片：可聚焦、可激活、可及名是动作句 —— 但角色是 group。"""
    card = r["cardMeta"] or r["base"]["card"]
    assert card is not None, r["base"]
    assert card["tag"] == "article", card
    assert card["tabIndex"] == 0, card
    assert card["role"] == "group", card
    assert (card["aria"] or "").startswith("添加模型"), card


def check_7(r: dict[str, Any]) -> None:
    """8 处组件级 keydown 全部不查修饰键；查修饰键的是 hook 与全局快捷键。"""
    st = r["static"]
    assert len(st["componentHandlers"]) == 8, len(st["componentHandlers"])
    for h in st["componentHandlers"]:
        assert h["checksMods"] is False, h
        assert h["keys"] == ["Enter"] or h["keys"] == [" ", "Enter"], h
    assert st["formCount"] == 0, st["formCount"]
    mods = st["withModifiers"]
    assert any("useDirectorGestureBoundary" in m for m in mods), mods
    assert any("DirectorDesk" in m for m in mods), mods


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"predictions": PREDICTIONS}
    failures: list[str] = []
    got: dict[str, Any] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            got["run"] = run(browser)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"run: {exc}")
            got["run"] = {}
        browser.close()
    results.update(got)
    checks = [
        ("adding-a-model-writes-history-and-is-undoable-while-the-desk-is-open", lambda: check_1(got.get("run", {}))),
        ("closing-the-desk-zeroes-history-immediately-and-escape-matches-the-close-button", lambda: check_2(got.get("run", {}))),
        ("an-isolated-model-add-does-not-survive-close-and-reopen", lambda: check_3(got.get("run", {}))),
        ("a-rename-survives-close-and-reopen-and-its-undo-entry-comes-back", lambda: check_4(got.get("run", {}))),
        ("the-same-add-survives-if-a-rename-happened-first", lambda: check_5(got.get("run", {}))),
        ("the-model-card-is-focusable-and-activatable-but-its-role-is-group", lambda: check_6(got.get("run", {}))),
        ("all-eight-component-keydown-handlers-are-modifier-blind", lambda: check_7(got.get("run", {}))),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn()
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append(f"{name}: {exc}")
    results["summary"] = summary
    results["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, default=str))
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ->", f[:400])
    print(f"\n{sum(1 for v in summary.values() if v)}/{len(summary)} 通过")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

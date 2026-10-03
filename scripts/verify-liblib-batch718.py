#!/usr/bin/env python3
"""batch 718 验收：任意媒体查询断点普查 —— 899 的 min/max 分区完整，「差 1」是 Tailwind 的语义不是缺陷

## 起点

717 撞见「`max-[899px]` 字面 899、实际生效 898」，并留下一个拍板项：
**要不要把这类写法统一成无歧义的**。

本批把问题一次性问全：**代码里所有任意媒体查询断点的分区是不是完整的？**
办法是**静态普查（必须排除注释）+ 运行时逐像素验证**。

## 决定性读数

### 静态（排除注释后，`src/` 7 个文件）

| 断点 | `min-[Npx]` | `max-[Npx]` | 分区 |
|---|---|---|---|
| **899** | **15** | **22** | `≥899` ∪ `<899` = **完整** |
| 850 | 0 | 2 | 单向 |
| 680 | 1 | 0 | 单向 |
| 620 | 0 | 1 | 单向 |
| 520 | 0 | 6 | 单向 |
| 480 | 1 | 0 | 单向 |
| 430 | 0 | 1 | 单向 |

**只有 899 是成对的**，且成对写法正是 `min-[899px]` + `max-[899px]` ⟹ **没有 1px 空洞**。

### 静态普查的第一个结果是假阳性

第一次普查（不排除注释）报出 `DirectorIconRail.tsx` 同时用
`min-[900px]` 与 `max-[899px]`，并据此以为分区漏了 899 那一格。
**那两个 token 只存在于 `DirectorIconRail.tsx:430-436` 的注释里** ——
那正是 batch 623 记录并**已经修好**这件事的地方（原文写着「Tailwind v4 把
`max-[899px]` 编译成 `@media (width < 899px)`…于是 899 那一格两边都不命中」）。
代码里实际是 `min-[899px]:flex`。

### 运行时：同一个名字，两种边界语义

`vw = 899` 这一格：

| 查询 | 命中？ |
|---|---|
| `matchMedia('(max-width: 899px)')` —— **CSS 原生** | **True（含等号）** |
| `matchMedia('(width < 899px)')` —— **Tailwind v4 变体实际编译成的** | **False** |
| `matchMedia('(width >= 899px)')` | **True** |
| 头部 `padding-right`（`max-[899px]:px-2` 的一处） | 已经是 **260px** ⟹ max 变体**没生效** |

⟹ **`max-[899px]` 与同名的 CSS `(max-width: 899px)` 边界相反**，
这正是 623 记录、717 又从外面撞了一次的那个 1px 陷阱。

### 运行时：分区完整，三个探针同步翻转

逐像素扫 894…906，三处**互相独立**的证据在 **898|899** 之间同时翻转：

| 探针 | ≤898 | ≥899 |
|---|---|---|
| icon rail（`hidden … min-[899px]:flex w-12 top-[52px]`） | `display: none` | `display: flex` |
| 头部 `padding-right` | **8px** | **260px** |
| 抽屉 `left`（`min-[899px]:left-12`） | **0px** | **48px** |

每个宽度上**恰好命中一个分支**（互斥且穷尽）⟹ 分区无空洞。

### 断点换的是「常驻竖条 ↔ 浮动按钮对」

717 记的两枚 `display` 切换叶子，现在都有身份了：

- **48×1098**：`w-12` + `top-[52px]` + `hidden min-[899px]:flex` 的 **icon rail**
- **68×32**：`absolute left-3 top-3 z-10 hidden gap-1 max-[899px]:flex` 的
  **浮动按钮对**，内含两枚命名按钮「打开场景对象」「打开属性面板」

**两枚切换完全互补**：宽屏给常驻竖条、窄屏给浮动按钮对。
容器本身没有 `data-*` 与 `aria-label`，但它是纯 flex 包裹层，
两个子按钮都有可及名 ⟹ **不是无障碍缺口**。

## 五条预测（写死在代码里，先于任何测量）

- **P1** 排除注释后**只有 899 成对**，其余 6 个断点单向 ⟹ 无成对空洞
- **P2** `min-[900px]:` 只存在于注释里，代码是 `min-[899px]:flex`（623 的修复在位）
- **P3** `max-[899px]` 实际是 `< 899`（严格小于），与同名 CSS `(max-width: 899px)`（含等号）**相反**
- **P4** 三个独立探针在 898\|899 之间同步翻转，且每个宽度**恰好命中一个分支**
- **P5** 断点换的是 48px 常驻竖条 ↔ 68×32 浮动按钮对，两枚切换互补

## 判据

1. `only-899-is-paired-the-rest-are-one-sided`
2. `the-min-900px-pair-only-survives-in-a-comment`
3. `max-899px-is-strictly-less-than-while-the-css-query-is-inclusive`
4. `the-two-branches-are-mutually-exclusive-and-jointly-exhaustive`
5. `the-breakpoint-swaps-a-48px-rail-for-a-68x32-button-pair`
6. `retraction-of-717-the-899-boundary-is-by-construction`
"""
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch718-2026-10-01"
SRC = ROOT / "src"
H = 1150

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "排除注释后只有 899 成对，其余 6 个断点单向 —— 无成对空洞",
    "P2": "min-[900px]: 只存在于注释里，代码是 min-[899px]:flex（623 的修复在位）",
    "P3": "max-[899px] 实际是 < 899（严格小于），与同名 CSS (max-width: 899px) 相反",
    "P4": "三个独立探针在 898|899 之间同步翻转，且每个宽度恰好命中一个分支",
    "P5": "断点换的是 48px 常驻竖条 <-> 68x32 浮动按钮对，两枚切换互补",
}

# ---- 静态：排除注释的任意媒体查询变体普查 ----
BLOCK_C = re.compile(r"\{/\*.*?\*/\}", re.S)
LINE_C = re.compile(r"(?<!:)//[^\n]*")
VAR_C = re.compile(r"(min|max)-\[(\d+)px\]:")
# 注释里常写成 `min-[900px]`（**不带冒号**），所以查「只在注释里」要用宽松模式
VAR_LOOSE = re.compile(r"(min|max)-\[(\d+)px\]")


def strip_comments(src: str) -> str:
    out = BLOCK_C.sub(lambda m: "\n" * m.group(0).count("\n"), src)
    return LINE_C.sub("", out)


def static_census() -> dict[str, Any]:
    paired: dict[int, dict[str, Any]] = defaultdict(lambda: {"min": 0, "max": 0})
    in_code: list[str] = []
    in_comment: list[str] = []
    for f in sorted(SRC.rglob("*.tsx")) + sorted(SRC.rglob("*.ts")):
        text = f.read_text(encoding="utf-8")
        clean = strip_comments(text)
        for m in VAR_C.finditer(clean):
            paired[int(m.group(2))][m.group(1)] += 1
            in_code.append(f"{m.group(1)}-[{m.group(2)}px]:")
        # 注释里出现、代码里没有的 token
        for tok in set(VAR_LOOSE.findall(text)):
            bare = f"{tok[0]}-[{tok[1]}px]"
            withcolon = bare + ":"
            if withcolon not in clean and bare not in clean:
                in_comment.append(f"{f.relative_to(ROOT)}:{bare}")
    return {"counts": {str(k): v for k, v in sorted(paired.items(), reverse=True)},
            "codeTokens": sorted(set(in_code)),
            "commentOnlyTokens": sorted(set(in_comment))}


# ---- 运行时 ----
PROBE = r"""() => {
  const out = { vw: innerWidth, mq: {} };
  for (const n of [899, 900]) {
    out.mq['cssMax' + n] = matchMedia('(max-width: ' + n + 'px)').matches;
    out.mq['lt' + n] = matchMedia('(width < ' + n + 'px)').matches;
    out.mq['ge' + n] = matchMedia('(width >= ' + n + 'px)').matches;
  }
  const find = (pred) => [...document.querySelectorAll('*')].find(pred);
  // 按**类名**认领，不按几何：窄屏下 display:none 时宽度是 0，按几何找会找不到
  const rail = find((el) => typeof el.className === 'string'
    && el.className.includes('min-[899px]:flex')
    && el.className.includes('w-12') && el.className.includes('top-[52px]')
    && el.className.includes('hidden'));
  out.rail = rail ? { display: getComputedStyle(rail).display,
    w: Math.round(rail.getBoundingClientRect().width),
    h: Math.round(rail.getBoundingClientRect().height),
    y: Math.round(rail.getBoundingClientRect().y) } : null;
  const pair = find((el) => typeof el.className === 'string'
    && el.className.includes('max-[899px]:flex')
    && el.className.includes('left-3') && el.className.includes('top-3')
    && el.className.includes('hidden') && el.className.includes('gap-1'));
  out.pair = pair ? { display: getComputedStyle(pair).display,
    kids: [...pair.children].map((c) => c.getAttribute('aria-label') || '?') } : null;
  const hdr = document.querySelector('[data-director-timeline-controls]');
  out.headerPr = hdr ? getComputedStyle(hdr).paddingRight : null;
  const drawer = find((el) => typeof el.className === 'string'
    && el.className.includes('min-[899px]:left-12')
    && el.className.includes('w-[233px]'));
  out.drawerLeft = drawer ? getComputedStyle(drawer).left : null;
  return out;
}"""

SWEEP = list(range(894, 907)) + [898, 899, 900, 1280]


def open_page(browser: Any) -> Page:
    page = browser.new_page(viewport={"width": 1280, "height": H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(500)
    return page


def run(browser: Any) -> dict[str, Any]:
    page = open_page(browser)
    sweep = []
    for vw in SWEEP:
        page.set_viewport_size({"width": vw, "height": H})
        page.wait_for_timeout(280)
        sweep.append(page.evaluate(PROBE))
    page.close()
    return {"static": static_census(), "sweep": sweep}


def check_1(r: dict[str, Any]) -> None:
    c = r["static"]["counts"]
    assert set(c) == {"899", "850", "680", "620", "520", "480", "430"}, sorted(c)
    both = [n for n, v in c.items() if v["min"] and v["max"]]
    assert both == ["899"], both
    assert c["899"]["min"] == 15 and c["899"]["max"] == 22, c["899"]
    for n in ("850", "620", "520", "430"):
        assert c[n]["max"] >= 1 and c[n]["min"] == 0, (n, c[n])
    for n in ("680", "480"):
        assert c[n]["min"] >= 1 and c[n]["max"] == 0, (n, c[n])


def check_2(r: dict[str, Any]) -> None:
    """623 的修复在位：`min-[900px]:` 只活在注释里。"""
    st = r["static"]
    assert "min-[900px]:" not in st["codeTokens"], st["codeTokens"]
    assert any("min-[900px]" in t for t in st["commentOnlyTokens"]), \
        st["commentOnlyTokens"]
    rail = [g for g in r["sweep"] if g["vw"] == 900][0]
    assert rail["rail"] is not None, "icon rail 在 900 下没被认出来"


def check_3(r: dict[str, Any]) -> None:
    """同名不同义：CSS `(max-width: 899px)` 含等号，Tailwind `max-[899px]` 严格小于。"""
    g = [x for x in r["sweep"] if x["vw"] == 899][0]
    assert g["mq"]["cssMax899"] is True, g["mq"]
    assert g["mq"]["lt899"] is False, g["mq"]
    assert g["mq"]["ge899"] is True, g["mq"]
    # max 变体在 899 上确实没生效（头部已经是宽屏的 260px）
    assert g["headerPr"] == "260px", g["headerPr"]
    g900 = [x for x in r["sweep"] if x["vw"] == 900][0]
    assert g900["mq"]["cssMax899"] is False, g900["mq"]


def check_4(r: dict[str, Any]) -> None:
    """三个独立探针在 898|899 之间同步翻转，且每个宽度恰好命中一个分支。"""
    by_vw = {g["vw"]: g for g in r["sweep"]}
    for vw in list(range(894, 907)) + [1280]:
        g = by_vw[vw]
        assert g["rail"] is not None and g["pair"] is not None, (vw, g)
        rail_on = g["rail"]["display"] == "flex"
        pair_on = g["pair"]["display"] == "flex"
        assert rail_on != pair_on, (vw, g["rail"], g["pair"])      # 互斥
        assert rail_on == (vw >= 899), (vw, g)                    # 穷尽且边界正确
        assert g["headerPr"] == ("8px" if vw <= 898 else "260px"), (vw, g["headerPr"])
        assert g["drawerLeft"] == ("0px" if vw <= 898 else "48px"), (vw, g["drawerLeft"])
    # 三个探针的翻转点必须同在 898|899
    flips = {}
    for name, path in (("rail", lambda g: g["rail"]["display"] == "flex"),
                       ("headerPr", lambda g: g["headerPr"] == "260px"),
                       ("drawerLeft", lambda g: g["drawerLeft"] == "48px")):
        on = [vw for vw in range(894, 907) if path(by_vw[vw])]
        assert on, name
        flips[name] = min(on)
    assert set(flips.values()) == {899}, flips


def check_5(r: dict[str, Any]) -> None:
    """断点换的是 48px 常驻竖条 ↔ 68×32 浮动按钮对。"""
    wide = [g for g in r["sweep"] if g["vw"] == 1280][0]
    narrow = [g for g in r["sweep"] if g["vw"] == 898][0]
    assert wide["rail"]["w"] == 48 and wide["rail"]["display"] == "flex", wide["rail"]
    assert wide["rail"]["y"] == 52 and wide["rail"]["h"] > 1000, wide["rail"]
    assert wide["pair"]["display"] == "none", wide["pair"]
    assert narrow["rail"]["display"] == "none", narrow["rail"]
    assert narrow["pair"]["display"] == "flex", narrow["pair"]
    # 那对按钮都有可及名 ⟹ 容器无 aria 不是缺口
    # 用集合比较：中文按码点排序（场 0x573A < 属 0x5C5E），列表顺序不可靠
    assert set(wide["pair"]["kids"]) == {"打开场景对象", "打开属性面板"}, wide["pair"]


def check_6(r: dict[str, Any]) -> None:
    """撤回 717 的待拍板项：899 走宽屏分支是**构造出来的**，不是差 1 的缺陷。

    竖条自己的类就是 `min-[899px]:flex`（不是 `min-[900px]`），
    于是「≥899 是宽屏」是写出来的定义；7 个断点里也没有别的成对分区。
    """
    st = r["static"]
    assert "min-[899px]:" in st["codeTokens"], st["codeTokens"]
    assert st["counts"]["899"]["min"] >= 1 and st["counts"]["899"]["max"] >= 1
    for n, v in st["counts"].items():
        if n == "899":
            continue
        assert not (v["min"] and v["max"]), (n, v)   # 其余没有配对
    # 而 623 记录的那个错开一像素的老写法确实已被替换掉
    assert any("DirectorIconRail.tsx:min-[900px]" in t
               for t in st["commentOnlyTokens"]), st["commentOnlyTokens"]


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
        ("only-899-is-paired-the-rest-are-one-sided", lambda: check_1(got.get("run", {}))),
        ("the-min-900px-pair-only-survives-in-a-comment", lambda: check_2(got.get("run", {}))),
        ("max-899px-is-strictly-less-than-while-the-css-query-is-inclusive", lambda: check_3(got.get("run", {}))),
        ("the-two-branches-are-mutually-exclusive-and-jointly-exhaustive", lambda: check_4(got.get("run", {}))),
        ("the-breakpoint-swaps-a-48px-rail-for-a-68x32-button-pair", lambda: check_5(got.get("run", {}))),
        ("retraction-of-717-the-899-boundary-is-by-construction", lambda: check_6(got.get("run", {}))),
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

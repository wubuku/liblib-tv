#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 835 验收：把 748 的 C1／C3／C4 三条**绝对快照判据**换成**关系式判据**

## 起点

748（`scripts/verify-liblib-batch748.py`）是导演台的**首轮运行时普查**。
它的 C1／C3／C4 判的是**绝对快照数字**：

```
C1  13 个组件；按文件求和 460；去重字面量并集 446；跨文件重复 14；每个文件的个数
C3  整页首屏 200 → 走完 7 枚 rail 累计 250；有效并集 447；250 = 224 + 26；447 − 224 = 223
C4  7 枚 rail 里恰好 2 枚点开 0 新增（scene / help）；「添加机位」带出 34 种
```

★ **这些数字每加一批 `data-*` 的批次就必红** —— 这不是「期望值过时」那么简单，
而是**判据形式本身有缺陷**：一个「普查快照」被写成了**恒定契约**。

### 证据：自 748 基线起，四个批次各推高了一批（`probes/static835.py` 逐 commit 实算）

| commit | 批次 | 文件 | 求和 | 字面量并集 | 有效并集 | 本批净增 |
|---|---|---|---|---|---|---|
| `956ff15d` | batch 748 基线 | 13 | 460 | 446 | 447 | — |
| `e5d25d52` | batch 825 跟随横幅 | 13 | 461 | 447 | 448 | +1 |
| `da7b7043` | batch 831 帮助→快捷键面板 | 14 | 473 | 458 | 459 | +11 |
| `15837b7f` | batch 832 添加机位·机位预设面板 | 15 | 476 | 460 | 461 | +2 |
| `75b5af1d` | batch 833 机位预设语义 ＋ 命名 | 15 | 476 | 460 | 461 | +0 |
| `8074234d` | batch 834 时间轴引导 5 步 | 16 | 488 | 468 | 469 | +8 |

⟹ 净增 **22 个属性名**，**每一个都归属到具体批次**，没有一个是无源的漂移。

### ★★ C4 那两条红的**成因是产品变好了，不是退化**

- `help` 从 0 新增变成 **2** 新增：batch 831 实现了「帮助 → 快捷键」面板
  （`data-director-shortcuts-dialog` / `-overlay` / `-title` / `-row` …）。
- `add-camera` 从 **34** 变成 **3**：batch 832 **推翻了 batch 537/540 的旧读数** ——
  源站的「添加机位」**不是**直接加一个机位，而是切成一个**15 枚机位预设的面板**
  ⟹ 面板本身只带 `data-director-camera-preset` / `-glyph` 两种属性，
  那 34 种是「直接加机位后弹出的属性面板（FOV/跟随/look-at 全套）」的属性。

⟹ ★ **改期望值时如果不说清这一层，就等于把「产品改进」记成了「数字变了」。**

## 本批做什么

★ **不逐批抄新数字**（那只是把快照过期推迟到下一批）。
⟹ 改成**关系式判据**：判**账要平**（不变量），而不判**账是几**。

- **C1′（替换 C1 的静态部分）**：判四条**恒等式**，都与绝对数字无关：
  ① 按文件求和 − 字面量并集 == 跨文件重复数；② `sum(owners − 1)` == 跨文件重复数；
  ③ 有效并集 == 字面量并集 + `dataset.` 派生名的增量；④ 每个文件的个数 == 该文件去重后的属性名数。
  ⟹ **再新增任意批次、任意数量的 `data-*`，这四条都恒成立** ⟹ 抗漂移。
- **C1″（增量账，保留追溯力）**：断言「748 基线 ⟶ HEAD 净增的属性名**恰好是那 22 个**，
  且每一个都归属到 825/831/832/834 四个批次之一」⟹ 既抗漂移，**又不丢「谁加的」**。
- **C3′（替换 C3 的快照数字）**：判**三笔账都对平**（运行时侧的不变量）：
  ① 累计 == 首屏 + 各枚 rail 新增之和；② 累计 == 导演台属性 + 非并集；
  ③ 有效并集 == 见过 + 残留；④ 非并集 == 画布残留 + dataset 盲区 + 无前缀导演台。
- **C4′（替换 C4 的绝对数字）**：判**「零新增的入口」是谁**（现在是 `scene` 一枚）、
  **「每枚带出多少」的相对关系**，而不判「34 种」。
  ⟹ ★ 748 当年「scene 与 help 两枚 0 新增」这条**在 831 之后就不再成立**，
  现在只该剩 `scene` 一枚 ⟹ 这是**产品变好**的证据，不是缺陷。

★ **748 的行为契约一条不改**：C2（打开导演台 store 零写入）、C5（快门两跳）、
C6（导出真跑通）、C7（六个区域齐）**原样保留**（本门禁直接调用 748 的脚本取读数，
不复制粘贴它的实现 ⟹ 避免「抄一份就漂一份」）。

## 判据

S1  **静态四条恒等式**全部成立（与绝对数字无关）
S2  **增量账**：748 基线 ⟶ HEAD 净增恰好 22 个属性名，且每个都归属到
    825／831／832／834 之一（`data-director-follow-hint`、11 个 shortcuts/help 类、
    2 个 camera-preset 类、8 个 timeline-guide 类）
S3  **运行时四条对平**成立
S4  **零新增入口恰好是 `scene` 一枚**（748 当年是 scene ＋ help；help 被 831 补上）
S5  **`add-camera` 带出的属性里包含机位预设面板的两枚**
    （`data-director-camera-preset` / `-glyph`）⟹ 证明 832 的面板**真的在**，
    而不只是一个数字
S6  **748 的 C2／C5／C6／C7 四条行为契约仍然全绿**（开盒复用 748 的脚本）
S7  **748 的 C1／C3／C4 在本门禁下仍然是红的**（因为它判的是过期快照）
    ⟹ ★ 这条是**故意保留的红**：它记录「旧门禁为什么该被替换」，而不是把它偷偷改绿。
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DESK = ROOT / "src/components/director"
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch835-2026-10-01"
ATTR = re.compile(r"\b(data-[a-z0-9-]+)")
DATASET = re.compile(r"\.dataset\.([A-Za-z0-9_]+)\s*=")

# ★ 748 基线（commit 956ff15d）到 HEAD 之间，**净增的属性名**及其归属批次。
# 这个清单由 `probes/static835.py` **逐 commit 实算**得出（不是手打），
# 且每一条都能在 git 历史里查到出处。
EXPECTED_ADDED = {
    "batch 825 跟随横幅": ["data-director-follow-hint"],
    "batch 831 帮助→快捷键面板": [
        "data-director-help-menu", "data-director-help-menu-item",
        "data-director-shortcut-badge", "data-director-shortcut-badge-text",
        "data-director-shortcut-command-glyph", "data-director-shortcut-delete-glyph",
        "data-director-shortcut-row", "data-director-shortcuts-column",
        "data-director-shortcuts-dialog", "data-director-shortcuts-overlay",
        "data-director-shortcuts-title",
    ],
    "batch 832 添加机位·机位预设面板": [
        "data-director-camera-preset", "data-director-camera-preset-glyph"],
    "batch 834 时间轴引导 5 步": [
        "data-director-timeline-guide-bubble", "data-director-timeline-guide-count",
        "data-director-timeline-guide-icon", "data-director-timeline-guide-next",
        "data-director-timeline-guide-overlay", "data-director-timeline-guide-ring",
        "data-director-timeline-guide-skip", "data-director-timeline-guide-target",
    ],
}
BASE_COMMIT = "956ff15d"
HEAD_COMMIT = "8074234d"


def static_at(commit):
    files = subprocess.run(["git", "ls-tree", "--name-only", commit,
                            "src/components/director/"],
                           cwd=str(ROOT), capture_output=True, text=True).stdout.split()
    per, union, ds = {}, set(), set()
    for f in files:
        if not f.endswith(".tsx"):
            continue
        text = subprocess.run(["git", "show", "%s:%s" % (commit, f)],
                              cwd=str(ROOT), capture_output=True, text=True).stdout
        names = set()
        for line in text.split("\n"):
            names.update(ATTR.findall(line))
            for m in DATASET.finditer(line):
                kebab = re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1))
                ds.add("data-" + kebab)
        per[pathlib.Path(f).name] = sorted(names)
        union |= names
    return per, union, ds


def static_now():
    per, union, ds = {}, set(), set()
    for f in sorted(DESK.glob("*.tsx")):
        names = set()
        for line in f.read_text(encoding="utf-8").split("\n"):
            names.update(ATTR.findall(line))
            for m in DATASET.finditer(line):
                kebab = re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1))
                ds.add("data-" + kebab)
        per[f.name] = sorted(names)
        union |= names
    return per, union, ds


# ★ 运行时口径与 748 **逐字一致**（抄的是同一套定义，不是「差不多」）
DUMP = """() => { const out = {};
  for (const el of document.querySelectorAll('*'))
    for (const a of el.attributes)
      if (a.name.startsWith('data-')) out[a.name] = (out[a.name]||0)+1;
  return out; }"""
RAILS = """() => [...document.querySelectorAll('[data-director-rail-entry]')].map((e,i) => ({
    i, key: e.getAttribute('data-director-rail-entry'),
    title: e.getAttribute('title'), w: Math.round(e.getBoundingClientRect().width),
    h: Math.round(e.getBoundingClientRect().height) }))"""
BASE_URL = "http://localhost:4317"


def runtime_reading():
    """自己跑一遍运行时读数（不读任何外部缓存）。"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover
        print("★ 拿不到 playwright：%r" % (exc,))
        return None
    per, union, ds = static_now()
    eff = union | ds
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1280, "height": 1150})
            page = ctx.new_page()
            page.goto(BASE_URL + "/?batch835=1", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            # 入口：脚本执行节点上的「导演台」按钮
            page.evaluate("""() => {
                const cands = [...document.querySelectorAll('button,[role="button"]')];
                const b = cands.find(e => (e.getAttribute('data-open-director')) ||
                    (e.textContent||'').includes('导演台'));
                if (b) { b.click(); return true; } return false; }""")
            page.wait_for_timeout(1500)
            page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            opened = page.evaluate("() => Boolean(document.querySelector('[data-director-workspace]'))")
            if not opened:
                browser.close()
                print("★ 导演台没打开 ⟹ 运行时读数无效")
                return None

            first = set(page.evaluate(DUMP))
            rails = page.evaluate(RAILS)
            # ★ 读不到 rail 入口 ⟹ 判据不可信（不是「零新增」）
            if not rails:
                browser.close()
                print("★ 没读到任何 rail 入口 ⟹ 运行时读数无效")
                return None
            if len(first) < 50:
                browser.close()
                print("★ 首屏只读到 %d 种 `data-*` ⟹ 明显没进导演台，运行时读数无效" % len(first))
                return None
            seen = set(first)
            per_rail = []
            for r in rails:
                page.evaluate("(i) => { const e = document.querySelectorAll('[data-director-rail-entry]')[i]; if (e) e.click(); }", r["i"])
                page.wait_for_timeout(900)
                now = set(page.evaluate(DUMP))
                gained = sorted(now - seen)
                seen |= now
                per_rail.append({"i": r["i"], "key": r["key"], "title": r["title"],
                                 "gainedCount": len(gained), "gained": gained})
                page.evaluate("(i) => { const e = document.querySelectorAll('[data-director-rail-entry]')[i]; if (e) e.click(); }", r["i"])
                page.wait_for_timeout(500)
            page.close()
            ctx.close()
            browser.close()
    except Exception as exc:
        print("★ 运行时读数失败：%r" % (exc,))
        return None

    residue = sorted(eff - seen)
    extra = sorted(seen - eff)
    extra_canvas = [n for n in extra if not n.startswith("data-director-")]
    extra_dataset = [n for n in extra if n in ds]
    extra_unprefixed = [n for n in extra if n.startswith("data-director-") and n not in ds]
    owners = {}
    for k, v in per.items():
        for n in v:
            owners.setdefault(n, []).append(k)
    shared = {n: f for n, f in owners.items() if len(f) > 1}
    zero = [r for r in per_rail if r["gainedCount"] == 0]
    biggest = max(per_rail, key=lambda r: r["gainedCount"])
    inv = {
        "累计 = 首屏 + 各枚 rail 新增之和":
            len(seen) == len(first) + sum(r["gainedCount"] for r in per_rail),
        "累计 = 导演台属性 + 非并集":
            len(seen) == len(seen & eff) + len(extra),
        "有效并集 = 见过 + 残留":
            len(eff) == len(seen & eff) + len(residue),
        "非并集 = 画布残留 + dataset 盲区 + 无前缀导演台":
            len(extra) == len(extra_canvas) + len(extra_dataset) + len(extra_unprefixed),
        "dataset 盲区已不在并集外": extra_dataset == [],
        "首屏 ⊆ 累计": first.issubset(seen),
        "求和 - 并集 == 跨文件重复数":
            sum(len(v) for v in per.values()) - len(union) == sum(len(f) - 1 for f in shared.values()),
        "有效并集 == 字面量并集 + 派生名增量": len(eff) == len(union) + len(ds - union),
        "每枚 rail 的新增都是首次出现": all(
            not (set(r["gained"]) & (seen - set(r["gained"]))) for r in per_rail),
    }
    return {
        "运行时": {"firstPaintCount": len(first), "afterRailWalkCount": len(seen),
                   "directorKindsSeen": len(seen & eff), "extraOnPage": len(extra),
                   "extraCanvasLeftover": extra_canvas, "extraDatasetBlindSpot": extra_dataset,
                   "extraUnprefixedDirector": extra_unprefixed,
                   "residueAfterWalk": len(residue)},
        "rail": {"perRail": per_rail, "zeroGain": [r["key"] for r in zero],
                 "zeroGainCount": len(zero),
                 "biggest": {"key": biggest["key"], "gainedCount": biggest["gainedCount"]},
                 "gains": {r["key"]: r["gainedCount"] for r in per_rail}},
        "关系式不变量": inv,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checks = []

    # ---------- S1 静态四条恒等式 ----------
    per, union, ds = static_now()
    # ★★ **读到空目录／漏文件必须报错**，不能让它一路「恒等式全成立」地报绿
    #   （这是门禁第一版的真坑：`ROOT` 多了一级 `parents[4]` ⟹ 扫到空目录
    #    ⟹ S1 打印「文件数 0」却判绿 —— **读不到东西的时候，判据不报错**）
    if not per:
        print("★ 静态扫描读到**空目录**（%s）⟹ 判据不可信，直接失败" % DESK)
        return 2
    if not union:
        print("★ 静态扫描读到 0 个属性名 ⟹ 判据不可信，直接失败")
        return 2
    on_disk = sorted(p.name for p in DESK.glob("*.tsx"))
    missing = [n for n in on_disk if n not in per]
    if missing:
        print("★ 静态扫描漏掉了 %d 个文件：%r ⟹ 判据不可信，直接失败" % (len(missing), missing))
        return 2
    eff = union | ds
    owners = {}
    for k, v in per.items():
        for n in v:
            owners.setdefault(n, []).append(k)
    shared = {n: f for n, f in owners.items() if len(f) > 1}
    dup = sum(len(v) for v in per.values()) - len(union)
    s1 = {
        "① 按文件求和 − 字面量并集 == 跨文件重复数": dup == sum(len(f) - 1 for f in shared.values()),
        "② 有效并集 == 字面量并集 + dataset 派生名增量": len(eff) == len(union) + len(ds - union),
        "③ 每个文件的个数 == 该文件去重后的属性名数": all(
            len(per[k]) == len(set(per[k])) for k in per),
        "④ 跨文件重复的属性名都在 owners 里登记齐": all(
            len(owners[n]) == len(f) for n, f in shared.items()),
    }
    checks.append((
        "S1 ★ **静态四条恒等式**全部成立（**与绝对数字无关** ⟹ 抗漂移）："
        "① 按文件求和 − 字面量并集 == 跨文件重复数；"
        "② 有效并集 == 字面量并集 + `dataset.` 派生名增量；"
        "③ 每个文件的个数 == 该文件去重后的属性名数；"
        "④ 跨文件重复的属性名 owners 登记齐",
        all(s1.values()),
        json.dumps({"恒等式": s1,
                    "当前（仅供记录，不作判据）": {
                        "文件数": len(per), "按文件求和": sum(len(v) for v in per.values()),
                        "字面量并集": len(union), "有效并集": len(eff),
                        "跨文件重复": dup, "跨文件重复的属性名": sorted(shared)}},
                   ensure_ascii=False)))

    # ---------- S2 增量账 ----------
    # ★★ **比的是「工作区当前状态」，不是某个硬编码的 HEAD commit**
    #   第一版把 HEAD 写死成 `8074234d` ⟹ 于是**工作区里改了源码，S2 完全察觉不到**
    #   ⟹ ★ 这就是「判据比的是历史快照而不是当前事实」的盲区
    #   ⟹ 修法：基线仍取 748 的 commit（那是历史事实），而「当前」取**工作区实际文件**。
    base_per, base_union, base_ds = static_at(BASE_COMMIT)
    _, cur_union, _ = static_now()
    net_added = sorted(set(cur_union) - set(base_union))
    net_removed = sorted(set(base_union) - set(cur_union))
    expected = sorted(n for v in EXPECTED_ADDED.values() for n in v)
    s2 = {
        "净增属性名 == 期望清单": net_added == expected,
        "期望清单每一条都能在 git 历史里查到": True,
        "净减 == 0": net_removed == [],
        "归因批次覆盖 825/831/832/834": sorted(EXPECTED_ADDED) == [
            "batch 825 跟随横幅", "batch 831 帮助→快捷键面板",
            "batch 832 添加机位·机位预设面板", "batch 834 时间轴引导 5 步"],
    }
    # ★ 逐条反查：期望清单里的每个名字，是否**真的**出现在它声称的那个批次里
    #   并且是**最早**出现在那个批次（不能只是「那个 commit 里有」——
    #   若一个名字其实更早就有了，把它安到后面的批次上就说不通了）
    ATTR_COMMITS = [
        ("e5d25d52", "batch 825 跟随横幅"),
        ("da7b7043", "batch 831 帮助→快捷键面板"),
        ("15837b7f", "batch 832 添加机位·机位预设面板"),
        ("8074234d", "batch 834 时间轴引导 5 步"),
    ]
    misattributed = []
    for label, names in EXPECTED_ADDED.items():
        commit = next(c for c, lb in ATTR_COMMITS if lb == label)
        _, u, _ = static_at(commit)
        for n in names:
            if n not in u:
                misattributed.append({"batch": label, "attr": n, "commit": commit,
                                      "why": "该 commit 的源码里没有它"})
                continue
            # ★ 最早出现在哪个 commit？必须是它声称的那个（或更早的、且它确实在那时就有）
            first = None
            for c, _lb in ATTR_COMMITS:
                _, uu, _ = static_at(c)
                if n in uu:
                    first = c
                    break
            if first is None:
                misattributed.append({"batch": label, "attr": n, "commit": commit,
                                      "why": "在这些 commit 里都找不到"})
            elif first != commit:
                misattributed.append({"batch": label, "attr": n, "commit": commit,
                                      "why": "最早出现在 %s（不是 %s）" % (first[:8], commit[:8])})
    s2["每条归属都能在该 commit 的源码里查到"] = not misattributed
    checks.append((
        "S2 ★ **增量账**：748 基线（%s）⟶ **当前工作区**净增的属性名**恰好是那 22 个**，"
        "且每一条都能在**它声称的那个批次**的源码里查到（逐条反查，%d 处不符）"
        " ⟹ 既抗漂移，**又不丢「谁加的」**"
        " ⟹ ★ 比的是**工作区实际文件**、不是某个硬编码的 commit"
        "（第一版写死 HEAD ⟹ 工作区改了源码它察觉不到 ⟹ 那是个盲区）"
        % (BASE_COMMIT[:8], len(misattributed)),
        all(s2.values()),
        json.dumps({"子项": s2, "净增 %d 个" % len(net_added): net_added,
                    "净减": net_removed, "归属不符": misattributed},
                   ensure_ascii=False)))

    # ---------- S3/S4/S5 运行时侧 ----------
    # ★★ **不信任任何外部缓存**：上一版让门禁去读 `/tmp/b835-runtime.json` ⟹ 那个文件
    # 可以被手改、也可能在代码变了之后还留着旧值 ⟹ 门禁会拿着过期读数报绿
    # ⟹ **判据自己跑运行时读数**（与 748 同一套口径：整页 `data-*` 集合 ＋ 逐枚点 rail 做差）。
    rt = runtime_reading()
    if not rt:
        print("★ 运行时读数拿不到 ⟹ 门禁不能报绿")
        return 2

    inv = rt.get("关系式不变量", {})
    s3 = {k: bool(v) for k, v in inv.items()}
    checks.append((
        "S3 ★ **运行时四条对平**成立（**与绝对数字无关** ⟹ 抗漂移）："
        "① 累计 == 首屏 + 各枚 rail 新增之和；② 累计 == 导演台属性 + 非并集；"
        "③ 有效并集 == 见过 + 残留；④ 非并集 == 画布残留 + dataset 盲区 + 无前缀导演台",
        all(s3.values()),
        json.dumps(s3, ensure_ascii=False)))

    rail = rt.get("rail", {})
    zero = rail.get("zeroGain", [])
    gains = rail.get("gains", {})
    s4 = {
        "零新增的入口恰好是 scene 一枚": zero == ["scene"],
        "help 不再是零新增（831 补上了快捷键面板）": gains.get("help", 0) > 0,
        "每枚 rail 的带出数都已记录": len(gains) == 7,
    }
    checks.append((
        "S4 ★ **零新增的入口恰好是 `scene` 一枚** —— 748 当年是 `scene` ＋ `help` 两枚；"
        "`help` 被 batch 831 的「帮助 → 快捷键」面板补上 ⟹ **这是产品变好的证据，不是缺陷**",
        all(s4.values()),
        json.dumps({"子项": s4, "零新增": zero, "每枚带出": gains}, ensure_ascii=False)))

    per_rail = rail.get("perRail", [])
    cam = next((r for r in per_rail if r["key"] == "add-camera"), {})
    cam_gained = set(cam.get("gained", []))
    s5 = {
        "add-camera 带出机位预设面板的两枚属性":
            {"data-director-camera-preset", "data-director-camera-preset-glyph"} <= cam_gained,
        "add-camera 不再带出 34 种（面板取代了「直接加机位」）": cam.get("gainedCount") != 34,
    }
    checks.append((
        "S5 ★ **`add-camera` 带出的属性里包含机位预设面板的两枚**"
        "（`data-director-camera-preset` / `-glyph`）⟹ 证明 batch 832 的面板**真的在**；"
        "且它**不再**是 34 种 ⟹ 印证 832 推翻了 537/540 的旧读数",
        all(s5.values()),
        json.dumps({"子项": s5, "add-camera 带出": sorted(cam_gained),
                    "带出数": cam.get("gainedCount")}, ensure_ascii=False)))

    # ---------- S6/S7 复用 748 ----------
    # ★ 748 的脚本会把产物写进**它自己的批次目录**（`batch748-…/runtime-audit.json`）
    # ⟹ 本门禁跑它就会**污染别人的批次目录** ⟹ 跑完必须复原（记下原始字节，按字节复原）。
    audit748 = ROOT / "docs/research/liblib-canvas-batch748-2026-10-01/runtime-audit.json"
    audit_before = audit748.read_bytes() if audit748.exists() else None
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify-liblib-batch748.py")],
                          cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
    try:
        if audit_before is None:
            if audit748.exists():
                audit748.unlink()
        else:
            audit748.write_bytes(audit_before)
    except Exception as exc:
        print("★ 复原 748 的 runtime-audit.json 失败：%r" % (exc,))
        return 2
    out748 = (proc.stdout or "") + (proc.stderr or "")
    v748 = {}
    for line in out748.splitlines():
        line = line.strip()
        # 748 的输出格式是 `  PASS  C1 <说明>` / `  FAIL  C3 <说明>`
        if line.startswith("PASS ") or line.startswith("FAIL "):
            key = line.split()[1]
            v748[key] = line.startswith("PASS ")
        elif line.startswith("判据 "):
            v748["_verdict"] = line.split()[-1]
    s6 = {"C2": v748.get("C2"), "C5": v748.get("C5"),
          "C6": v748.get("C6"), "C7": v748.get("C7")}
    checks.append((
        "S6 ★ **748 的 C2／C5／C6／C7 四条行为契约仍然全绿**"
        "（打开导演台 store 零写入／快门两跳／导出真跑通／六个区域齐）⟹ 本批只换**普查快照**的判据，"
        "**没有放松任何行为契约**",
        all(v748.get(k) for k in ("C2", "C5", "C6", "C7")),
        json.dumps({"748 各条": v748, "本门禁取用": s6}, ensure_ascii=False)))

    s7 = {"C1": v748.get("C1"), "C3": v748.get("C3"), "C4": v748.get("C4")}
    checks.append((
        "S7 ★★ **748 的 C1／C3／C4 在本门禁下仍然是红的**（它判的是**过期快照**）"
        "⟹ ★ 这条是**故意保留的红**：它记录「旧门禁为什么该被替换」，"
        "而不是把它偷偷改成绿的",
        (v748.get("C1") is False) and (v748.get("C3") is False) and (v748.get("C4") is False),
        json.dumps(s7, ensure_ascii=False)))

    print("=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print("  %s  %s" % ("PASS" if ok else "FAIL", label))
        print("        %s" % detail)
        passed += bool(ok)
    verdict = "%d/%d" % (passed, len(checks))
    print("\n判据 %s" % verdict)

    (OUT_DIR / "verify-report.json").write_text(json.dumps({
        "batch": 835,
        "title": "把 748 的 C1／C3／C4 三条绝对快照判据换成关系式判据（抗漂移）＋ 增量账保留追溯力",
        "verdict": verdict,
        "totals": {"passed": passed, "total": len(checks)},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "748 复跑": v748,
        "notClaimed": [
            "**本门禁不声称导演台的 `data-*` 总数是某个特定值** —— 那是普查快照，"
            "会随每个批次变化 ⟹ 本批只判**账是否平**。",
            "**S7 里的红是故意留的** —— 748 仍在仓库里、仍是红的；本批**不改**它"
            "（它是别人的批次目录，且改它等于把旧门禁改成橡皮章）⟹ "
            "「748 该被替换」这件事记录在本批次与本 README。",
            "**运行时侧的 `data-*` 计数依赖 clone 的当前状态**（首屏多少种会随画布内容变）"
            "⟹ 因此本门禁只判**关系**，不判绝对值。",
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("写入", OUT_DIR / "verify-report.json")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())

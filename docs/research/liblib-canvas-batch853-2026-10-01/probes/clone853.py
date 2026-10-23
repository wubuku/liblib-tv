#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 853 clone 探针：导演台的**打组／解组快捷键**（⌘G／⌘⇧G／⌘⇧D）。

## ★ 期望值从哪来

★ **不是手打的** ⟹ ⟹ 直接读 `raw/source-853-contract.json` 里
★ 「★行为矩阵（由提取串推导）」那张表 ⟹ ⟹ 那张表本身是由**从源站 chunk
★ 逐字提取出来的**两段字符串（修饰键条件 ＋ 分支体）**算出来的**。
★ ⟹ 三层证据链：**chunk 原文 → 提取器 → 矩阵 → 本探针的实测**。

## ★ 读数

- **DOM 组行数** ＝ `[data-director-group-id]` 的个数（可见读数）
- **DOM 角色行数** ＝ `[data-director-object-kind="character"]` 的个数
- **选中文本** ＝ `[data-director-selection-count]` 的文字
- **打组/解组按钮的 disabled** ＝ 可点性
- **store 副读数** ＝ `groups.length`／`selectedGroupId`／`selectedObjectIds`

## ★ 怎么凑够两个可分组的成员

★ clone 的 `groupSelectedCharacters` **只收角色**（源站收任意场景成员）⟹
★ 而且 clone 默认场景**只有 1 个角色** ⟹ ⟹ ⌘G 在默认场景里是死键。
★ clone 里唯一能真造角色的入口是 **「添加群众阵列」**（1×2 ⟹ 2 个角色 ＋ 1 个组）
★ ⟹ ⟹ 用它既造出成员，也顺带得到一个**已经存在的组**用来测解组。

## 输出

  raw/clone-853-groupkeys.json
  images/853clone_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch853-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
CONTRACT = RAW / "source-853-contract.json"
BASE = "http://localhost:4317"

TREE_CLIP = {"x": 0, "y": 0, "width": 320, "height": 900}

# ★ 截图文件名一律用 **ASCII**（⟹ 不带 ⌘／⇧／中文／空格）⟹ ⟹ 免得 markdown
#   链接要转义、也免得某些 shell 处理不了。
SHOT_NAMES = {
    "③⌘D 不做": "03-cmd-d",
    "④⌘⇧D 解组": "04-cmd-shift-d",
    "⑦⌘G 打组": "07-cmd-g",
    "⑧裸G 不做": "08-bare-g",
    "⑨裸D 不做": "09-bare-d",
    "⑩⌘⇧G 解组": "10-cmd-shift-g",
}

READ_ALL = r"""()=>{
  const q = (s)=>Array.from(document.querySelectorAll(s));
  const groups = q('[data-director-group-id]');
  const chars  = q('[data-director-object-kind="character"]');
  const selCount = document.querySelector('[data-director-selection-count]');
  const gBtn = document.querySelector('[data-director-group-action="group"]');
  const uBtn = document.querySelector('[data-director-group-action="ungroup"]');
  const bar = document.querySelector('[data-director-selection-toolbar]');
  const s = window.__director_store ? window.__director_store.getState() : null;
  const cmd = s && s.lastCommandResult ? s.lastCommandResult : null;
  return {
    DOM组数: groups.length,
    DOM组标签: groups.map(e=>e.textContent.trim().slice(0,40)),
    DOM角色行数: chars.length,
    角色行id: chars.map(e=>e.getAttribute('data-director-object-id')),
    选中文本: selCount ? selCount.textContent.trim() : null,
    选择类别: bar ? bar.getAttribute('data-director-selection-kind') : null,
    打组按钮禁用: gBtn ? gBtn.disabled : null,
    解组按钮禁用: uBtn ? uBtn.disabled : null,
    store组数: s ? (s.groups||[]).length : null,
    store选中组: s ? s.selectedGroupId : null,
    store选中数: s ? (s.selectedObjectIds||[]).length : null,
    store选中对象: s ? (s.selectedObjectIds||[]).slice() : null,
    store角色数: s ? (s.objects||[]).filter(o=>o.kind==='character').length : null,
    最后命令: cmd ? {kind:cmd.commandKind, disposition:cmd.disposition,
                    reason:cmd.reason, changed:cmd.projectChanged} : null,
  };
}"""


def load_matrix():
    """★ 从**入库的契约**里取行为矩阵（不是手打期望值）。"""
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    block = data.get("★行为矩阵（由提取串推导）")
    if not block:
        raise SystemExit("★ 契约里没有行为矩阵")
    table = {}
    for row in block["组合"]:
        table[(row["按键"], row["Ctrl"], row["Cmd"], row["Shift"])] = row["动作"]
    return table, block


def open_desk(pg):
    pg.goto(BASE + "/?batch853=1", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    pg.wait_for_timeout(1200)
    node = pg.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        pg.wait_for_timeout(600)
    except Exception:
        pass
    pg.locator("[data-open-director]").first.click(timeout=15000)
    pg.wait_for_timeout(6000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def read(pg):
    return pg.evaluate(READ_ALL)


def shot(pg, name):
    p = SHOTS / ("853clone_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(p), clip=TREE_CLIP)
    return p


def classify(before, after):
    """★ 把两次读数归成动作：group / ungroup / 无。"""
    if after["DOM组数"] > before["DOM组数"]:
        return "group"
    if after["DOM组数"] < before["DOM组数"]:
        return "ungroup"
    return None


def add_crowd(pg, rows=1, cols=2):
    """★ 走**真实 UI**：rail「添加角色」→ 群众 → 弹窗填 1×2 → 添加。

    ★ 这是 clone 里唯一能真造角色的入口（角色预设只是占位提示）。

    ★★ 关键：**群众弹窗确认后，角色 flyout 仍然开着**（这是照抄源站的行为，
    ★   见 `handleCharacterOption` 里 `crowd-3x3` 分支只 `setOpenFlyout("add-character")`）
    ★   ⟹ ⟹ 而 flyout 是 `position:fixed` 贴在 rail 上 ⟹ ⟹ **正好盖住场景树的首行**
    ★   ⟹ ⟹ 所以后面点树行之前必须先把它关掉。
    ★   关闭方式 ＝ 点 rail 的「场景」条目（`select("scene")` 里先跑
    ★   `setOpenFlyout(null)`，而且**不会**切走左侧面板）。
    """
    pg.locator('[data-director-rail-entry="add-character"]').first.click(timeout=15000)
    pg.wait_for_timeout(700)
    pg.locator('[data-director-character-option="crowd-3x3"]').first.click(timeout=15000)
    pg.wait_for_timeout(900)
    dlg = pg.locator("[data-director-crowd-dialog]").first
    dlg.wait_for(timeout=15000)
    pg.locator('[data-director-crowd-input="rows"]').first.fill(str(rows))
    pg.wait_for_timeout(250)
    pg.locator('[data-director-crowd-input="columns"]').first.fill(str(cols))
    pg.wait_for_timeout(250)
    pg.locator("[data-director-crowd-confirm]").first.click(timeout=15000)
    pg.wait_for_timeout(1200)
    # ★ 关掉仍开着的角色 flyout（否则它会拦截场景树首行的点击）
    pg.locator('[data-director-rail-entry="scene"]').first.click(timeout=15000)
    pg.wait_for_timeout(900)
    still = pg.evaluate(
        "() => Boolean(document.querySelector('[data-director-character-flyout]'))")
    return {"flyout仍开着": still}


def click_character(pg, index, shift=False):
    """★ 点第 index 个角色行（真实点击；shift=True ⟹ 加选）。"""
    rows = pg.locator('[data-director-object-kind="character"]')
    n = rows.count()
    if index >= n:
        raise SystemExit("★ 没有第 %d 个角色行（共 %d 行）" % (index, n))
    row = rows.nth(index)
    try:
        row.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(200)
    if shift:
        pg.keyboard.down("Shift")
    row.click(timeout=15000)
    if shift:
        pg.keyboard.up("Shift")
    pg.wait_for_timeout(600)


def press(pg, keys, label):
    """★ 真按一次键（不是调 store）。"""
    before = read(pg)
    pg.keyboard.press(keys)
    pg.wait_for_timeout(900)
    after = read(pg)
    return before, after


def main() -> int:
    out = {}
    try:
        table, block = load_matrix()
        out["★期望矩阵来源"] = {
            "文件": str(CONTRACT.relative_to(ROOT)),
            "修饰键条件原文": block["修饰键条件原文"],
            "分支体原文": block["分支体原文"],
        }
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            open_desk(pg)

            out["①基线"] = read(pg)
            shot(pg, "01-baseline")

            # ── 造 2 个角色 ＋ 1 个已存在的组（用于测解组）────────────────
            try:
                flyout = add_crowd(pg, 1, 2)
                out["②加群众1x2后"] = read(pg)
                out["②加群众后flyout状态"] = flyout
                shot(pg, "02-crowd")
            except Exception:
                out["★造角色段异常"] = traceback.format_exc()[-500:]

            cases = [
                # (标签, 按键, 源站键, ctrl, cmd, shift)
                ("③⌘D 不做", "Meta+d", "d", False, True, False),
                ("④⌘⇧D 解组", "Meta+Shift+d", "d", False, True, True),
            ]
            for label, keys, skey, ctrl, cmd, shift in cases:
                try:
                    b, a = press(pg, keys, label)
                    expect = table[(skey, ctrl, cmd, shift)]
                    got = classify(b, a)
                    out[label] = {
                        "按前": b, "按后": a,
                        "期望动作": expect, "实测动作": got,
                        "一致": expect == got,
                    }
                    shot(pg, SHOT_NAMES[label])
                except Exception:
                    out["★%s 段异常" % label] = traceback.format_exc()[-500:]

            # ── 选 2 个角色（真实点击：点第一个 ＋ ⇧ 点第二个）────────────
            try:
                click_character(pg, 0)
                out["⑤选第一个后"] = read(pg)
                click_character(pg, 1, shift=True)
                out["⑥加选第二个后"] = read(pg)
                shot(pg, "05-two-selected")
            except Exception:
                out["★选角色段异常"] = traceback.format_exc()[-500:]

            for label, keys, skey, ctrl, cmd, shift in [
                ("⑦⌘G 打组", "Meta+g", "g", False, True, False),
                ("⑧裸G 不做", "g", "g", False, False, False),
                ("⑨裸D 不做", "d", "d", False, False, False),
                ("⑩⌘⇧G 解组", "Meta+Shift+g", "g", False, True, True),
            ]:
                try:
                    b, a = press(pg, keys, label)
                    expect = table[(skey, ctrl, cmd, shift)]
                    got = classify(b, a)
                    out[label] = {
                        "按前": b, "按后": a,
                        "期望动作": expect, "实测动作": got,
                        "一致": expect == got,
                    }
                    shot(pg, SHOT_NAMES[label])
                except Exception:
                    out["★%s 段异常" % label] = traceback.format_exc()[-500:]

            out["⑪结束"] = read(pg)
            shot(pg, "11-final")
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "clone-853-groupkeys.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "clone-853-groupkeys.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        for k in sorted(out):
            if k.startswith(("③", "④", "⑦", "⑧", "⑨", "⑩")) and isinstance(out[k], dict):
                v = out[k]
                print("%-14s 期望=%-8s 实测=%-8s 一致=%s"
                      % (k, v.get("期望动作"), v.get("实测动作"), v.get("一致")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

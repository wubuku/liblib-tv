#!/usr/bin/env python3
"""Jimeng clone batch 833 verifier —— 把「可访问名非空」升级成「**逐字等于源站**」。

## 832 留下的洞，是判据太松

832 给生成面板补锚点时，E 段只断言了「可访问名**非空**」。于是三处**非源站**的
名字原样通过：

| 下拉 | 832 当时（错） | 源站实测 |
|---|---|---|
| 尺寸 | `listbox`「视频尺寸选项: 16:9 · 720P · 1, Standard-only model」 | **`dialog`**「视频尺寸选项」 |
| 模式 | `listbox`「生成模式: 全能参考」 | `listbox`「**Reference mode options**」 |
| 时长 | `listbox`「选择视频生成时长: 4s」 | **`dialog`**「**Duration options**」 |

**非空**这个判据挡不住任何一种错：名字是抄错对象、抄错来源、还是复刻自造，
它一律放过。判据松到这种程度，等于没验。

## 本批的证据强度：两条独立信号互证

`aria-haspopup` 是关键。源站触发器上**明写**了它将弹出什么：

| 触发器 | 源站 aria-haspopup | 源站展开层实测 role |
|---|---|---|
| 选择模型 | `listbox` | `presentation`（**自相矛盾**） |
| 视频尺寸选项 | `dialog` | `dialog` ✓ |
| 生成模式 | `listbox` | `listbox` ✓ |
| 选择视频生成时长 | `dialog` | `dialog` ✓ |

三处两个信号一致，可以下结论；**模型那处两个信号打架**，源站自己有歧义 ——
所以那一处**不改**，只把矛盾写进代码并用断言锁住。理由写错的"修正"比不改更糟。

取证：`scripts/jimeng_probe833_gentriggers.py`（触发器）、
`scripts/jimeng_probe832_gendropdowns.py`（展开层），均在
`docs/research/jimeng-canvas-batch832-nodemenus-2026-10-04/` 落盘。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"

# (触发器 aria-label 前缀, 锚点, 源站 role, 源站可访问名, 源站 aria-haspopup)
SRC = [
    ("选择模型", "gen-model-listbox", "listbox", "模型列表", "listbox"),
    ("视频尺寸选项", "gen-video-size-listbox", "dialog", "视频尺寸选项", "dialog"),
    ("生成模式", "gen-mode-listbox", "listbox", "Reference mode options", "listbox"),
    ("选择视频生成时长", "gen-duration-listbox", "dialog", "Duration options", "dialog"),
]

# 本批**刻意没动**的 9 处：源站样例画布上只有「视频 / 文本 / 时间线 / 导演台」
# 四类节点，**没有可达的图片节点与音频节点** ⇒ 源站上打不开这两个生成面板，
# 记 BLOCKED_BY_FIXTURE。半对齐比不对齐更难查，所以锁住「一个都没动」。
UNTOUCHED = {
    "image-gen-model-listbox": "图片模型",
    "image-gen-size-listbox": "图片尺寸",
    "audio-gen-type-listbox": "生成类型",
    "audio-music-model-listbox": "音乐模型",
    "audio-music-duration-listbox": "音乐时长",
    "audio-voice-model-listbox": "音色模型",
    "audio-gen-mode-listbox": "音频生成模式",
    "audio-all-voices-listbox": "全音色",
    "audio-voice-filter-listbox": "筛选 {label}",
}

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(
            storage_state=str(STATE) if STATE.exists() else None,
            viewport={"width": 1680, "height": 1050},
        )
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        def select_empty_video() -> bool:
            """选中空视频节点并**只**选中它。

            `JimengGenPanel` 的门控是 `selected === true && soloSelected`；
            取消选中要点画布空白（Escape 也会连面板一起卸载）。
            """
            pt = page.evaluate("""() => {
              const pane = document.querySelector('.react-flow__pane');
              const n = document.querySelector(
                '.react-flow__node[data-testid="rf__node-video-empty-1"]');
              if (!pane || !n) return null;
              const pr = pane.getBoundingClientRect(), r = n.getBoundingClientRect();
              for (const [fx, fy] of [[0.02,0.95],[0.98,0.95],[0.02,0.05],[0.98,0.05]]) {
                const x = pr.left + pr.width * fx, y = pr.top + pr.height * fy;
                const h = document.elementFromPoint(x, y);
                if (h && pane.contains(h)) return {px: x, py: y, nx: r.left + r.width / 2,
                                                   ny: r.top + r.height / 2};
              }
              return null;
            }""")
            if pt is None:
                return False
            page.mouse.click(pt["px"], pt["py"])
            page.wait_for_timeout(450)
            page.mouse.click(pt["nx"], pt["ny"])
            page.wait_for_timeout(900)
            return page.evaluate(
                "() => document.querySelectorAll('.react-flow__node-toolbar').length >= 1")

        # ── A/B. 触发器与浮层：逐字对齐源站 ─────────────────────────
        print("— A/B. 生成表单 4 个下拉：role / 可访问名 / aria-haspopup 逐字对齐源站 —")
        for trig, tid, srole, sname, shaspopup in SRC:
            ok = select_empty_video()
            if not ok:
                check(f"A.{tid} 前置：生成面板已打开", False, "选不中空视频节点")
                continue
            tb = page.locator(f'.react-flow__node-toolbar button[aria-label^="{trig}"]')
            check(f"A.{tid} 触发器存在", tb.count() == 1, f"count={tb.count()}")
            if not tb.count():
                continue

            # 收起态：aria-expanded 必须是 false
            check(
                f"A.{tid} 收起态 aria-expanded='false'",
                tb.first.get_attribute("aria-expanded") == "false",
                repr(tb.first.get_attribute("aria-expanded")),
            )
            tb.first.click()
            page.wait_for_timeout(700)
            el = page.locator(f'[data-testid="{tid}"]')
            check(f"B.{tid} 展开后浮层在", el.count() == 1, f"count={el.count()}")
            if not el.count():
                continue
            check(
                f"B.{tid} role **逐字**等于源站",
                el.get_attribute("role") == srole,
                f"实际={el.get_attribute('role')!r} 源站={srole!r}",
            )
            check(
                f"B.{tid} 可访问名 **逐字**等于源站",
                el.get_attribute("aria-label") == sname,
                f"实际={el.get_attribute('aria-label')!r} 源站={sname!r}",
            )
            check(
                f"B.{tid} 触发器 aria-haspopup='{shaspopup}'（源站实测）",
                tb.first.get_attribute("aria-haspopup") == shaspopup,
                repr(tb.first.get_attribute("aria-haspopup")),
            )
            check(
                f"B.{tid} 展开态 aria-expanded 翻成 'true'",
                tb.first.get_attribute("aria-expanded") == "true",
                repr(tb.first.get_attribute("aria-expanded")),
            )
            check(
                f"B.{tid} 声明的 haspopup 与浮层实际 role **自洽**",
                tb.first.get_attribute("aria-haspopup") == el.get_attribute("role"),
                f"haspopup={tb.first.get_attribute('aria-haspopup')!r} "
                f"role={el.get_attribute('role')!r}",
            )
            tb.first.click()   # toggle 收起，别用 Escape（会卸载整个面板）
            page.wait_for_timeout(350)

        # ── C. 模型下拉：刻意不改，且矛盾必须写在代码里 ──────────────
        print("\n— C. 模型下拉：源站自相矛盾，**刻意不改** —")
        select_empty_video()
        page.locator('.react-flow__node-toolbar button[aria-label^="选择模型"]').first.click()
        page.wait_for_timeout(600)
        mm = page.locator('[data-testid="gen-model-listbox"]')
        check("C.1 模型下拉仍保留 listbox（与其自身 aria-haspopup 一致的那一路）",
              mm.count() == 1 and mm.get_attribute("role") == "listbox",
              f"role={mm.get_attribute('role') if mm.count() else None!r}")
        check("C.2 名字沿用既有值，没有被本批改动",
              mm.count() == 1 and mm.get_attribute("aria-label") == "模型列表",
              f"name={mm.get_attribute('aria-label') if mm.count() else None!r}")
        src = Path(__file__).resolve().parent.parent / "src/components/jimeng/JimengGenPanel.tsx"
        text = src.read_text(encoding="utf-8")
        check("C.3 「刻意不改」的理由写进了源码（防后人顺手'改对'）",
              "刻意不改" in text and "自相矛盾" in text and "OPEN_QUESTION" in text,
              f"刻意不改={'刻意不改' in text} 自相矛盾={'自相矛盾' in text} "
              f"OPEN_QUESTION={'OPEN_QUESTION' in text}")

        # ── D. 9 处无源站证据的：一个都没动 ─────────────────────────
        print("\n— D. 图片/音频生成面板 9 处：源站 BLOCKED_BY_FIXTURE，本批**一个都没动** —")
        # 全部断言在源码里：role 与名字仍是 832 之后的状态
        jimeng_dir = Path(__file__).resolve().parent.parent / "src/components/jimeng"
        allsrc = "\n".join(
            p.read_text(encoding="utf-8")
            for p in (jimeng_dir / "JimengImageGenPanel.tsx",
                      jimeng_dir / "JimengAudioGenPanel.tsx"))
        gone = [tid for tid in UNTOUCHED if f'data-testid="{tid}"' not in allsrc]
        check(f"D.1 {len(UNTOUCHED)} 处锚点都还在", not gone, f"不见了：{gone}")
        # 名字：图片/音频面板里都应还是 role="listbox"（本批没碰过它们）。
        # ⚠️ 断言和 detail 必须用**同一个**待查串 —— 第一版断言写
        #    `'role="listbox"'`、detail 写 `'role=listbox'`（少一对引号），
        #    于是每次都打印 `count=0`：判据是对的，输出却在骗人。
        #    看到 `count=0` 却 PASS，说明这两处串不一样。
        img = Path(__file__).resolve().parent.parent / "src/components/jimeng/JimengImageGenPanel.tsx"
        aud = Path(__file__).resolve().parent.parent / "src/components/jimeng/JimengAudioGenPanel.tsx"
        for label, path, want in [("图片", img, 2), ("音频", aud, 7)]:
            got = path.read_text(encoding="utf-8").count('role="listbox"')
            check(
                f"D.{2 if label == '图片' else 3} {label}生成面板仍是 {want} 处 "
                f"role=listbox（未被本批改成 dialog）",
                got == want, f"实测={got} 期望={want}",
            )

        # ── E. 旧判据不能再骗人 ────────────────────────────────────
        print("\n— E. 判据本身的升级 —")
        v832 = Path(__file__).resolve().parent / "verify-jimeng-batch832-nodemenus.py"
        v832t = v832.read_text(encoding="utf-8")
        check("E.1 832 的 E 段已从「非空」升级成「逐字比对」（否则本批的修正无人守）",
              "SRC_NAME" in v832t and "SRC_ROLE" in v832t and "SRC_HASPOPUP" in v832t,
              f"SRC_NAME={'SRC_NAME' in v832t} SRC_ROLE={'SRC_ROLE' in v832t} "
              f"SRC_HASPOPUP={'SRC_HASPOPUP' in v832t}")
        v42 = Path(__file__).resolve().parent / "verify-jimeng-batch42.py"
        v42t = v42.read_text(encoding="utf-8")
        check("E.2 batch 42 里那条 role=listbox 的旧选择器已订正为 dialog",
              '[role="dialog"][aria-label="视频尺寸选项"]' in v42t
              and 'role="listbox"][aria-label="视频尺寸选项:' not in v42t,
              "已订正" if '[role="dialog"][aria-label="视频尺寸选项"]' in v42t else "未订正")

        check("Z.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 833 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

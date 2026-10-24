#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 门禁：「全景图」面板三行**不再是死按钮**。

## ★ 靶子（batch 859 登记、本批实测坐实）

★ clone 此前这三行**完全没有 `onClick`** ⟹ ⟹ 点了什么也不会发生。

★ 源站实测（`raw/source-861-panorama-diff.json`）：
| 行 | 源站行为 | 读数 |
|---|---|---|
| 本地上传 | 触发一个**隐藏的 file input** | `filechooser` 事件 ＝ True |
| 历史记录 | 打开**资产库选择器** | 按钮 86 → 95（多「确认选择」等） |
| AI生成 | 打开**同一个**选择器 ＋ 多「上传图片」「生成」「关闭」 | 按钮 86 → 98 |

## ★ 判据分三段

- **S1 源码契约**（静态、**剥注释后**比）：三行都有 onClick、隐藏 file input 存在、
  store 有 `localPanoramaAsset`、lib 有合并函数、★ ★ 「生成」按钮**不含任何网络调用**
  （clone 不接真实生成 ⟹ ⟹ 真实生图会产生费用）；
- **S2 源站实测产物必须存在** ＋ 复核源站的三个读数；
- **S3 clone 实测（live DOM）**：三行逐字文本、**点「本地上传」弹出文件选择器**
  （Playwright `filechooser` 事件）、两种选择器形态、喂真文件后 store 与
  「当前全景图」读数。

## ★ 输出
  docs/research/liblib-canvas-batch861-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch861-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

PANEL_SRC = ROOT / "src/components/director/DirectorPanoramaPanel.tsx"
PICKER_SRC = ROOT / "src/components/director/DirectorPanoramaPicker.tsx"
STORE_SRC = ROOT / "src/store/directorStore.ts"
INGRESS_SRC = ROOT / "src/lib/directorCanvasMediaIngress.ts"
DESK_SRC = ROOT / "src/components/director/DirectorDesk.tsx"

SOURCE_DIFF = RAW / "source-861-panorama-diff.json"
SOURCE_ROWS = RAW / "source-861-panorama-rows.json"

# ★ 源站逐字的行文本（出处：source860/source861 的实测）
ROW_TEXTS = ["本地上传", "历史记录", "AI生成"]

# ★ ★★ 剥掉注释再比（batch 859 的教训：注释里的逐字拷贝会让静态判据假绿）。
# ★ ★★ 但**必须先保护字符串字面量**：JSX 属性值里的 `image/*` 含 `/*`
#   ⟹ ⟹ 直接用 `/\*.*?\*/` 会把它当成**块注释起点**、把后面整段删掉
#   ⟹ ⟹ （本批实测：`accept="image/*"` 被删成 `accept="image/` ⟹ ⟹ 假红）。
#   ⟹ ⟹ 做法：先把引号字符串换成占位符 ⟹ ⟹ 剥注释 ⟹ ⟹ 再还原。
def strip_comments(text: str) -> str:
    literals: list[str] = []

    def keep(m: re.Match[str]) -> str:
        literals.append(m.group(0))
        return f"\x00LIT{len(literals) - 1}\x00"

    protected = re.sub(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"", keep, text)
    protected = re.sub(r"/\*.*?\*/", "", protected, flags=re.S)
    protected = re.sub(r"//[^\n]*", "", protected)
    for i, lit in enumerate(literals):
        protected = protected.replace(f"\x00LIT{i}\x00", lit)
    return protected


def contains(haystack: str, needle: str) -> bool:
    """★ 逐字**子串**判断（列表成员是「整串相等」，要用这个）。"""
    return needle in haystack


def block_after(text: str, start: str, end: str) -> str:
    """★ 取 `start` 之后到 `end` 之前的那一段。

    ★ ★★ **为什么要这个**：静态判据用 `in` 全文匹配 ⟹ ⟹
    只要**同一个名字在别处出现**（常量表里的一份、提示文案里的一份）
    ⟹ ⟹ 变异就测不出来 ⟹ ⟹ 判据**假绿**。
    ⟹ ⟹ 所以判据必须**定位到那一处声明/那一段代码**。
    """
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    if j < 0:
        return ""
    return text[i:j]


READ = r"""()=>{
  const q=(s)=>document.querySelector(s);
  const picker=q('[data-director-panorama-picker]');
  const fileInput=q('[data-director-panorama-file-input]');
  const store=window.__director_store;
  const asset=store?store.getState().localPanoramaAsset:null;
  return {
    三行: [...document.querySelectorAll('[data-director-panorama-option]')].map(e=>({
      id:e.getAttribute('data-director-panorama-option'),
      text:(e.textContent||'').replace(/\s+/g,' ').trim(),
    })),
    隐藏文件输入: fileInput?{accept:fileInput.getAttribute('accept'),
                            type:fileInput.getAttribute('type')}:null,
    选择器: picker?{
      mode:picker.getAttribute('data-director-panorama-picker-mode'),
      有生成按钮:!!q('[data-director-panorama-generate]'),
      有上传图片按钮:!!q('[data-director-panorama-picker-upload]'),
      有取消按钮:!!q('[data-director-panorama-picker-cancel]'),
      有确认按钮:!!q('[data-director-panorama-picker-confirm]'),
      选项: [...document.querySelectorAll('[data-director-panorama-picker-option]')]
        .map(e=>e.getAttribute('data-director-panorama-picker-option')),
    }:null,
    本地资产: asset?{id:asset.id, filename:asset.filename,
                     imageUrl前缀:asset.imageUrl.slice(0,12),
                     w:asset.width, h:asset.height}:null,
    当前全景图元素在场: !!q('[data-director-panorama-current]'),
    当前全景图来源: q('[data-director-panorama-current]')
      ? q('[data-director-panorama-current]').getAttribute('data-director-panorama-current-source')
      : null,
    当前全景图文本: q('[data-director-panorama-current]')
      ? (q('[data-director-panorama-current]').textContent||'').replace(/\s+/g,' ').trim()
      : null,
  };
}"""


class Verifier:
    def __init__(self) -> None:
        self.count = 0
        self.failures: list[str] = []
        self.audit: dict = {}

    def check(self, name: str, ok: bool, detail: object = "") -> None:
        self.count += 1
        if not ok:
            self.failures.append(f"{name}  ⟵ {detail}")
            print(f"  FAILED: {name}  ⟵ {detail}")
        else:
            print(f"  ok: {name}")


def safe_click(page, selector: str, timeout: int = 15000) -> bool:
    """★ 安全点击：元素不存在（MIX 态）时**不抛**⟹ ⟹ 门禁不崩。

    ★ 崩在等元素上的红是**假牙**（batch 859 的教训）⟹ ⟹
    真正该红的是那些**读状态**的判据，不是崩出来的 traceback。
    """
    try:
        page.locator(selector).first.click(timeout=timeout)
        return True
    except Exception:  # noqa: BLE001
        return False


def read_source(path: pathlib.Path) -> str:
    """★ 源文件缺失时不崩 ⟹ ⟹ 当空串 ⟹ ⟹ 逐条判据各自报红（batch 859 的教训）。"""
    if not path.exists():
        return ""
    return strip_comments(path.read_text(encoding="utf-8"))


def main() -> int:
    v = Verifier()
    audit: dict = {"batch": 861, "title": "全景图面板三行不再是死按钮"}

    # ══ S1 源码契约 ══════════════════════════════════════════════
    panel = read_source(PANEL_SRC)
    picker = read_source(PICKER_SRC)
    store = read_source(STORE_SRC)
    ingress = read_source(INGRESS_SRC)
    desk = read_source(DESK_SRC)

    v.check("source:panel-has-three-rows",
            all(t in panel for t in ROW_TEXTS),
            detail={"缺失": [t for t in ROW_TEXTS if t not in panel]})
    # ★ 三行**共用一个** onClick（`map` 出来）⟹ ⟹ 不能数「onClick 出现三次」；
    #   真正的契约是：那个 onClick 里**按 id 分派**到三种行为。
    #   ★ ★★ **必须匹配「分派语句」本身**（不能全文 `in`、也不能按 id 字符串）
    #   ⟹ ⟹ 否则常量表 `panoramaItems` 里的同名 id 会让判据**假绿**
    #   （★ 本批阴性 N1 实测：全文匹配 ⟹ ⟹ 变异改坏了分派却仍绿）。
    dispatch = all(f'item.id === "{t}"' in panel
                   for t in ("local-upload", "history", "ai-generate"))
    v.check("source:every-row-has-an-onclick",
            "onClick" in panel and dispatch,
            detail={"onClick": "onClick" in panel,
                    "分派段缺失": [t for t in ("local-upload", "history", "ai-generate")
                                   if f'item.id === "{t}"' not in panel]})
    v.check("source:panel-has-a-hidden-file-input",
            'type="file"' in panel and 'accept="image/*"' in panel,
            detail={"type=file": 'type="file"' in panel,
                    "accept=image/*": 'accept="image/*"' in panel})
    v.check("source:panel-clicks-the-file-input",
            "fileInputRef.current?.click()" in panel,
            detail="源站逐字：et.current?.click()")
    v.check("source:store-has-the-local-panorama-asset",
            "localPanoramaAsset: DirectorLocalPanoramaAsset | null;" in store
            and "setLocalPanoramaAsset: (" in store,
            detail={"state 声明": "localPanoramaAsset: DirectorLocalPanoramaAsset | null;" in store,
                    "action 声明": "setLocalPanoramaAsset: (" in store})
    v.check("source:ingress-merges-the-local-input",
            "mergeDirectorLocalPanoramaInput" in ingress
            and 'DIRECTOR_LOCAL_PANORAMA_SOURCE_PREFIX = "local-panorama:"' in ingress,
            detail={"merge": "mergeDirectorLocalPanoramaInput" in ingress,
                    "前缀": 'DIRECTOR_LOCAL_PANORAMA_SOURCE_PREFIX = "local-panorama:"' in ingress})
    v.check("source:desk-wires-the-local-asset",
            "mergeDirectorLocalPanoramaInput" in desk
            and "localPanoramaAsset" in desk,
            detail={"merge": "mergeDirectorLocalPanoramaInput" in desk,
                    "asset": "localPanoramaAsset" in desk})
    # ★ ★★ 「四个动作入口」用**属性名**判（不是可见文本）⟹ ⟹
    #   可见文本里「生成」这个词还会出现在提示文案里 ⟹ ⟹ 用文本判会假绿
    #   （★ 本批阴性 N4 实测）。
    v.check("source:the-picker-has-the-source-actions",
            all(a in picker for a in (
                "data-director-panorama-generate",
                "data-director-panorama-picker-upload",
                "data-director-panorama-picker-cancel",
                "data-director-panorama-picker-confirm")),
            detail={"缺失": [a for a in (
                "data-director-panorama-generate",
                "data-director-panorama-picker-upload",
                "data-director-panorama-picker-cancel",
                "data-director-panorama-picker-confirm") if a not in picker]})
    # ★ ★★ 「生成」**绝不**能触发真实生成（真实生图会产生费用）
    v.check("source:the-generate-button-makes-no-network-call",
            not re.search(r"\bfetch\s*\(|XMLHttpRequest|axios|navigator\.sendBeacon",
                          picker),
            detail="clone 不接真实全景图生成 ⟹ ⟹ 选择器里不许出现网络调用")

    # ══ S2 源站实测产物 ══════════════════════════════════════════
    v.check("source:the-source-measurements-exist",
            SOURCE_DIFF.exists() and SOURCE_ROWS.exists(),
            detail=[str(SOURCE_DIFF), str(SOURCE_ROWS)])
    if SOURCE_DIFF.exists():
        sd = json.loads(SOURCE_DIFF.read_text(encoding="utf-8"))
        hist = (sd.get("历史记录") or {}).get("新增按钮") or []
        ai = (sd.get("AI生成") or {}).get("新增按钮") or []
        # ★ 按钮标签是「`||取消`」这种**分隔符拼起来的整串** ⟹ ⟹
        #   要判**子串**（`in` 对 list 判的是整串相等 ⟹ ⟹ 会假红）
        hist_text = " ".join(hist)
        ai_text = " ".join(ai)
        v.check("source:history-opens-the-asset-picker",
                contains(hist_text, "确认选择") and contains(hist_text, "生成历史"),
                detail=hist)
        v.check("source:ai-generate-adds-generate-and-upload",
                contains(ai_text, "生成") and contains(ai_text, "上传图片"),
                detail=ai)
        v.check("source:the-ai-row-has-one-more-button-than-history",
                len(ai) == len(hist) + 3,
                detail={"历史": len(hist), "AI": len(ai)})
    if SOURCE_ROWS.exists():
        sr = json.loads(SOURCE_ROWS.read_text(encoding="utf-8"))
        v.check("source:the-three-rows-are-not-disabled",
                all(r.get("disabled") is False for r in (sr.get("三行_前") or [])),
                detail=sr.get("三行_前"))
        # ★ 「本地上传」弹文件选择器这条读数在 **rows** 探针里（不是 diff 探针）
        v.check("source:local-upload-opens-a-file-chooser",
                sr.get("本地上传_弹了文件选择器") is True,
                detail=sr.get("本地上传_弹了文件选择器"))

    # ══ S3 clone 实测（live DOM）══════════════════════════════════
    fixture = pathlib.Path("/tmp/b861-gate-panorama.png")
    if not fixture.exists():
        import struct
        import zlib

        rows = []
        for y in range(4):
            row = b"\x00"
            for x in range(4):
                row += bytes([(x * 60) % 256, (y * 60) % 256, 200])
            rows.append(row)
        raw = b"".join(rows)

        def chunk(tag: bytes, data: bytes) -> bytes:
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        fixture.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))

    chooser_fired: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text)
                    if m.type == "error" else None)
            page.on("filechooser", lambda fc: chooser_fired.append("filechooser"))

            page.goto(BASE + "/", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            page.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
            page.wait_for_timeout(1500)
            node = page.locator(".react-flow__node-script-execution").first
            try:
                node.scroll_into_view_if_needed(timeout=8000)
            except Exception:  # noqa: BLE001
                pass
            page.wait_for_timeout(400)
            try:
                node.hover(timeout=8000)
                page.wait_for_timeout(600)
            except Exception:  # noqa: BLE001
                pass
            page.locator("[data-open-director]").first.click(timeout=15000)
            page.wait_for_timeout(6500)
            page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
            page.locator("[data-director-rail-entry='panorama']").first.click(timeout=15000)
            page.wait_for_timeout(900)

            base = page.evaluate(READ)
            audit["打开面板后"] = base
            v.check("clone:the-three-rows-are-present",
                    [r["text"] for r in base["三行"]] == ROW_TEXTS,
                    detail=[r["text"] for r in base["三行"]])
            v.check("clone:there-is-a-hidden-image-file-input",
                    base["隐藏文件输入"] == {"accept": "image/*", "type": "file"},
                    detail=base["隐藏文件输入"])

            # ★ 点「本地上传」⟹ ⟹ 弹出文件选择器
            page.locator("[data-director-panorama-option='local-upload']").first.click(
                timeout=15000)
            page.wait_for_timeout(1200)
            v.check("clone:local-upload-opens-a-file-chooser",
                    len(chooser_fired) >= 1,
                    detail={"filechooser 次数": len(chooser_fired)})

            # ★ 点「历史记录」⟹ ⟹ 选择器（history 形态）
            page.locator("[data-director-panorama-option='history']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            hist = page.evaluate(READ)
            audit["历史记录_后"] = hist
            v.check("clone:history-opens-the-picker",
                    hist["选择器"] is not None
                    and hist["选择器"]["mode"] == "history",
                    detail=hist["选择器"])
            v.check("clone:the-history-picker-has-cancel-and-confirm",
                    bool(hist["选择器"]
                         and hist["选择器"]["有取消按钮"]
                         and hist["选择器"]["有确认按钮"]),
                    detail=hist["选择器"])
            v.check("clone:the-history-picker-has-no-generate-button",
                    bool(hist["选择器"] and not hist["选择器"]["有生成按钮"]),
                    detail=hist["选择器"])
            safe_click(page, "[data-director-panorama-picker-cancel]")
            page.wait_for_timeout(700)
            v.check("clone:cancel-closes-the-picker",
                    page.evaluate(READ)["选择器"] is None,
                    detail=page.evaluate(READ)["选择器"])

            # ★ 点「AI生成」⟹ ⟹ 选择器（ai 形态，多「生成」「上传图片」）
            page.locator("[data-director-panorama-option='ai-generate']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            ai = page.evaluate(READ)
            audit["AI生成_后"] = ai
            v.check("clone:ai-generate-opens-the-picker",
                    ai["选择器"] is not None and ai["选择器"]["mode"] == "ai",
                    detail=ai["选择器"])
            v.check("clone:the-ai-picker-adds-generate-and-upload",
                    bool(ai["选择器"] and ai["选择器"]["有生成按钮"]
                         and ai["选择器"]["有上传图片按钮"]),
                    detail=ai["选择器"])
            safe_click(page, "[data-director-panorama-picker-cancel]")
            page.wait_for_timeout(700)

            # ★ 喂一张真文件 ⟹ ⟹ store 出现本地资产 ＋ 当前全景图换成它
            # ★ ★★ **崩在等元素上的红也是假牙**（batch 859 的教训）：
            #   MIX 态下面板被换回 HEAD（**没有**那个 file input）
            #   ⟹ ⟹ `set_input_files` 会**超时抛错** ⟹ ⟹ 整条门禁崩掉
            #   ⟹ ⟹ 改成「等不到就报一条具名红条」并继续往下走。
            fed: dict = {}
            try:
                page.locator("[data-director-panorama-file-input]").first.set_input_files(
                    str(fixture), timeout=15000)
                page.wait_for_timeout(1600)
                fed = page.evaluate(READ)
            except Exception as exc:  # noqa: BLE001
                v.check("clone:the-local-file-becomes-a-local-asset", False,
                        detail=f"CRASH: {type(exc).__name__}: 面板没有那个 file input")
                fed = page.evaluate(READ)
            audit["选完文件后"] = fed
            v.check("clone:the-local-file-becomes-a-local-asset",
                    fed["本地资产"] is not None
                    and fed["本地资产"]["imageUrl前缀"].startswith("blob:"),
                    detail=fed["本地资产"])
            v.check("clone:the-current-panorama-becomes-the-local-one",
                    (fed["当前全景图来源"] or "").startswith("local-panorama:"),
                    detail=fed["当前全景图来源"])
            v.check("clone:the-current-panorama-shows-the-filename",
                    bool(fed["当前全景图文本"] and fed["本地资产"]
                         and fed["本地资产"]["filename"] in fed["当前全景图文本"]),
                    detail=fed["当前全景图文本"])

            # ★ 选择器里应当**多出**本地那张
            page.locator("[data-director-panorama-option='history']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            picked = page.evaluate(READ)
            audit["含本地的选择器"] = picked
            options = (picked["选择器"] or {}).get("选项") or []
            v.check("clone:the-picker-lists-the-local-asset",
                    any(o.startswith("local-panorama:") for o in options),
                    detail=options)
            safe_click(page, "[data-director-panorama-picker-cancel]")
            page.wait_for_timeout(600)

            v.check("clone:no-page-errors",
                    not [e for e in errors if "TransformControls" not in e],
                    detail=errors[:5])
        finally:
            browser.close()

    result = {"判据数": v.count, "失败": v.failures, "audit": audit}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "runtime-audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n== batch 861 门禁：{v.count} 判据，{len(v.failures)} 失败 ==")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

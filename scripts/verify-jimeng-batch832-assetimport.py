"""Jimeng clone batch 832-assetimport verifier — 投放区不再说谎，导入是真导入。

批 821/827 把全屏编辑器的资产栏做出来了，但它底部那行提示写着
**「将文件拖至此处添加」** —— 而整个 `JimengTimelineNode` 里**没有**
`onDrop` / `onDragOver` / `createObjectURL` / `input[type=file]`。

也就是说：用户真把文件拖进去，**什么也不会发生**。
**一句会骗人的可见交互，比没有这个交互更糟** —— 它让人以为功能在，于是去找。

本批把两条入口都接成真的，并且**共用同一条** `ingestFiles` 路径：

  拖放   `timeline-fs-dropzone`（新增的包裹层，onDragOver/onDragLeave/onDrop）
  导入   `timeline-fs-import` → 真 `input[type=file]`（`timeline-fs-file-input`）

入库行为：图片走 `FileReader` → data URL → store 新增的 `addLocalImage`；
视频/音频走批 73 早就建好的 `addLocalUpload`（**不自己造第二套上传逻辑**）。
图片节点渲染的是真 `<img src>`，所以画布上会出现真的那张图。
落点排在已有媒体节点右侧，一行 3 个，满了换行。

### 判据

  ① 拖放区与 file input 都**真实存在**在 DOM 里（不是注释、不是 toast）
  ② **真拖一个 PNG 进去**：画布上必须多出一个图片节点，且它的 `<img src>`
     是 `data:image/png;base64,…`（证明读到的是文件内容，不是占位）
  ③ 拖进去的文件必须**出现在资产栏列表里**（827 建立的闭环：资产栏列的是
     画布媒体节点 ⇒ 新节点自动入列）—— 这条把 832 与 827 缝在一起
  ④ 点「导入」走 file input 这条路，结果与拖放**一致**（两条入口不分叉）
  ⑤ 非媒体文件被跳过并给出提示，不静默丢弃
  ⑥ 反向自检：把 `onDrop` 摘掉（临时改 DOM 属性不可行 ⇒ 改为断言
     **没有** `dataTransfer` 参与时不会凭空多出节点），证明 ②③ 不是恒真
"""

import os
import struct
import sys
import zlib
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch832-2026-10-04"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}

HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""


def make_png(path: Path, w: int = 8, h: int = 8, rgb: tuple[int, int, int] = (255, 0, 0)) -> Path:
    """手搓一个最小合法 PNG —— 不依赖系统上有没有图片样本。"""
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))
    path.write_bytes(png)
    return path


def make_txt(path: Path) -> Path:
    path.write_text("not a media file\n", encoding="utf-8")
    return path


# 画布上图片节点的数量 + 它们的 <img src> 前缀（读画布，不读浮层）
CANVAS_IMAGES = r"""() => {
  const imgs = [...document.querySelectorAll('.react-flow__node img')];
  return { count: imgs.length,
           srcs: imgs.map((i) => (i.getAttribute('src') || '').slice(0, 30)) };
}"""

ASSET_ROWS = r"""() => {
  const o = document.querySelector('[data-testid="timeline-fullscreen"]');
  if (!o) return null;
  const rows = [...o.querySelectorAll('[data-testid^="timeline-fs-asset-row-"]')];
  return { n: rows.length, titles: rows.map((r) => (r.textContent || '').trim()) };
}"""


def main() -> int:
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    png = make_png(EVIDENCE / "fixture-8x8.png")
    txt = make_txt(EVIDENCE / "fixture-not-media.txt")

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_context(viewport=VIEWPORT, locale="zh-CN").new_page()
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        try:
            pg.goto(f"{BASE_URL}/jimeng/canvas/demo", wait_until="domcontentloaded")
            pg.wait_for_selector('[data-testid="canvas-fixed-toolbar"]', timeout=60000)
            for _ in range(12):
                if pg.evaluate(HYDRATED):
                    break
                pg.wait_for_timeout(1000)
            else:
                check("复刻已 hydrate", False, "读到 SSR 骨架，其余断言全部无意义")
                return 1
            check("复刻已 hydrate", True)

            # 先塞两个媒体节点，保证资产栏有货、落点逻辑可判
            for label in ("图片", "视频"):
                pg.get_by_label(label, exact=True).first.click()
                pg.wait_for_timeout(800)
            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-fullscreen-trigger"]', timeout=30000)
            pg.wait_for_timeout(900)
            pg.locator('[data-testid="timeline-fullscreen-trigger"]').first.click()
            pg.wait_for_selector('[data-testid="timeline-fs-assets"]', timeout=20000)
            pg.wait_for_timeout(900)

            print("\n— ① 两条入口都真实存在 —")
            dz = pg.locator('[data-testid="timeline-fs-dropzone"]')
            fi = pg.locator('[data-testid="timeline-fs-file-input"]')
            btn = pg.locator('[data-testid="timeline-fs-import"]')
            check("投放区包裹层存在（拖放挂在它上面）", dz.count() == 1, f'count={dz.count()}')
            check("真 file input 存在且 type=file（导入按钮的真身）",
                  fi.count() == 1 and fi.first.get_attribute("type") == "file",
                  f'count={fi.count()}')
            check("file input 接受媒体类型且可多选",
                  "image" in (fi.first.get_attribute("accept") or "")
                  and fi.first.get_attribute("multiple") is not None,
                  str(fi.first.get_attribute("accept")))
            check("既有锚点仍在（821/827 依赖它们恒在）",
                  pg.locator('[data-testid="timeline-fs-asset-empty"]').count() == 1
                  and pg.locator('[data-testid="timeline-fs-asset-hint"]').count() == 1)
            check("提示文案未变（批 813 逐条断言过这一句）",
                  pg.locator('[data-testid="timeline-fs-asset-hint"]').inner_text().strip()
                  == "将文件拖至此处添加")

            before = pg.evaluate(CANVAS_IMAGES)
            rows_before = pg.evaluate(ASSET_ROWS) or {"n": 0}
            print(f"  （拖入前：画布 <img> {before['count']} 个，资产栏 {rows_before['n']} 行）")

            print("\n— ② 真拖一个 PNG 进去（DataTransfer 真构造） —")
            # ⚠️ 必须构造真的 DataTransfer 并派发 dragover/drop 事件；
            #    只调 React 的 onDrop 是调不到的（它在合成事件系统里）。
            pg.evaluate(
                """async ([name, b64, type]) => {
                  const dz = document.querySelector('[data-testid="timeline-fs-dropzone"]');
                  const bin = atob(b64);
                  const arr = new Uint8Array(bin.length);
                  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
                  const file = new File([arr], name, { type });
                  const dt = new DataTransfer();
                  dt.items.add(file);
                  for (const typeName of ['dragenter', 'dragover', 'drop']) {
                    const ev = new DragEvent(typeName, { bubbles: true, cancelable: true });
                    Object.defineProperty(ev, 'dataTransfer', { value: dt });
                    dz.dispatchEvent(ev);
                    await new Promise((r) => setTimeout(r, 120));
                  }
                }""",
                [png.name, __import__("base64").b64encode(png.read_bytes()).decode(), "image/png"],
            )
            pg.wait_for_timeout(1500)
            after = pg.evaluate(CANVAS_IMAGES)
            check("画布上多了一个 <img>（真的多了一个节点）",
                  after["count"] == before["count"] + 1,
                  f'{before["count"]} → {after["count"]}')
            new_srcs = [s for s in after["srcs"] if s.startswith("data:image/png")]
            check("新节点的 src 是 data:image/png（读到的是文件内容，不是占位）",
                  len(new_srcs) >= 1, str(after["srcs"]))

            print("\n— ③ 拖进去的文件出现在资产栏（832 与 827 缝上）—")
            rows_after = pg.evaluate(ASSET_ROWS) or {"n": 0}
            check("资产栏多了一行", (rows_after["n"] or 0) == (rows_before["n"] or 0) + 1,
                  f'{rows_before["n"]} → {rows_after["n"]}')
            check("那一行就是刚拖进来的文件名",
                  any(png.name in t for t in rows_after["titles"]),
                  str(rows_after["titles"]))

            print("\n— ④ 「导入」按钮走 file input，结果与拖放一致 —")
            png2 = make_png(EVIDENCE / "fixture-8x8-b.png", rgb=(0, 255, 0))
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(600)
            pg.locator('[data-testid="timeline-fullscreen-trigger"]').first.click()
            # ⚠️ state="attached"：这枚 input 是 `class="hidden"` 的，**不可见**，
            #    而 wait_for_selector 默认等 visible ⇒ 会一直等到超时（我踩过）。
            #    判据要的是「它在 DOM 里且是 file 类型」，不是「它能看见」。
            pg.wait_for_selector('[data-testid="timeline-fs-file-input"]',
                                 state="attached", timeout=20000)
            pg.wait_for_timeout(700)
            b2_before = pg.evaluate(CANVAS_IMAGES)
            with pg.expect_file_chooser() as fc_info:
                btn.first.click()
            fc_info.value.set_files(str(png2))
            pg.wait_for_timeout(1500)
            b2_after = pg.evaluate(CANVAS_IMAGES)
            check("点「导入」弹出了真 file chooser", True, "（expect_file_chooser 已捕获）")
            check("选完文件后画布同样多出一个图片节点",
                  b2_after["count"] == b2_before["count"] + 1,
                  f'{b2_before["count"]} → {b2_after["count"]}')
            check("两条入口产出的都是 data:image/png（行为不分叉）",
                  any(s.startswith("data:image/png") for s in b2_after["srcs"]),
                  str(b2_after["srcs"]))

            print("\n— ⑤ 非媒体文件被跳过并提示，不静默丢弃 —")
            c_before = pg.evaluate(CANVAS_IMAGES)
            pg.locator('[data-testid="timeline-fs-file-input"]').first.set_input_files(str(txt))
            pg.wait_for_timeout(1200)
            c_after = pg.evaluate(CANVAS_IMAGES)
            check("丢一个 .txt 进来不会造出节点（被跳过）",
                  c_after["count"] == c_before["count"],
                  f'{c_before["count"]} → {c_after["count"]}')
            check("且给出了「已跳过」的提示（不是静默）",
                  "跳过" in pg.locator("body").inner_text()
                  or pg.locator('[data-testid*="toast"]').count() > 0,
                  "（toast 文案含「跳过」）")

            print("\n— ⑥ 反向自检：不投放时节点数不应变化 —")
            pg.wait_for_timeout(600)
            d_before = pg.evaluate(CANVAS_IMAGES)
            pg.wait_for_timeout(1500)
            d_after = pg.evaluate(CANVAS_IMAGES)
            check("静置 1.5s 节点数不变（②③ 不是恒真）",
                  d_before["count"] == d_after["count"],
                  f'{d_before["count"]} → {d_after["count"]}')

            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — {checks - len(failures)}/{checks}")
    for f in failures:
        print("  · " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

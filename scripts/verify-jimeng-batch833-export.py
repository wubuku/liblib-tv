"""Jimeng clone batch 833-export verifier — 「导出时间线」真的下载了一个文件。

批 833 之前，点「导出时间线」只弹一句 `导出时间线` —— 一个字节都没产出。

⚠️ **格式与源站不同，本 verifier 明确承认这一点**：源站导出的是**渲染好的视频**；
复刻没有渲染器（时间线在这里是数据，不是帧序列），所以导出**结构化 JSON**。
所以本 verifier **不**断言「导出的是视频」，而是断言：

  ① 真发生了下载（Playwright `expect_download` 捕获到，拿到真实文件路径）
  ② 文件名以 `.json` 结尾、内容是**合法 JSON**
  ③ 内容里真的有这条时间线的数据：节点名、时长、逐个片段的 名称/起点秒/时长秒
     —— 这一条是关键：**必须由操作产生**，不能是写死的模板
  ④ **先加片段再导出，导出的 JSON 里片段数随之变多**（内容随状态走，不是快照）
  ⑤ 空态导出也要成功（0 个片段也要产出合法文件，不是报错也不是不响应）
  ⑥ 反向自检：不点导出时**不会**产生下载（证明 ① 不是环境自己在下东西）

  ⑦ toast 里必须写明「源站导出视频，此处为结构化 JSON」——
     这是本批最要紧的一条**诚实性**契约：格式不同这件事不许瞒着用户。
"""

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch833-2026-10-04"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}

HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""

FS_CLIP_COUNT = r"""() => {
  const o = document.querySelector('[data-testid="timeline-fullscreen"]');
  return o ? o.querySelectorAll('[data-testid="timeline-fullscreen-clip"]').length : -1;
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
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_context(viewport=VIEWPORT, locale="zh-CN", accept_downloads=True).new_page()
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

            # ⚠️ 顺序：先插时间线节点，再等壳（壳在插入前不存在）
            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-fullscreen-trigger"]', timeout=30000)
            pg.wait_for_timeout(900)
            pg.locator('[data-testid="timeline-fullscreen-trigger"]').first.click()
            pg.wait_for_selector('[data-testid="timeline-fullscreen"]', timeout=20000)
            pg.wait_for_timeout(900)

            export_btn = pg.locator('[data-testid="timeline-fullscreen-export"]').first

            print("\n— ①③ 空态导出：真下载 + 合法 JSON + 内容来自状态 —")
            with pg.expect_download(timeout=15000) as dl_info:
                export_btn.click()
            dl = dl_info.value
            fname = dl.suggested_filename
            path = EVIDENCE / fname
            dl.save_as(str(path))
            check("真发生了下载（expect_download 捕获到真实文件）", path.exists(),
                  f'suggested_filename={fname}')
            check("文件名以 .json 结尾（格式差异在文件名上就看得出来）",
                  fname.endswith(".json"), repr(fname))
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                parsed = True
            except Exception as e:  # noqa: BLE001
                data, parsed = {}, False
                check("内容是合法 JSON", False, str(e)[:120])
            if parsed:
                check("内容是合法 JSON", True)
                check("含节点名 / 时长 / 片段三段结构",
                      all(k in data for k in ("节点", "时长秒", "片段")),
                      str(list(data.keys())))
                check("空态：片段是空数组（不是缺字段、也不是报错占位）",
                      data.get("片段") == [], str(data.get("片段")))
                check("含时长秒（数值）", isinstance(data.get("时长秒"), (int, float)),
                      repr(data.get("时长秒")))

            print("\n— ④ 先加片段再导出：内容随状态变多 —")
            n_before = pg.evaluate(FS_CLIP_COUNT)
            # 用空态投放区那枚「添加素材到时间线」加一个片段
            pg.get_by_label("添加素材到时间线", exact=True).first.click()
            pg.wait_for_timeout(700)
            n_after = pg.evaluate(FS_CLIP_COUNT)
            check("先加进去一个片段（前置条件）", n_after == n_before + 1,
                  f'{n_before} → {n_after}')
            with pg.expect_download(timeout=15000) as dl2_info:
                export_btn.click()
            dl2 = dl2_info.value
            path2 = EVIDENCE / dl2.suggested_filename
            dl2.save_as(str(path2))
            data2 = json.loads(path2.read_text(encoding="utf-8"))
            check("导出的 JSON 里片段数 = 当前片段数（内容随状态走，不是快照）",
                  len(data2.get("片段", [])) == n_after,
                  f'JSON {len(data2.get("片段", []))} vs 界面 {n_after}')
            seg = (data2.get("片段") or [{}])[0]
            check("每个片段含 名称/起点秒/时长秒 三项",
                  all(k in seg for k in ("名称", "起点秒", "时长秒")), str(seg))
            check("片段起点是秒数（与刻度世界坐标模型同源）",
                  isinstance(seg.get("起点秒"), (int, float)), repr(seg.get("起点秒")))

            print("\n— ⑤ 不点导出就不会下载（反向自检） —")
            downloaded = {"n": 0}
            pg.on("download", lambda _d: downloaded.__setitem__("n", downloaded["n"] + 1))
            pg.wait_for_timeout(2500)
            check("静置 2.5s 没有发生任何下载（① 不是环境自己在下东西）",
                  downloaded["n"] == 0, f'下载 {downloaded["n"]} 次')

            print("\n— ⑥⑦ 诚实性：toast 必须写明格式差异 —")
            with pg.expect_download(timeout=15000):
                export_btn.click()
            pg.wait_for_timeout(600)
            body = pg.locator("body").inner_text()
            check("toast 写明「源站导出视频，此处为结构化 JSON」",
                  "源站导出视频" in body and "结构化 JSON" in body,
                  "（文案在浮层 toast 里）")
            check("toast 含导出的片段数", f"{n_after} 个片段" in body, f'期望 {n_after} 个片段')

            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — {checks - len(failures)}/{checks}")
    for f in failures:
        print("  · " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

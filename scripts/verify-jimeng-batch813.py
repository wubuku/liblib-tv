"""Jimeng clone batch 813 verifier — 807 新增的三个节点：补齐内部死按钮 + 尺寸订正。

## 起因：普查漏了一整类界面

batch 807 往画布里加了**时间线 / 主体 / 导演台**三种节点，但 807/808 的普查
只覆盖了「默认视图 + 既有交互态」，**从没进过"插入之后"这个态** ——
那三个节点里的死按钮一个都没被发现：

```
时间线节点: 8 个内部按钮, 死 3: ['下载', '全屏编辑', '静音']
主体节点:   7 个内部按钮, 死 1: ['编辑主体']
```

**运行时才长出来的界面，静态普查是够不着的。** 这和 810 的 contenteditable
是同一类问题的另一个面：那次是探针够不着状态，这次是探针没进状态。

## 源站实测（登录态，逐个按钮点）

| 控件 | 源站行为 |
|---|---|
| 导出时间线 42×42 | 弹导出菜单：导出为 MP4（附「当前时间线暂不支持此操作」）/ 导出为 XML（附「批量导出时间线素材 · 请选择至少一个组、文本、图片或视频项」）/ 导出到 剪映 · DaVinci Resolve · Premiere · Final Cut Pro |
| 全屏编辑 126×42 | 打开全屏时间线编辑器：标题 +「Edit the main visual track and multiple audio tracks」+ 来源 tab（已导入资产/画布资产/全部）+ 类型筛选（图片/视频/音频）+ 资产区（空态「没有媒体可供预览 · 将文件拖至此处添加」）+ 底部「Timeline playhead 00:00:00 / 00:00:00」 |
| 静音 42×42 `timeline-mute-button` | 真的切换 |
| 编辑主体 | 打开 `subject-metadata-editor` 描述编辑器 |

## 顺带纠正的尺寸

时间线节点源站实测 **1200×207**，此前按截图读成 1206×212，偏了 6×5。

## 顺带修掉的可用性缺陷：静音钮被连接手柄吞掉

节点的左侧连接手柄命中盒实测 **44×88**，从左缘往里吞掉约 30px（世界像素）。
左槽只有 w-12(48) 时，静音钮整个落在手柄命中盒里 ——
Playwright 报 `handle intercepts pointer events`，**用户同样点不到**。
w-24(96) 让开了但只剩 1px 余量（实测手柄右缘 424、钮左缘 425），太险；
最终 w-32(128)，余量 ~13px。源站那枚钮是从左缘内缩约 36px 放的，正是为了避开手柄。
手柄几何是 batch 806 的地盘，不去动那边。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}
# SOURCE_FACT: 源站时间线节点 1200×207
TL_SIZE = (1200, 207)


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    def near(a, b, tol=0.6):
        return abs(a - b) <= tol

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, locale="zh-CN")
        page = ctx.new_page()
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        def fresh():
            page.reload(wait_until="domcontentloaded")
            page.wait_for_selector('[data-testid="canvas-top-bar"]', timeout=25000)
            page.wait_for_timeout(500)

        def insert(rail: str, tid: str):
            fresh()
            page.locator(f'[aria-label="{rail}"]').first.click()
            page.wait_for_selector(f'[data-testid="{tid}"]', timeout=10000)
            page.wait_for_timeout(400)

        def toasts() -> str:
            t = page.locator('[role="status"]')
            return " ".join(t.nth(i).inner_text() for i in range(t.count()))

        def sample_toast(want: str, tries: int = 20) -> str:
            """toast 短命，120ms 级采样"""
            for _ in range(tries):
                seen = toasts()
                if want in seen or seen:
                    return seen
                page.wait_for_timeout(120)
            return toasts()

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_selector('[data-testid="canvas-top-bar"]', timeout=25000)
        page.wait_for_timeout(700)

        print("— 时间线节点：尺寸订正 —")
        insert("时间线", "timeline-node")
        wh = page.evaluate("""() => {
            const el = document.querySelector('[data-testid="timeline-node"]');
            return {w: el.offsetWidth, h: el.offsetHeight};
        }""")
        check(f"时间线节点 {TL_SIZE[0]}×{TL_SIZE[1]}（源站实测，非 1206×212）",
              near(wh["w"], TL_SIZE[0]) and near(wh["h"], TL_SIZE[1]), str(wh))

        print("— 静音：真切换，且不被连接手柄吞掉 —")
        mute = page.locator('[data-testid="timeline-mute-button"]')
        check("静音钮存在", mute.count() == 1)
        gap = page.evaluate("""() => {
            const node = document.querySelector('[data-testid="timeline-node"]');
            const nb = node.getBoundingClientRect();
            const mb = node.querySelector('[data-testid="timeline-mute-button"]').getBoundingClientRect();
            const h = Array.from(node.parentElement.querySelectorAll('.react-flow__handle'))
                .find(x => x.getAttribute('data-handlepos') === 'left');
            const hr = h.getBoundingClientRect();
            return Math.round(mb.x - hr.right);   // 负数=被吞
        }""")
        check("静音钮不被左侧手柄覆盖（用户点得到）", gap >= 4, f"与手柄右缘间距 {gap}px")
        before_al = mute.get_attribute("aria-label")
        mute.click()
        page.wait_for_timeout(400)
        after = page.locator('[data-testid="timeline-mute-button"]')
        check("点静音后 aria-label 切换", after.get_attribute("aria-label") != before_al,
              f"{before_al!r} -> {after.get_attribute('aria-label')!r}")
        check("点静音后 aria-pressed 置位", after.get_attribute("aria-pressed") == "true",
              f"aria-pressed={after.get_attribute('aria-pressed')!r}")

        print("— 导出时间线：源站那枚不是「下载」而是导出菜单 —")
        page.locator('[data-testid="timeline-export-trigger"]').click()
        page.wait_for_selector('[data-testid="timeline-export-menu"]', timeout=10000)
        menu = page.locator('[data-testid="timeline-export-menu"]').inner_text()
        for frag in ["导出为 MP4", "当前时间线暂不支持此操作", "导出为 XML",
                     "导出到剪映", "导出到 DaVinci Resolve", "导出到 Premiere", "导出到 Final Cut Pro"]:
            check(f"导出菜单含「{frag}」", frag in menu, repr(menu[:120]))
        page.locator('[data-testid="timeline-export-menu"] [role=menuitem]').first.click()
        # 空时间线点 MP4 导出，源站给的是「当前时间线暂不支持此操作」这一条，
        # 所以断言查的是这句话而不是「MP4」两个字
        seen = sample_toast("不支持")
        check("点导出 MP4 有反馈 toast（源站的「暂不支持」）",
              "不支持" in seen, repr(seen[:60]))

        print("— 全屏编辑：打开源站那套编辑器 —")
        page.locator('[data-testid="timeline-fullscreen-trigger"]').click()
        page.wait_for_selector('[data-testid="timeline-fullscreen"]', timeout=10000)
        fs = page.locator('[data-testid="timeline-fullscreen"]')
        fs_txt = fs.inner_text()
        for frag in ["Edit the main visual track and multiple audio tracks",
                     "已导入资产", "画布资产", "全部",
                     "图片", "视频", "音频", "没有媒体可供预览", "将文件拖至此处添加", "导入",
                     "Timeline playhead"]:
            check(f"全屏编辑器含「{frag}」", frag in fs_txt, repr(fs_txt[:140]))
        page.locator('[data-testid="timeline-fs-source-画布资产"]').click()
        page.wait_for_timeout(300)
        cls = page.locator('[data-testid="timeline-fs-source-画布资产"]').get_attribute("class")
        check("切来源 tab 有选中态", "bg-white/15" in (cls or ""), repr(cls))
        page.locator('[data-testid="timeline-fs-kind-音频"]').click()
        page.wait_for_timeout(300)
        kcls = page.locator('[data-testid="timeline-fs-kind-音频"]').get_attribute("class")
        check("切类型筛选有选中态", "bg-white/15" in (kcls or ""), repr(kcls))
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch813-timeline-fullscreen-1680.png"))
        page.locator('[data-testid="timeline-fullscreen-close"]').click()
        page.wait_for_timeout(500)
        check("能关掉全屏编辑器", page.locator('[data-testid="timeline-fullscreen"]').count() == 0)

        print("— 主体：编辑笔接成 subject-metadata-editor —")
        insert("主体", "subject-node")
        check("编辑笔存在", page.locator('[data-testid="subject-meta-trigger"]').count() == 1)
        page.locator('[data-testid="subject-meta-trigger"]').click()
        page.wait_for_selector('[data-testid="subject-metadata-editor"]', timeout=10000)
        check("点笔打开描述编辑器", page.locator('[data-testid="subject-metadata-editor"]').count() == 1)
        ta = page.locator('[data-testid="subject-metadata-editor"] textarea')
        ta.fill("主角：一名侦探")
        page.locator('[data-testid="subject-meta-save"]').click()
        page.wait_for_timeout(500)
        check("保存后编辑器关闭", page.locator('[data-testid="subject-metadata-editor"]').count() == 0)
        check("描述写回常驻输入行",
              page.locator('[data-testid="subject-description"]').input_value() == "主角：一名侦探",
              page.locator('[data-testid="subject-description"]').input_value())
        check("保存有反馈 toast", "主体描述" in sample_toast("主体描述"), repr(toasts()[:60]))

        print("— 内部控件普查已并入 jimeng_state_audit —")
        audit = (ROOT / "scripts" / "jimeng_state_audit.py").read_text(encoding="utf-8")
        for frag in ["时间线节点内部", "主体节点内部", "导演台节点内部"]:
            check(f"普查脚本覆盖「{frag}」", frag in audit)

        print("— 回归 —")
        fresh()
        check("刷新后画布仍是初始 2 节点", page.locator(".react-flow__node").count() == 2)
        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        ctx.close()
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 813 三节点内部死按钮归零 + 尺寸订正（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()

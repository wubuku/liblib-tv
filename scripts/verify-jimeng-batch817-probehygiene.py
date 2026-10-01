"""Jimeng clone batch 817-probehygiene verifier — 给**探针本身**上锁。

这一批的产品改动只有 1 行（`全屏` → `全屏预览`）。真正的收获是两次
**取证事故**，本 verifier 就是它们的护栏：

## 事故一：探针读到一个「没 hydrate 的降级页面」

`next dev` 下，从**非 `localhost` 主机**访问会让 React **完全不 hydrate**：
页面只剩 SSR 静态 HTML —— 节点不渲染、`defaultViewport` 不生效、所有交互
失效、`store` 写入无效，而且**零报错、零警告**。

实测（2026-10-04，同一 dev server、同一时刻、同一视口）：

| 主机 | `.react-flow__node` | 根元素 React fiber | 点「视频」后顶栏计数 |
|---|---|---|---|
| `localhost:4317` | 2 | `__reactFiber$…` 有 | 2 → **3** |
| `127.0.0.1:4317` | **0** | **空** | 2 → 2（没变） |
| `[::1]:4317` | **0** | 空 | — |

顺序无关、cache-buster 无关，所以不是缓存假象。全仓没有任何按 Host 分流的
代码（无 middleware、无 hostname 判断），这是 `next dev` 的
`allowedDevOrigins` 行为，**不是产品缺陷**。

**危害不在这一次**：症状是"复刻缺一堆东西"，很容易被读成产品缺口并照着去
实现。`scripts/jimeng_a11y_census.py` 首轮就是这么把 4 个「复刻缺失」报出来
的 —— 改对 URL 后同样的普查，复刻侧读数从 24 变成 30，那 4 条全部消失。
**复现「判据够不着 ≠ 事实如此」的第 N 次，而且这次伪装成产品缺陷。**

护栏：
1. 应用 origin 一律 `localhost`（保留 `127.0.0.1:9444/9555`，那是 CDP 调试
   端口，不是应用 origin，不在管辖范围）
2. 读复刻侧之前必须先过 **hydrate 闸门**（`__reactFiber$*` 探针）

## 事故二：源站 fixture 在退化，不能当稳定常量

同一源站 URL 连续两次全新加载：节点 **7 → 6 → 5**（`图片 1`、`音频 1` 逐次
消失），顶栏全程显示「已保存」。媒体未加载的空节点被源站自己清掉并落盘。

后果：`Canvas node summary: 节点 N` **不能**当跨站对比键，它每次都在变。
本批之前的 census 把它列为一条「复刻缺失」，纯属误报。

## 词汇收口

`全屏` / `全屏预览` / `退出全屏预览` 三处本是一套词的前两个在漂移。
收口到 `全屏预览`（2/3 处在用，且与该按钮自己的 onAction 动作名一致）。
`退出全屏预览` 语义不同（退出 vs 进入），**保持独立**。

刻意**不收口**的一处：`播放`（媒体卡中央 32px 圆钮）与 `底部播放`（同卡底栏）
看着像重复命名，实为**同卡片内的有意消歧** —— 改成同名反而会让屏幕阅读器用户
在两个控件之间无法区分。别去"统一"它。
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")

# 应用 origin 的硬编码红线。CDP 调试端口（9444/9555）不在此列 —— 那是
# connectOverCDP 的浏览器控制端点，和应用 origin 无关。
APP_ORIGIN_BAD = re.compile(r"https?://127\.0\.0\.1:4317")
CDP_OK = re.compile(r"https?://127\.0\.0\.1:9\d{3}")

HYDRATED = """() => {
  const el = document.getElementById('__next')
          || document.body.firstElementChild
          || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$'));
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

    print("— 组 1：应用 origin 一律 localhost（源码级）—")
    for p in sorted(SCRIPTS.rglob("*")):
        if p.suffix not in (".py", ".mjs", ".js") or not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in APP_ORIGIN_BAD.finditer(text):
            line = text[: m.start()].count("\n") + 1
            ctx = text[max(0, m.start() - 30): m.end() + 30].replace("\n", " ")
            # 注释里提到这个串是**说明为什么不能这么写**，不算违规
            tail = text[m.end():m.end() + 120]
            if ctx.lstrip().startswith("#") or "不能" in tail or "⚠" in text[max(0, m.start() - 200):m.start()]:
                continue
            check(f"{p.relative_to(ROOT)}:{line} 未用 localhost", False, ctx)
    check("应用 origin 无 127.0.0.1:4317 硬编码", True)

    print("\n— 组 2：census 脚本必须带 hydrate 闸门 —")
    census = (SCRIPTS / "jimeng_a11y_census.py")
    ctext = census.read_text(encoding="utf-8") if census.exists() else ""
    check("census 脚本存在", bool(ctext))
    check("census 用了 JIMENG_BASE_URL / localhost",
          "localhost" in ctext and "JIMENG_BASE_URL" in ctext)
    check("census 里有 __reactFiber hydrate 探针", "__reactFiber" in ctext)
    check("census 在读复刻侧前调用了 hydrate 闸门",
          bool(re.search(r"HYDRATED", ctext)) and ctext.count("HYDRATED") >= 2)
    check("census 闸门失败时会中止而不是硬读",
          "SystemExit" in ctext and "SSR" in ctext)

    print("\n— 组 3：无障碍名词汇收口（源码级）—")
    tb = (ROOT / "src/components/jimeng/JimengNodeToolbar.tsx").read_text(encoding="utf-8")
    check("JimengNodeToolbar 用 `全屏预览`", 'aria-label="全屏预览"' in tb)
    check("裸 `全屏` 名已消失", not re.search(r'aria-label="全屏"', tb))
    # 退出浮层是另一个语义，必须保持独立
    vp = (ROOT / "src/components/jimeng/JimengVideoPreview.tsx").read_text(encoding="utf-8")
    check("预览浮层保留独立的 `退出全屏预览`", 'aria-label="退出全屏预览"' in vp)
    # 刻意不收口的一处，写成反向断言挡住"顺手统一"
    card = (ROOT / "src/components/jimeng/nodes/JimengVideoMediaCard.tsx").read_text(encoding="utf-8")
    check("媒体卡中央 `播放/暂停` 保留", 'aria-label={playing ? "暂停" : "播放"}' in card)
    check("媒体卡底栏 `底部播放/底部暂停` 保留（同卡片内消歧）",
          'aria-label={playing ? "底部暂停" : "底部播放"}' in card)
    # 静音三处必须一致。**按文件计数，不按字符串出现次数** —— 媒体卡里
    # `aria-label` 和 `title` 各写了一遍，字符串出现 4 次但组件只有 3 个。
    # 同理**不断言代码形状**：三处的状态变量写法本就不同（`muted` / `d.muted`），
    # 把变量名写进正则等于把写法钉成契约（批 807-topleft「控件矩形 ≠ 容器
    # 矩形」、批 800「断言点位踩亚像素」都是这个教训）。契约是**读出来的那两个词**。
    MUTE_FILES = [
        ROOT / "src/components/jimeng/nodes/JimengVideoMediaCard.tsx",
        ROOT / "src/components/jimeng/JimengVideoPreview.tsx",
        ROOT / "src/components/jimeng/nodes/JimengTimelineNode.tsx",
    ]
    for f in MUTE_FILES:
        rel = f.relative_to(ROOT)
        got = len(re.findall(r'"取消静音"\s*:\s*"静音"', f.read_text(encoding="utf-8")))
        check(f"{rel} 含 静音/取消静音 对", got >= 1, f"命中 {got} 次")
    stray = [str(f.relative_to(ROOT)) for f in (ROOT / "src/components/jimeng").rglob("*.tsx")
             if f not in MUTE_FILES
             and re.search(r'"取消静音"\s*:\s*"静音"', f.read_text(encoding="utf-8"))]
    check("没有第四处静音词汇", not stray, str(stray))

    print("\n— 组 4：运行时 hydrate 实测 —")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport={"width": 1512, "height": 950}, locale="zh-CN")
        try:
            pg.goto(f"{BASE_URL}/jimeng/canvas/demo", wait_until="domcontentloaded")
            pg.wait_for_selector('[data-testid="canvas-fixed-toolbar"]', timeout=45000)
            ok = False
            for _ in range(12):
                if pg.evaluate(HYDRATED):
                    ok = True
                    break
                pg.wait_for_timeout(1000)
            check(f"{BASE_URL} 已 hydrate", ok,
                  "读到的是 SSR 骨架，本 verifier 的其余运行时断言全部无意义")
            n = pg.locator(".react-flow__node").count()
            check("画布确实渲染出节点（降级页会读到 0）", n > 0, f"nodes={n}")
        finally:
            b.close()

    print()
    if failures:
        print(f"FAIL batch817-probehygiene — {checks} 项中 {len(failures)} 项失败")
        for f in failures:
            print("  -", f)
        return 1
    print(f"PASS batch817-probehygiene — {checks} 项断言全通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())

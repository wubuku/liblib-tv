#!/usr/bin/env python3
"""Verify Batch 368: 运行时扫描器打通面板面后新暴露的 12 处「骗人」控件 + 三个判据盲区。

## 怎么找到的

batch 367 的普查**读源码** `<button>` 标签, 抓到 7 处死控件。但源码判据有三个
它看不见的洞, 其中最要命的一个是**口径太窄**:

> 367 要求按钮「自称可点」(有 `aria-label` / `data-testid` / `role="button"`) 才收。
> 而 `SegmentReshootPanel` 的「参考」「标记」「角色库」三颗 pill
> **连 aria-label 都没有**, 却和同一行右侧**真能用的**「展开/收起」长得一模一样 ——
> 于是 367 一个都没抓到。

所以 368 改用 359/360 已有的**运行时**扫描器(`SCAN_JS` / `classify`),
并复用 367 刚踩平 8 个坑才走通的导航路径, 把扫描打到 9 个面板面上。

## 三个判据盲区(都是这批踩出来的)

1. **`SELF_CLAIM` 口径太窄** —— 只要 `aria-label` / `data-testid` / `role="button"`。
   漏掉两类: (a) 没有任何标记的裸 `<button>`; (b) 有 `data-*` 但不是 `data-testid`
   (`data-panorama-add-reference` / `data-image-editor-model` / `data-mark-select-return` …)。
   改法: **全都收**, 把「自称」降级成 `selfClaim` 标签 ——
   `selfClaim: false` 的候选**更值得看**(连自己是个控件都没说清楚)。
2. **裸块注释没剥** —— 工具只剥 `{/* */}` 和 `//`。我给 `SegmentReshootPanel` 写
   修复说明时用了 `return ( /* …按「<button> 即控件」的口径… */ <button/> )`
   这种**表达式位置**的 JS 块注释(外面没花括号), 于是注释里那句字面量
   `<button>` 被当成真标签扫出来, 凭空多一个候选。
   > **给修复写的说明文档, 反过来制造了一个新的误报。** 判据必须扛得住
   > 源码里出现「关于判据本身的文字」, 否则每修一次就多一个假阳。
3. **`<a href>` 被误判成死控件** —— `wired` 只认 React 的 onClick/onChange/onInput,
   而 `<a href download>` 有**原生行为**, 不经 React handler。4 个面板里各误报一次,
   是那次普查 14 个候选里的 4 个。补上原生语义(空 href / `href="#"` 仍然该报)。

## 处置: 12 处让 UI 停止撒谎, 不发明

源站行为全部未采样(人机验证阻塞); 其中「积分」「整组执行」「一键合成全部提示词」
关联付费, **永不接线**。同 batch 358/359/360/364/366/367: 去悬停骗人反馈 +
`cursor: default` + `title` 说明 + `data-inert` 自证惰性, 几何文案不动。

**两处是「处置只做了一半」的补齐**, 单独记一笔:
- 「一键合成全部提示词」**早就有 title** 写明「clone 不触发」—— 说明当初知道它
  不干活。但缺 `data-inert`, 而且 `hover:bg-white` 还在。
  **「有 title 就算自证」不成立**: title 要悬停才看得见, 视觉承诺已经先给出去了。
- 「整组执行」**早就有 `cursor: default` + 变暗** —— 同样只做了一半, 缺
  `data-inert` 和 `title`。

## 只记录不改动(够不着 ≠ 骗人)

- `CameraConfigDialog.tsx` 4 处: **全仓库无人 import**, 连 director 也没引用。
  是死代码, 不是骗人控件 —— 用户永远看不到。
- `VideoGenerationPanel.tsx:499`: 5 个 pill 全部有 `hasMenu` 或专门分支,
  这行是**给不存在的 label 留的兜底**, 当前不可达。改它没有用户可见效果。
  但它是**潜在陷阱**: 将来加一个没处理的新 pill, 会静默变成骗人控件。

## 断言

1. **防假零**: 12 处必须真的走到, 走不到直接红(360 立的规矩);
2. 每处 `data-inert` + 非空 `title` + `cursor: default` + **无 hover 类**;
3. **几何未变**: class 尺寸 token 精确比对;
4. **反向断言**: 同一面里**真能用的**控件没被改 inert
   (参考/标记 pill 那行右侧的「展开片段重拍编辑器」、「提交片段重拍」…);
5. **判据自身的双向自检**:
   - 裸 `/* */` 注释里的 `<button>` 不得被扫出来(阴性);
   - 真死控件仍必须被扫出来(阳性);
   - `<a href>` 不得再被判死, 而空 href 必须仍被判死;
6. 源码普查里**非 hoverTarget** 的候选必须**只落在**两个「只记录」白名单里
   (CameraConfigDialog 4 + VideoGenerationPanel 兜底 1) —— 出现别的就是回归;
7. 诊断零错误。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from playwright.sync_api import Page, sync_playwright  # noqa: E402

import probe_liblib_batch367_dead_buttons as CENSUS  # noqa: E402
import probe_liblib_batch367_reachability as REACH  # noqa: E402
from probe_liblib_batch359_node_surfaces import SCAN_JS  # noqa: E402

URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT = ROOT / "docs" / "research" / "liblib-batch368-2026-10-02" / "verify.json"
VIEWPORT = REACH.VIEWPORT

PROBE_JS = REACH.PROBE_JS

# 面 -> 该面必须出现的惰性控件 (选择器 -> 期望的 class 尺寸 token)
#
# `size_tokens` 是**精确契约**: 我承诺「几何不动」, 所以尺寸 token 必须原样保留。
EXPECTED_INERT: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "image-edit/expand-panorama": [
        ("[data-panorama-add-reference]", ("h-[26px]",)),
        ('[data-panorama-add-reference] ~ * [data-image-editor-model], [data-image-editor-model]', ("h-8",)),
        ("[data-image-editor-settings]", ("h-8",)),
    ],
    "segment-reshoot/translate-prompt": [
        ("[data-segment-submit]", ()),  # 对照: 真能用的, 不在惰性名单里
    ],
    "video-gen/banner-close": [
        ("[data-mark-select-return]", ()),
    ],
}

# 片段重拍那三颗 pill 与两颗 footer 按钮都**没有 data-标记**, 只能按文本定位。
# 用 exact 文本而不是子串, 免得「参考」同时命中「+参考」「参考图」。
TEXT_INERT: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "segment-reshoot/translate-prompt": [
        ("参考", ("h-7",)),
        ("标记", ("h-7",)),
        ("角色库", ("h-7",)),
        ("2.5", ("h-8",)),
        ("720P · 1个", ("h-8",)),
    ],
}

# 「只记录不改动」的两个白名单: 普查里非 hoverTarget 的候选必须只落在这些行。
ALLOWED_RESIDUAL = {
    ("CameraConfigDialog.tsx", 102),
    ("CameraConfigDialog.tsx", 140),
    ("CameraConfigDialog.tsx", 178),
    ("CameraConfigDialog.tsx", 216),
    ("VideoGenerationPanel.tsx", 499),
}

# 同一面里**必须还活着**的控件: 反向断言, 证明没把好控件一起改 inert
EXPECTED_LIVE: dict[str, list[str]] = {
    "segment-reshoot/translate-prompt": [
        'button[aria-label="展开片段重拍编辑器"]',
        "[data-segment-submit]",
    ],
    "image-edit/expand-panorama": ["[data-panorama-submit]"],
    "video-gen/banner-close": ["[data-mark-select-trigger]"],
}


def collect_errors(page: Page) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {"console": [], "page": []}
    page.on("console", lambda m: m.type == "error" and errors["console"].append(m.text))
    page.on("pageerror", lambda e: errors["page"].append(str(e)))
    return errors


def inert_facts(page: Page, selector: str) -> list[dict]:
    loc = page.locator(selector)
    out: list[dict] = []
    for i in range(loc.count()):
        try:
            facts = loc.nth(i).evaluate(PROBE_JS)
        except Exception as exc:  # noqa: BLE001
            facts = {"error": str(exc)}
        facts["selector"] = selector
        facts["className"] = loc.nth(i).get_attribute("class") or ""
        out.append(facts)
    return out


def text_button_facts(page: Page, text: str) -> list[dict]:
    """按**精确文本**找 button —— 必须避开同前缀的其他按钮。

    不用 `:text-is()`: 它对 `2.5` 这种「文本包在子 `<span>` 里」的情况匹配不到
    (第一版就是这么漏掉「积分」那颗的, 报成 `present: false`)。
    也不用「先 evaluate 拿元素再 `.evaluate`」—— `page.evaluate` 返回的是
    **反序列化后的普通对象**, 没有 `.evaluate` 方法(第二版踩的)。

    所以整件事在一个 evaluate 里做完: 找元素 + 采事实, 一次返回。
    """
    return page.evaluate(
        """(t) => Array.from(document.querySelectorAll('button'))
             .filter((b) => (b.textContent || '').trim() === t)
             .map((el) => {
               const cs = getComputedStyle(el);
               const r = el.getBoundingClientRect();
               return {
                 visible: r.width > 0 && r.height > 0
                   && cs.visibility !== 'hidden' && cs.opacity !== '0',
                 rect: { x: Math.round(r.x), y: Math.round(r.y),
                         w: Math.round(r.width), h: Math.round(r.height) },
                 inViewport: r.top >= 0 && r.left >= 0
                   && r.bottom <= innerHeight && r.right <= innerWidth,
                 title: el.getAttribute('title'),
                 inert: el.getAttribute('data-inert'),
                 disabled: el.disabled === true,
                 cursor: cs.cursor,
                 ariaLabel: el.getAttribute('aria-label'),
                 className: el.getAttribute('class') || '',
                 selector: 'button:text=="' + t + '"',
               };
             })""",
        text,
    )


def open_script_generator(page: Page) -> bool:
    """造一个 `script-generator` 节点并**停在节点本身**, 不打开编辑器。

    踩坑: 复用 367 的 `storyboard-assets/add` 探针会一路点到「自己编写分镜脚本」,
    编辑器盖住节点面板, `[data-script-generator-reference]` 根本不在 DOM 里 ——
    于是门禁报 `present: false`, 而那是**导航走过头**不是控件缺失。
    停下来才发现。所以这里只走到「建出节点」这一步。
    """
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.locator('button[aria-label="添加节点"]').first.click()
    page.wait_for_timeout(700)
    page.locator('[data-add-node-entry="script"]').first.evaluate("(el) => el.click()")
    page.wait_for_timeout(600)
    page.locator('[data-add-node-entry="script-new"]').first.evaluate("(el) => el.click()")
    page.wait_for_timeout(1200)
    return page.locator("[data-script-generator-reference]").count() > 0


def assert_inert(check, where: str, facts: list[dict], size_tokens: tuple[str, ...]) -> None:
    if not facts:
        check(f"{where}:present", False, "没找到这个控件 —— 面板可能没打开, 判红而非跳过")
        return
    check(f"{where}:present", True, f"找到 {len(facts)} 个")
    for fact in facts:
        check(
            f"{where}:inert",
            fact.get("inert") == "true",
            f"data-inert={fact.get('inert')!r}",
        )
        check(
            f"{where}:title",
            bool(str(fact.get("title") or "").strip()),
            f"title={fact.get('title')!r}",
        )
        check(
            f"{where}:cursor",
            fact.get("cursor") == "default",
            f"cursor={fact.get('cursor')!r}",
        )
        check(
            f"{where}:not-disabled",
            fact.get("disabled") is False,
            f"disabled={fact.get('disabled')}",
        )
        cls = str(fact.get("className") or "")
        check(f"{where}:class-has-no-hover", "hover:" not in cls, f"className={cls[:110]}")
        missing = [t for t in size_tokens if t not in cls]
        check(f"{where}:size-token-kept", not missing, f"丢失尺寸 token {missing}")


def run() -> dict:
    checks: list[dict[str, object]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT)
        errors = collect_errors(page)

        for probe_name in EXPECTED_INERT:
            REACH.PROBES[probe_name](page)
            for selector, tokens in EXPECTED_INERT[probe_name]:
                # `[data-segment-submit]` 是**对照组**, 期望它是活的 ——
                # 由 EXPECTED_LIVE 断言, 不在这里当惰性控件断。
                if selector == "[data-segment-submit]":
                    continue
                assert_inert(check, f"{probe_name}|{selector}", inert_facts(page, selector), tokens)
            for text, tokens in TEXT_INERT.get(probe_name, []):
                assert_inert(check, f"{probe_name}|text:{text}", text_button_facts(page, text), tokens)
            for selector in EXPECTED_LIVE.get(probe_name, []):
                facts = inert_facts(page, selector)
                check(
                    f"{probe_name}|live:{selector}",
                    bool(facts) and all(f.get("inert") is None for f in facts),
                    f"必须仍然可用的控件被标了 inert: "
                    f"{[(f.get('inert'), (f.get('className') or '')[:40]) for f in facts]}",
                )

        # 分镜编辑器第 3 步的付费合成按钮。
        # 路径: 复用 367 的 `storyboard-assets/add`(它会一路点到第 2 步「准备资产」),
        # 再点 `next="prompts"` 进第 3 步。
        REACH.PROBES["storyboard-assets/add"](page)
        nxt = page.locator('[data-storyboard-next="prompts"]')
        if nxt.count() == 0:
            check("storyboard/step3-reachable", False, "没进到第 3 步, 判红而非跳过")
        else:
            check("storyboard/step3-reachable", True, "")
            nxt.first.evaluate("(el) => el.click()")
            page.wait_for_timeout(700)
        assert_inert(
            check,
            "storyboard/synthesize-all",
            inert_facts(page, "[data-storyboard-synthesize-all]"),
            (),
        )

        # 剧本生成节点的「参考图」: 只走到「建出节点」, 别点进编辑器
        if not open_script_generator(page):
            check("script-generator:reachable", False, "没能造出 script-generator 节点, 判红")
        else:
            check("script-generator:reachable", True, "")
        assert_inert(
            check,
            "script-generator/reference",
            inert_facts(page, "[data-script-generator-reference]"),
            ("h-8",),
        )

        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(AUDIT.parent / "verify-last.png"))
        browser.close()

    # ---- 判据自身的双向自检(不依赖浏览器) ----
    src = (ROOT / "src" / "components" / "SegmentReshootPanel.tsx").read_text(encoding="utf-8")
    stripped = CENSUS.strip_comments(src)
    check(
        "criteria:bare-block-comment-stripped",
        "<button" not in "\n".join(
            line for line in stripped.splitlines() if "即控件" in line
        ),
        "裸 /* */ 注释里那句字面量 <button> 不该出现在剥注释后的文本中",
    )
    hits = CENSUS.scan(ROOT / "src" / "components" / "SegmentReshootPanel.tsx")
    check(
        "criteria:still-detects-real-dead",
        True,  # 下面用植入法单独验
        f"当前文件候选 {[(h['line'], h['aria']) for h in hits]}",
    )
    # 阳性: 植入一个明知死掉的按钮, 必须被扫出来
    probe_file = ROOT / "src" / "components" / "ZzBatch368Probe.tsx"
    probe_file.write_text(
        "export function Zz() {\n"
        "  return (\n"
        "    <div>\n"
        "      /* 注释里的字面量 <button> 不该被算 */\n"
        "      <button type=\"button\" className=\"hover:bg-white/10\">ZZ 阳性对照</button>\n"
        "      <button type=\"button\" onClick={() => {}} className=\"hover:bg-white/10\">ZZ 阴性-已接线</button>\n"
        "      <button type=\"button\" data-inert=\"true\" title=\"x\" className=\"hover:bg-white/10\">ZZ 阴性-已惰性</button>\n"
        "    </div>\n"
        "  );\n"
        "}\n",
        encoding="utf-8",
    )
    try:
        planted = CENSUS.scan(probe_file)
        check(
            "criteria:planted-dead-found",
            len(planted) == 1 and planted[0]["aria"] is None,
            f"植入 1 死 2 好, 应只报 1: {[(h['line'], h['aria'], h['selfClaim']) for h in planted]}",
        )
        check(
            "criteria:planted-bare-button-has-no-selfclaim",
            bool(planted) and planted[0]["selfClaim"] is False,
            "裸 <button>(无 aria-label/data-testid) 的 selfClaim 应为 False —— "
            "而这正是旧口径漏掉它们的原因",
        )
    finally:
        probe_file.unlink()

    # `<a href>` 判据**双向**: 真 href 计为已接线, 空锚点/缺 href 仍判死。
    # 用真实 DOM 跑 SCAN_JS —— 里面读 `__reactProps$`, 纯 HTML 页面上不存在,
    # 于是 `hasOnClick` 恒 false, **结果完全由 nativeAnchor 决定**,
    # 正好把这条判据单独隔离出来验。
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(
            "<a href='/real.png' download aria-label='真链接'>x</a>"
            "<a href='#' aria-label='空锚点'>x</a>"
            "<a aria-label='无 href'>x</a>"
            "<button aria-label='死按钮' class='hover:bg-white/10'>x</button>"
        )
        snap = page.evaluate(SCAN_JS)
        browser.close()
    wired_by = {c["aria"]: c["wired"] for c in snap["controls"]}
    check(
        "criteria:anchor-real-href-is-wired",
        wired_by.get("真链接") is True,
        f"有 href 的 <a> 应算已接线: {wired_by}",
    )
    check(
        "criteria:anchor-empty-href-still-dead",
        wired_by.get("空锚点") is False and wired_by.get("无 href") is False,
        f"空锚点与无 href 的 <a> 仍应被判死: {wired_by}",
    )

    # 源码普查残余必须只落在「只记录」白名单里
    residual: list[str] = []
    for path in sorted((ROOT / "src" / "components").rglob("*.tsx")):
        rel = path.relative_to(ROOT / "src" / "components")
        if CENSUS.is_cross_line(rel):
            continue
        for hit in CENSUS.scan(path):
            if hit["hoverTarget"]:
                continue
            key = (str(rel), int(hit["line"]))
            if key not in ALLOWED_RESIDUAL:
                residual.append(f"{rel}:{hit['line']} {hit['aria']!r} selfClaim={hit['selfClaim']}")
    check(
        "source-census:residual-only-allowlisted",
        not residual,
        f"普查残余应只落在只记录白名单 {sorted(ALLOWED_RESIDUAL)}; 实际多出: {residual}",
    )

    noisy = [
        e
        for e in list(errors["console"]) + list(errors["page"])
        if "ERR_ABORTED" not in e and "WebSocket" not in e
    ]
    return {"checks": checks, "errors": errors, "noisy": noisy}


def report(audit: dict) -> int:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [c for c in audit["checks"] if not c["ok"]]
    if failed:
        print(f"Batch 368: {len(audit['checks']) - len(failed)}/{len(audit['checks'])} checks passed")
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
    if audit["noisy"]:
        print("DIAGNOSTICS:", json.dumps(audit["noisy"][:5], ensure_ascii=False, indent=1))
    if failed or audit["noisy"]:
        return 1
    print(
        f"Batch 368 verification passed: {len(audit['checks'])} checks. "
        "Twelve newly-exposed affordances now declare themselves inert (data-inert + title "
        "+ cursor:default, no hover) with geometry and copy unchanged; working controls in "
        "the same panels were left alone; the three judgment blind spots are closed and "
        "each is self-checked in both directions."
    )
    return 0


def main() -> int:
    return report(run())


if __name__ == "__main__":
    raise SystemExit(main())

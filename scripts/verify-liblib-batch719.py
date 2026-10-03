#!/usr/bin/env python3
"""batch 719 验收：场景描述 prompt 的语义与反馈 —— 纯本地回显，store 零变化

## 起点

715/716/717 连着三批都指向同一件事：**底部条里被推出框外的，恰好是
「描述想搭建的场景」这个 prompt 输入框和它的发送按钮** ——
视口里最核心的输入，却是最难够到的控件。

那个控件（`DirectorScenePromptBar.tsx`）**从来没有被测过**。
本批补上：可达性、提交语义、反馈、修饰键、空值守卫、附件、以及 `aria-live`。

## 决定性读数

| 读数 | 值 |
|---|---|
| 打字 / 提交 / 上传 / 带附件提交 / 2 秒后，`objects` | **5 → 5** |
| `history.past` / `history.future` | **0 条 / 0 条**（始终） |
| `lastCommandResult` / `selection` | **null / null**（始终） |
| 提交反馈 | status `opacity` **0 → 1**，**2.2 秒后回 0** |
| 提交后输入内容 | **不清空**（草稿一直在） |
| 提交期间输入框 | `opacity: 0`（**已输入的文本隐身 2 秒**） |
| Enter / Shift+Enter / Control+Enter / Meta+Enter | **四种全部提交**（status 0→1） |
| 空值 | 发送按钮 **`disabled = true`**；Enter **无任何反馈** |
| 纯空格 `'   '` | 同样 **`disabled = true`**、Enter 无反馈 ⟹ `trim()` 同时管住两者 |
| 上传附件后 status 文本 | **「已附上本地图片：X」** |
| 带附件提交时的 status 文本 | **仍是附件那句**（提交确认被顶掉） |
| `aria-live="polite"` 区域的文本 | 打字前 / 提交后 / 2 秒后 **恒为同一串**，只有 opacity 变 |
| 1280 下 prompt 的命中测试 | 滚之前 **`other`（被 inspector 盖住）**，滚之后 `self` |

## 五条预测（写死在代码里，先于任何测量）

- **P1** 提交是纯本地回显，**store 零变化**
- **P2** 反馈是 2000ms 的视觉替换，草稿不清空
- **P3** 四种 Enter 组合全部提交（无修饰键判断）
- **P4** `trim()` 同时管住 `disabled` 与早退，**纯空格等同空值**
- **P5** 附件名顶掉提交确认；`aria-live` 区域**内容不变、只有 class 变**

## 判据

1. `submitting-changes-nothing-in-the-store`
2. `the-confirmation-is-a-2000ms-visual-swap-and-the-draft-survives`
3. `all-four-enter-combinations-submit`
4. `trim-governs-both-the-disabled-state-and-the-early-return`
5. `the-attachment-name-hides-the-submit-confirmation`
6. `the-live-region-text-never-changes-only-opacity-does`
7. `reaching-the-prompt-takes-a-scroll-then-a-click`
"""
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch719-2026-10-01"
W, H = 1280, 1150
IMG = Path("/tmp/dbg719-verify-attachment.png")
IMG.write_bytes(bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"))

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

PREDICTIONS = {
    "P1": "提交是纯本地回显，store 零变化",
    "P2": "反馈是 2000ms 的视觉替换，草稿不清空",
    "P3": "四种 Enter 组合全部提交（无修饰键判断）",
    "P4": "trim() 同时管住 disabled 与早退，纯空格等同空值",
    "P5": "附件名顶掉提交确认；aria-live 区域内容不变、只有 class 变",
}

READ = r"""() => {
  const s = window.__director_store.getState();
  const q = (sel) => document.querySelector(sel);
  const bar = q('[data-director-bottom-bar]');
  const inner = bar ? bar.querySelector(':scope > div') : null;
  const inp = q('[data-director-scene-prompt-input]');
  const sub = q('[data-director-scene-prompt-submit]');
  const st = q('[data-director-scene-prompt-status]');
  const hit = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    if (cx < 0 || cx > innerWidth || cy < 0 || cy > innerHeight) return 'offscreen';
    const h = document.elementFromPoint(cx, cy);
    return h ? (h === el || el.contains(h) ? 'self' : 'other') : 'none';
  };
  return {
    vw: innerWidth,
    barScrollLeft: inner ? inner.scrollLeft : null,
    barMax: inner ? inner.scrollWidth - inner.clientWidth : null,
    store: {
      objects: s.objects ? s.objects.length : null,
      pastLen: s.history && s.history.past ? s.history.past.length : null,
      futureLen: s.history && s.history.future ? s.history.future.length : null,
      lastCommandResult: s.lastCommandResult === undefined ? 'ABSENT'
        : (s.lastCommandResult === null ? null : 'SET'),
      selected: s.selection ? JSON.stringify(s.selection) : null,
    },
    input: inp ? { value: inp.value, focused: document.activeElement === inp,
                   opacity: getComputedStyle(inp).opacity,
                   hit: hit(inp), w: Math.round(inp.getBoundingClientRect().width),
                   h: Math.round(inp.getBoundingClientRect().height) } : null,
    submit: sub ? { disabled: sub.disabled, hit: hit(sub) } : null,
    status: st ? { text: (st.textContent || '').trim(),
                   opacity: getComputedStyle(st).opacity,
                   ariaLive: st.getAttribute('aria-live'), hit: hit(st) } : null,
  };
}"""

def read(page: Page) -> Any:
    return page.evaluate(READ)


def open_desk(browser: Any) -> Page:
    page = browser.new_page(viewport={"width": W, "height": H},
                            device_scale_factor=1)
    b617.open_desk(page)
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(500)
    return page


def reach(page: Page) -> dict[str, Any]:
    """滚到底部条最右 → 真实点击 prompt → 断言焦点到手。到不了就报错。"""
    before = read(page)
    bar = page.evaluate(r"""() => {
      const b = document.querySelector('[data-director-bottom-bar]');
      const k = b.querySelector(':scope > div').getBoundingClientRect();
      return {x: Math.round(k.x), y: Math.round(k.y),
              w: Math.round(k.width), h: Math.round(k.height)};
    }""")
    page.mouse.move(bar["x"] + bar["w"] / 2, bar["y"] + bar["h"] / 2)
    page.wait_for_timeout(160)
    page.mouse.wheel(2000, 0)
    page.wait_for_timeout(600)
    mid = read(page)
    geo = page.evaluate(r"""() => {
      const el = document.querySelector('[data-director-scene-prompt-input]');
      const b = el.getBoundingClientRect();
      return {x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width)};
    }""")
    page.mouse.click(geo["x"] + geo["w"] / 2, geo["y"] + 8)
    page.wait_for_timeout(300)
    after = read(page)
    assert after["input"]["focused"], "真实点击后焦点没到手，本批所有读数作废"
    return {"beforeHit": before["input"]["hit"], "beforeScroll": before["barScrollLeft"],
            "afterHit": mid["input"]["hit"], "afterScroll": mid["barScrollLeft"],
            "barMax": mid["barMax"], "focused": after["input"]["focused"],
            "inputBox": [after["input"]["w"], after["input"]["h"]],
            "submitHitBefore": before["submit"]["hit"]}


def run(browser: Any) -> dict[str, Any]:
    # --- 主线：可达 → 打字 → 提交 → 2 秒后 ---
    page = open_desk(browser)
    reach_info = reach(page)
    base = read(page)
    page.keyboard.type("一个雨夜的街道")
    page.wait_for_timeout(250)
    typed = read(page)
    page.keyboard.press("Enter")
    page.wait_for_timeout(350)
    submitted = read(page)
    page.wait_for_timeout(2200)
    after2s = read(page)

    combos: dict[str, Any] = {}
    for name, mods in (("Enter", []), ("Shift+Enter", ["Shift"]),
                       ("Control+Enter", ["Control"]), ("Meta+Enter", ["Meta"])):
        page.evaluate("() => { const i = document.querySelector"
                      "('[data-director-scene-prompt-input]');"
                      "i.focus(); i.select(); }")
        page.wait_for_timeout(120)
        page.keyboard.type("测试 " + name)
        page.wait_for_timeout(200)
        before_op = read(page)["status"]["opacity"]
        for m in mods:
            page.keyboard.down(m)
        page.keyboard.press("Enter")
        for m in mods:
            page.keyboard.up(m)
        page.wait_for_timeout(350)
        g = read(page)
        combos[name] = {"statusBefore": before_op, "statusAfter": g["status"]["opacity"],
                        "inputOpacity": g["input"]["opacity"], "value": g["input"]["value"]}
        page.wait_for_timeout(2100)

    # 真实键盘清空 → 空值守卫
    page.keyboard.press("Meta+a")
    page.wait_for_timeout(150)
    page.keyboard.press("Backspace")
    page.wait_for_timeout(450)
    cleared = read(page)
    assert cleared["input"]["value"] == "", "真实键盘清空没生效"
    assert cleared["submit"]["disabled"] is True, ("空值时发送按钮应 disabled", cleared)
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)
    empty_enter = read(page)
    # 纯空格
    page.keyboard.type("   ")
    page.wait_for_timeout(350)
    ws = read(page)
    page.keyboard.press("Enter")
    page.wait_for_timeout(400)
    ws_enter = read(page)
    page.close()

    # --- 附件：干净页 ---
    page2 = open_desk(browser)
    reach(page2)
    page2.set_input_files("[data-director-scene-prompt-file]", str(IMG))
    page2.wait_for_timeout(450)
    uploaded = read(page2)
    page2.keyboard.type("配这张图")
    page2.wait_for_timeout(200)
    page2.keyboard.press("Enter")
    page2.wait_for_timeout(400)
    uploaded_submit = read(page2)
    page2.wait_for_timeout(2200)
    uploaded_2s = read(page2)
    page2.close()

    return {"reach": reach_info, "base": base, "typed": typed,
            "submitted": submitted, "after2s": after2s, "combos": combos,
            "cleared": cleared, "emptyEnter": empty_enter,
            "whitespace": {"before": ws, "afterEnter": ws_enter},
            "uploaded": uploaded, "uploadedSubmit": uploaded_submit,
            "uploaded2s": uploaded_2s}


def check_1(r: dict[str, Any]) -> None:
    """提交是纯本地回显：store 逐字段零变化。"""
    for key in ("base", "typed", "submitted", "after2s",
                "uploaded", "uploadedSubmit"):
        st = r[key]["store"]
        assert st["objects"] == 5, (key, st)
        assert st["pastLen"] == 0, (key, st)
        assert st["futureLen"] == 0, (key, st)
        assert st["lastCommandResult"] is None, (key, st)
        assert st["selected"] is None, (key, st)


def check_2(r: dict[str, Any]) -> None:
    """反馈是 2000ms 的视觉替换，草稿不清空，提交期间文本隐身。"""
    assert r["typed"]["status"]["opacity"] == "0", r["typed"]["status"]
    assert r["submitted"]["status"]["opacity"] == "1", r["submitted"]["status"]
    assert r["submitted"]["input"]["opacity"] == "0", r["submitted"]["input"]
    assert r["submitted"]["input"]["value"] == "一个雨夜的街道", r["submitted"]["input"]
    assert r["after2s"]["status"]["opacity"] == "0", r["after2s"]["status"]
    assert r["after2s"]["input"]["opacity"] == "1", r["after2s"]["input"]
    assert r["after2s"]["input"]["value"] == "一个雨夜的街道", r["after2s"]["input"]
    assert r["typed"]["submit"]["disabled"] is False, r["typed"]["submit"]


def check_3(r: dict[str, Any]) -> None:
    """四种 Enter 组合全部提交 —— onKeyDown 只判 key，不看修饰键。"""
    assert set(r["combos"]) == {"Enter", "Shift+Enter",
                                "Control+Enter", "Meta+Enter"}, sorted(r["combos"])
    for name, v in r["combos"].items():
        assert v["statusBefore"] == "0", (name, v)
        assert v["statusAfter"] == "1", (name, v)
        assert v["inputOpacity"] == "0", (name, v)
        assert v["value"] == "测试 " + name, (name, v)


def check_4(r: dict[str, Any]) -> None:
    """trim() 同时管住 disabled 与早退；纯空格等同空值。"""
    c = r["cleared"]
    assert c["input"]["value"] == "" and c["submit"]["disabled"] is True, c
    assert r["emptyEnter"]["status"]["opacity"] == "0", r["emptyEnter"]
    assert r["emptyEnter"]["submit"]["disabled"] is True, r["emptyEnter"]
    ws = r["whitespace"]["before"]
    assert ws["input"]["value"] == "   ", ws
    assert ws["submit"]["disabled"] is True, ws
    assert r["whitespace"]["afterEnter"]["status"]["opacity"] == "0", \
        r["whitespace"]["afterEnter"]


def check_5(r: dict[str, Any]) -> None:
    """附件名顶掉了提交确认。"""
    up = r["uploaded"]["status"]
    assert up["text"].startswith("已附上本地图片："), up
    assert IMG.name in up["text"], up
    sub = r["uploadedSubmit"]
    assert sub["status"]["opacity"] == "1", sub["status"]
    assert sub["status"]["text"] == up["text"], (sub["status"], up)
    assert "场景描述已记录" not in sub["status"]["text"], sub["status"]
    # 附件状态在 2 秒后仍在（只是不可见）
    assert r["uploaded2s"]["status"]["opacity"] == "0", r["uploaded2s"]["status"]
    assert r["uploaded2s"]["status"]["text"] == up["text"], r["uploaded2s"]["status"]


def check_6(r: dict[str, Any]) -> None:
    """aria-live 区域的内容恒定：变的是 class，不是文本。"""
    texts = {r["typed"]["status"]["text"], r["submitted"]["status"]["text"],
             r["after2s"]["status"]["text"]}
    assert texts == {"场景描述已记录（本地草稿）"}, texts
    assert r["submitted"]["status"]["ariaLive"] == "polite", r["submitted"]["status"]
    assert r["typed"]["status"]["opacity"] == "0"
    assert r["submitted"]["status"]["opacity"] == "1"


def check_7(r: dict[str, Any]) -> None:
    """默认可达性：滚之前被别的元素盖住，滚一下 + 点一下才用得到。"""
    rc = r["reach"]
    assert rc["beforeHit"] == "other", rc
    assert rc["beforeScroll"] == 0, rc
    assert rc["afterScroll"] == rc["barMax"] and rc["barMax"] > 0, rc
    assert rc["afterHit"] == "self", rc
    assert rc["focused"] is True, rc
    assert rc["submitHitBefore"] == "other", rc
    assert rc["inputBox"] == [143, 16], rc


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
        ("submitting-changes-nothing-in-the-store", lambda: check_1(got.get("run", {}))),
        ("the-confirmation-is-a-2000ms-visual-swap-and-the-draft-survives", lambda: check_2(got.get("run", {}))),
        ("all-four-enter-combinations-submit", lambda: check_3(got.get("run", {}))),
        ("trim-governs-both-the-disabled-state-and-the-early-return", lambda: check_4(got.get("run", {}))),
        ("the-attachment-name-hides-the-submit-confirmation", lambda: check_5(got.get("run", {}))),
        ("the-live-region-text-never-changes-only-opacity-does", lambda: check_6(got.get("run", {}))),
        ("reaching-the-prompt-takes-a-scroll-then-a-click", lambda: check_7(got.get("run", {}))),
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

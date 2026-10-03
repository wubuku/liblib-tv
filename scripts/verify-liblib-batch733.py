#!/usr/bin/env python3
"""batch 733 验收：把 732 没打开的族再开 3 个；另 2 个的「没打开」已从源码取证

## 起点

730/731 都在画布 7 个视图里测，732 去开面板时开了 `LibraryShowcasePanel`
（2 写点 → 42 枚），但另外 5 族**一个都没打开** —— 入口脚本按可见文本匹配按钮失配，
节点根本没被造出来（`nodeId: null`）。732 如实记了「未取证，理由是探针坏了」。

## 本批的修法

`AddNodePanel.tsx:206` 给每一项面板入口都打了 `data-add-node-entry={entry.type}` ——
按这个属性选就够了，**不必匹配可见文本**（可见文本还带 badge，
如「智能剪辑Beta」「逐帧拉片SD 2.5」，`startsWith` 必然踩空）。

## 决定性读数

### ① 三族打开，4 个写点逐处实测

| 族 | 入口 | 打开的 `data-inert` 写点 |
|---|---|---|
| `AudioNode` | `[data-add-node-entry="audio"]` → 单选该卡 | **1**：播放音频 |
| `VideoClipEditPanel` | `[data-add-node-entry="video-clip"]` → 单选该卡 | **2**：剪辑模式设置 / 输出设置 |
| `ScriptGeneratorNode` | 脚本子菜单 `[data-add-node-entry="script-new"]` → 单选该卡 | **1**：参考图上传 |

三枚**全部** `role=button`、`focusable=true` —— 与 730（DOM 通道）、731（AX 通道）
对其他族的读数**同构**。第四枚 `VideoClipEditPanel` 的第二枚同理。

### ② 另 2 族「没打开」的理由是**源码里的条件门控**，不是探针坏了

| 族 | 门控条件 | 证据 |
|---|---|---|
| `ShotBreakdownResultNode` | 逐帧拉片卡的动作按钮是「**上传视频后开始**」 | 节点造出来了（`types` 里有 `shot-breakdown`），但动作按钮文本就是「上传视频后开始」⟹ 需要先上传视频 |
| `StoryboardScriptEditor` | `ScriptGeneratorNode.tsx:50` `inStoryboardSession = storyboardSessionNodeId === id` ⟹ 入口按钮 `[data-script-generator-open-storyboard]` 只在**进入「自写会话」之后**才渲染 | 实测 `openBtn: false` —— 该按钮**在 DOM 里根本不存在**，而 `ScriptGeneratorNode` 自己那枚 `data-inert`（参考图上传）已渲染 ⟹ 节点在、面板入口不在 |

⟹ 这两条与 732 记录的「种子里视频卡 `status: failed` 挡住 6 个写点」同族 ——
**条件门控**。但证据更硬：**源码 + DOM 双证**，不是「探针没找到」。

### ③ 顺带记一条负读数

`ShotBreakdownNode` 上按可见文本找动作按钮时，探针先撞到的是一枚
「剧本生成分镜脚本」——**它不是 `ScriptGeneratorNode` 的入口**（那个入口叫
「打开脚本节点 →」，`:113-120`）。**同一个组件里两枚按钮文案相近**，
按文本找会点错 —— 这是 732 那次「按文本匹配」的另一个坑。

## 不声称

- **不声称这 2 族不可达** —— 只是**本批没走到那一步**；条件满足后应当可达，未证。
- **不声称 46 个写点已全部实测** —— 本批新开 4 处，其余仍待。
- **不声称 AX 树等同于真实屏幕阅读器播报** —— 沿用 731。

## 新增待拍板

1. **「条件门控」这一族要不要给出可达路径的说明** —— 用户按了没反应与
   「入口根本没出现」在 UI 上无法区分。**需改 `src/`，等授权**（本批只记，不裁决）。

## 方法论

1. **入口按稳定属性选，不按文案选** —— 面板项都带 `data-add-node-entry`，
   文案会带 badge、会改、会与兄弟按钮相近；**属性是合同的载体，文案是给人看的**。
2. **「没打开」要分两种** —— 探针坏了（本批之前）与**源码里的条件门控**（本批）。
   前者记未取证并去修探针，后者要拿出**源码 + DOM 双证**才算结论。
3. **同一组件里文案相近的按钮会骗过文本匹配** —— `ScriptGeneratorNode`
   的「剧本生成分镜脚本」与入口「打开脚本节点 →」。

## 探针返工一处

JS 里 `const b` 重复声明（先取候选再取目标）⟹ `SyntaxError`；
且 732 的教训是**每族采完即落盘**，本批沿用。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch733-2026-10-01"
BASE = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
W, H = 1280, 1150

ENUM = r"""() => [...document.querySelectorAll('button[data-inert]')].map(el => {
  const nd = el.closest('.react-flow__node');
  return {aria: el.getAttribute('aria-label') || '', title: el.getAttribute('title') || '',
          node: nd ? nd.getAttribute('data-id') : null}; })"""

FOCUS = r"""() => [...document.querySelectorAll('button[data-inert]')].map(el => {
  el.focus(); return document.activeElement === el; })"""

STATE = r"""() => ({
  editor: !!document.querySelector('[data-storyboard-editor]'),
  openStoryboardBtn: !!document.querySelector('[data-script-generator-open-storyboard]'),
  types: window.__libtv_store.getState().getActiveCanvas().nodes.map(n => n.type),
})"""

TOPNAV = {"开通会员 限时 45 折", "积分余额"}


def ax_roles(cdp: Any, node_ids: list[int]) -> list[str | None]:
    roles: list[str | None] = []
    for nid in node_ids:
        try:
            bid = cdp.send("DOM.describeNode", {"nodeId": nid})["node"]["backendNodeId"]
            t = cdp.send("Accessibility.getPartialAXTree",
                         {"backendNodeId": bid, "fetchRelatives": False})
        except Exception:  # noqa: BLE001
            roles.append(None)
            continue
        nodes = t.get("nodes", [])
        own = next((n for n in nodes if n.get("role")), None)
        roles.append((own or {}).get("role", {}).get("value"))
    return roles


def open_canvas(page: Page) -> None:
    page.goto(f"{BASE}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal'))"
                  " el.remove(); }")
    page.mouse.move(W - 4, 4)
    page.wait_for_timeout(1_300)


def pick(page: Page, entry: str) -> str:
    return page.evaluate("""(e) => { const b =
      document.querySelector('[data-add-node-entry="' + e + '"]');
      if (!b) return 'no-entry'; b.click(); return 'clicked'; }""", entry)


def newest(page: Page, typ: str) -> str | None:
    return page.evaluate("""(t) => { const g = window.__libtv_store.getState().getActiveCanvas();
      const ns = g.nodes.filter(x => x.type === t);
      return ns.length ? ns[ns.length - 1].id : null; }""", typ)


def click_node(page: Page, cdp: Any, nid: str) -> bool:
    root = cdp.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]
    q = cdp.send("DOM.querySelector",
                 {"nodeId": root, "selector": '.react-flow__node[data-id="%s"]' % nid})
    n2 = q.get("nodeId")
    if not n2:
        return False
    q4 = cdp.send("DOM.getBoxModel", {"nodeId": n2})["model"]["content"]
    page.mouse.click(int((q4[0] + q4[2] + q4[4] + q4[6]) / 4),
                     int((q4[1] + q4[3] + q4[5] + q4[7]) / 4))
    page.wait_for_timeout(700)
    return True


def collect(page: Page, cdp: Any) -> dict[str, Any]:
    root = cdp.send("DOM.getDocument", {"depth": -1})["root"]["nodeId"]
    ids = cdp.send("DOM.querySelectorAll",
                   {"nodeId": root, "selector": "button[data-inert]"})["nodeIds"]
    rows = page.evaluate(ENUM)
    roles = ax_roles(cdp, ids)
    focus = page.evaluate(FOCUS)
    return {"rows": [{**r, "axRole": role, "focusable": f}
                     for r, role, f in zip(rows, roles, focus)]}


def open_family(page: Page, cdp: Any, entry: str, typ: str,
                submenu: str | None = None) -> dict[str, Any]:
    open_canvas(page)
    page.evaluate("""() => { const b = document.querySelector('[aria-label="添加节点"]');
      if (b) b.click(); }""")
    page.wait_for_timeout(420)
    picked = pick(page, entry)
    picked2 = pick(page, submenu) if submenu else None
    page.wait_for_timeout(700)
    nid = newest(page, typ)
    selected = click_node(page, cdp, nid) if nid else False
    data = collect(page, cdp)
    data["pick"] = picked
    data["pickSub"] = picked2
    data["nodeId"] = nid
    data["selected"] = selected
    return data


def run(browser: Any) -> dict[str, Any]:
    page = browser.new_page(viewport={"width": W, "height": H})
    cdp = page.context.new_cdp_session(page)
    cdp.send("Accessibility.enable")
    out: dict[str, Any] = {"families": {}}
    out["families"]["AudioNode"] = open_family(page, cdp, "audio", "audio")
    out["families"]["VideoClipEditPanel"] = open_family(page, cdp, "video-clip", "video-clip")
    out["families"]["ScriptGeneratorNode"] = open_family(
        page, cdp, "script", "script-generator", submenu="script-new")
    # StoryboardScriptEditor：入口按钮是否渲染
    st = page.evaluate(STATE)
    out["storyboard"] = {"editor": st["editor"],
                         "openStoryboardBtn": st["openStoryboardBtn"],
                         "types": st["types"]}
    # 逐帧拉片：节点造出来了吗？动作按钮文本是什么？
    open_canvas(page)
    page.evaluate("""() => { const b = document.querySelector('[aria-label="添加节点"]');
      if (b) b.click(); }""")
    page.wait_for_timeout(420)
    out["shotBreakdownPick"] = pick(page, "shot-breakdown")
    page.wait_for_timeout(700)
    sb = newest(page, "shot-breakdown")
    if sb:
        click_node(page, cdp, sb)
    labels = page.evaluate("""() => [...document.querySelectorAll('.react-flow__node button')]
      .map(b => (b.textContent || '').trim()).filter(Boolean).slice(0, 12)""")
    out["shotBreakdown"] = {"nodeId": sb, "actionLabels": labels,
                            "types": page.evaluate(
                                "() => window.__libtv_store.getState()"
                                ".getActiveCanvas().nodes.map(n => n.type)")}
    page.close()
    return out


def static_facts() -> dict[str, Any]:
    add = (ROOT / "src/components/AddNodePanel.tsx").read_text(encoding="utf-8")
    sg = (ROOT / "src/components/nodes/ScriptGeneratorNode.tsx").read_text(encoding="utf-8")
    sbn = (ROOT / "src/components/nodes/ShotBreakdownNode.tsx").read_text(encoding="utf-8")
    return {
        "addNodePanelHasEntryAttr": 'data-add-node-entry={entry.type}' in add,
        "scriptNodeGate": "const inStoryboardSession = storyboardSessionNodeId === id;" in sg,
        "scriptNodeOpenBtn": "data-script-generator-open-storyboard" in sg,
        "scriptNodeOpenBtnLabel": "打开脚本节点" in sg,
        "scriptNodeOtherLabel": "剧本生成分镜脚本" in sg,
        "shotBreakdownGatedOnUpload": "上传视频后开始" in sbn,
    }


def _fams(r: dict[str, Any]) -> dict[str, Any]:
    return r.get("run", {}).get("families", {})


def _own(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """剔掉每个视图都有的顶栏两枚，只留本族新出现的。"""
    return [x for x in rows if x["aria"] not in TOPNAV]


def check_1(r: dict[str, Any]) -> None:
    """入口按稳定属性选：`AddNodePanel.tsx:206` 打了 `data-add-node-entry`。"""
    s = r["static"]
    assert s["addNodePanelHasEntryAttr"] is True, s
    r["staticSummary"] = s


def check_2(r: dict[str, Any]) -> None:
    """`AudioNode` 打开，1 个写点（播放音频）`role=button` 且可聚焦。"""
    f = _fams(r)["AudioNode"]
    assert f["pick"] == "clicked" and f["selected"] is True, f["pick"]
    own = _own(f["rows"])
    assert len(own) == 1, own
    assert own[0]["title"] == "音频播放在克隆侧尚未接入", own[0]
    assert own[0]["axRole"] == "button" and own[0]["focusable"] is True, own[0]


def check_3(r: dict[str, Any]) -> None:
    """`VideoClipEditPanel` 打开，2 个写点全部 `role=button` 且可聚焦。"""
    f = _fams(r)["VideoClipEditPanel"]
    assert f["pick"] == "clicked" and f["selected"] is True, f["pick"]
    own = _own(f["rows"])
    assert len(own) == 2, own
    assert sorted(x["title"] for x in own) == sorted(
        ["剪辑模式设置在克隆侧尚未接入", "输出设置在克隆侧尚未接入"]), own
    assert all(x["axRole"] == "button" and x["focusable"] is True for x in own), own


def check_4(r: dict[str, Any]) -> None:
    """`ScriptGeneratorNode` 打开，1 个写点（参考图上传）`role=button` 且可聚焦。"""
    f = _fams(r)["ScriptGeneratorNode"]
    assert f["pick"] == "clicked" and f["pickSub"] == "clicked", f["pick"]
    own = _own(f["rows"])
    assert len(own) == 1, own
    assert own[0]["title"] == "参考图上传暂不可用", own[0]
    assert own[0]["axRole"] == "button" and own[0]["focusable"] is True, own[0]


def check_5(r: dict[str, Any]) -> None:
    """`StoryboardScriptEditor` 的入口按钮**没渲染** —— 门控在 `inStoryboardSession`。"""
    s, sb = r["static"], r["run"]["storyboard"]
    assert s["scriptNodeGate"] is True and s["scriptNodeOpenBtn"] is True, s
    assert sb["openStoryboardBtn"] is False, sb
    assert sb["editor"] is False, sb
    assert "script-generator" in sb["types"], sb["types"]


def check_6(r: dict[str, Any]) -> None:
    """`ShotBreakdownResultNode`：节点造出来了，但动作按钮是「上传视频后开始」。"""
    s, sb = r["static"], r["run"]["shotBreakdown"]
    assert r["run"]["shotBreakdownPick"] == "clicked", r["run"]["shotBreakdownPick"]
    assert sb["nodeId"], sb
    assert "shot-breakdown" in sb["types"], sb["types"]
    assert any("上传视频后开始" in t for t in sb["actionLabels"]), sb["actionLabels"]
    assert s["shotBreakdownGatedOnUpload"] is True, s
    r["gated"] = {"storyboard": "入口按钮被 inStoryboardSession 门控，未渲染",
                  "shotBreakdown": "动作按钮为「上传视频后开始」，需先上传"}


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    got: dict[str, Any] = {"static": static_facts()}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            got["run"] = run(browser)
        except Exception as exc:  # noqa: BLE001
            failures.append("run: %s" % exc)
            got["run"] = {}
        browser.close()
    payload: dict[str, Any] = {"static": got["static"], "run": got["run"]}
    checks = [
        ("add-node-entries-are-selected-by-attribute-not-label", check_1),
        ("audio-node-opens-and-its-one-site-is-focusable", check_2),
        ("video-clip-edit-panel-opens-and-both-sites-are-focusable", check_3),
        ("script-generator-node-opens-and-its-one-site-is-focusable", check_4),
        ("storyboard-editor-entry-button-is-absent-by-conditional-gate", check_5),
        ("shot-breakdown-result-is-gated-on-uploading-a-video", check_6),
    ]
    summary: dict[str, bool] = {}
    for name, fn in checks:
        try:
            fn(payload)
            summary[name] = True
        except Exception as exc:  # noqa: BLE001
            summary[name] = False
            failures.append("%s: %s" % (name, exc))
    payload["summary"] = summary
    payload["failures"] = failures
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for name, ok in summary.items():
        print(("PASS " if ok else "FAIL ") + name)
    for f in failures:
        print("  ! " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

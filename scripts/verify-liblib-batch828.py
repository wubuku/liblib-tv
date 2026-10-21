#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 828 验收器 —— 导演台「关台重开到底丢不丢工作」：**用同一个节点重测**。

## ★ 这一批在更正什么

batch 709 的第 2/4/5 条结论（以及 README 里「第一次关台丢工作」）**是在一个
「测错了对象」的条件下得出的** ⟹ 本批把条件修正后重测。

★ **测错在哪**：709 的测量里，第一次开台走**后门**
（`uiStore.openDirectorDesk(nodes.at(-1).id, …)`），而重开走**真实按钮**
（`page.locator("[data-open-director]").first.click()`）⟹
★ ★★ 画布上**有两个** script-execution 节点 —— 种子节点 `b-bTLLuU4w5q`
（标题「第一集：咖啡馆对峙」）＋ 后门 `addNode` 新造的那个
（`script-execution-<时间戳>-<随机>`）⟹ ⟹ **`.first` 点的是种子节点的按钮**
⟹ ⟹ 两次开台**根本不是同一个节点** ⟹ ⟹ 「工作丢了」是必然的
（换了个节点当然看不到前一个节点的工作）。

★ ★★ 更深一层：709 当时**连真实按钮都点不动**（batch 827 查实真因是
**页面不 hydration**：Next 16 默认拦截来自 `127.0.0.1` 的 dev 资源）⟹
⟹ 它把那笔账记成了「用户路径未取证」。

## ★ 本批与 batch 710 的关系（别把本批当成「第一次同节点重测」）

710 已经用 `b-bTLLuU4w5q` **同节点**建立过「关台重开**保留**已提交内容与历史」。
本批**不是**它的重复，本批的增量是五件它没做的事：

1. ★ **撤销可用性**（S4）：重开后按 `Cmd+Z` 是不是**真的** `UNDO/COMMITTED`
   （710 只测了 `pastLen` 仍是 1，没测「那条历史还能不能用」）；
2. ★ **两条开台路径等价**（S5）：后门开台与真实按钮开台在**同一个节点**上
   是否给出同一结果（710 只跑了一条路径）；
3. ★ **混搭 / 反混搭对照**（S6 / S7）：把「换了节点」与「换了路径」两个变量
   分开 ⟹ 决定变量是**节点身份**，不是**开台路径**；
4. ★ **hydration 前提闸门**（S1）：batch 827 查实过「页面看着正常但点击全无效」
   ⟹ 读数作废；710 当时**没有**这道闸门；
5. ★ **手势的重新定性**（S9）：709 的 P4「关台丢弃未提交手势」**在同一个节点上
   也是假的** ⟹ 关台不是丢弃手势，是**把它提交**成一条 `camera-fov` 条目。

★ 并且：本批的**工程产物**是修掉 `scripts/verify-liblib-batch709.py` ——
709 那条门禁**一直是绿的，但它绿在「测的不是那个东西」上**（它用 617 仪器开后门
节点、再用 `.first` 点种子节点，**恒定复现**那个假象）⟹ 一条会持续把假结论
钉成「事实」的门禁。

## ★ 本批的六臂

序 | 臂 | 第一次开台 | 重开 | 作用 |
| --- | --- | --- | --- | --- |
| 1 | A | 真实按钮（种子节点） | 真实按钮（**同一个**节点） | **用户路径** |
| 2 | E | 后门（后门节点） | 真实按钮（**同一个**节点） | 两条路径在同节点上是否等价 |
| 3 | G | 真实按钮 | 真实按钮（同节点） | 方向键手势关台后**保留**还是**丢弃** |
| 4 | F | 真实按钮 | 真实按钮（同节点）＋**刷新页面** | 刷新后是否还在 |
| 5 | C | 后门（后门节点） | 真实按钮（**另一个**节点） | 709 的混搭（对照） |
| 6 | D | 真实按钮（种子节点） | 后门（**另一个**节点） | 反混搭（对照） |

## ★ 判据纪律

- ★ 判据只认**绝对读数**（projectId / 名字集合 / 历史长度 / 撤销结果 / fov）
- ★ **每条阴性只翻它自己那一条** ⟹ 六臂的读数分属**互不重叠**的字段
- ★ **S1 先证明页面 hydration 了**（batch 827 的教训 ⟹ 页面不交互时读数一律作废）
- ★ 探针**只**用「建节点」这一处 store 后门（画布的「新建节点」纯 UI 入口至今没找到，
  batch 823 已记）；**开台 / 关台 / 改名 / 撤销全部走真实 UI**
"""
import copy
import json
import os
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch828-2026-10-01"
RAW = BATCH / "raw" / "vb828a.json"
SRC_PERSIST = ROOT / "src" / "lib" / "directorProjectPersistence.ts"
SRC_STORE = ROOT / "src" / "store" / "directorStore.ts"

PROBE_BEGIN = "# ── ★ 探针区开始"
PROBE_END = "# ── ★ 探针区结束"

BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1920, "height": 1080}
RENAME_TO = "Batch 828 改名"
SEED_NODE_TITLE = "第一集：咖啡馆对峙"

# ── ★ 探针区开始 ────────────────────────────────────────────────────────────────
READ_HYDRATION = """()=>{
  const b=document.querySelector('button[aria-label="素材库"]');
  if(!b) return {found:false};
  const keys=Object.keys(b).filter(k=>k.startsWith('__react'));
  return {found:true, keys:keys,
          hasOnClick:keys.some(k=>typeof b[k].onClick==='function')};}"""

READ_CENSUS = """()=>{
  const out=[];
  for(const b of document.querySelectorAll('[data-open-director]')){
    const host=b.closest('.react-flow__node');
    out.push({nodeId: host?host.getAttribute('data-id'):null});}
  const nodes=window.__libtv_store.getState().getActiveCanvas().nodes
    .filter(n=>n.type==='script-execution')
    .map(n=>({id:n.id, title:(n.data&&n.data.title)||null}));
  return {buttons:out, scriptExecutionNodes:nodes};}"""

READ = """() => {
  const s = window.__director_store.getState();
  const h = s.history; const r = s.lastCommandResult;
  const w = document.querySelector('[data-director-workspace]');
  const cam = s.objects.find((o) => o.kind === 'camera');
  const ui = window.__libtv_ui_store.getState();
  return {
    deskOpen: !!w,
    projectId: w ? w.getAttribute('data-director-project-id') : null,
    pastLen: (h.past || []).length,
    pastKinds: (h.past || []).map((e) => e.commandKind),
    last: r ? r.commandKind + '/' + r.disposition : null,
    active: h.activeGesture ? h.activeGesture.commandKind : null,
    fovStore: cam ? cam.camera.fov : null,
    names: s.objects.map((o) => o.name),
    nodeId: ui.activeDirectorNodeId,
  };
}"""

SEL_CAMERA = r"""() => {
  const s = window.__director_store.getState();
  const c = s.objects.find((o) => o.kind === 'camera');
  const row = document.querySelector('[data-director-tree] [role="treeitem"]'
    + '[data-director-object-id="' + c.id + '"]');
  if (!row) return { ok: false, stage: 'no-row' };
  row.click();
  return { ok: window.__director_store.getState().selectedObjectId === c.id };
}"""


def btn_for(node_id: str) -> str:
    """★ 按**节点 id** 定位按钮 ⟹ 绝不 `.first`（`.first` 会命中另一个节点）。"""
    return '.react-flow__node[data-id="%s"] [data-open-director]' % node_id


def read(page):
    return page.evaluate(READ)


def clean(page):
    page.evaluate(
        "() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(300)
    # ★ 选中相机**必须成功** —— 否则改名输入框不出现，而「等 30 秒找不到元素」
    #   会把真正的错因（树还没渲染）盖住 ⟹ 显式重试并断言。
    page.wait_for_function(
        "() => document.querySelectorAll('[data-director-tree] [role=\"treeitem\"]').length > 0",
        timeout=20_000)
    sel = {"ok": False}
    for _ in range(20):
        sel = page.evaluate(SEL_CAMERA)
        if sel.get("ok"):
            break
        page.wait_for_timeout(300)
    if not sel.get("ok"):
        raise AssertionError("选中相机失败：%s" % sel)
    page.wait_for_selector("[data-director-object-name]", timeout=20_000)
    page.wait_for_timeout(500)


def open_node(page, node_id, via):
    if via == "real":
        page.locator(btn_for(node_id)).first.click()
    else:
        page.evaluate("""(nid) => {
          const s = window.__libtv_store.getState();
          window.__libtv_ui_store.getState().openDirectorDesk(nid, s.activeCanvasId);
        }""", node_id)
    page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
    page.wait_for_timeout(1_800)
    page.evaluate(
        "() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")


def close_desk(page):
    page.locator("[data-close-director]").first.click()
    page.locator("[data-director-workspace]").wait_for(state="detached", timeout=15_000)
    page.wait_for_timeout(1_000)


def rename(page, text):
    el = page.locator("[data-director-object-name]").first
    el.click()
    page.wait_for_timeout(200)
    el.fill(text)
    el.press("Tab")
    page.wait_for_timeout(800)


def gesture(page, n):
    """相机 fov 的方向键手势。"""
    el = page.locator("[data-director-shot-end]").first
    el.click()
    page.wait_for_timeout(200)
    el.press("Tab")
    page.wait_for_timeout(500)
    for _ in range(n):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)


def setup(browser, add_node):
    page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)
    page.goto(f"{BASE_URL}/?batch828=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_function(
        "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
        "&& window.__director_store)", timeout=60_000)
    if add_node:
        # ★ 全探针**唯一**一处 store 后门：画布的「新建节点」纯 UI 入口至今没找到
        #   （batch 823 已记）⟹ 这里只用来**多造一个节点**当对照，不参与测量对象。
        page.evaluate("""() => {
          const s = window.__libtv_store.getState();
          s.addNode("script-execution", { title: "Batch 828" });
        }""")
        page.wait_for_timeout(1_500)
        page.evaluate(
            "() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        page.mouse.move(5, 5)
        page.wait_for_timeout(300)
    node_id = page.evaluate("""() => {
      const nodes = window.__libtv_store.getState().getActiveCanvas().nodes;
      return nodes.filter((n) => n.type === 'script-execution').at(-1).id;
    }""")
    return page, node_id


def arm_user_path(browser):
    """A：真实按钮 → 真实按钮（同一个节点）＝ 用户路径。"""
    page, nid = setup(browser, add_node=False)
    rec = {"node": nid, "节点普查": page.evaluate(READ_CENSUS)}
    open_node(page, nid, "real")
    clean(page)
    rec["开台后"] = read(page)
    rename(page, RENAME_TO)
    rec["改名后"] = read(page)
    close_desk(page)
    rec["关台后"] = read(page)
    open_node(page, nid, "real")
    clean(page)
    rec["重开后"] = read(page)
    page.mouse.click(640, 900)
    page.wait_for_timeout(500)
    page.keyboard.press("Meta+z")
    page.wait_for_timeout(800)
    rec["重开后撤销"] = read(page)
    page.close()
    return rec


def arm_backdoor_same_node(browser):
    """E：后门开 → 真实按钮重开（**同一个**节点）⟹ 两条路径是否等价。"""
    page, nid = setup(browser, add_node=True)
    rec = {"node": nid, "节点普查": page.evaluate(READ_CENSUS)}
    open_node(page, nid, "backdoor")
    clean(page)
    rec["开台后"] = read(page)
    rename(page, RENAME_TO)
    rec["改名后"] = read(page)
    close_desk(page)
    rec["关台后"] = read(page)
    open_node(page, nid, "real")
    clean(page)
    rec["重开后"] = read(page)
    page.close()
    return rec


def arm_gesture(browser):
    """G：相机 fov 方向键手势，关台重开（同节点）⟹ 手势的值还在不在。"""
    page, nid = setup(browser, add_node=False)
    rec = {"node": nid}
    open_node(page, nid, "real")
    clean(page)
    rec["开台后"] = read(page)
    gesture(page, 3)
    rec["手势后"] = read(page)
    close_desk(page)
    rec["关台后"] = read(page)
    open_node(page, nid, "real")
    clean(page)
    rec["重开后"] = read(page)
    page.close()
    return rec


def arm_reload(browser):
    """F：刷新页面后重开（同一个节点）⟹ 工作是否持久化。"""
    page, nid = setup(browser, add_node=False)
    rec = {"node": nid}
    open_node(page, nid, "real")
    clean(page)
    rename(page, RENAME_TO)
    rec["改名后"] = read(page)
    close_desk(page)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(3_000)
    rec["刷新后"] = read(page)
    open_node(page, nid, "real")
    clean(page)
    rec["刷新后重开"] = read(page)
    page.close()
    return rec


def arm_mixed(browser):
    """C：709 的混搭（后门开 → **另一个**节点的按钮）＝ 对照。"""
    page, nid = setup(browser, add_node=True)
    seed = page.evaluate("""() => {
      const nodes = window.__libtv_store.getState().getActiveCanvas().nodes;
      return nodes.filter((n) => n.type === 'script-execution')[0].id;
    }""")
    rec = {"node": nid, "另一个节点": seed}
    open_node(page, nid, "backdoor")
    clean(page)
    rec["开台后"] = read(page)
    rename(page, RENAME_TO)
    rec["改名后"] = read(page)
    close_desk(page)
    open_node(page, seed, "real")
    clean(page)
    rec["重开后"] = read(page)
    page.close()
    return rec


def arm_mixed_reverse(browser):
    """D：反混搭（真实按钮开 → 后门重开**另一个**节点）＝ 对照。"""
    page, nid = setup(browser, add_node=True)
    seed = page.evaluate("""() => {
      const nodes = window.__libtv_store.getState().getActiveCanvas().nodes;
      return nodes.filter((n) => n.type === 'script-execution')[0].id;
    }""")
    rec = {"node": nid, "另一个节点": seed}
    open_node(page, seed, "real")
    clean(page)
    rec["开台后"] = read(page)
    rename(page, RENAME_TO)
    rec["改名后"] = read(page)
    close_desk(page)
    open_node(page, nid, "backdoor")
    clean(page)
    rec["重开后"] = read(page)
    page.close()
    return rec


READ_BLUR_LOG = """() => (window.__blurLog || []).map((e) => ({
  target: e.target, before: e.before, after: e.after || null }))"""

INSTALL_BLUR_RECORDER = """() => {
  if (window.__blurRecorderInstalled) return;
  window.__blurRecorderInstalled = true;
  window.__blurLog = [];
  const snap = () => {
    const s = window.__director_store.getState();
    const cam = s.objects.find((o) => o.kind === 'camera');
    return {active: s.history.activeGesture ? s.history.activeGesture.commandKind : null,
            pastLen: (s.history.past || []).length,
            pastKinds: (s.history.past || []).map((e) => e.commandKind),
            fov: cam ? cam.camera.fov : null};
  };
  document.addEventListener('blur', (e) => {
    const entry = {target: e.target && e.target.getAttribute
      ? (e.target.getAttribute('data-director-camera-fov') !== null
         ? 'camera-fov-range' : e.target.tagName) : 'unknown',
      before: snap()};
    window.__blurLog.push(entry);
    setTimeout(() => { entry.after = snap(); }, 0);
  }, true);
}"""

CLEAR_BLUR_LOG = """() => { window.__blurLog = []; }"""


def arm_blur_commit(browser):
    """H：手势的**失焦**语义 —— 什么操作会提交它、什么操作不会。

    ★ 这条臂是为了把「关台时手势已被提交」从**推断**变成**实测**：
    源码里 `closeWorkspace`（DirectorDesk.tsx:451）在 `closeSession` 之前
    会 `if (history.activeGesture) cancelDirectorGesture()` ⟹ 若那个分支走了，
    手势会被**回滚**（fov 回 43，条目 kind = GESTURE_CANCEL）。
    ★ 而实测 fov 留在 46、条目 kind = `camera-fov` ⟹ 说明**关台那一刻
    手势已经不是 active 了** ⟹ 一定是在关台**之前**就有人提交了它。
    ★ 本臂直接测那件事，并且用**事件记录器**（document 上的 capture 阶段
    `blur` 监听）把「blur 发生时手势还是 active、blur 之后它已被提交」
    逐拍记下来 ⟹ 顺序是**测出来的**，不是推出来的。
    """
    page, nid = setup(browser, add_node=False)
    rec = {"node": nid}
    open_node(page, nid, "real")
    clean(page)
    page.evaluate(INSTALL_BLUR_RECORDER)
    rec["开台后"] = read(page)
    gesture(page, 3)
    page.evaluate(CLEAR_BLUR_LOG)
    rec["手势后"] = read(page)
    # ★ 操作 A：点 3D 画布空白处 ⟹ 焦点**不动**（画布 pointerdown 阻止默认行为）
    page.mouse.click(640, 900)
    page.wait_for_timeout(1_000)
    rec["点画布后"] = read(page)
    rec["点画布后的blur日志"] = page.evaluate(READ_BLUR_LOG)
    # ★ 操作 B：按 Tab（键盘移动焦点**一定**触发 blur）⟹ 手势当场被提交
    page.keyboard.press("Tab")
    page.wait_for_timeout(1_000)
    rec["失焦后"] = read(page)
    rec["失焦后的blur日志"] = page.evaluate(READ_BLUR_LOG)
    close_desk(page)
    rec["关台后"] = read(page)
    open_node(page, nid, "real")
    clean(page)
    rec["重开后"] = read(page)
    page.close()
    return rec


def probe(page):
    out = {"viewport": VIEWPORT}
    out["hydration"] = page.evaluate(READ_HYDRATION)
    return out


def probe_all(browser):
    out = {"viewport": VIEWPORT}
    # ★ 先导航再读 hydration ⟹ 否则页面里根本没有那个按钮 ⟹ 读数是「没找到」，
    #   而**不是**「不 hydration」⟹ ★ 这两种失败必须分得开。
    hp = browser.new_page(viewport=VIEWPORT)
    hp.goto(f"{BASE_URL}/?batch828=1", wait_until="networkidle", timeout=90_000)
    hp.wait_for_timeout(1_500)
    out["hydration"] = hp.evaluate(READ_HYDRATION)
    hp.close()
    out["A 用户路径·同节点"] = arm_user_path(browser)
    out["E 后门开·同节点真实按钮重开"] = arm_backdoor_same_node(browser)
    out["G 手势臂·同节点"] = arm_gesture(browser)
    out["H 失焦提交·同节点"] = arm_blur_commit(browser)
    out["F 刷新·同节点"] = arm_reload(browser)
    out["C 混搭（后门→别的节点）"] = arm_mixed(browser)
    out["D 反混搭（真实→别的节点）"] = arm_mixed_reverse(browser)
    return out


# ── ★ 探针区结束 ────────────────────────────────────────────────────────────────

# ── 判据（纯函数：吃读数吐检查）───────────────────────────────────────────────
def build_checks(clone, src_texts, probe_src):
    C = []

    def ok(cid, cond, detail=None):
        C.append({"id": cid, "name": cid, "ok": bool(cond),
                  "detail": detail if detail is not None else ""})

    A = clone["A 用户路径·同节点"]
    E = clone["E 后门开·同节点真实按钮重开"]
    G = clone["G 手势臂·同节点"]
    F = clone["F 刷新·同节点"]
    Cc = clone["C 混搭（后门→别的节点）"]
    D = clone["D 反混搭（真实→别的节点）"]

    # ── S1 前提：页面 hydration ＋ 探针区零 store 写调用
    i0 = probe_src.find(PROBE_BEGIN)
    j0 = probe_src.find(PROBE_END)
    region = probe_src[i0:j0] if 0 <= i0 < j0 else probe_src
    store_writes = re.findall(r"\.(setState|addNode|removeNode|updateCamera)\s*\(",
                              region)
    hyd = clone.get("hydration") or {}
    ok("S1:★★ **前提**：页面**已 hydration**（DOM 上有 React props）"
       "＋ 探针源码**零 store 写调用**",
       hyd.get("hasOnClick") is True and not store_writes,
       {"hydration": hyd,
        "扫的区间": "探针区（%s … %s）" % (PROBE_BEGIN, PROBE_END),
        "探针里的 store 写调用": store_writes,
        "★为什么": "Next 16 默认拦截来自 127.0.0.1 的 dev 资源 ⟹ 整页不 hydration "
                "⟹ 页面看起来正常但点击全无效 ⟹ 读数会是假的（batch 827 §4）"})

    # ── S2 节点普查：种子节点在 ＋ 后门加节点后变成两个 ⟹ `.first` 会命中「另一个」
    census_seed = A.get("节点普查") or {}
    census_two = E.get("节点普查") or {}
    ok("S2:★★★ 画布上**种子** script-execution 节点**只有一枚**，"
       "它的「打开导演台」按钮在（`.first` 命中它）；后门加一个节点后变成**两枚**"
       "⟹ ⟹ 709 用 `.first` 重开 ⟹ 点到的是**另一个**节点",
       len(census_seed.get("scriptExecutionNodes", [])) == 1
       and len(census_seed.get("buttons", [])) == 1
       and census_seed["scriptExecutionNodes"][0]["title"] == SEED_NODE_TITLE
       and census_seed["buttons"][0]["nodeId"]
       == census_seed["scriptExecutionNodes"][0]["id"]
       and len(census_two.get("scriptExecutionNodes", [])) == 2
       and len(census_two.get("buttons", [])) == 2
       and census_two["buttons"][0]["nodeId"]
       == census_two["scriptExecutionNodes"][0]["id"]
       and census_two["buttons"][1]["nodeId"]
       == census_two["scriptExecutionNodes"][1]["id"],
       {"种子状态": census_seed, "后门加节点后": census_two,
        "★709 踩的坑": "709 的重开用 `[data-open-director]` 的 `.first` ⟹ "
                  "而它的第一次开台是后门加的**另一个**节点 ⟹ 两次根本不是同一个节点"})

    # ── S3 用户路径（同一节点）：关台重开后**工作与历史都还在**、projectId 不变
    a_open, a_rename, a_reopen = A["开台后"], A["改名后"], A["重开后"]
    ok("S3:★★★★ **用户路径**（真实按钮 → 真实按钮，**同一个节点**）："
       "关台重开后 **projectId 一字不变** ＋ **已提交的改名还在** ＋ **历史那条也还在**",
       a_reopen["projectId"] == a_open["projectId"] == a_rename["projectId"]
       and RENAME_TO in a_reopen["names"]
       and RENAME_TO in a_rename["names"]
       and a_reopen["pastLen"] == 1
       and a_reopen["pastKinds"] == ["UPDATE_OBJECT"]
       and a_reopen["nodeId"] == A["node"],
       {"第一次开台": a_open, "改名后": a_rename, "重开后": a_reopen,
        "★更正": "batch 709 断言「第一次关台重开丢掉一切已提交内容（含历史）」"
               "⟹ 在**同一个节点**上这是**假的**"})

    # ── S4 用户路径：重开后 **Cmd+Z 仍然能撤销**（历史没被清掉）
    a_undo = A["重开后撤销"]
    ok("S4:★★★ 用户路径：**关台重开之后撤销仍然可用**"
       "（Cmd+Z 记 UNDO/COMMITTED、历史归零、那次改名被撤掉）",
       a_undo["last"] == "UNDO/COMMITTED"
       and a_undo["pastLen"] == 0
       and RENAME_TO not in a_undo["names"]
       and a_undo["projectId"] == a_open["projectId"],
       {"重开后撤销": a_undo,
        "★更正": "batch 709 断言「关台重开后 history.past 归零、之后按 Cmd+Z 记 UNDO/NOOP」"
               "⟹ 在**同一个节点**上 past 仍是 1、Cmd+Z 是真的 UNDO"})

    # ── S5 后门开 → **同节点**真实按钮重开：与用户路径**同结果** ⟹ 两条路径等价
    e_open, e_reopen = E["开台后"], E["重开后"]
    ok("S5:★★★ **后门开台** → **同一个节点**的真实按钮重开：结果与用户路径**相同**"
       "（projectId 不变、改名还在、历史还在）⟹ ⟹ 决定变量是「同一个节点」，"
       "**不是**「哪条开台路径」",
       e_reopen["projectId"] == e_open["projectId"]
       and RENAME_TO in e_reopen["names"]
       and e_reopen["pastLen"] == 1
       and e_reopen["nodeId"] == E["node"]
       and E["node"] != A["node"],
       {"后门臂开台后": e_open, "后门臂重开后": e_reopen,
        "节点": {"用户路径臂": A["node"], "后门臂": E["node"]},
        "★两条路径的函数完全相同": "真实按钮 `ScriptExecutionNode.tsx:57` 调的就是 "
                        "`openDirectorDesk(id, activeCanvasId)`"})

    # ── S6 混搭（709 的条件）：projectId **变** ＋ 改名**不在**
    c_open, c_reopen = Cc["开台后"], Cc["重开后"]
    ok("S6:★★★★ **709 的条件**（后门开 → **另一个**节点的按钮）："
       "projectId **变了** ＋ 改名**不见了** ＋ 历史**归零** ⟹ ⟹ 709 测到的是"
       "「**换了个节点**」，不是「丢了工作」",
       c_reopen["projectId"] != c_open["projectId"]
       and RENAME_TO not in c_reopen["names"]
       and c_reopen["pastLen"] == 0
       and c_reopen["nodeId"] == Cc["另一个节点"]
       and c_reopen["nodeId"] != Cc["node"],
       {"混搭臂开台后": c_open, "混搭臂重开后": c_reopen,
        "第一次的节点": Cc["node"], "重开的节点": Cc["另一个节点"]})

    # ── S7 反混搭：同样丢 ⟹ ⟹ 决定变量是「同一个节点」而不是「哪条路径」
    d_open, d_reopen = D["开台后"], D["重开后"]
    ok("S7:★★★ **反混搭**（真实按钮开 → **另一个**节点的后门重开）："
       "**同样** projectId 变 ＋ 改名不见 ⟹ ⟹ 进一步证明决定变量是**节点**，不是路径",
       d_reopen["projectId"] != d_open["projectId"]
       and RENAME_TO not in d_reopen["names"]
       and d_reopen["pastLen"] == 0
       and d_reopen["nodeId"] == D["node"]
       and d_reopen["nodeId"] != D["另一个节点"],
       {"反混搭臂开台后": d_open, "反混搭臂重开后": d_reopen,
        "第一次的节点": D["node"], "重开的节点": D["另一个节点"]})

    # ── S8 刷新页面（同节点）：**工作还在** ⟹ ⟹ 它是持久化过的
    f_rename, f_reload, f_reopen = F["改名后"], F["刷新后"], F["刷新后重开"]
    ok("S8:★★★ **刷新页面**后重开（**同一个节点**）：**已提交的改名还在**、"
       "projectId 不变 ⟹ ⟹ 工作是**持久化**过的（不是内存态）",
       RENAME_TO in f_reopen["names"]
       and f_reopen["projectId"] == f_rename["projectId"]
       and f_reopen["nodeId"] == F["node"]
       and f_reload["deskOpen"] is False
       and RENAME_TO not in f_reload["names"],
       {"刷新前改名后": f_rename, "刷新后": f_reload, "刷新后重开": f_reopen,
        "★更正": "batch 709 断言「刷新页面后重开也丢」⟹ 在**同一个节点**上这也是**假的**",
        "★机制": "clone 的导演台工程持久化在 localStorage"
               "（src/lib/directorProjectPersistence.ts）"})

    # ── S9 手势（相机 fov 方向键）：**前提重定性** ⟹ 709 的 P4 判据作废
    g_open, g_gesture, g_reopen = G["开台后"], G["手势后"], G["重开后"]
    ok("S9:★★★★ 相机 fov 的方向键手势**不是**「会被丢弃的未提交改动」："
       "① 手势活动期间**值已落盘**（`last` = `UPDATE_CAMERA/COMMITTED`）但"
       "**不产生历史条目**（`pastLen` 0）⟹ 「未提交」的真实含义是「**没有可撤销条目**」，"
       "不是「值会被丢掉」；② 关台时手势被**提交**成一条 `camera-fov` 的历史条目 ⟹ "
       "同节点重开后 **fov 保留 46**、**pastLen 1**、**pastKinds ['camera-fov']**、"
       "**projectId 一字不变** ⟹ ⟹ batch 709 的 P4（「关台丢弃未提交手势，fov 46→43」）"
       "**在同一个节点上也是假的**：它读到的 43 是**另一个节点**的新工程基线",
       g_open["fovStore"] == 43
       and g_gesture["fovStore"] == 46
       and g_gesture["last"] == "UPDATE_CAMERA/COMMITTED"
       and g_gesture["active"] == "camera-fov"
       and g_gesture["pastLen"] == 0
       and g_reopen["fovStore"] == 46
       and g_reopen["pastLen"] == 1
       and g_reopen["pastKinds"] == ["camera-fov"]
       and g_reopen["projectId"] == g_open["projectId"],
       {"开台后": g_open, "手势后": g_gesture, "重开后": g_reopen,
        "★机制（源码可查）": "commitDirectorMutation 在 `history.activeGesture` 存在时"
                    "返回 `historyEntries: 0` ⟹ 值实时落到文档上但**不记账**；"
                    "关台时焦点离开 ⟹ `useDirectorGestureBoundary` 的 `onBlur` ⟹ "
                    "`commitDirectorGesture()` ⟹ 生成 kind=`camera-fov` 的条目并 "
                    "`rememberDirectorHistory(projectId, …)`；"
                    "重开时 `historyForDirectorProject(projectId)` 把它取回来",
        "★709 判据作废": "709 P4 的读数 43 来自**另一个节点**的工程默认值"})

    # ── S10 静态锚点：持久化实现与历史键都在
    persist_src, store_src = src_texts
    ok("S10:★ 静态锚点：导演台工程的**持久化实现**在"
       "（localStorage ＋ schema 版本 ＋ owner ＋ tombstone）",
       "localStorage" in persist_src
       and "DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION" in persist_src
       and "TOMBSTONED" in persist_src
       and "directorProjectPersistence" in store_src,
       {"持久化文件里有 localStorage": "localStorage" in persist_src,
        "有 schema 版本": "DIRECTOR_PROJECT_STORAGE_SCHEMA_VERSION" in persist_src,
        "store 引用了持久化": "directorProjectPersistence" in store_src})

    # ── S11 手势的失焦语义：什么提交它、什么**不**提交它（机制实测，不是推断）
    H = clone["H 失焦提交·同节点"]
    h_gesture = H["手势后"]
    h_canvas = H["点画布后"]
    h_blur = H["失焦后"]
    h_reopen = H["重开后"]
    log_canvas = H.get("点画布后的blur日志") or []
    log_blur = H.get("失焦后的blur日志") or []
    ok("S11:★★★★ 手势的**失焦语义**（事件记录器逐拍实测）："
       "① 手势期间**值已落盘**（`last` = `UPDATE_CAMERA/COMMITTED`）但"
       "**不产生历史条目**（`pastLen` 0）；② **点 3D 画布不会让它失焦** ⟹ "
       "**不提交**（焦点仍在滑杆上、blur 日志**零条**）；③ **按 Tab 失焦 ⟹ 当场提交**"
       "（`last` = `GESTURE_COMMIT/COMMITTED`、`pastLen` 1、条目 kind = `camera-fov`、"
       "`active` 转 null），且 blur 事件**发生时**手势还是 active、**之后**已被提交 "
       "⟹ ⟹ ⟹ **关台那一刻手势已经不在 active** ⟹ ⟹ "
       "`DirectorDesk.tsx:453` 那个 `cancelDirectorGesture()` 分支**根本没走** ⟹ "
       "⟹ **关台不是「取消手势」，是「把手势带着走」** ⟹ ⟹ batch 709 台账里"
       "「关台等于取消当前手势 ⟹ 文档回滚到手势基线」这条**机制解释**也不成立",
       h_gesture["fovStore"] == 46
       and h_gesture["active"] == "camera-fov"
       and h_gesture["last"] == "UPDATE_CAMERA/COMMITTED"
       and h_gesture["pastLen"] == 0
       # ② 点画布：焦点不动、不失焦、不提交
       and h_canvas["active"] == "camera-fov"
       and h_canvas["pastLen"] == 0
       and h_canvas["fovStore"] == 46
       and len(log_canvas) == 0
       # ③ Tab 失焦：当场提交
       and h_blur["last"] == "GESTURE_COMMIT/COMMITTED"
       and h_blur["pastLen"] == 1
       and h_blur["pastKinds"] == ["camera-fov"]
       and h_blur["active"] is None
       and h_blur["fovStore"] == 46
       # ★ blur 事件**之前**手势还是 active、**之后**已被提交（顺序是测出来的）
       and len(log_blur) >= 1
       and log_blur[0]["target"] == "camera-fov-range"
       and log_blur[0]["before"]["active"] == "camera-fov"
       and log_blur[0]["before"]["pastLen"] == 0
       and log_blur[0]["after"]["active"] is None
       and log_blur[0]["after"]["pastLen"] == 1
       and log_blur[0]["after"]["pastKinds"] == ["camera-fov"]
       # ④ 关台重开后：值与条目都还在
       and h_reopen["fovStore"] == 46
       and h_reopen["pastKinds"] == ["camera-fov"]
       and h_reopen["projectId"] == H["开台后"]["projectId"],
       {"手势后": h_gesture, "点画布后": h_canvas, "失焦后": h_blur,
        "重开后": h_reopen,
        "点画布后的blur日志": log_canvas, "失焦后的blur日志": log_blur,
        "★源码对得上": "commitDirectorGesture 成功 ⟹ commandKind='GESTURE_COMMIT'、"
                  "disposition='COMMITTED'、historyEntries=1、条目 kind = gesture.commandKind"
                  "（= 'camera-fov'）⟹ 与读数逐字吻合；而 cancelDirectorGesture 会 "
                  "`restoreDirectorDocumentState(gesture.baseline)` ⟹ fov 必回 43 "
                  "⟹ 实测 46 ⟹ cancel 分支未走",
        "★为什么这条重要": "它把「关台时手势已被提交」从**推断**变成**实测**；"
                     "否则「关台保留手势」还有另一种解释（关台恰好没走 cancel）",
        "★顺带一条产品读数": "在滑杆上改完值**不去失焦**、直接点 3D 画布 ⟹ "
                       "手势**不会**被提交（画布 pointerdown 阻止了默认行为 ⟹ 焦点不动）"
                       "⟹ 手势会一直开着，直到你 Tab 走或点「关闭」"})
    return C


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def n1_no_hydration(clone, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["hydration"]["hasOnClick"] = False
    return c, src_texts, probe_src


def n2_probe_writes_store(clone, src_texts, probe_src):
    i = probe_src.find(PROBE_END)
    fake = (probe_src[:i] + "\n# fake: store.setState({})\n" + probe_src[i:]
            if i > 0 else probe_src + "\n# fake: store.setState({})\n")
    return clone, src_texts, fake


def n3_census(clone, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["A 用户路径·同节点"]["节点普查"]["scriptExecutionNodes"].append(
        {"id": "x", "title": "多出来的"})
    return c, src_texts, probe_src


def n4_user_path_lost(clone, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["A 用户路径·同节点"]["重开后"]["projectId"] = "director-project-x-3"
    return c, src_texts, probe_src


def n5_undo_broken(clone, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["A 用户路径·同节点"]["重开后撤销"]["last"] = "UNDO/NOOP"
    return c, src_texts, probe_src


def n6_backdoor_arm(clone, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["E 后门开·同节点真实按钮重开"]["重开后"]["pastLen"] = 0
    return c, src_texts, probe_src


def n7_mixed_not_lost(clone, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["C 混搭（后门→别的节点）"]["重开后"]["projectId"] = \
        c["C 混搭（后门→别的节点）"]["开台后"]["projectId"]
    return c, src_texts, probe_src


def n8_reverse_mixed(clone, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["D 反混搭（真实→别的节点）"]["重开后"]["pastLen"] = 1
    return c, src_texts, probe_src


def n9_gesture_discarded(clone, src_texts, probe_src):
    """把 G 臂重开后的 fov 改成基线 43（= 假装手势被丢弃）⟹ 只该翻 S9。"""
    c = copy.deepcopy(clone)
    c["G 手势臂·同节点"]["重开后"]["fovStore"] = 43
    return c, src_texts, probe_src


def n10_reload_lost(clone, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["F 刷新·同节点"]["刷新后重开"]["names"] = [
        n for n in c["F 刷新·同节点"]["刷新后重开"]["names"] if n != RENAME_TO]
    return c, src_texts, probe_src


def n11_persistence_anchor(clone, src_texts, probe_src):
    persist, store = src_texts
    return (clone, (persist.replace("TOMBSTONED", "GONE"), store), probe_src)


def n12_blur_cancelled(clone, src_texts, probe_src):
    """把 H 臂失焦后的结果改成 GESTURE_CANCEL ⟹ 只该翻 S11。"""
    c = copy.deepcopy(clone)
    c["H 失焦提交·同节点"]["失焦后"]["last"] = "GESTURE_CANCEL/COMMITTED"
    return c, src_texts, probe_src


def main():
    probe_src = (HERE / "verify-liblib-batch828.py").read_text(encoding="utf-8")
    src_texts = (SRC_PERSIST.read_text(encoding="utf-8"),
                 SRC_STORE.read_text(encoding="utf-8"))

    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport=VIEWPORT, locale="zh-CN")
        clone = probe_all(br)
        br.close()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(clone, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    checks = build_checks(clone, src_texts, probe_src)

    neg = []
    for label, expect, builder in [
        ("N1 把 hydration 读数改成 false ⟹ S1 翻红", "S1", n1_no_hydration),
        ("N2 在探针源码副本里塞一个 store 写调用 ⟹ S1 翻红", "S1", n2_probe_writes_store),
        ("N3 在节点普查里塞一个多出来的节点 ⟹ S2 翻红", "S2", n3_census),
        ("N4 把用户路径臂的 projectId 改掉 ⟹ S3 翻红", "S3", n4_user_path_lost),
        ("N5 把重开后的撤销结果改成 UNDO/NOOP ⟹ S4 翻红", "S4", n5_undo_broken),
        ("N6 把后门臂的 pastLen 改成 0 ⟹ S5 翻红", "S5", n6_backdoor_arm),
        ("N7 把混搭臂的 projectId 改成不变 ⟹ S6 翻红", "S6", n7_mixed_not_lost),
        ("N8 把反混搭臂的 pastLen 改成 1 ⟹ S7 翻红", "S7", n8_reverse_mixed),
        ("N9 把手势臂重开后的 fov 改成基线 43（假装被丢弃）⟹ S9 翻红", "S9",
         n9_gesture_discarded),
        ("N10 把刷新臂的名字里去掉那次改名 ⟹ S8 翻红", "S8", n10_reload_lost),
        ("N11 在持久化源码副本里去掉 TOMBSTONED ⟹ S10 翻红", "S10", n11_persistence_anchor),
        ("N12 把失焦臂的结果改成 GESTURE_CANCEL ⟹ S11 翻红", "S11", n12_blur_cancelled),
    ]:
        c2, t2, p2 = builder(clone, src_texts, probe_src)
        mc = build_checks(c2, t2, p2)
        turned = sorted({c["id"].split(":")[0] for c in mc if not c["ok"]})
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": turned == [expect]})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 828,
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                            "total": len(neg)},
              "checks": checks, "阴性": neg}
    (BATCH / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:78])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:66]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())

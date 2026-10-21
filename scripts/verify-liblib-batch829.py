#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 829 验收器 —— 源站导演台「**关掉再打开**、以及**刷新页面**后，参数留不留？」

## ★ 这一批补的是哪条洞

- batch 599 §遗留：「**源站关闭再打开导演台时 zoom 是否保留，没有观测过**」
- batch 604 §遗留：同一条
- batch 828 把 **clone 侧**测清楚了（同一个节点关台重开**保留**；刷新页面**内容留住、
  历史归零**），但**源站侧**始终没有对照 ⟹ 「clone 这样对不对」无法回答。

★ 本批**首次**观测到源站的行为（2026-10-21，无头 + 登录态）：

| 参数 | 类别 | 初始 | 改后 | 关台重开后 | 刷新页面后 |
| --- | --- | --- | --- | --- | --- |
| 机位 **FOV**（range 15–90） | **场景参数** | 67 | **34** | **34（保留）** | **34（保留）** |
| **场景缩放**（range 0.1–10） | **视口视图态** | 3 | 3.1 | 3.1（保留） | 3.1（保留） |

⟹ 源站把导演台工程**持久化到服务端** ⟹ 关台重开、刷新页面都**留得住**。
⟹ ⟹ **与 clone 一致**（clone 828：同节点关台重开保留、刷新后内容留住）⟹
⟹ 828 对 709 的更正**方向被源站侧支持**。

## ★ 两种模式

- 默认（**离线**）：对着**入库读数**断言 ⟹ 不需要网络、不需要登录态；
- `--live`：**重测源站**（需要 `/tmp/liblib-cookie.json`）⟹ 同一套判据跑新读数。

★ 纪律：
- 改值一律**真实鼠标点**源站那枚透明的原生 `input[type=range]`（用户点的就是它）；
- ★ 改完**回读校验**：值必须真的变了，否则换一格再点（不许拿「读数没变」当结论）；
- ★ 测完**把值改回原值**（别把测试项目改脏）；
- ★ 不点任何生成/付费控件（发送 / 截图 / 上传图片 一律不碰）。
"""
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch829-2026-10-01"
RAW_SOURCE = BATCH / "raw" / "source-829-desk.json"
RAW_STRUCTURE = BATCH / "raw" / "source-829-structure.json"
RAW_RESTORE = BATCH / "raw" / "source-829-restore.json"
RAW_FRESHCTX = BATCH / "raw" / "source-829-freshctx.json"
CLONE_RAW = (ROOT / "docs" / "research" / "liblib-canvas-batch828-2026-10-01"
             / "raw" / "vb828a.json")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")
RENAME_TO = "Batch 828 改名"

# ── ★ 探针区开始（live 模式用；离线模式不读网）────────────────────────────────
READ_RANGES = """()=>{
  const realVis=(e)=>{
    for(let n=e;n&&n.nodeType===1;n=n.parentElement){
      const cs=getComputedStyle(n);
      if(cs.display==='none')return false;
      if(cs.visibility==='hidden')return false;
      if(Number(cs.opacity||'1')<=0.001)return false;
    }
    return true;
  };
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const rows=Array.from(document.querySelectorAll('div,span,label,p'))
    .filter(e=>realVis(e)&&e.children.length===0&&txt(e).length>0&&txt(e).length<20)
    .map(e=>({t:txt(e),box:box(e)}));
  const out=[];
  for(const e of document.querySelectorAll('input[type=range]')){
    const b=box(e);
    let label=null;
    for(const r of rows){
      if(r.box.y+r.box.h<=b.y+2
         && r.box.x < b.x+b.w && b.x < r.box.x+r.box.w){
        if(!label || r.box.y>label.box.y) label=r;
      }
    }
    out.push({label:label?label.t:null, labelBox:label?label.box:null,
              box:b, min:e.min, max:e.max, step:e.step, value:e.value});
  }
  return out;
}"""

READ_DESK = """()=>{
  const all=Array.from(document.querySelectorAll('*'));
  const header=all.find(e=>e.children.length===0 && (e.textContent||'').trim()==='3D导演台'
    && e.getBoundingClientRect().width>10);
  return {deskOpen: !!header};
}"""

READ_FOV = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const ranges=Array.from(document.querySelectorAll('input[type=range]'))
    .filter(e=>e.min==='15'&&e.max==='90')
    .map(e=>({box:box(e),value:e.value,min:e.min,max:e.max,step:e.step}));
  return {fovRanges:ranges};
}"""


def _pick_range(ranges, label_key, minv=None, maxv=None):
    for r in ranges:
        if r["label"] and label_key in r["label"]:
            if minv is not None and r["min"] != minv:
                continue
            if maxv is not None and r["max"] != maxv:
                continue
            return r
    return None


def _click_range(page, rng, frac):
    b = rng["box"]
    x = b["x"] + int(b["w"] * frac)
    y = b["y"] + b["h"] // 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.wait_for_timeout(120)
    page.mouse.up()
    page.wait_for_timeout(800)
    return {"clickedAt": [x, y], "frac": frac}


def _change_range(page, ranges, label_key, fracs, minv=None, maxv=None):
    rng = _pick_range(ranges, label_key, minv, maxv)
    if not rng:
        return {"error": "no range for %s" % label_key}
    before = rng["value"]
    tries = []
    for f in fracs:
        act = _click_range(page, rng, f)
        now = _pick_range(page.evaluate(READ_RANGES), label_key, minv, maxv)
        nowv = now["value"] if now else None
        tries.append({**act, "value_after": nowv})
        if nowv is not None and nowv != before:
            return {"label": label_key, "before": before, "after": nowv,
                    "tries": tries, "box": rng["box"],
                    "min": rng["min"], "max": rng["max"], "step": rng["step"]}
    return {"label": label_key, "before": before, "after": None, "tries": tries,
            "★没改成": "所有 frac 都没让值变化"}


def _fov_read(page):
    info = page.evaluate(READ_FOV)
    rs = sorted(info["fovRanges"], key=lambda x: x["box"]["y"])
    return rs[0] if rs else None


def _open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(6_000)
    return page.evaluate(READ_DESK)


def _restore_all(page, out):
    """把源站测试项目复原，并且**刷新后回读验证**。

    ★ 第一轮复原失败的原因：改完立刻关浏览器 ⟹ **改动没落盘** ⟹ 再开时还是脏值。
    ⟹ 正确做法：改值 → **干净关台** → **刷新页面** → 重开 → 回读。
    """
    rec = {}
    # ① ★ 先**重开台**：新开的台右栏停在「3D场景」⟹ 「场景缩放」那枚 range 才在 DOM 里
    #   （上一轮复原失败的原因：右栏停在**机位1 的属性面板**上 ⟹ 那枚 range 压根不在
    #    ⟹ 按旧坐标去点，点了个寂寞）
    page.locator("[aria-label='关闭']:visible").first.click()
    page.wait_for_timeout(3_000)
    _open_desk(page)
    rs = page.evaluate(READ_RANGES)
    zc = _pick_range(rs, "场景缩放")
    z0 = out.get("场景缩放_初始")
    rec["★场景缩放此刻在DOM"] = zc is not None
    if z0 and zc and zc["value"] != z0["value"]:
        span = float(zc["max"]) - float(zc["min"])
        frac = (float(z0["value"]) - float(zc["min"])) / span
        rec["恢复缩放_动作"] = _click_range(page, zc, max(0.0, min(1.0, frac)))
    # ② FOV → 回到原值（选中机位1 后才有 FOV）
    page.locator("text=机位1").first.click()
    page.wait_for_timeout(2_500)
    f0 = out.get("FOV_初始")
    fc = _fov_read(page)
    if f0 and fc and fc["value"] != f0["value"]:
        span = float(fc["max"]) - float(fc["min"])
        frac = (float(f0["value"]) - float(fc["min"])) / span
        rec["恢复FOV_动作"] = _click_range(page, fc, max(0.0, min(1.0, frac)))
    # ③ **干净关台**（落盘的触发点）→ 刷新 → 重开 → 回读
    page.locator("[aria-label='关闭']:visible").first.click()
    page.wait_for_timeout(3_000)
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(12_000)
    _open_desk(page)
    rs = page.evaluate(READ_RANGES)
    zoom = _pick_range(rs, "场景缩放")
    page.locator("text=机位1").first.click()
    page.wait_for_timeout(2_500)
    fov = _fov_read(page)
    rec["回读"] = {"场景缩放": zoom["value"] if zoom else None,
                   "FOV": fov["value"] if fov else None}
    rec["★已复原"] = (rec["回读"]["场景缩放"] == "3" and rec["回读"]["FOV"] == "67")
    return rec


def _fresh_context_read(br, cookies):
    """★ **全新浏览器 context**（localStorage 独立）读一次 ⟹ 证明服务端干净。

    ★ 为什么要这一手：同一个 context 里改值 → 刷新页面 → 读回新值，只能证明
      **本地**那份还在；**换一个 context** 读到的才是**服务端**的值。
    ★ ★ 注意：必须**复用外层那个 browser**（`br.new_context()`）⟹
      在 `sync_playwright()` 里面再开一个 `sync_playwright()` 会炸
      （「using Playwright Sync API inside the asyncio loop」）。
    """
    out = {}
    if True:
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        _open_desk(page)
        rs = page.evaluate(READ_RANGES)
        z = _pick_range(rs, "场景缩放")
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        f = _fov_read(page)
        out["场景缩放"] = z["value"] if z else None
        out["FOV"] = f["value"] if f else None
        ctx.close()
    return out


def live_measure():
    """重测源站 ⟹ 返回与入库 raw 同构的读数。"""
    from playwright.sync_api import sync_playwright

    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {"url": URL, "mode": "live"}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        out["开台返回"] = _open_desk(page)
        r0 = page.evaluate(READ_RANGES)
        out["开台后ranges"] = r0
        out["场景缩放_初始"] = _pick_range(r0, "场景缩放")
        out["改场景缩放"] = _change_range(page, r0, "场景缩放", [0.3, 0.75, 0.15])
        r1 = page.evaluate(READ_RANGES)
        out["场景缩放_改后"] = _pick_range(r1, "场景缩放")
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out["FOV_初始"] = _fov_read(page)
        out["改FOV"] = _change_range(page, page.evaluate(READ_RANGES), "FOV",
                                     [0.25, 0.8, 0.1], minv="15", maxv="90")
        out["FOV_改后"] = _fov_read(page)
        page.locator("[aria-label='关闭']:visible").first.click()
        page.wait_for_timeout(3_000)
        out["关台返回"] = page.evaluate(READ_DESK)
        out["重开返回"] = _open_desk(page)
        r2 = page.evaluate(READ_RANGES)
        out["场景缩放_重开后"] = _pick_range(r2, "场景缩放")
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out["FOV_重开后"] = _fov_read(page)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(12_000)
        out["刷新后开台返回"] = _open_desk(page)
        r3 = page.evaluate(READ_RANGES)
        out["场景缩放_刷新后"] = _pick_range(r3, "场景缩放")
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out["FOV_刷新后"] = _fov_read(page)
        # 恢复原值
        if out.get("FOV_改后") and out.get("FOV_初始"):
            want = out["FOV_初始"]["value"]
            cur = out["FOV_刷新后"]
            if cur and cur["value"] != want:
                span = float(cur["max"]) - float(cur["min"])
                frac = (float(want) - float(cur["min"])) / span
                out["恢复FOV_动作"] = _click_range(page, cur, max(0.0, min(1.0, frac)))
                out["FOV_恢复后"] = _fov_read(page)
        # ★ 复原：改值 → **干净关台** → 刷新页面 → 重开 → **回读** ⟹ 落盘才算数
        out["复原动作"] = _restore_all(page, out)
        out["全新context回读"] = _fresh_context_read(br, cookies)
        ctx.close()
        br.close()
    return out
# ── ★ 探针区结束 ──────────────────────────────────────────────────────────────


def build_checks(src, structure, restore, clone, fresh_raw=None):
    C = []
    fresh_raw = fresh_raw or {}

    def ok(cid, cond, detail=None):
        C.append({"id": cid, "name": cid, "ok": bool(cond),
                  "detail": detail if detail is not None else ""})

    desk_open = src.get("开台返回") or {}
    desk_closed = src.get("关台返回") or {}
    desk_reopen = src.get("重开返回") or {}
    desk_reload = src.get("刷新后开台返回") or {}
    fov0 = src.get("FOV_初始") or {}
    fov_after = src.get("FOV_改后") or {}
    fov_reopen = src.get("FOV_重开后") or {}
    fov_reload = src.get("FOV_刷新后") or {}
    fov_restored = src.get("FOV_恢复后") or {}
    chg_fov = src.get("改FOV") or {}
    zoom0 = src.get("场景缩放_初始") or {}
    zoom_after = src.get("场景缩放_改后") or {}
    zoom_reopen = src.get("场景缩放_重开后") or {}
    zoom_reload = src.get("场景缩放_刷新后") or {}

    ok("S1:★★★ 源站导演台**开得起来**（三次都开：首次 / 关台后重开 / 刷新页面后）",
       desk_open.get("deskOpen") is True
       and desk_reopen.get("deskOpen") is True
       and desk_reload.get("deskOpen") is True,
       {"首次开台": desk_open, "关台后重开": desk_reopen, "刷新后开台": desk_reload,
        "★入口": "画布节点 `.react-flow__node-director-console-3d`（「导演台 2」）"
                "悬停后点它的「打开导演台」按钮"})

    ok("S2:★★★ 源站导演台**关得掉**（点 `aria-label='关闭'` 后 `3D导演台` 真的不见了）"
       "⟹ 后面「重开后还留着」才不是「压根没关成」",
       desk_closed.get("deskOpen") is False,
       {"关台后": desk_closed,
        "★为什么这条必须先过": "batch 581 记过「点击无响应」的旧账 ⟹ "
                     "**先证明关掉了**，才轮到谈「重开后留不留」"})

    ok("S3:★★★★ 改 FOV **真的改了**（值从初始变成另一个值，且**回读校验**过）"
       "⟹ 排除「点击没生效、读数没变」这种假象",
       bool(chg_fov.get("after")) and chg_fov.get("before") != chg_fov.get("after")
       and chg_fov.get("before") == fov0.get("value")
       and chg_fov.get("after") == fov_after.get("value")
       and fov_after.get("value") != fov0.get("value")
       and bool(chg_fov.get("tries")),
       {"改FOV": chg_fov, "FOV_初始": fov0, "FOV_改后": fov_after,
        "★做法": "真实鼠标点源站那枚**透明原生 range**（用户点的就是它）"
                "⟹ 产生真 pointerdown/change；点完**回读**，值没变就换一格再点"})

    ok("S4:★★★★ 源站**关台重开后 FOV 保留**（场景参数留住 ⟹ 源站把导演台工程"
       "**持久化**了）⟹ ⟹ 这是 batch 599/604 那条「源站关闭再打开导演台时 zoom 是否保留，"
       "没有观测过」的**首次观测**",
       fov_reopen.get("value") == fov_after.get("value")
       and fov_reopen.get("value") != fov0.get("value"),
       {"改后": chg_fov.get("after"), "关台重开后": fov_reopen.get("value"),
        "★答": "源站**保留**（FOV 67→34，关掉再打开仍是 34）"})

    ok("S5:★★★★ 源站**刷新页面后 FOV 仍保留** ⟹ ⟹ 不只是「本次会话内留住」，"
       "而是**跨会话持久化**（源站工程存在服务端）",
       fov_reload.get("value") == fov_after.get("value")
       and fov_reload.get("value") != fov0.get("value"),
       {"刷新后": fov_reload.get("value"),
        "★答": "源站**保留**（刷新页面、重新开台，FOV 仍是 34）"})

    ok("S6:★★★ **视口视图态**（场景缩放）同样**保留**（关台重开 + 刷新后）"
       "⟹ 源站连视图态也一起存",
       zoom_after.get("value") is not None
       and zoom_after.get("value") == zoom_reopen.get("value")
       and zoom_after.get("value") == zoom_reload.get("value"),
       {"初始": zoom0.get("value"), "改后": zoom_after.get("value"),
        "关台重开后": zoom_reopen.get("value"), "刷新后": zoom_reload.get("value"),
        "★注意": "这一条与 clone 不同：clone 的视口 zoom 是**内存态**（刷新归 1）"})

    rb = restore.get("回读") or {}
    ok("S7:★★★★ **测试项目已复原**（FOV 回到 67、场景缩放回到 3，且是**刷新页面后回读**的）"
       "⟹ 测量没把用户的测试项目改脏",
       rb.get("FOV") == "67" and rb.get("场景缩放") == "3"
       and restore.get("★已复原") is True,
       {"复原后回读": rb, "★已复原": restore.get("★已复原"),
        "★为什么要回读": "★ 第一轮复原**只改了客户端、没落盘**（改完立刻关浏览器 ⟹ "
                   "再开时读到的还是脏值）⟹ 所以「复原」必须**干净关台 + 刷新页面 + 回读**"
                   "才算数（见 raw/source-829-restore-attempt1-unpersisted.json）",
        "★落盘时机": "源站的滑杆改动**不是即时落盘** ⟹ **干净关台**（或刷新）才写下去 "
                 "⟹ 与 clone 的 `closeSession → persistence.save` **同构**"})

    # ── 与 clone 的对照（读 828 的入库读数）
    arm_a = (clone.get("A 用户路径·同节点") or {})
    a_open = arm_a.get("开台后") or {}
    a_reopen = arm_a.get("重开后") or {}
    ok("S8:★★★★ **对照 clone（batch 828 入库读数）**：clone 在**同一个节点**上"
       "关台重开**保留**已提交内容（改名还在、projectId 一字不变）⟹ ⟹ "
       "**两边一致** ⟹ ⟹ 828 对 709「第一次关台丢工作」的更正**方向被源站侧支持**",
       RENAME_TO in (a_reopen.get("names") or [])
       and a_reopen.get("projectId") == a_open.get("projectId")
       and a_reopen.get("projectId") is not None,
       {"clone 开台后": a_open, "clone 重开后": a_reopen,
        "★源站侧": "FOV 保留（34）",
        "★结论": "clone 与源站在「关台重开留得住工作」这一点上**行为一致**",
        "★仍不同": "clone 的**历史栈**刷新页面后归零；源站**有没有**撤销栈本批**没测**"})

    # ── 静态锚点：源站那枚滑杆是「透明原生 range」
    struct_btn = structure.get("点按钮后") or {}
    ranges = struct_btn.get("range") or []
    fov_range = next((r for r in ranges if r.get("min") == "0.1"), None)
    ok("S9:★ 静态锚点：源站的滑杆是**原生 `input[type=range]`**（自绘轨道 + 透明原生控件"
       "叠加）⟹ 交互必须点原生控件，且「读数没变」不能直接当成「产品没反应」",
       bool(ranges) and all(r.get("visible") is False for r in ranges)
       and fov_range is not None and fov_range.get("max") == "10",
       {"源站浮层内的 range": ranges,
        "★为什么": "源站 range 是 `opacity:0` 覆盖在自绘轨道上 ⟹ 可见轨道与真实控件"
                "**不是同一个盒子** ⟹ 用截图量位置会量错"})

    # ── S10 全新 context 回读 ⟹ 服务端干净（不是本地残留）
    # ★ 两种形状：live 模式是 {"场景缩放":…, "FOV":…}；归档 raw 是
    #   {context1_场景缩放, context1_FOV, context2_…} ⟹ 这里归一化
    fresh = src.get("全新context回读") or {}
    if not fresh:
        fresh = {"场景缩放": fresh_raw.get("context1_场景缩放"),
                 "FOV": fresh_raw.get("context1_FOV")}
    ctx2 = {"场景缩放": fresh_raw.get("context2_场景缩放"),
            "FOV": fresh_raw.get("context2_FOV")}
    ok("S10:★★★★ **全新浏览器 context** 读到的也是原值（FOV 67、场景缩放 3）"
       "⟹ ⟹ 服务端**确实**干净，不是「同一个 context 的本地残留」"
       "⟹ ⟹ 复原这件事**独立验证过**（两个互相独立的 context 读数一致）",
       fresh.get("FOV") == "67" and fresh.get("场景缩放") == "3"
       and ctx2["FOV"] == "67" and ctx2["场景缩放"] == "3",
       {"全新context回读": fresh, "另一个独立context": ctx2,
        "★为什么": "同一 context 里「改值 → 刷新 → 读回」只能证明**本地**那份还在；"
                "换 context 读到的才是**服务端**的值",
        "★两次读数": (fresh_raw.get("context1_场景缩放"),
                    fresh_raw.get("context2_场景缩放"))})
    return C


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def _negations():
    def n2(src, st, rs, cl, fr):
        c = copy.deepcopy(src)
        c["关台返回"]["deskOpen"] = True
        return c, st, rs, cl, fr

    def n3(src, st, rs, cl, fr):
        # ★ 只动**动作记录**（不改读数）⟹ S4/S5 用的是读数互比，不该连坐
        c = copy.deepcopy(src)
        c["改FOV"]["after"] = c["改FOV"]["before"]
        return c, st, rs, cl, fr

    def n4(src, st, rs, cl, fr):
        c = copy.deepcopy(src)
        c["FOV_重开后"]["value"] = "67"
        return c, st, rs, cl, fr

    def n5(src, st, rs, cl, fr):
        c = copy.deepcopy(src)
        c["FOV_刷新后"]["value"] = "67"
        return c, st, rs, cl, fr

    def n6(src, st, rs, cl, fr):
        c = copy.deepcopy(src)
        c["场景缩放_刷新后"]["value"] = c["场景缩放_初始"]["value"]
        return c, st, rs, cl, fr

    def n7(src, st, rs, cl, fr):
        # ★ S7 现在断言的是**复原回读**（刷新后读到的值）⟹ 负控要改那个字段
        r2 = copy.deepcopy(rs)
        r2["回读"]["FOV"] = "34"
        return src, st, r2, cl, fr

    def n8(src, st, rs, cl, fr):
        c = copy.deepcopy(cl)
        arm = c.get("A 用户路径·同节点")
        if arm and arm.get("重开后"):
            arm["重开后"]["names"] = [
                n for n in arm["重开后"]["names"] if n != RENAME_TO]
        return src, st, rs, c, fr

    def n9(src, st, rs, cl, fr):
        s2 = copy.deepcopy(st)
        btn = s2.get("点按钮后") or {}
        for r in btn.get("range") or []:
            r["visible"] = True
        return src, s2, rs, cl, fr

    def n10(src, st, rs, cl, fr):
        # ★ S10 读的是「context1 / context2 两个独立读数」⟹ 负控要把**两处**都改脏
        f2 = copy.deepcopy(fr)
        f2["场景缩放"] = "3.1"
        f2["context1_场景缩放"] = "3.1"
        f2["context2_场景缩放"] = "3.1"
        return src, st, rs, cl, f2

    return [
        ("N1 把「关台后」改成没关掉 ⟹ S2 翻红", "S2", n2),
        ("N2 把 FOV 的「改后」改回初值 ⟹ S3 翻红", "S3", n3),
        ("N3 把「关台重开后」的 FOV 改成 67 ⟹ S4 翻红", "S4", n4),
        ("N4 把「刷新后」的 FOV 改成 67 ⟹ S5 翻红", "S5", n5),
        ("N5 把「刷新后」的场景缩放改回初值 ⟹ S6 翻红", "S6", n6),
        ("N6 把「复原回读」的 FOV 改成 34 ⟹ S7 翻红", "S7", n7),
        ("N7 把 clone 臂里的改名删掉 ⟹ S8 翻红", "S8", n8),
        ("N8 把源站 range 标成可见 ⟹ S9 翻红", "S9", n9),
        ("N9 把「全新 context 回读」的场景缩放改成 3.1 ⟹ S10 翻红", "S10", n10),
    ]


def main():
    live = "--live" in sys.argv
    if live:
        if not COOKIE.exists():
            print("★ --live 需要 %s（源站登录态）" % COOKIE)
            return 2
        src = live_measure()
        (BATCH / "raw" / "source-829-desk-live.json").write_text(
            json.dumps(src, ensure_ascii=False, indent=1), encoding="utf-8")
        structure = json.loads(RAW_STRUCTURE.read_text(encoding="utf-8"))
        # ★ live 模式下 S7 **必须**读**这一轮自己的**复原读数 ⟹ 读归档那份是**假绿**
        restore = src.get("复原动作") or {}
    else:
        src = json.loads(RAW_SOURCE.read_text(encoding="utf-8"))
        structure = json.loads(RAW_STRUCTURE.read_text(encoding="utf-8"))
        restore = json.loads(RAW_RESTORE.read_text(encoding="utf-8"))
    clone = json.loads(CLONE_RAW.read_text(encoding="utf-8"))
    fresh_raw = json.loads(RAW_FRESHCTX.read_text(encoding="utf-8")) if RAW_FRESHCTX.exists() else {}

    checks = build_checks(src, structure, restore, clone, fresh_raw)
    neg = []
    for label, expect, builder in _negations():
        s2, st2, rs2, cl2, fr2 = builder(src, structure, restore, clone, fresh_raw)
        mc = build_checks(s2, st2, rs2, cl2, fr2)
        turned = sorted({c["id"].split(":")[0] for c in mc if not c["ok"]})
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": turned == [expect]})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 829, "mode": "live" if live else "offline",
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                            "total": len(neg)},
              "checks": checks, "阴性": neg}
    (BATCH / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("模式：%s ｜ 主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        report["mode"], passed, len(checks),
        report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:96])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:60]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())

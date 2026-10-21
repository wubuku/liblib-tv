#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 829 源站实测（v2）：导演台**关掉再打开**、以及**刷新页面**后，参数留不留？

★ 回答 batch 599/604 留下的那条未观测项：「源站关闭再打开导演台时 zoom 是否保留」。
★ 测三类参数（源站把它们分成三种东西，不能混为一谈）：
  ① **视口视图态**：场景缩放（range 0.1–10）
  ② **场景参数**：机位 FOV（range 15–90）
  ③ 视口平移/旋转（x/y/z 三个 range）—— 留作对照
★ 交互纪律：
  - 改值一律**真实鼠标点**源站那枚透明的原生 range（用户点的就是它）⟹ 真 pointerdown；
  - ★ 改完**回读校验**：值必须真的变了，否则换一格再点（不许拿「读数没变」当结论）；
  - ★ 测完**把值改回原值**（别把测试项目改脏）；
  - ★ 不点任何生成/付费控件（发送/截图/上传图片 一律不碰）。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk829_measure2.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

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
    // ★ 标签必须是**同一列**（x 区间有重叠）且在它上方最近的那行
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


def open_desk(page):
    """开台：★ 先**悬停**节点卡（「打开导演台」是悬停才显形的：opacity-0 +
    pointer-events-none + group-hover:opacity-100），否则按钮被节点缩略图挡住。"""
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(6_000)
    return page.evaluate(READ_DESK)


def close_desk(page):
    page.locator("[aria-label='关闭']:visible").first.click()
    page.wait_for_timeout(3_000)
    return page.evaluate(READ_DESK)


def pick_range(ranges, label_key, minv=None, maxv=None):
    for r in ranges:
        if r["label"] and label_key in r["label"]:
            if minv is not None and r["min"] != minv:
                continue
            if maxv is not None and r["max"] != maxv:
                continue
            return r
    return None


def click_range(page, rng, frac):
    """在 range 轨道的 frac 位置**真实点击**（源站 range 透明但可点）。"""
    b = rng["box"]
    x = b["x"] + int(b["w"] * frac)
    y = b["y"] + b["h"] // 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.wait_for_timeout(120)
    page.mouse.up()
    page.wait_for_timeout(800)
    return {"clickedAt": [x, y], "frac": frac}


def change_range(page, ranges, label_key, fracs, minv=None, maxv=None):
    """改成**另一个**值：逐个 frac 试，直到回读的值真的变了。"""
    rng = pick_range(ranges, label_key, minv, maxv)
    if not rng:
        return {"error": "no range for %s" % label_key}
    before = rng["value"]
    tries = []
    for f in fracs:
        act = click_range(page, rng, f)
        now = pick_range(page.evaluate(READ_RANGES), label_key, minv, maxv)
        nowv = now["value"] if now else None
        tries.append({**act, "value_after": nowv})
        if nowv is not None and nowv != before:
            return {"label": label_key, "before": before, "after": nowv,
                    "tries": tries, "box": rng["box"],
                    "min": rng["min"], "max": rng["max"], "step": rng["step"]}
    return {"label": label_key, "before": before, "after": None, "tries": tries,
            "★没改成": "所有 frac 都没让值变化"}


def fov_read(page):
    info = page.evaluate(READ_FOV)
    rs = sorted(info["fovRanges"], key=lambda x: x["box"]["y"])
    return rs[0] if rs else None


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {"url": URL}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)


def run(out, cookies):
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

        # ── 第一次开台
        out["开台返回"] = open_desk(page)
        r0 = page.evaluate(READ_RANGES)
        out["开台后ranges"] = r0
        zoom0 = pick_range(r0, "场景缩放")
        out["场景缩放_初始"] = zoom0

        # ── 改「场景缩放」（视口视图态）
        out["改场景缩放"] = change_range(page, r0, "场景缩放", [0.3, 0.75, 0.15])
        r1 = page.evaluate(READ_RANGES)
        out["场景缩放_改后"] = pick_range(r1, "场景缩放")

        # ── 选机位1 → 改 FOV（场景参数）
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        fov0 = fov_read(page)
        out["FOV_初始"] = fov0
        if fov0:
            out["改FOV"] = change_range(page, page.evaluate(READ_RANGES), "FOV",
                                       [0.25, 0.8, 0.1], minv="15", maxv="90")
        else:
            out["改FOV"] = {"error": "没找到 FOV range"}
        out["FOV_改后"] = fov_read(page)

        # ── 关台 → 重开（同一页面会话内）
        out["关台返回"] = close_desk(page)
        out["重开返回"] = open_desk(page)
        r2 = page.evaluate(READ_RANGES)
        out["场景缩放_重开后"] = pick_range(r2, "场景缩放")
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out["FOV_重开后"] = fov_read(page)
        page.screenshot(path="/tmp/liblib_source_desk829_v2_reopen.png")

        # ── 刷新页面 → 再开台（跨会话）
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(12_000)
        out["刷新后开台返回"] = open_desk(page)
        r3 = page.evaluate(READ_RANGES)
        out["场景缩放_刷新后"] = pick_range(r3, "场景缩放")
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        out["FOV_刷新后"] = fov_read(page)
        page.screenshot(path="/tmp/liblib_source_desk829_v2_reload.png")

        # ── 恢复原值（别把测试项目改脏）
        if out.get("FOV_改后") and out.get("FOV_初始"):
            want = out["FOV_初始"]["value"]
            cur = out["FOV_刷新后"]
            if cur and cur["value"] != want:
                span = float(cur["max"]) - float(cur["min"])
                frac = (float(want) - float(cur["min"])) / span
                out["恢复FOV_动作"] = click_range(page, cur, max(0.0, min(1.0, frac)))
                out["FOV_恢复后"] = fov_read(page)

        ctx.close()
        br.close()


if __name__ == "__main__":
    main()

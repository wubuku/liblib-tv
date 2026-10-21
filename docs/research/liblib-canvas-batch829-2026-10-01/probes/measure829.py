#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 829 源站实测：导演台**关掉再打开**，参数留不留？

★ 回答 batch 599/604 留下的那条未观测项：「源站关闭再打开导演台时 zoom 是否保留」。
★ 测两类参数（它们在源站是**两种东西**）：
  ① **视口视图态**：场景缩放 / 平移 / 旋转（右栏「3D场景」页签）
  ② **场景参数**：机位 FOV（选中「机位1」后的属性面板，range 15–90）
★ 交互纪律：
  - 改值一律用**真实鼠标点/拖原生 range**（源站的 range 是 opacity:0 的透明原生控件，
    盖在自绘轨道上 —— 用户点的就是它）⟹ 产生真实 pointerdown/change ⟹ 不是后门。
  - ★ 不预测具体值：点完**读回实际值**（滑轨有效区与步进决定落点）。
  - ★ 不点任何生成/付费控件（底部「发送」「截图」「上传图片」一律不碰）。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk829_measure.json")
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
  const rows=Array.from(document.querySelectorAll('div,span,label,p,span'))
    .filter(e=>realVis(e)&&e.children.length===0&&txt(e).length>0&&txt(e).length<20)
    .map(e=>({t:txt(e),box:box(e)}));
  // 给每个 range 找**它上面最近**的那行文字当标签
  const out=[];
  for(const e of document.querySelectorAll('input[type=range]')){
    const b=box(e);
    let label=null;
    for(const r of rows){
      if(r.box.y+r.box.h<=b.y+2 && (!label || r.box.y>label.box.y)) label=r;
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

READ_CAM = """()=>{
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
  const fovRows=Array.from(document.querySelectorAll('*'))
    .filter(e=>e.children.length===0 && /FOV/i.test(txt(e)) && realVis(e))
    .map(e=>({t:txt(e),box:box(e)}));
  const ranges=Array.from(document.querySelectorAll('input[type=range]'))
    .filter(e=>e.min==='15'&&e.max==='90')
    .map(e=>({box:box(e),value:e.value,min:e.min,max:e.max,step:e.step}));
  const nameInputs=Array.from(document.querySelectorAll('input'))
    .filter(e=>e.type==='text'&&realVis(e))
    .map(e=>({v:e.value,box:box(e)}));
  return {fovRows, fovRanges:ranges, nameInputs:nameInputs.slice(0,6)};
}"""


def find_fov_range(page):
    """返回 FOV range 的（x, y, w, h, value）—— 从 15–90 那个 range 里挑。"""
    info = page.evaluate(READ_CAM)
    if not info["fovRanges"]:
        return None, info
    # 取 y 最小的那个（属性面板顶部那个 FOV）
    r = sorted(info["fovRanges"], key=lambda x: x["box"]["y"])[0]
    return r, info


def click_range(page, rng, frac):
    """在 range 轨道的 frac 位置**真实点击**（源站 range 是透明原生控件）。"""
    b = rng["box"]
    x = b["x"] + int(b["w"] * frac)
    y = b["y"] + b["h"] // 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.wait_for_timeout(120)
    page.mouse.up()
    page.wait_for_timeout(700)
    return {"clickedAt": [x, y], "frac": frac}


def open_desk(page):
    """开台：★ 先**悬停**节点卡（源站「打开导演台」是悬停才显形的：opacity-0 +
    pointer-events-none + group-hover:opacity-100），否则按钮被节点的缩略图挡住。"""
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    btn = page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first
    btn.click()
    page.wait_for_timeout(6_000)
    return page.evaluate(READ_DESK)



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

        # ── 开台
        out["开台返回"] = open_desk(page)
        out["开台后"] = {"desk": page.evaluate(READ_DESK),
                         "ranges": page.evaluate(READ_RANGES)}

        # ── 改「场景缩放」（视口视图态）
        zoom_before = None
        for r in out["开台后"]["ranges"]:
            if r["label"] and "场景缩放" in r["label"]:
                zoom_before = r
        if zoom_before:
            out["改缩放_动作"] = click_range(page, zoom_before, 0.7)
        out["改缩放后"] = page.evaluate(READ_RANGES)
        out["场景缩放_before"] = zoom_before
        out["场景缩放_after"] = next(
            (r for r in out["改缩放后"]
             if r["label"] and "场景缩放" in r["label"]), None)

        # ── 选机位1 → 改 FOV（场景参数）
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        fov_before, cam_info = find_fov_range(page)
        out["机位面板"] = cam_info
        if fov_before:
            out["改FOV_动作"] = click_range(page, fov_before, 0.7)
        fov_after, _ = find_fov_range(page)
        out["FOV_before"] = fov_before
        out["FOV_after"] = fov_after

        # ── 关台
        page.locator("[aria-label='关闭']:visible").first.click()
        page.wait_for_timeout(3_000)
        out["关台后"] = page.evaluate(READ_DESK)
        page.screenshot(path="/tmp/liblib_source_desk829_closed.png")

        # ── 重开
        out["重开返回"] = open_desk(page)
        out["重开后"] = {"desk": page.evaluate(READ_DESK),
                         "ranges": page.evaluate(READ_RANGES)}
        out["场景缩放_重开后"] = next(
            (r for r in out["重开后"]["ranges"]
             if r["label"] and "场景缩放" in r["label"]), None)
        page.locator("text=机位1").first.click()
        page.wait_for_timeout(2_500)
        fov_reopen, _ = find_fov_range(page)
        out["FOV_重开后"] = fov_reopen
        page.screenshot(path="/tmp/liblib_source_desk829_reopened.png")

        ctx.close()
        br.close()
    print(json.dumps(out, ensure_ascii=False, indent=1)[:3500])


if __name__ == "__main__":
    main()

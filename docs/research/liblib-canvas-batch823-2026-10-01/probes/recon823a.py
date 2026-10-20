#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 823 侦察 —— 把「读数字段名」和「真实入口」查对

★ 上一版探针栽在两处**读数/匹配写错**上（809/810/821 的老坑：
  **读数对不上时先怀疑自己的动作与读数**）：
  ① `RO()` 读 `S.nodes` ⟹ 得到 0，而 DOM 上明明有节点
  ② 匹配时间轴行时拿**轨道 id** 去比**对象 id** ⟹ 匹配失败、根本没点
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

KEYS = """()=>{const S=window.__libtv_store.getState();
  const out={};
  for(const k of Object.keys(S)){
    const v=S[k];
    if(Array.isArray(v))out[k]='array['+v.length+']';
    else if(v&&typeof v==='object')out[k]='object{'+Object.keys(v).slice(0,12).join(',')+'}';
    else if(typeof v==='function')out[k]='fn';
    else out[k]=String(v).slice(0,40);}
  return out;}"""

DKEYS = """()=>{const S=window.__director_store.getState();
  const out={};
  for(const k of Object.keys(S)){
    const v=S[k];
    if(Array.isArray(v))out[k]='array['+v.length+']';
    else if(v&&typeof v==='object')out[k]='object{'+Object.keys(v).slice(0,14).join(',')+'}';
    else if(typeof v==='function')out[k]='fn';
    else out[k]=String(v).slice(0,40);}
  return out;}"""

# ★ 找「添加节点」的真实入口：把**所有**带 data- 的可点元素连同其
#   data 属性一起列出来（不猜标记名，先看事实）
DUMP = """()=>{const out=[];
  for(const e of Array.from(document.querySelectorAll('*'))){
    const attrs=Array.from(e.attributes).filter(a=>a.name.startsWith('data-'));
    if(!attrs.length)continue;
    const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)continue;
    out.push({tag:e.tagName,
      data:attrs.map(a=>a.name+'='+a.value).join(' '),
      text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,30),
      aria:e.getAttribute('aria-label')||'',
      title:e.getAttribute('title')||'',
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)}});}
  return out;}"""


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        pg = br.new_page()
        pg.set_default_timeout(25000)
        pg.goto(A.BASE, wait_until="domcontentloaded")
        pg.wait_for_timeout(3000)
        print("═══ 画布 store 顶层键 ═══")
        print(json.dumps(pg.evaluate(KEYS), ensure_ascii=False, indent=1)[:2600])
        print()
        print("═══ 画布上所有带 data- 的可见元素（前 60）═══")
        for d in pg.evaluate(DUMP)[:60]:
            print("  %-6s %-46s %-22s %s" % (
                d["tag"], d["data"][:46], (d["aria"] or d["title"])[:22],
                d["rect"]))
        # 打开导演台，再 dump 导演台的 data- 元素
        btn = pg.query_selector("[data-open-director]")
        if btn:
            btn.click()
        pg.wait_for_timeout(4000)
        print()
        print("═══ 导演台 store 顶层键 ═══")
        print(json.dumps(pg.evaluate(DKEYS), ensure_ascii=False, indent=1)[:1800])
        print()
        print("═══ 导演台里带 track / follow / lock / preset 的 data- 元素 ═══")
        for d in pg.evaluate(DUMP):
            s = d["data"]
            if any(k in s for k in ("track", "follow", "lock", "preset",
                                    "timeline", "object-row")):
                print("  %-6s %-58s %-20s %s" % (
                    d["tag"], s[:58], (d["aria"] or d["title"])[:20], d["rect"]))
        br.close()


if __name__ == "__main__":
    main()

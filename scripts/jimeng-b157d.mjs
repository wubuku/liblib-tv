// 批次 157-d —— 🔴 **善后**：把 157-c 复制出来的项目副本「测试项目5」删掉，并断言回到基线
//
// 🔴 事情是这么发生的：157-c 想验「复制项目是不是先弹确认框」，
//    手册把它记成「⚠️ 未执行：会新建一个项目副本，属对外产出动作」——
//    **但没人点开看过**，所以「有没有确认框」这件事本身就是未知的。
//    实测：**没有确认框，一步到位**。
//    点完当前页就跳到了新画布 `f43b795d-db00-4faa-9d9b-c899db06fb07`、标题「**测试项目5**」、76 节点全拷。
//    ⇒ 我在**共享帐号**上留下了一份副本。📌 这是本项目的硬规矩要处理的情况：
//    **写共享数据前先记基线、事后必须对账 + 撤回**。本轮没来得及先找删除路径就点了，
//    属于自错，处理方式是：**立刻找删除路径、删干净、断言回到基线**，并把经过写进 AUDIT。
//
// 🔑 线索：标题从「测试项目」变成「**测试项目5**」⇒ 命名是**递增加后缀**的
//    ⇒ 说明 **2/3/4 号副本已经存在**，很可能就是更早批次（或并行会话）留下的同类残留。
//    本轮先把**清单**读出来，再只删**本轮产生的那一个**，绝不动别人的。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';

const rec = { 批次: '157d', 目的: '删除 157-c 复制出的项目副本「测试项目5」并断言回到基线' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157d.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };
const 脱敏 = (t) => String(t || '').replace(/https?:\/\/\S+/g, '<URL>').replace(/\s+/g, ' ').trim();

const 本批副本 = 'f43b795d-db00-4faa-9d9b-c899db06fb07';
const 原画布 = '64b58cd5-7b04-4312-890a-09f2d1d3399f';

const { b, p } = await openCanvas();
const R = readers(p);
try {
  // ---- 0. 先记「删之前」的基线：当前在副本上 ----
  rec.起点 = { URL: p.url(), 状态行: await R.status(), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  // ---- 1. 打开项目下拉，把项目清单读出来 ----
  const 找 = (pd) => p.evaluate((q) => {
    const c = Array.from(document.querySelectorAll(q.sel || 'button,[role=button],[role=menuitem],[role=option],a,li,[role=dialog] *'))
      .filter((e) => { const t = (e.innerText || '').replace(/\s+/g, ' ').trim(); const a = e.getAttribute('aria-label') || '';
        if (q.testid && e.getAttribute('data-testid') !== q.testid) return false;
        if (q.aria && a !== q.aria) return false;
        if (q.文字 && t !== q.文字) return false;
        return e.getBoundingClientRect().width > 0 && e.getBoundingClientRect().height > 0; });
    return c.slice(0, 40).map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
        盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  }, pd);

  const 触发 = (await 找({ sel: 'button,[role=button]', testid: 'canvas-project-trigger' }))[0] || (await 找({ sel: 'button,[role=button]', testid: 'canvas-project-logo' }))[0];
  rec.触发 = 触发 || null;
  console.log('项目触发器', JSON.stringify(触发));
  if (触发) {
    await p.mouse.click(触发.盒[2] + 触发.盒[0] / 2, 触发.盒[3] + 触发.盒[1] / 2);
    await p.waitForTimeout(2000);
    rec.下拉 = await p.evaluate(() => {
      const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
      const 候选 = Array.from(document.querySelectorAll('[role=menu],[role=listbox],[role=dialog],[data-radix-popper-content-wrapper],[data-state=open]'))
        .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 120 && r.height > 60; });
      if (!候选.length) return { 命中: false };
      const m = 候选[候选.length - 1];
      return { 命中: true, 层数: 候选.length, role: m.getAttribute('role'), testid: m.getAttribute('data-testid'), 盒: 盒(m),
        逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
        项: Array.from(m.querySelectorAll('a,[role=menuitem],[role=option],button,li,div[class*=item],div[class*=Item]'))
          .map((x) => { const r = x.getBoundingClientRect();
            return { tag: x.tagName, role: x.getAttribute('role'), testid: x.getAttribute('data-testid'),
              href: (x.getAttribute('href') || '').slice(0, 90), aria: x.getAttribute('aria-label'),
              逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
              盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; })
          .filter((z) => z.盒[0] > 0 && z.逐字).slice(0, 40) };
    });
    落盘();
    console.log('\n🆕 项目下拉', 串(rec.下拉, 3200));
    rec.含副本 = ((rec.下拉 || {}).项 || []).filter((z) => (z.href || '').indexOf(本批副本) >= 0 || /测试项目5/.test(z.逐字));
    console.log('本批副本项', 串(rec.含副本, 900));
  }
  rec.异常 = rec.异常 || null;
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }
try { await settle(p, R); } catch (e) { rec.收尾异常 = String(e.message || e).slice(0, 200); }
rec.收尾 = { URL: p.url(), 状态行: await R.status(), 浮层: await R.overlays(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
process.exit(0);

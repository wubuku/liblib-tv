// 批次 157-f —— 逐个试顶栏「项目」一族 testid，找出真正能打开项目切换器的那个
//
// 🔴 157-e 的结果：`canvas-project-trigger`（实测 `20×28@128,16`）点它的中心**毫无反应**
//    —— 点前点后可见浮层都是 0。它只是个 20px 宽的壳（`canvas-project-launcher-shell` 也在同一处）。
//    📌 **testid 叫 trigger 不等于它就是能点开的那个**。
//    156-l 记下的同族还有：`canvas-project-logo` `40×40@12,10`、
//    `canvas-project-title-trigger` `68×28@52,16`（项目名本身，最像入口）。
//    本轮逐个试，每次都判「点开没有」并把落点归属读出来。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';

const rec = { 批次: '157f', 目的: '找出真正能打开项目切换器的那个 testid' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157f.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };

const { b, p } = await openCanvas();
const R = readers(p);

const 候选 = ['canvas-project-title-trigger', 'canvas-project-trigger', 'canvas-project-launcher-shell', 'canvas-project-logo', 'canvas-workspace-title', 'canvas-project-logo-gradient-path'];
const 计数 = () => p.evaluate(() => Array.from(document.querySelectorAll('[data-state=open],[role=menu],[role=listbox],[role=dialog],[data-radix-popper-content-wrapper]'))
  .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length);
const dump = () => p.evaluate(() => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const 可见 = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const 层 = Array.from(document.querySelectorAll('[data-state=open],[role=menu],[role=listbox],[role=dialog],[data-radix-popper-content-wrapper]'))
    .filter(可见).filter((x) => x.getBoundingClientRect().width > 80);
  return { 层数: 层.length, 层: 层.map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
      cls: (e.className || '').toString().slice(0, 60), 盒: 盒(e), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400) })),
    链接: Array.from(document.querySelectorAll('a[href]')).filter(可见).map((e) => ({ href: e.getAttribute('href'),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), 盒: 盒(e) })) };
});

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1000);
  rec.起点 = { URL: p.url(), 状态行: await R.status(), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));
  rec.基线层数 = await 计数();
  rec.尝试 = [];

  for (const id of 候选) {
    const t = await p.evaluate((q) => { const e = document.querySelector('[data-testid="' + q + '"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) return { 无面积: true };
      const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy);
      return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], x: cx, y: cy,
        中心tag: h ? h.tagName : null, 中心testid: h ? h.getAttribute('data-testid') : null,
        中心是它自己: !!(h && (h === e || h.closest('[data-testid="' + q + '"]') || e.contains(h))) }; }, id);
    const rec1 = { testid: id, 读数: t };
    if (t && !t.无面积 && t.x != null) {
      await p.mouse.click(t.x, t.y); await p.waitForTimeout(1900);
      rec1.点后层数 = await 计数();
      rec1.点后 = await dump();
      rec1.开开了 = rec1.点后层数 > (rec1.前层数 || rec.基线层数);
      rec1.前层数 = rec.基线层数;
      for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
      rec.基线层数 = await 计数();
    }
    rec.尝试.push(rec1);
    落盘();
    console.log(`\n【${id}】`, JSON.stringify(t), '| 点后层数', rec1.点后层数, '| 开开了', rec1.开开了);
    if (rec1.开开了) {
      console.log('层', 串(rec1.点后.层, 2200));
      console.log('链接', 串(rec1.点后.链接, 1600));
      rec.命中 = id; rec.命中层 = rec1.点后.层; rec.命中链接 = rec1.点后.链接;
      break;
    }
  }
  断言('① 五个「项目」族 testid 里至少有一个能打开浮层', !!rec.命中,
    { 尝试: rec.尝试.map((z) => ({ id: z.testid, 点后层数: z.点后层数 })) });
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }
try { await settle(p, R); } catch (e) { rec.收尾异常 = String(e.message || e).slice(0, 200); }
rec.收尾 = { URL: p.url(), 浮层: await R.overlays(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
process.exit(0);

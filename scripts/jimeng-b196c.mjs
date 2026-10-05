// 批次 196 c 轮：那两条 `jimeng-b195-test.mp4: Upload complete` 到底**在哪个容器里**？
//
// a 轮扫全页找到了这两个 SPAN，b 轮扫资产库 dialog 却**一条都没有**
// ⇒ 🔴 「页面上有这串字」**不等于**「它在资产库里」。
//   a 轮的扫描是 `document.querySelectorAll('*')`，**没有限定范围**；
//   手册 assets-and-upload.md:397-402 那条「画布上传不进资产库」**很可能仍然成立**
//   —— 我差点推翻一条正确的记录。
//
// 本轮：打印那两个 SPAN 的**祖先链**（每层的 tag / role / data-testid / aria / 屏上矩形），
//   定位它真正属于哪个面板。顺带把「左栏上传区」的结构读出来
//   （手册此前只记了左栏有「资产库」「上传」两个 40×40 入口，没记上传队列）。
import fs from 'node:fs';
import { openCanvas, readers, settle, endState } from './jimeng-b135-lib.mjs';

const MINE = ['jimeng-b195-test.mp4', 'jimeng-b195b-test.mp4'];
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b196c', 找的: MINE };

const 定位 = async (标签) => {
  const r = await p.evaluate((ns) => {
    const hits = [];
    for (const n of document.querySelectorAll('*')) {
      const txt = (n.innerText || '').trim();
      if (txt.length > 120 || !n.matches('span,div,p')) continue;
      if (!ns.some((x) => txt === x)) continue;
      const 链 = []; let e = n;
      for (let k = 0; k < 12 && e && e !== document.body; k++) {
        const b = e.getBoundingClientRect();
        链.push({ 层: k, tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
          aria: e.getAttribute('aria-label'), cls: (e.className || '').toString().slice(0, 70),
          屏上: [b.x, b.y, b.width, b.height].map((z) => Math.round(z * 100) / 100),
          文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90) });
        e = e.parentElement;
      }
      hits.push({ 文字: txt, 祖先链: 链 });
    }
    return hits;
  }, MINE);
  log(`【${标签}】命中 ${r.length} 处`);
  for (const h of r) { log('  ▸', h.文字); for (const l of h.祖先链) log(`     L${l.层} ${l.tag}${l.role ? '[role=' + l.role + ']' : ''}${l.testid ? '[testid=' + l.testid + ']' : ''}${l.aria ? '[aria=' + l.aria + ']' : ''} @${JSON.stringify(l.屏上)} :: ${l.文字}`); }
  return r;
};

// —— 状态 ①：什么都没开 ——
out.裸页面 = await 定位('裸页面（什么都没打开）');

// —— 状态 ②：打开资产库 dialog ——
const 入口 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
  .find((x) => (x.getAttribute('aria-label') || '') === '资产库' && x.getBoundingClientRect().width > 0);
  if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
if (入口) { await p.mouse.click(入口[0], 入口[1]); await p.waitForTimeout(2000); }
out.开资产库后 = await 定位('打开资产库 dialog 之后');
out.资产库文本 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  return d ? d.innerText.replace(/\s+/g, ' ').trim().slice(0, 260) : null; });
log('资产库文本：', out.资产库文本);
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);

// —— 状态 ③：悬停左栏（手册说左栏入口「悬停可见文字标签」）——
const 左栏 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
  .find((x) => (x.getAttribute('aria-label') || '') === '上传' && x.getBoundingClientRect().width > 0);
  if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
if (左栏) { await p.mouse.move(左栏[0], 左栏[1]); await p.waitForTimeout(1400); }
out.悬停左栏后 = await 定位('悬停左栏「上传」之后');

// —— 左栏区域的完整结构（不限定字符串，直接扫左栏那一列）——
out.左栏结构 = await p.evaluate(() => {
  const 盒 = Array.from(document.querySelectorAll('button,[role="button"],div,span'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { e, r }; })
    .filter((x) => x.r.width > 0 && x.r.height > 0 && x.r.x < 70 && x.r.y > 400 && x.r.y < 720);
  return 盒.slice(-40).map(({ e, r }) => ({ tag: e.tagName, aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
    cls: (e.className || '').toString().slice(0, 50), 屏上: [r.x, r.y, r.width, r.height].map(Math.round),
    文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70) }));
});
log('左栏结构（x<70 且 y 400-720，末 40 个）：');
for (const s of out.左栏结构) log(`   ${s.tag}${s.aria ? '[aria=' + s.aria + ']' : ''}${s.testid ? '[testid=' + s.testid + ']' : ''} @${JSON.stringify(s.屏上)} :: ${s.文字}`);

fs.writeFileSync('/tmp/b196c.json', JSON.stringify(out, null, 1));
await p.mouse.move(1276, 716);
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();

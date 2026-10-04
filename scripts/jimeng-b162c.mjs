// 批次 162-c —— 查清 `[data-testid="node-toolbar"]` 到底是什么
//
// 🔑 起因：批次 160-e 与 162-a 两次都「用 `node-toolbar` 读到了一个 680×2xx、
//    内容是底部生成面板（Seedream 5.0 Lite / 全能配音…）、`closest('.react-flow__node')`
//    为 `null`」的元素。而 `20-reference.md:1752` 明明白白写着底部面板的真 testid 是
//    **`generation-form`**（图片 `680×208`，7 项）。⇒ 两个 testid 指向**同一个盒子**？
//    还是我两次都读错了元素？本轮把页面上所有相关 testid **一次列全**，对齐盒子与归属。
//
// 🔴 建-删护栏同前；⛔ 不点任何生成/提交按钮。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '162c', 目的: '列全 node-toolbar / generation-form 等 testid 的盒子与归属' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b162c.json', import.meta.url), JSON.stringify(rec, null, 1));

const 列出 = () => p.evaluate(() => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const 条 = [];
  for (const e of document.querySelectorAll('[data-testid]')) {
    const t = e.getAttribute('data-testid') || '';
    if (!/toolbar|generation|node-toolbar|panel/i.test(t)) continue;
    const 挂 = e.closest('.react-flow__node');
    条.push({ testid: t, tag: e.tagName, 盒: 盒(e),
      挂在节点id: 挂 ? 挂.getAttribute('data-id') : null,
      子testid: [...new Set(Array.from(e.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')))].slice(0, 8),
      按钮数: e.querySelectorAll('button,[role=button]').length,
      前四个按钮: Array.from(e.querySelectorAll('button,[role=button]')).slice(0, 4).map((b) => b.getAttribute('aria-label')),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70) });
  }
  return { 总数: 条.length, 条, 选中数: document.querySelectorAll('.react-flow__node.selected').length };
});

const { b, p } = await openCanvas();
const R = readers(p);
let SELF = null;

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  rec.未选中时 = await 列出();
  console.log('未选中时命中 =', rec.未选中时.总数, JSON.stringify(rec.未选中时.条.map((z) => z.testid)));
  落盘();

  const 图钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]')).find((x) => (x.getAttribute('aria-label') || '') === '图片'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(图钮[0], 图钮[1]);
  await p.waitForTimeout(4200);
  const 建后 = await idsOf(p);
  const 差 = 建后.filter((x) => !建前.includes(x));
  SELF = 差.length === 1 ? 差[0] : null;
  rec.建后 = { 差集: 差, SELF, 选中: await selCount(p), 积分: await R.credits(), 缩放: await R.zoom() };
  落盘();
  console.log('建后 =', JSON.stringify(rec.建后));
  断言('⓪ 建出一个图片节点、选中、积分不变', SELF != null && rec.建后.选中 === 1 && rec.建后.积分 === rec.起点.积分, rec.建后);

  rec.选中后 = await 列出();
  console.log('选中后命中 =', rec.选中后.总数);
  for (const z of rec.选中后.条) console.log('  ', z.testid, JSON.stringify(z.盒), '挂节点=', z.挂在节点id, '按钮=', z.按钮数, JSON.stringify(z.前四个按钮));
  落盘();

  // 关键对比：`node-toolbar` 与 `generation-form` 是不是同一个盒子
  const nt = rec.选中后.条.find((z) => z.testid === 'node-toolbar');
  const gf = rec.选中后.条.find((z) => z.testid === 'generation-form');
  rec.对比 = { node_toolbar: nt || null, generation_form: gf || null,
    是同一个盒子: !!(nt && gf && JSON.stringify(nt.盒) === JSON.stringify(gf.盒)),
    node_toolbar挂在节点上: nt ? nt.挂在节点id != null : null,
    node_toolbar有按钮: nt ? nt.按钮数 : null };
  console.log('对比 =', JSON.stringify(rec.对比, null, 1));
  落盘();
  断言('① 页面上**确实存在** `node-toolbar` 这个 testid', !!nt, { testid列表: rec.选中后.条.map((z) => z.testid) });
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// 收尾
try {
  if (SELF) {
    const 落 = await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return null;
      const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, SELF);
    if (落) {
      await p.mouse.click(落[0], 落[1]); await p.waitForTimeout(1400);
      await p.mouse.click(落[0], 落[1], { button: 'right' }); await p.waitForTimeout(1700);
      const del = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-context-menu"]'); if (!d) return { 错: 'no-menu' };
        const it = Array.from(d.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim().startsWith('删除')); if (!it) return { 错: 'no-删除项' };
        const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      rec.删除落点 = del;
      if (del && !del.错) { await p.mouse.click(del[0], del[1]); await p.waitForTimeout(2400); }
    }
    for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  }
} catch (e) { rec.删异常 = String((e && e.stack) || e).slice(0, 600); 落盘(); }
try { await settle(p, R); } catch (e) {}
try { await setZoom(p, 60); await p.waitForTimeout(1200); } catch (e) {}
try {
  const mm = await R.minimap();
  if (!mm || mm.ariaPressed !== 'true') {
    const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1400); }
  }
} catch (e) {}
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾));
断言('② 收尾回到基线：76 / 0 选中 / 0 浮层 / 60% / 积分不变',
  rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && /60%/.test(String(rec.收尾.zoom)) && String(rec.收尾.积分) === String((rec.起点 || {}).积分),
  { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);

// 批次 162-b —— 干净复测「空图片节点」尺寸：**量之前先读缩放，量完再读一次**
//
// 🔴 162-a 的教训：它先开了资产库（已知会把缩放从 60% 改成 57%），
//    然后才建节点、才量尺寸 —— 而**量的时候没有记录缩放**，
//    页面里也没有 `.react-flow__transform` 可反推（react-flow 新版走 CSS 变量）。
//    ⇒ 182×182 这个屏上读数**无法换算成 canvas 尺寸**，那一批的推算是无效的。
//    📌 立规 33：**任何「屏上尺寸 ÷ 缩放 = canvas 尺寸」的换算，
//      必须在量的那一刻把缩放一起读下来**；读不到就不报数，只报屏上值并写明缩放未知。
//
// 🔴 顺带修掉 162-a 的收尾缺陷：它只断言了节点数/选中/浮层/积分，**没断言缩放**，
//    于是「点开资产库把 60% 改成 57%」这个**已知副作用**溜过去了。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf } from './jimeng-b139-lib.mjs';

const rec = { 批次: '162b', 目的: '带缩放记录地复测空图片节点尺寸' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b162b.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

const 读缩放 = async () => {
  const aria = await R.zoom();
  const 数值 = parseInt(String(aria).match(/(\d+)%/)?.[1] || '0', 10);
  const 视口 = await p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
    if (!v) return null; const s = getComputedStyle(v);
    return { transform: s.transform, zoomVar: s.getPropertyValue('--xy-flow-zoom') || s.getPropertyValue('zoom') || null }; });
  const 从transform = 视口?.transform ? (String(视口.transform).match(/matrix\(([^,]+)/)?.[1]) : null;
  return { aria, 数值, viewportTransform: 视口?.transform || null, transform里的缩放: 从transform ? Number(从transform) : null };
};

const { b, p } = await openCanvas();
const R = readers(p);
let SELF = null;

try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1500);
  const 建前 = await idsOf(p);
  rec.起点 = { 状态行: await R.status(), 节点数: 建前.length, 选中: await selCount(p), 积分: await R.credits() };
  rec.起点缩放 = await 读缩放();
  console.log('起点缩放 =', JSON.stringify(rec.起点缩放));

  const 图钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '图片'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await p.mouse.click(图钮[0], 图钮[1]);
  await p.waitForTimeout(3600);
  const 建后 = await idsOf(p);
  const 差 = 建后.filter((x) => !建前.includes(x));
  SELF = 差.length === 1 ? 差[0] : null;
  rec.建后 = { 数: 建后.length, 差集: 差, SELF, 选中: await selCount(p), 积分: await R.credits() };
  落盘();
  console.log('建后 =', JSON.stringify(rec.建后));
  断言('⓪ 差集恰好 1、新节点选中、积分不变', SELF != null && 差.length === 1 && rec.建后.选中 === 1 && rec.建后.积分 === rec.起点.积分, rec.建后);

  if (SELF) {
    await p.waitForTimeout(2400);
    // 🔴 **量的这一刻把缩放读下来**
    rec.量时缩放 = await 读缩放();
    rec.节点 = await p.evaluate((id) => {
      const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return { 不在: true };
      const r = n.getBoundingClientRect();
      const 空 = n.querySelector('[data-testid="image-node-empty"]');
      const 描边 = n.querySelector('[data-testid="flow-node-media-stroke"]');
      const 标题 = n.querySelector('[data-testid="flow-node-title"]');
      const 盒 = (e) => { if (!e) return null; const q = e.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)]; };
      return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
        className: n.className,
        空态盒: 盒(空), 描边盒: 盒(描边), 标题盒: 盒(标题),
        内部testid: [...new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))],
        img数: n.querySelectorAll('img').length, video数: n.querySelectorAll('video').length };
    }, SELF);
    console.log('量时缩放 =', JSON.stringify(rec.量时缩放));
    console.log('节点 =', JSON.stringify(rec.节点).slice(0, 600));
    落盘();

    const 缩放值 = rec.量时缩放.transform里的缩放 || rec.量时缩放.数值 / 100 || null;
    rec.换算 = 缩放值 ? {
      用的缩放: 缩放值,
      canvas宽: Math.round(rec.节点.盒[0] / 缩放值),
      canvas高: Math.round(rec.节点.盒[1] / 缩放值),
      宽是否整除: rec.节点.盒[0] / 缩放值,
    } : null;
    console.log('换算 =', JSON.stringify(rec.换算));
    断言('① **量的时候读到了缩放**（否则 canvas 尺寸不可换算）', !!rec.换算, { 量时缩放: rec.量时缩放 });
    落盘();

    await p.evaluate((id) => { const n = document.querySelector('.react-flow__node[data-id="' + id + '"]'); if (!n) return false;
      const r = n.getBoundingClientRect(); const ov = document.createElement('div'); ov.id = '__hl__';
      ov.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;border:3px solid rgb(255,146,48);border-radius:10px;box-sizing:border-box;left:' + (r.x - 4) + 'px;top:' + (r.y - 4) + 'px;width:' + (r.width + 8) + 'px;height:' + (r.height + 8) + 'px;';
      document.body.appendChild(ov); return true; }, SELF);
    await p.waitForTimeout(600);
    await p.screenshot({ path: new URL('./122-empty-image-node.png', 出图).pathname });
    rec.图 = 'screenshots/122-empty-image-node.png';
    await p.evaluate(() => { const e = document.getElementById('__hl__'); if (e) e.remove(); return true; });
    console.log('🖼 已拍 122');
    落盘();
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

// 收尾：删节点 → **显式把缩放归位到 60%** → 断言里**带上缩放**
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
try { await setZoom(p, 60); await p.waitForTimeout(1200); } catch (e) { rec.归位缩放异常 = String(e.message || e).slice(0, 200); }
try {
  const mm = await R.minimap();
  if (!mm || mm.ariaPressed !== 'true') {
    const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (t) { await p.mouse.click(t[0], t[1]); await p.waitForTimeout(1400); }
  }
} catch (e) {}
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits() };
rec.SELF = SELF;
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾));
断言('② 收尾回到基线：76 节点 / 0 选中 / 0 浮层 / **60%** / 积分不变',
  rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0 && /60%/.test(String(rec.收尾.zoom)) && String(rec.收尾.积分) === String((rec.起点 || {}).积分),
  { 起点: rec.起点, 收尾: rec.收尾 });
rec.断言全过 = 断言过; 落盘();
console.log('断言全过 =', rec.断言全过);
process.exit(0);

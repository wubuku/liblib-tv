// 批次 173 b 轮：核「视频 / 图片 尺寸面板渲染在 node-toolbar 内还是外」。
//
// 手册 `prepare-generation.md` 的表逐字写着：
//   视频「视频尺寸选项」渲染在 `node-toolbar` **外部**（浮在画布上方）
//   图片「图片尺寸选项」渲染在 `node-toolbar` **内部**
// 而 173 a 轮量到视频侧 `e.closest('[data-testid="node-toolbar"]') === true`（**在内**）
// ⇒ 与手册相反。⚠️ 但批次 162 记过「`node-toolbar` 这个 testid **被复用：页面同时存在两个实例**」，
//    所以必须把**祖先链逐层打出来**（谁 → 谁 → 面板），并**两侧用同一套代码**比，
//    否则又是「量了不同的东西」。
//
// 两侧各建一个临时节点、按 id 删、按 id 验（立规 44）。
// ⛔ 只打开看，不点任何选项、不点生成。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '173b' };

const 关浮层 = async () => {
  for (let i = 0; i < 4; i++) {
    const st = await p.evaluate(() => ({ sidecar: !!document.querySelector('aside[aria="Agent"]'),
      menu: !!document.querySelector('[data-testid="canvas-context-menu"]') }));
    if (!st.sidecar && !st.menu) break;
    if (st.sidecar) {
      const c = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('aside[aria="Agent"] button,[role=button]'))
          .find((x) => (x.getAttribute('aria-label') || '') === '收起');
        if (!e) return null; const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      if (c) { await p.mouse.click(c[0], c[1]); await p.waitForTimeout(700); continue; }
    }
    await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  }
};
await 关浮层();

/** 打开某一侧（视频/图片）的尺寸面板，返回祖先链 + 关键属性。 */
const 打开 = async (哪) => {
  const 前 = await p.evaluate((k) => document.querySelectorAll(k).length, `.react-flow__node-${哪}`);
  const 钮 = await p.evaluate((名) => {
    const e = Array.from(document.querySelectorAll('button,[role=button]'))
      .find((x) => (x.getAttribute('aria-label') || '') === 名 && !x.closest('.react-flow__node'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 哪);
  if (!钮) return { 失败: '没有左栏按钮' };
  await p.mouse.click(钮[0], 钮[1]);
  await p.waitForTimeout(3500);
  const 新id = await p.evaluate(([k, n0]) => {
    const ids = Array.from(document.querySelectorAll(k)).map((x) => x.getAttribute('data-id'));
    return ids.length > n0 ? ids[ids.length - 1] : null; }, [`.react-flow__node-${哪}`, 前]);
  const 前缀 = '图片尺寸选项', 视频 = 哪 === '视频';
  const 尺钮 = await p.evaluate(([pfx, v]) => {
    const e = Array.from(document.querySelectorAll('button,[role=button]'))
      .find((x) => { const a = x.getAttribute('aria-label') || ''; return v ? /^视频尺寸选项/.test(a) : /^图片尺寸选项/.test(a); });
    if (!e) return null; const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  }, [前缀, 视频]);
  if (!尺钮) return { 失败: '参数行里没有尺寸按钮', 新id };
  await p.mouse.click(尺钮.pt[0], 尺钮.pt[1]);
  await p.waitForTimeout(1300);
  const 读 = await p.evaluate((v) => {
    const e = Array.from(document.querySelectorAll('[role=dialog]'))
      .find((x) => (v ? /^视频尺寸选项/ : /^图片尺寸选项/).test(x.getAttribute('aria-label') || ''));
    if (!e) return null;
    const 链 = [];
    for (let n = e; n && n !== document.body && 链.length < 10; n = n.parentElement) {
      const r = n.getBoundingClientRect();
      链.push({ tag: n.tagName, testid: n.getAttribute('data-testid'), role: n.getAttribute('role'),
        aria: n.getAttribute('aria-label'),
        cls前60: (n.getAttribute('class') || '').split(/\s+/).slice(0, 3).join(' '),
        盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] });
    }
    // 全页有几个 node-toolbar 实例？面板挂在哪一个上（按矩形匹配）？
    const r = e.getBoundingClientRect();
    const tbs = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((t) => {
      const q = t.getBoundingClientRect();
      return { 盒: [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)],
        含面板: !!t.contains(e),
        矩形相交: !(q.right < r.left || q.left > r.right || q.bottom < r.top || q.top > r.bottom) };
    });
    const cs = getComputedStyle(e);
    return { 链, 'node-toolbar实例数': tbs.length, tbs,
      在closest内: !!e.closest('[data-testid="node-toolbar"]'),
      computed: { w: cs.width, maxW: cs.maxWidth, pos: cs.position, left: cs.left, transform: cs.transform },
      style: e.getAttribute('style'),
      class: e.getAttribute('class') };
  }, 视频);
  return { 新id, 尺钮, 读 };
};

const 删掉 = async (id) => {
  if (!id) return { 跳过: '没有临时节点' };
  await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.scrollIntoView({ block: 'center', inline: 'center' }), id);
  await p.waitForTimeout(700);
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  if (pt) { await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1000); }
  const d = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
      .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (d) { await p.mouse.click(d[0], d[1]); await p.waitForTimeout(2000); }
  const 验 = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), id);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  return { 目标还在: 验, status: await R.status() };
};

rec.基线 = { status: await R.status(), credits: await R.credits() };
console.log('基线:', JSON.stringify(rec.基线));

rec.视频 = await 打开('视频');
console.log('\n=== 视频侧 ===');
if (rec.视频.读) {
  const d = rec.视频.读;
  console.log('node-toolbar 实例数:', d['node-toolbar实例数'], '| closest 命中:', d['在closest内']);
  console.log('各实例:', JSON.stringify(d.tbs));
  console.log('computed:', JSON.stringify(d.computed));
  console.log('祖先链（自下而上）:');
  d.链.forEach((n, i) => console.log(`  ${i} ${n.tag}${n.testid ? '[' + n.testid + ']' : ''}${n.role ? ' role=' + n.role : ''} ${JSON.stringify(n.盒)}  ${n.cls前60}`));
} else console.log('失败:', rec.视频.失败 || '没读到');
rec.删视频 = await 删掉(rec.视频.新id);
console.log('删视频:', JSON.stringify(rec.删视频));
await 关浮层();

rec.图片 = await 打开('图片');
console.log('\n=== 图片侧 ===');
if (rec.图片.读) {
  const d = rec.图片.读;
  console.log('node-toolbar 实例数:', d['node-toolbar实例数'], '| closest 命中:', d['在closest内']);
  console.log('各实例:', JSON.stringify(d.tbs));
  console.log('computed:', JSON.stringify(d.computed));
  console.log('祖先链（自下而上）:');
  d.链.forEach((n, i) => console.log(`  ${i} ${n.tag}${n.testid ? '[' + n.testid + ']' : ''}${n.role ? ' role=' + n.role : ''} ${JSON.stringify(n.盒)}  ${n.cls前60}`));
} else console.log('失败:', rec.图片.失败 || '没读到');
rec.删图片 = await 删掉(rec.图片.新id);
console.log('删图片:', JSON.stringify(rec.删图片));
await 关浮层();

const bp = await p.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
if (bp) { await p.mouse.click(bp[0], bp[1]); await p.waitForTimeout(500); }
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
rec.收尾 = { status: await R.status(), sel: await R.selCount(), credits: await R.credits() };
console.log('\n收尾:', JSON.stringify(rec.收尾));
fs.writeFileSync(new URL('./_tmp-b173b.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();

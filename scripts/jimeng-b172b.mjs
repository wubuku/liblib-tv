// 批次 172 b 轮：打开「生成尺寸面板」`max-w-canvas-generation-size-panel-viewport`。
//
// 路线（按批次 134 的护栏）：左栏「文本」→ **建一个**文本节点 → 生成面板自动展开
//   → 点「比例 / 分辨率」下拉。⛔ 只打开看，**不点任何选项**（改分辨率会改参数状态）、
//   **不点生成**；量完把节点删掉，画布回到 76。
//
// 为什么必须新建：a 轮实测**选中已有的「文本 1」不会展开生成面板**
//   （可点元素里只有缩放把手 / Rename / Add tags，**没有比例分辨率按钮**）
//   ⇒ 生成面板是「空节点 / 新建节点」态才有的（与批次 134 的结论一致）。
//
// 立规 43 复用：**先在 1280 下打开面板，再只改视口**读夹取，不要在窄视口里重走交互。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url).pathname;
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '172b' };

const pin = async (w, h) => {
  await p.context().newCDPSession(p).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await p.waitForTimeout(600);
  const vp = await p.evaluate(() => [innerWidth, innerHeight]);
  if (vp[0] !== w || vp[1] !== h) throw new Error(`钉视口失败 ${JSON.stringify(vp)}`);
};
const 复原 = () => pinViewport(p);

const 扫描 = () => p.evaluate(() => {
  const c = 'max-w-canvas-generation-size-panel-viewport';
  const live = Array.from(document.querySelectorAll('.' + c))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 || r.height > 0; });
  return live.length ? live.map((e) => {
    const cs = getComputedStyle(e), r = e.getBoundingClientRect();
    return { testid: e.getAttribute('data-testid'), role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      布局: [e.offsetWidth, e.offsetHeight], scrollW: e.scrollWidth, clientW: e.clientWidth,
      class: e.getAttribute('class'), style: e.getAttribute('style'),
      computed: { w: cs.width, h: cs.height, maxW: cs.maxWidth, maxH: cs.maxHeight, ovfX: cs.overflowX, ovfY: cs.overflowY },
      文字: (e.innerText || '').trim().split('\n').filter(Boolean).slice(0, 16),
      直接子: Array.from(e.children).map((k) => { const kr = k.getBoundingClientRect(); const kc = getComputedStyle(k);
        return { tag: k.tagName, testid: k.getAttribute('data-testid'), role: k.getAttribute('role'),
          cls: (k.getAttribute('class') || '').split(/\s+/).filter((x) => /^(max-w|max-h|w|h)-canvas-/.test(x)).join(' '),
          盒: [Math.round(kr.width), Math.round(kr.height)] }; }) };
  }) : 0;
});

const 基线节点数 = (await R.status()).match(/(\d+) nodes/)[1];
rec.基线 = { status: await R.status(), credits: await R.credits(), 节点数: Number(基线节点数) };
console.log('基线:', JSON.stringify(rec.基线));

// ① 左栏「文本」建节点
const 文本钮 = await p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '文本' && !x.closest('.react-flow__node'));
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
console.log('左栏「文本」:', JSON.stringify(文本钮));
if (!文本钮) { await b.close(); process.exit(1); }
await p.mouse.click(文本钮[0], 文本钮[1]);
await p.waitForTimeout(3000);
rec.建后 = { status: await R.status(), 面板在: await p.evaluate(() => !!document.querySelector('.max-w-canvas-generation-size-panel-viewport')) };
console.log('建节点后:', JSON.stringify(rec.建后));

// ② 找「比例 / 分辨率」下拉
const 下拉 = await p.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('button,[role=button],[role=combobox]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const a = e.getAttribute('aria-label') || (e.innerText || '').trim().split('\n').slice(0, 2).join('⏎');
    if (/比例|分辨率|尺寸|options|数量|模型/.test(a)) {
      out.push({ a: a.slice(0, 40), testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
    }
  }
  return out;
});
console.log('候选下拉:', JSON.stringify(下拉, null, 1));

let 命中 = null;
for (const d of 下拉) {
  await p.mouse.click(d.pt[0], d.pt[1]);
  await p.waitForTimeout(1100);
  const s = await 扫描();
  if (s) { 命中 = { 入口: d, 读数: s }; console.log(`\n点「${d.a}」→ 命中生成尺寸面板`); break; }
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
}
if (!命中) {
  console.log('❌ 没找到生成尺寸面板；当前各下拉点完仍为 0');
  console.log('全部 class 命中:', JSON.stringify(await p.evaluate(() => Array.from(new Set(Array.from(document.querySelectorAll('*'))
    .flatMap((e) => (e.getAttribute('class') || '').split(/\s+/)).filter((c) => /^(max-w|max-h)-canvas-/.test(c)))))));
} else {
  rec.尺寸面板 = 命中.读数;
  console.log(JSON.stringify(命中.读数, null, 1));
  // 拍图
  const hl = await p.evaluate(() => {
    document.querySelectorAll('.__b172hl').forEach((e) => e.remove());
    const e = document.querySelector('.max-w-canvas-generation-size-panel-viewport');
    if (!e) return { 失败: '不在 DOM' };
    const r = e.getBoundingClientRect();
    const d = document.createElement('div');
    d.className = '__b172hl';
    d.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
      `border:3px solid #ff8c00;border-radius:12px;pointer-events:none;z-index:2147483646`;
    document.body.appendChild(d);
    return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  console.log('高亮框:', JSON.stringify(hl));
  if (!hl.失败) {
    await p.waitForTimeout(300);
    await p.screenshot({ path: DIR + '135-generation-size-panel-clamped.png' });
    rec.图 = 'screenshots/135-generation-size-panel-clamped.png';
  }

  // ③ 立规 43：只改视口，读夹取
  console.log('\n--- 只改视口，读夹取（立规 43）---');
  rec.档位 = [];
  for (const [w, h] of [[1280, 720], [900, 720], [700, 720], [600, 720], [500, 720], [400, 720], [1280, 400], [1280, 300]]) {
    await pin(w, h);
    const s = await 扫描();
    if (!s) { rec.档位.push({ 视口: [w, h], 还在: false }); console.log(`  ${w}×${h}: 面板没了`); continue; }
    const x = s[0];
    rec.档位.push({ 视口: [w, h], 盒: x.盒, 布局: x.布局, computed: x.computed, scrollW: x.scrollW, clientW: x.clientW });
    console.log(`  ${w}×${h}: ${x.盒[2]}×${x.盒[3]}  布局 ${x.布局[0]}×${x.布局[1]}  maxW=${x.computed.maxW}  scrollW=${x.scrollW}/client=${x.clientW}`);
  }
  await 复原();
  console.log('视口已复原:', JSON.stringify(await 复原()));
}
await p.evaluate(() => document.querySelectorAll('.__b172hl').forEach((e) => e.remove()));

// ③ 收尾：删掉刚建的节点，画布回到 76
const 后节点数 = (await R.status()).match(/(\d+) nodes/)[1];
rec.建后节点数 = Number(后节点数);
if (Number(后节点数) > Number(基线节点数)) {
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const del = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button,[role=menuitem]'))
      .find((x) => (x.getAttribute('aria-label') || (x.innerText || '').trim()) === '删除');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  });
  console.log('删除入口:', JSON.stringify(del));
  if (del) {
    await p.mouse.click(del.pt[0], del.pt[1]);
    await p.waitForTimeout(1500);
    rec.删后 = { status: await R.status(), credits: await R.credits() };
    console.log('删除后:', JSON.stringify(rec.删后));
  }
} else {
  rec.删后 = { 说明: '节点数没增加，无需清理', status: await R.status() };
}
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
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
console.log('收尾:', JSON.stringify(rec.收尾));
fs.writeFileSync(new URL('./_tmp-b172b.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();

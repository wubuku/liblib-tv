// 批次 173 a 轮：**视频侧**尺寸面板的机制，检验它与图片侧是否同族。
//
// 手册 `prepare-generation.md` 有一张「视频与图片不一样」的表，逐字记着：
//   视频「视频尺寸选项」容器 **334×292**，渲染在 `node-toolbar` **外部**
//   图片「图片尺寸选项」容器 **432×292**，渲染在 `node-toolbar` **内部**
// 但那张表**只记了数字，没记机制**（定尺来自 class 还是内联 style？余量多少？
// 夹取门槛在哪？朝哪个方向弹？）。批次 172 给图片侧补齐了：
//   min(432, 100vw−32)、门槛 464、内联 width:432px、class bottom-full…left-0 向上弹
//
// 本轮对视频侧做同一套取证，回答「两边是不是同一族机制」。
// 入口与图片侧对称：左栏「视频」→ **新建**视频节点 → 参数行里 aria 逐字以
//   `视频尺寸选项` 开头的按钮。
//
// 🔴 立规 43 复用：**先在 1280 下打开面板，再只改视口**读夹取。
// 🔴 立规 44 复用：清理**按 node id 认人**，删完**按同一个 id 验明**。
// ⛔ 只打开看，不点任何选项、不点生成。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url).pathname;
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '173a' };

const pin = async (w, h) => {
  await p.context().newCDPSession(p).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await p.waitForTimeout(600);
  const vp = await p.evaluate(() => [innerWidth, innerHeight]);
  if (vp[0] !== w || vp[1] !== h) throw new Error(`钉视口失败 ${JSON.stringify(vp)}`);
};

// ① 关可能开着的浮层（侧栏要用它自己的「收起」）
for (let i = 0; i < 4; i++) {
  const st = await p.evaluate(() => ({ sidecar: !!document.querySelector('aside[aria="Agent"]'),
    menu: !!document.querySelector('[data-testid="canvas-context-menu"]') }));
  if (!st.sidecar && !st.menu) break;
  if (st.sidecar) {
    const c = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('aside[aria="Agent"] button,[role=button]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '收起');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (c) { await p.mouse.click(c[0], c[1]); await p.waitForTimeout(700); continue; }
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
}

const 基线 = { status: await R.status(), credits: await R.credits(),
  视频节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node-video').length) };
rec.基线 = 基线;
console.log('基线:', JSON.stringify(基线));

// ② 新建视频节点
const 钮 = await p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '视频' && !x.closest('.react-flow__node'));
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
if (!钮) { console.log('没有左栏「视频」按钮'); await b.close(); process.exit(1); }
await p.mouse.click(钮[0], 钮[1]);
await p.waitForTimeout(3500);
const 新id = await p.evaluate((n0) => {
  const ids = Array.from(document.querySelectorAll('.react-flow__node-video')).map((x) => x.getAttribute('data-id'));
  return ids.length > n0 ? ids[ids.length - 1] : null;
}, 基线.视频节点数);
rec.新建 = { id: 新id, status: await R.status() };
console.log('新建视频节点:', JSON.stringify(rec.新建));

// ③ 找参数行里的尺寸按钮
const 候选 = await p.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('button,[role=button],[role=combobox]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const a = e.getAttribute('aria-label') || (e.innerText || '').trim().split('\n').slice(0, 2).join('⏎');
    out.push({ a: a.slice(0, 44), testid: e.getAttribute('data-testid'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
  }
  return out;
});
console.log('候选按钮:', JSON.stringify(候选.filter((c) => /尺寸|比例|分辨率|数量|模型|16:9|720P/.test(c.a)), null, 1));

let 命中 = null;
for (const c of 候选) {
  if (!/尺寸/.test(c.a)) continue;
  await p.keyboard.press('Escape'); await p.waitForTimeout(250);
  await p.mouse.click(c.pt[0], c.pt[1]);
  await p.waitForTimeout(1200);
  const s = await p.evaluate(() => {
    // 视频侧渲染在 node-toolbar **外部** ⇒ 用 aria 找，别用 class
    const e = Array.from(document.querySelectorAll('[role=dialog]'))
      .find((x) => /^视频尺寸选项/.test(x.getAttribute('aria-label') || ''));
    if (!e) return null;
    const cs = getComputedStyle(e), r = e.getBoundingClientRect();
    const inTB = !!e.closest('[data-testid="node-toolbar"]');
    return { testid: e.getAttribute('data-testid'), role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      布局: [e.offsetWidth, e.offsetHeight], scrollW: e.scrollWidth, clientW: e.clientWidth,
      '在node-toolbar内': inTB,
      class: e.getAttribute('class'), style: e.getAttribute('style'),
      computed: { w: cs.width, h: cs.height, maxW: cs.maxWidth, maxH: cs.maxHeight, pos: cs.position, bottom: cs.bottom, top: cs.top, left: cs.left },
      文字: (e.innerText || '').trim().split('\n').filter(Boolean),
      直接子: Array.from(e.children).map((k) => { const kr = k.getBoundingClientRect();
        return { tag: k.tagName, role: k.getAttribute('role'), aria: k.getAttribute('aria-label'),
          cls: (k.getAttribute('class') || '').split(/\s+/).filter((x) => /^(max-w|max-h|w|h)-canvas-/.test(x)).join(' '),
          盒: [Math.round(kr.width), Math.round(kr.height)] }; }) };
  });
  if (s) { 命中 = { 入口: c, 读数: s }; console.log(`\n点「${c.a}」→ 命中`); break; }
}
if (!命中) { console.log('❌ 没找到视频尺寸面板'); }
else {
  rec.视频尺寸面板 = 命中.读数;
  console.log(JSON.stringify(命中.读数, null, 1).slice(0, 2200));
  const hl = await p.evaluate(() => {
    document.querySelectorAll('.__b173hl').forEach((e) => e.remove());
    const e = Array.from(document.querySelectorAll('[role=dialog]'))
      .find((x) => /^视频尺寸选项/.test(x.getAttribute('aria-label') || ''));
    if (!e) return { 失败: '没开' };
    const r = e.getBoundingClientRect();
    const d = document.createElement('div');
    d.className = '__b173hl';
    d.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
      `border:3px solid #ff8c00;border-radius:12px;pointer-events:none;z-index:2147483646`;
    document.body.appendChild(d);
    return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  console.log('高亮框:', JSON.stringify(hl));
  if (!hl.失败) {
    const clip = { x: Math.max(0, hl.盒[0] - 60), y: Math.max(0, hl.盒[1] - 40),
      width: Math.min(1280 - Math.max(0, hl.盒[0] - 60), hl.盒[2] + 120), height: Math.min(720 - Math.max(0, hl.盒[1] - 40), hl.盒[3] + 120) };
    await p.waitForTimeout(300);
    await p.screenshot({ path: DIR + '136-video-size-panel-334x292.png', clip });
    rec.图 = 'screenshots/136-video-size-panel-334x292.png';
    console.log('已拍 136，裁剪', JSON.stringify(clip));
  }
  // 立规 43：只改视口
  console.log('\n--- 只改视口（立规 43）---');
  rec.档位 = [];
  for (const [w, h] of [[1280, 720], [800, 720], [600, 720], [500, 720], [400, 720], [360, 720], [1280, 400], [1280, 300]]) {
    await pin(w, h);
    const s = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('[role=dialog]'))
        .find((x) => /^视频尺寸选项/.test(x.getAttribute('aria-label') || ''));
      if (!e) return null;
      const cs = getComputedStyle(e), r = e.getBoundingClientRect();
      return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        布局: [e.offsetWidth, e.offsetHeight], maxW: cs.maxWidth, scrollW: e.scrollWidth, clientW: e.clientWidth };
    });
    if (!s) { rec.档位.push({ 视口: [w, h], 还在: false }); console.log(`  ${w}×${h}: 面板没了`); continue; }
    const 预测宽 = Math.min(334, Math.max(0, w - 32));
    rec.档位.push({ 视口: [w, h], ...s, 预测宽 });
    console.log(`  ${w}×${h}: ${s.盒[2]}×${s.盒[3]}  布局 ${s.布局[0]}×${s.布局[1]}  maxW=${s.maxW}  预测宽 ${预测宽} ${s.盒[2] === 预测宽 ? '✅' : '❌'}  scrollW=${s.scrollW}/client=${s.clientW}`);
  }
  await pinViewport(p);
  console.log('视口已复原:', JSON.stringify(await pinViewport(p)));
}
await p.evaluate(() => document.querySelectorAll('.__b173hl').forEach((e) => e.remove()));
await p.keyboard.press('Escape'); await p.waitForTimeout(500);

// ④ 立规 44：按 id 删掉临时节点，删完按 id 验明
if (新id) {
  await p.evaluate((id) => document.querySelector(`.react-flow__node[data-id="${id}"]`)?.scrollIntoView({ block: 'center', inline: 'center' }), 新id);
  await p.waitForTimeout(800);
  const pt = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 新id);
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  if (pt) { await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1000); }
  const d = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
      .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (d) { await p.mouse.click(d[0], d[1]); await p.waitForTimeout(2000); }
  const 验 = await p.evaluate((id) => !!document.querySelector(`.react-flow__node[data-id="${id}"]`), 新id);
  rec.清理 = { 目标还在: 验, status: await R.status() };
  console.log('清理：目标还在 =', 验, '（应为 false）｜', rec.清理.status);
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
rec.收尾 = { status: await R.status(), sel: await R.selCount(), credits: await R.credits(),
  视口: await p.evaluate(() => [innerWidth, innerHeight]) };
console.log('收尾:', JSON.stringify(rec.收尾));
fs.writeFileSync(new URL('./_tmp-b173a.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();

// 批次 172 d 轮：重拍 135。
// 第一版的问题：① 右侧挂着 AI 侧栏（前一���的残留）② 顶栏写着「节点 77」——
//   截图发生在「临时新建的图片节点」还在的时候（量完才删）。
//   ⇒ 两条都处理：先关侧栏；alt 里**如实写明**截图时画布是 77 节点、量完已删回 76。
//
// ⛔ 只打开尺寸面板看，不点任何选项、不点生成。清理**按 node id 认人**，删完再按 id 验明。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url).pathname;
const { b, p } = await openCanvas();
const R = readers(p);

// ① 关 AI 侧栏（Esc 关不掉，要用它自己的「收起」）
for (let i = 0; i < 4; i++) {
  const has = await p.evaluate(() => !!document.querySelector('aside[aria="Agent"]'));
  if (!has) break;
  const c = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('aside[aria="Agent"] button,[role=button]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '收起');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (!c) break;
  await p.mouse.click(c[0], c[1]); await p.waitForTimeout(800);
}
console.log('侧栏已关 =', !(await p.evaluate(() => !!document.querySelector('aside[aria="Agent"]'))));
const 基线 = await R.status();
console.log('基线:', 基线);

const 图片数0 = await p.evaluate(() => document.querySelectorAll('.react-flow__node-image').length);
// ② 建图片节点
const 钮 = await p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '图片' && !x.closest('.react-flow__node'));
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
await p.mouse.click(钮[0], 钮[1]);
await p.waitForTimeout(3500);
const 新id = await p.evaluate((n0) => {
  const ids = Array.from(document.querySelectorAll('.react-flow__node-image')).map((x) => x.getAttribute('data-id'));
  return ids.length > n0 ? ids[ids.length - 1] : null;
}, 图片数0);
console.log('新建图片节点 id =', 新id, '|', await R.status());

// ③ 打开尺寸面板
const 尺钮 = await p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => /^图片尺寸选项/.test(x.getAttribute('aria-label') || ''));
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return { aria: e.getAttribute('aria-label'), pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
});
console.log('尺寸按钮:', JSON.stringify(尺钮));
await p.mouse.click(尺钮.pt[0], 尺钮.pt[1]);
await p.waitForTimeout(1400);

const hl = await p.evaluate(() => {
  document.querySelectorAll('.__b172hl').forEach((e) => e.remove());
  const e = document.querySelector('.max-w-canvas-generation-size-panel-viewport');
  if (!e) return { 失败: '面板没开' };
  const r = e.getBoundingClientRect();
  const d = document.createElement('div');
  d.className = '__b172hl';
  d.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
    `border:3px solid #ff8c00;border-radius:12px;pointer-events:none;z-index:2147483646`;
  document.body.appendChild(d);
  return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    aria: e.getAttribute('aria-label'), role: e.getAttribute('role'),
    文字: (e.innerText || '').trim().split('\n').filter(Boolean),
    顶栏: (document.querySelector('[data-testid="canvas-node-summary-trigger"]') || {}).getAttribute
      ? document.querySelector('[data-testid="canvas-node-summary-trigger"]').getAttribute('aria-label') : null };
});
console.log('高亮框:', JSON.stringify(hl, null, 1).slice(0, 900));
if (!hl.失败) {
  // 裁到面板周边（含下方那排按钮，说明它是「向上弹出」）
  const clip = { x: Math.max(0, hl.盒[0] - 70), y: Math.max(0, hl.盒[1] - 50),
    width: Math.min(1280 - Math.max(0, hl.盒[0] - 70), hl.盒[2] + 140), height: Math.min(720 - Math.max(0, hl.盒[1] - 50), hl.盒[3] + 130) };
  await p.waitForTimeout(300);
  await p.screenshot({ path: DIR + '135-generation-size-panel-viewport.png', clip });
  console.log('已重拍 135，裁剪', JSON.stringify(clip));
}
await p.evaluate(() => document.querySelectorAll('.__b172hl').forEach((e) => e.remove()));
await p.keyboard.press('Escape'); await p.waitForTimeout(500);

// ④ 清理：按 id 删掉临时节点并验明
if (新id) {
  await p.evaluate((id) => document.querySelector(`.react-flow__node[data-id="${id}"]`)?.scrollIntoView({ block: 'center', inline: 'center' }), 新id);
  await p.waitForTimeout(800);
  const pt = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 新id);
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  await p.mouse.click(pt[0], pt[1], { button: 'right' });
  await p.waitForTimeout(1000);
  const d = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
      .find((x) => (x.innerText || '').trim().startsWith('删除'));
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (d) { await p.mouse.click(d[0], d[1]); await p.waitForTimeout(2000); }
  const 验 = await p.evaluate((id) => !!document.querySelector(`.react-flow__node[data-id="${id}"]`), 新id);
  console.log('清理：目标还在 =', 验, '（应为 false）｜', await R.status());
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
console.log('收尾:', JSON.stringify({ status: await R.status(), sel: await R.selCount(), credits: await R.credits(),
  视口: await p.evaluate(() => [innerWidth, innerHeight]) }));
fs.writeFileSync(new URL('./_tmp-b172d.json', import.meta.url), JSON.stringify({ 截图盒: hl }, null, 1));
await b.close();

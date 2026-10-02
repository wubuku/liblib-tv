// 批次 95 · 收尾第 8 轮：定性 **文本节点 resize 角/边控件的尺寸机制**。
//
// 现状是一堆互相打架的读数（同一 canvas 320×320 的节点）：
//     23% 档  corner 11×11   （b95h）   → canvas 47.0
//     40% 档  corner 19×19   （b95g）   → canvas 47.5
//     60% 档  corner 24×24   （b95e）   → canvas 40.0   ← 对不上
//     60% 档  corner 11×11   （b95g）   → 但那次节点是 75×75，不是 320 的节点
// 三个假设都还没排除：
//     H1 角控件是 **canvas 恒定**（屏上随缩放变）
//     H2 角控件是 **屏上恒定**（像批次 93 钉的工具条按钮）
//     H3 **读数时机污染** —— 缩放动画没停就量了（b95g 切完档只等 400ms×2 就读）
//
// 这一轮把 H3 控掉：每档切完**等 2 秒**再**连读两次**，两次不同就当场判「未静止」并重读，
// 最多 3 轮；只有拿到**静止**读数才拿去和别的档比。
// 节点锁 `node_3bfb9r79qe`（canvas 已独立确认恒 320×320），全程锁 id、每档回读 aria 自证。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), locked: 'node_3bfb9r79qe', zooms: [] };
const TID = out.locked;

const zoomPct = () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]');
  return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });

const setZoom = async (target) => {
  for (let k = 1; k <= 4; k++) {
    if (await zoomPct() === target) return true;
    await p.click('button[aria-label^="Zoom options"]');
    await p.waitForTimeout(900);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
      await p.keyboard.press('Escape'); await p.waitForTimeout(600); continue;
    }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, target);
    await p.waitForTimeout(1700); await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  }
  return await zoomPct() === target;
};

// 一次读全部几何（不点击、不要求可见）
const geom = (tag) => p.evaluate((l) => {
  const n = document.querySelector(`.react-flow__node[data-id="${l.id}"]`);
  if (!n) return null;
  const g = (t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const r = e.getBoundingClientRect(); return { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 }; };
  const r = n.getBoundingClientRect();
  return { tag: l.tag, aria: n.getAttribute('aria-label'), selected: n.classList.contains('selected'),
    editable: document.querySelectorAll('[contenteditable="true"]').length,
    node: { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 },
    inView: r.right > 0 && r.bottom > 0 && r.left < 1280 && r.top < 720,
    corner: g('text-node-resize-top-left'), edgeTop: g('text-node-resize-top'), edgeLeft: g('text-node-resize-left'),
    controls: g('text-node-resize-controls'), outline: g('text-node-selection-outline'),
    affordance: g('textarea-resize-affordance'),
    selSurface: g('selection-context-toolbar-surface'), selToolbar: g('selection-context-toolbar'),
    nodeToolbar: g('node-toolbar') };
}, { id: TID, tag });

// 连读两次相同才算静止 —— 这条是本轮专门为 H3 设的闸
const settled = async (tag) => {
  for (let k = 1; k <= 3; k++) {
    const a = await geom(`${tag}#${k}a`);
    await p.waitForTimeout(700);
    const b2 = await geom(`${tag}#${k}b`);
    const key = (x) => JSON.stringify([x?.node, x?.corner, x?.edgeTop, x?.outline, x?.selSurface, x?.nodeToolbar]);
    if (key(a) === key(b2)) return { a, b: b2, still: true, tries: k };
    log(`  ${tag} 第 ${k} 轮未静止，重读`);
  }
  return { a, b: b2, still: false, tries: 3 };
};

out.start = { zoom: await zoomPct(), scale: await scaleNow(), sel: await selN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));

for (const z of [40, 60, 100]) {
  const ok = await setZoom(z);
  const tag = `${await zoomPct()}%`;            // 用**实测标签**，不用目标值
  await p.waitForTimeout(2000);               // 🔴 等缩放动画彻底停（b95g 只等了 400ms）
  const st = await settled(tag);
  const m = st.a;
  const sc = await scaleNow();
  const canvas = (x) => (x && sc ? { w: Math.round(x.w / sc * 100) / 100, h: Math.round(x.h / sc * 100) / 100 } : null);
  const rec = { target: z, label: tag, ok, scale: sc, still: st.still, tries: st.tries,
    aria: m?.aria, selected: m?.selected, editable: m?.editable, inView: m?.inView,
    node: m?.node, nodeCanvas: canvas(m?.node),
    corner: m?.corner, cornerCanvas: canvas(m?.corner),
    edgeTop: m?.edgeTop, edgeTopCanvas: canvas(m?.edgeTop),
    controls: m?.controls, controlsCanvas: canvas(m?.controls),
    outline: m?.outline, outlineCanvas: canvas(m?.outline),
    affordance: m?.affordance, affordanceCanvas: canvas(m?.affordance),
    selSurface: m?.selSurface, selSurfaceCanvas: canvas(m?.selSurface),
    selToolbar: m?.selToolbar, selToolbarCanvas: canvas(m?.selToolbar),
    nodeToolbar: m?.nodeToolbar, nodeToolbarCanvas: canvas(m?.nodeToolbar) };
  out.zooms.push(rec);
  log(`[${tag}] scale=${sc} 静止=${st.still}(${st.tries}) aria=${m?.aria} sel=${m?.selected} inView=${m?.inView}`);
  log(`   屏上  node=${m?.node?.w}×${m?.node?.h} corner=${m?.corner?.w}×${m?.corner?.h} edgeTop=${m?.edgeTop?.w}×${m?.edgeTop?.h} outline=${m?.outline?.w}×${m?.outline?.h} affordance=${m?.affordance?.w}×${m?.affordance?.h}`);
  log(`   canvas node=${rec.nodeCanvas?.w}×${rec.nodeCanvas?.h} corner=${rec.cornerCanvas?.w}×${rec.cornerCanvas?.h} edgeTop=${rec.edgeTopCanvas?.w}×${rec.edgeTopCanvas?.h} outline=${rec.outlineCanvas?.w}×${rec.outlineCanvas?.h} surface=${rec.selSurfaceCanvas?.w}×${rec.selSurfaceCanvas?.h} content=${rec.selToolbarCanvas?.w}×${rec.selToolbarCanvas?.h}`);
}

await setZoom(60);
if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
out.end = { zoom: await zoomPct(), scale: await scaleNow(), sel: await selN(), credits: await credits(),
  nodes: await p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]) };
log('终态：', JSON.stringify(out.end), '｜缩放归位', out.end.zoom === 60 ? '✅' : '🔴');
writeFileSync(new URL('./_tmp-b95j.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

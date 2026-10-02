// 批次 103 · a 轮：`20-reference.md`（普查 89）同步前的取证。
//
// 这一页是**参照页**，作用是给后面每一批提供交叉校验的基准。
// 批次 101 / 102 产出了一大票新读数（视频播放控件、上传白名单、两个文件选择框），
// 而**这一页一个字都没有** ⇒ 参照页已经和任务页脱节。本批先把它补齐。
//
// 本轮取证两件事（**只读，不建节点、不删节点**）：
//   A 🔑 **尺寸契约的跨缩放复核**。参照页第 48-50 行那条契约是
//      「屏上读数 = canvas 尺寸 × 当前缩放，所以把缩放设成 100% 再读，屏上数字就是 canvas 数字」，
//      而批次 79 的整张表**只在 100% 量过一次** —— 从没在别的缩放下验过这条等式。
//      本轮在 40% / 60% / 100% 三档各量一次同一个节点，**逐档验等式**。
//   B 左栏 9 项入口的读数复核（批次 99 记过 y = 193/235/…/543）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const setZoom = async (t) => { for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel(); if (zl && new RegExp(`, ${t}%`).test(zl)) return true;
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t);
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  return false; };
// **除数必须当场读、连读两次相同才算静止**（绝不写死 0.6）
const stableScale = async () => { const a = await scaleNow(); await p.waitForTimeout(900); const b2 = await scaleNow(); return [a, b2, a !== null && a === b2]; };

out.start = { scale: await scaleNow(), zoom: await zoomLabel() };
log('起点：', JSON.stringify(out.start));

// ---- 选一个「类型确定、且此刻在视口内」的节点当量尺：优先文本节点（契约值 320×320） ----
out.subject = await p.evaluate(() => {
  const cands = Array.from(document.querySelectorAll('.react-flow__node-text')).map((n) => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      inViewport: r.x + r.width > 0 && r.y + r.height > 0 && r.x < 1280 && r.y < 720,
      screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      transform: n.style.transform }; });
  return { n: cands.length, inView: cands.filter((c) => c.inViewport), pick: cands.find((c) => c.inViewport) || cands[0] || null };
});
log('候选文本节点：', JSON.stringify(out.subject, null, 1));
if (!out.subject.pick) { log('🔴 没有文本节点可量'); writeFileSync(new URL('./_tmp-b103a.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }
const PICK = out.subject.pick.id;

// ---- A 三档缩放各量一次 ----
out.zoomSeries = [];
for (const z of [40, 60, 100]) {
  await setZoom(z);
  const [s1, s2, same] = await stableScale();
  if (!same) { log(`  ${z}% 档 scale 连读不一致：${s1} / ${s2} ⇒ 跳过这一档`); out.zoomSeries.push({ z, skipped: 'unstable', pair: [s1, s2] }); continue; }
  const m = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    // 同时读「节点本体」与「内部那个满铺的层」——两者理论上同尺寸
    const inner = n.querySelector('[data-testid$="-flow-node-full"]') || n.firstElementChild;
    const ri = inner ? inner.getBoundingClientRect() : null;
    return { screen: { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100, x: Math.round(r.x), y: Math.round(r.y) },
      inner: ri ? { tid: inner.getAttribute('data-testid'), w: Math.round(ri.width * 100) / 100, h: Math.round(ri.height * 100) / 100 } : null };
  }, PICK);
  if (!m) { out.zoomSeries.push({ z, skipped: 'node-gone' }); continue; }
  const row = { z, scale: s1, label: await zoomLabel(), ...m,
    canvasW: Math.round(m.screen.w / s1 * 100) / 100, canvasH: Math.round(m.screen.h / s1 * 100) / 100 };
  out.zoomSeries.push(row);
  log(`  ${z}% 档（scale=${s1}）：屏上 ${m.screen.w}×${m.screen.h} ⇒ ÷scale 得 canvas ${row.canvasW}×${row.canvasH}`);
}

// ---- 尺寸契约：三档推出的 canvas 值应彼此相等（差 < 0.5） ----
const cvs = out.zoomSeries.filter((r) => !r.skipped).map((r) => [r.canvasW, r.canvasH]);
out.contract = { rows: cvs, spread: cvs.length >= 2 ? {
  w: Math.max(...cvs.map((c) => c[0])) - Math.min(...cvs.map((c) => c[0])),
  h: Math.max(...cvs.map((c) => c[1])) - Math.min(...cvs.map((c) => c[1])) } : null };
out.contract.holds = out.contract.spread ? (out.contract.spread.w < 0.5 && out.contract.spread.h < 0.5) : null;
log('三档推出的 canvas 值：', JSON.stringify(cvs), '｜极差：', JSON.stringify(out.contract.spread));
log('⇒ 尺寸契约在三个缩放下都成立？', out.contract.holds === null ? '样本不足' : (out.contract.holds ? '✅' : '🔴'));

// ---- B 左栏 9 项读数 ----
out.rail = await p.evaluate(() => {
  const ASIDE = Array.from(document.querySelectorAll('aside,nav,[data-testid="canvas-navigation-shell"]'))
    .map((e) => ({ tid: e.getAttribute('data-testid'), tag: e.tagName, r: e.getBoundingClientRect() }))
    .filter((x) => x.r.x < 60 && x.r.height > 200);
  const box = ASIDE[0];
  if (!box) return { noRail: true, ASIDE };
  const items = Array.from(box.r && document.querySelectorAll('button,[role=button]'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
        y: Math.round(r.y), x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height) }; })
    .filter((x) => x.aria && x.w > 0 && x.h > 0 && x.x < box.r.width + 40
      && x.y >= box.r.y - 2 && x.y <= box.r.y + box.r.height + 2);
  return { box: `${Math.round(box.r.x)},${Math.round(box.r.y)} ${Math.round(box.r.width)}×${Math.round(box.r.height)}`,
    count: items.length, items, testidNull: items.filter((i) => !i.tid).length,
    ys: items.map((i) => i.y), steps: items.slice(1).map((i, k) => i.y - items[k].y) };
});
log('\n=== 左栏 ===');
log(JSON.stringify(out.rail, null, 1));

// ---- 归位缩放 ----
for (let k = 0; k < 3; k++) { await setZoom(60);
  const [a, b2, s] = await stableScale(); log(`  归位第 ${k + 1} 次：`, JSON.stringify([a, b2, s]), '｜', await zoomLabel());
  if (s && a === 0.6) break; }
out.end = { scale: await scaleNow(), zoom: await zoomLabel() };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b103a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

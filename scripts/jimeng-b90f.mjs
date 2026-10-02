// 批次 90 · F：抓手态 → 选择态的**唯一**回程路径，以及它对应的排障条目。
//
// e 轮钉死三件事：
//   ① 底部 dock 只有**一个**工具钮 `[data-testid="canvas-pointer-tool-toggle"]`（`28×28@16,672`），
//      它的 `aria-label` 在 `选择工具` / `抓手工具` 之间**翻** —— **不存在**一个叫「选择工具」的按钮；
//      ⇒ 我上一版恢复逻辑「找 aria-label==='选择工具' 的按钮去点」必然找不到（报 no-button）。
//   ② **抓手态下单击节点不选中**（`sel` 恒 0）；
//   ③ **双击也不选中**。
//
// ⇒ 抓手态就是「节点点不中」这条排障的**成因**（而症状很像「失灵了」）。
//
// ⇒ **P1**：点那个 toggle 钮 ⇒ aria 翻成 `选择工具` 且**点节点立刻能选中**。
//   若成立 ⇒ 抓手态的退出路径只有这一条（批次 82 已证 **V 键不切工具**），
//   「节点点不中」的第一条建议就应该是「先看 dock 那个钮的 aria」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const toolAria = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  if (!e) return null; const r = e.getBoundingClientRect();
  return { aria: e.getAttribute('aria-label'), box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
const clickTool = async () => { const t = await toolAria(); if (!t) return null;
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900); return toolAria(); };
const pickPoint = () => p.evaluate(() => {
  for (const n of document.querySelectorAll('.react-flow__node')) { const r = n.getBoundingClientRect();
    if (!(r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720)) continue;
    for (let fx = 0.3; fx <= 0.7; fx += 0.2) for (let fy = 0.3; fy <= 0.7; fy += 0.2) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const el = document.elementFromPoint(x, y);
      if (el && el.closest('.react-flow__node') === n) return { id: n.getAttribute('data-id'), x, y }; } }
  return null; });

out.before = { tool: await toolAria(), sel: await selCount() };
log('起点：', JSON.stringify(out.before));
const pt = await pickPoint();
log('落点：', JSON.stringify(pt));

if (pt) {
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900);
  out.inGrab = { tool: await toolAria(), sel: await selCount() };
  log('① 抓手态点节点：', JSON.stringify(out.inGrab));

  const after = await clickTool();
  out.afterToggle = { tool: after, sel: await selCount() };
  log('② 点 dock toggle 之后：', JSON.stringify(out.afterToggle));

  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900);
  out.inSel = { tool: await toolAria(), sel: await selCount() };
  log('③ 选择态再点同一落点：', JSON.stringify(out.inSel));

  out.verdict = { grabBlocksSelection: out.inGrab.sel === '0', toggleFlipsAria: after && out.before.tool && after.aria !== out.before.tool.aria,
    selectionWorksAfterToggle: out.inSel.sel === '1' };
  log('P1 判定：', JSON.stringify(out.verdict));
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
}
out.end = { tool: await toolAria(), sel: await selCount() };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b90f.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

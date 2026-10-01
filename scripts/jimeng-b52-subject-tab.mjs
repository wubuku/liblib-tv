// 批次 52 补充（只读）：画布资产库的「主体」页签 —— 第二级页签与空态
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('canvas page not found'); process.exit(1); }
await pinViewport(p);
for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); }

const snapshot = () => p.evaluate(() => {
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return { open: false };
  const area = d.querySelector('[data-testid="canvas-asset-library-operation-area"]');
  const v = d.querySelector('[data-testid="canvas-asset-library-viewport"]');
  const f = d.querySelector('[data-testid="canvas-asset-library-footer"]');
  const item = (e) => { const r = e.getBoundingClientRect(); return { txt: (e.innerText || '').trim().split('\n')[0], aria: e.getAttribute('aria-label'), role: e.getAttribute('role'), sel: e.getAttribute('aria-selected'), rect: [r.x, r.y, r.width, r.height].map(Math.round) }; };
  // 按 y 分行
  const rows = {};
  for (const e of area.querySelectorAll('button,[role="tab"],[role="button"]')) { const it = item(e); (rows[it.rect[1]] = rows[it.rect[1]] || []).push(it); }
  return { open: true,
    rows: Object.entries(rows).map(([y, items]) => ({ y: +y, items })),
    viewport: v ? { text: (v.innerText || '').replace(/\n+/g, ' | ').trim().slice(0, 120), rect: (() => { const r = v.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); })() } : null,
    footer: f ? (f.innerText || '').replace(/\n+/g, ' | ').trim().slice(0, 120) : null,
    full: (d.innerText || '').replace(/\n+/g, ' | ').slice(0, 320) };
});

await p.click('button[aria-label="资产库"]');
await p.waitForTimeout(2200);
console.log('=== 初始（资产/图片）===');
console.log(JSON.stringify(await snapshot(), null, 1));

// 点第一级的「主体」
const ok = await p.evaluate(() => {
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  const area = d.querySelector('[data-testid="canvas-asset-library-operation-area"]');
  const t = Array.from(area.querySelectorAll('[role="tab"],button')).find((e) => (e.innerText || '').trim().split('\n')[0] === '主体' && e.getBoundingClientRect().y < 100);
  if (!t) return false; t.click(); return true;
});
await p.waitForTimeout(1500);
console.log(`\n=== 点第一级「主体」（${ok ? '成功' : '失败'}）===`);
const s1 = await snapshot();
console.log(JSON.stringify(s1, null, 1));
// 逐个点第二级页签（y>100 的那一行）
if (s1.open && s1.rows) {
  const second = (s1.rows.find((r) => +r.y > 100) || { items: [] }).items.filter((i) => i.role === 'tab' || (i.txt && i.txt.length <= 4));
  console.log('\n第二级候选:', JSON.stringify(second.map((i) => i.txt)));
  for (const t of second) {
    const clicked = await p.evaluate((txt) => {
      const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
      if (!d) return false;
      const e = Array.from(d.querySelectorAll('[role="tab"],button')).find((x) => (x.innerText || '').trim().split('\n')[0] === txt && x.getBoundingClientRect().y > 100);
      if (!e) return false; e.click(); return true;
    }, t.txt);
    await p.waitForTimeout(1200);
    const s = await snapshot();
    console.log(`  [主体/${t.txt}] ${clicked ? '' : '点击失败 '}→`, JSON.stringify(s.open ? { vp: s.viewport, footer: s.footer } : { open: false }));
  }
}
await p.keyboard.press('Escape'); await p.waitForTimeout(900);
const bad = await diffNodePositions(p, BASELINE.nodes, 1.5);
console.log('\n结束，位置偏离:', bad.length, bad.length ? bad.join(',') : '✅ 0');
await b.close();

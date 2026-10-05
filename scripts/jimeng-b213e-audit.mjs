import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, PORT } from './jimeng-b135-lib.mjs';
const 基线 = JSON.parse(fs.readFileSync('/tmp/b212-dump.json', 'utf8'));
const b = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = b.contexts()[0];
const p = await ctx.newPage();
await p.setViewportSize({ width: 1280, height: 720 });
await p.goto('https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f', { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 45000 });
await p.waitForTimeout(5000);
const now = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  const cands = ['video-node-compact','video-node-empty','video-node-result','audio-node-compact','audio-node-empty','image-node-compact','image-node-result','text-flow-node-compact','text-flow-node-full','timeline-flow-node','director-stage-flow-node-shell'];
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    画布: t ? [Number(t[1]), Number(t[2])] : null, 屏上: [Math.round(r.width), Math.round(r.height)],
    变体: cands.filter((c) => n.querySelector(`[data-testid="${c}"]`)) };
}));
const 基线id = new Set(基线.按x排序.map((n) => n.id));
const 多 = now.filter((n) => !基线id.has(n.id));
const 少 = 基线.按x排序.filter((n) => !now.some((x) => x.id === n.id));
const 积分 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label')||'').startsWith('Credits')); return e ? e.getAttribute('aria-label') : null; });
const 状态行 = await p.evaluate(() => { const m = (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0]; return m || null; });
console.log('现在节点数', now.length, '｜基线 76');
console.log('状态行:', 状态行, '｜积分:', 积分);
console.log('\n多出来的节点：');
for (const n of 多) console.log('  ', n.id, n.aria, JSON.stringify(n.画布), '屏上', JSON.stringify(n.屏上), '变体', JSON.stringify(n.变体));
console.log('\n少了的节点：', 少.length, 少.map((n) => n.id + ' ' + n.aria).join(' | ') || '(无)');
fs.writeFileSync('/tmp/b213e-audit.json', JSON.stringify({ 现在数: now.length, 多, 少: 少.map((n) => n.id), 积分, 状态行, now }, null, 1));
await p.close();
process.exit(0);

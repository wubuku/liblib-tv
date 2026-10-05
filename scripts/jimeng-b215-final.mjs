/**
 * 批次 215 收尾核验（只读）：确认画布已回到前置基线。
 * 前置基线取自 /tmp/b215.json 的 步骤0（76 节点 / 76 个 id / 0 选中 / 26% / 813 积分）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 前 = JSON.parse(fs.readFileSync('/tmp/b215.json', 'utf8'));
const 基线id = new Set((前.步骤0_前置 || {}).基线id || []);
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b215-收尾核验' };

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const p = await ctx.newPage();
await p.setViewportSize({ width: 1280, height: 720 });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 45000 });
await p.waitForTimeout(5000);
const 节点 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
  id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label') })));
out.节点数 = 节点.length;
out.多出来 = 节点.filter((n) => !基线id.has(n.id)).map((n) => n.id + ' ' + n.aria);
out.少了 = [...基线id].filter((x) => !节点.some((n) => n.id === x));
out.状态行 = await p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
out.缩放 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
out.积分 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits')); return e ? e.getAttribute('aria-label') : null; });
out.选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
out.基线 = { 节点数: (前.步骤0_前置 || {}).基线数, 积分: (前.步骤0_前置 || {}).积分 };
out.通过 = out.节点数 === out.基线.节点数 && !out.多出来.length && !out.少了.length && out.选中数 === 0 && out.积分 === out.基线.积分;
log('【收尾】' + out.节点数 + ' 节点 ｜ 多 ' + JSON.stringify(out.多出来) + ' ｜ 少 ' + JSON.stringify(out.少了));
log('【收尾】' + out.状态行 + ' ｜ 缩放 ' + out.缩放 + ' ｜ 积分 ' + out.积分 + ' ｜ 选中 ' + out.选中数);
log('【前置基线】' + JSON.stringify(out.基线));
log(out.通过 ? '✅ 与前置基线逐项一致' : '🔴 与前置基线不一致');
fs.writeFileSync('/tmp/b215-final.json', JSON.stringify(out, null, 1));
await p.close();
process.exit(0);

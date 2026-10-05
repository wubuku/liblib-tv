/**
 * 批次 215 · 步骤 0：只读状态普查（不碰任何东西）。
 * 目的：共享画布可能已被别的会话漂移 ⇒ 动手前先确认节点数 / 积分 / 状态行。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b215a0.json';
const log = (...a) => console.log(a.join(' '));

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const out = { 轮次: 'b215a0-状态普查' };
try {
  const p = await ctx.newPage();
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(5000);
  out.节点 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      画布: t ? [Number(t[1]), Number(t[2])] : null, 屏上: [Math.round(r.width), Math.round(r.height)] };
  }));
  out.积分 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
    return e ? e.getAttribute('aria-label') : null;
  });
  out.状态行 = await p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
  out.缩放aria = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
  out.探针节点 = out.节点.filter((n) => /probe/i.test(n.aria || ''));
  out.探针mp4 = out.节点.filter((n) => /jimeng-b196-probe/.test(n.aria || ''));
  out.媒体类节点 = out.节点.filter((n) => /node: /.test(n.aria || ''));
  await p.close();
} catch (e) { out.出错 = e.message; log('🔴 ' + e.message); }
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('节点数 ' + (out.节点 || []).length + ' ｜ ' + out.状态行 + ' ｜ 缩放 ' + out.缩放aria + ' ｜ 积分 ' + out.积分);
log('探针节点 ' + JSON.stringify((out.探针节点 || []).map((n) => n.id + ' ' + n.aria)));
log('媒体类 ' + JSON.stringify((out.媒体类节点 || []).map((n) => n.id + ' ' + n.aria + ' ' + JSON.stringify(n.屏上))));
process.exit(0);

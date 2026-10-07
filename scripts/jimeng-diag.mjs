/**
 * 画布加载诊断：节点为什么一个都不出来。
 * 只读，不点任何东西（不生成、不进扣费页）。
 */
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
const net = [];
p.on('response', (r) => {
  const u = r.url();
  if (/api|canvas|project/i.test(u)) net.push(`${r.status()} ${u.slice(0, 140)}`);
});
await p.setViewportSize({ width: 1280, height: 720 });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForTimeout(20000);
const 态 = await p.evaluate(() => ({
  url: location.href,
  title: document.title,
  ready: document.readyState,
  节点数: document.querySelectorAll('.react-flow__node').length,
  reactFlow: !!document.querySelector('.react-flow'),
  顶层testid: Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.dataset.testid).slice(0, 30),
  正文前600: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 600),
  积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).textContent || null,
}));
console.log(JSON.stringify(态, null, 1));
console.log('--- 网络 ---');
console.log(net.slice(0, 40).join('\n'));
await p.close();
process.exit(0);

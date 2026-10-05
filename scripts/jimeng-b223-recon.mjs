/**
 * 批次 223 · 步骤 0：**只读侦察** —— 把全画布各类节点的 CSS 尺寸列出来。
 *
 * 📌 靶子：批次 222 收尾留下的入口 —— `w*₍族₎`（取景带起点，已知音频 `1212`、媒体 `≈1201.8`）
 *   是不是**节点 CSS 宽度的函数**。要判它，先得知道**画布上有哪些不同尺寸的族**。
 *
 * ⛔ 全程只读：不点任何节点、不搜索、不改动画布。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b223-recon' };

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6000);

  const 读 = await p.evaluate(() => {
    const 展开 = (aria) => (aria || '').replace(/^node:\s*/, '');
    return Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
      const 标签 = n.getAttribute('aria-label') || '';
      const 名 = 展开(标签.replace(/^视频 /, '').replace(/^图片 /, '').replace(/^音频 /, ''));
      return { id: n.getAttribute('data-id'), aria: 标签, 名,
        画布: t ? [Number(t[1]), Number(t[2])] : null,
        css: [n.offsetWidth, n.offsetHeight],
        角: n.getAttribute('class') || '' };
    });
  });
  out.全部 = 读;
  log('节点总数 ' + 读.length);

  // 按「尺寸 + 名字前缀」归组
  const 组 = new Map();
  for (const n of 读) {
    const 前缀 = (n.名.match(/^[^\d]+/) || [n.名])[0];
    const 键 = 前缀 + '|' + n.css[0] + 'x' + n.css[1];
    if (!组.has(键)) 组.set(键, { 前缀, css: n.css, 数: 0, 例: [], id: n.id });
    const g = 组.get(键);
    g.数 += 1;
    if (g.例.length < 3) g.例.push(n.名);
  }
  out.分组 = [...组.values()];
  log('\n=== 按「名字前缀 + CSS 尺寸」分组 ===');
  for (const g of out.分组.sort((a, b) => (a.前缀 < b.前缀 ? -1 : a.前缀 > b.前缀 ? 1 : b.数 - a.数))) {
    log(`  ${g.前缀.padEnd(6)} ${String(g.css[0]).padStart(4)}×${String(g.css[1]).padEnd(4)} ×${String(g.数).padStart(2)}  例：${g.例.join(' / ')}`);
  }
  log('\n=== 不同 CSS 宽度 ===');
  const 宽集 = [...new Set(读.map((n) => n.css[0]))].sort((a, b) => a - b);
  log('  ' + 宽集.join(', '));
  log('=== 不同 CSS 高度 ===');
  const 高集 = [...new Set(读.map((n) => n.css[1]))].sort((a, b) => a - b);
  log('  ' + 高集.join(', '));
  log('\n=== 关键节点 ===');
  for (const id of ['node_tadm1nyykc', 'node_5gftn3dnt1', 'node_236ctpehgg', 'node_pxvkay973v', 'node_3bfb9r79qe', 'node_d4tjtpnatq', 'node_gref4sw056']) {
    const n = 读.find((x) => x.id === id);
    log(`  ${id}  ${n ? n.aria + '  css=' + JSON.stringify(n.css) + '  画布=' + JSON.stringify(n.画布) : '（不在画布上）'}`);
  }
  out.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
  out.缩放 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
  log('\n状态行: ' + out.状态行 + ' ｜ 缩放: ' + out.缩放);
} catch (e) { out.出错 = e.message; log('🔴 ' + e.message); }
await p.close();
fs.writeFileSync('/tmp/b223-recon.json', JSON.stringify(out, null, 1));
log('写入 /tmp/b223-recon.json');
process.exit(0);

// 批次 108 · 收尾补丁：门 9 报 `1 selected`，先把选中态清掉再复跑。
//
// 背景：批次 108 的 z 轮收尾读数是 `0 selected`；这次门 9 读到 `1 selected`，
// 且 `node_d4tjtpnatq`（时间线 2）的 canvas 坐标从 `[1476.57, 998.61]`
// 变成了 `[1282.76, 998.61]` ⇒ **别人正在这张共享画布上操作**。
//
// 动作只有一个：**点画布空白处取消选中**。这是无副作用的界面态，
// 不写任何持久数据，不碰任何节点。
// 收尾判据：`sel` 回到 `0`，并记录是谁被选中的（只记录，不动它）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const save = () => writeFileSync(new URL('./_tmp-b108y.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return {
    nodes: (t.match(/(\d+) nodes?/) || [])[1],
    sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1],
    zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
  };
});
// 哪些节点带 .selected —— 只读，不动
const selectedIds = () => p.evaluate(() => Array.from(
  document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));

out.before = await status();
out.selectedBefore = await selectedIds();
log('取消前：', JSON.stringify(out.before), '｜带 .selected 的 id：', JSON.stringify(out.selectedBefore));
save();

// 点画布空白处（x=8 在左栏 12px 左边，y=300 在视口内）
await p.mouse.click(8, 300);
await p.waitForTimeout(1500);
out.afterClick = await status();
out.selectedAfter = await selectedIds();
log('点空白后：', JSON.stringify(out.afterClick), '｜带 .selected 的 id：', JSON.stringify(out.selectedAfter));
save();

// 复核：连读两次，确认不是「读不够就下结论」
out.read2 = await status();
log('连读第二次：', JSON.stringify(out.read2));
out.selStable = out.afterClick.sel === '0' && out.read2.sel === '0';
log('sel 连读一致 =', out.selStable);
save();
log('\nDONE');

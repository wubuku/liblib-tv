// 批次 126 · z 轮（收尾自检）：本批**没有建任何节点、没有点任何扣费/生成控件**，
// 所以护栏只需核「画布终态与开工前逐字一致」：
//   · 节点/连线/选中数；缩放**连读两次**；积分；浮层全清；工具态。
//   · 节点 id 集合与批次 120 存的基线比对（若有该文件）⇒ 证明本批没留下任何自建对象。
import { chromium } from 'playwright';
import { readFileSync, existsSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')).filter(Boolean).sort());
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const tool = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-tool-toggle"]') || document.querySelector('[aria-label*="工具"]');
  return e ? (e.getAttribute('aria-label') || e.innerText || '').replace(/\s+/g, ' ').trim() : null; });

await keyGuard(p);
const r = {};
r.url = p.url();
r.浮层 = await overlays();
r.选中 = await sel();
r.状态行 = await status();
r.credits = await credits();
r.工具态 = await tool();
r.缩放读数1 = await zoom();
await p.waitForTimeout(1500);
r.缩放读数2 = await zoom();
await p.waitForTimeout(1500);
r.缩放读数3 = await zoom();
r.缩放三次一致 = r.缩放读数1 === r.缩放读数2 && r.缩放读数2 === r.缩放读数3;
const now = await ids();
r.节点id数 = now.length;
const base = '/tmp/b120-baseline-ids.txt';
if (existsSync(base)) {
  const bset = new Set(readFileSync(base, 'utf8').split('\n').map((s) => s.trim()).filter(Boolean));
  r.基线文件 = base;
  r.基线id数 = bset.size;
  r.多出来的id = now.filter((x) => !bset.has(x));
  r.少掉的id = [...bset].filter((x) => !now.includes(x));
  r.与基线完全一致 = r.多出来的id.length === 0 && r.少掉的id.length === 0;
} else { r.基线文件 = '不存在（跳过比对，节点计数仍记录）'; }
r.面板在 = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]'));
r.项目信息在 = await p.evaluate(() => !!document.querySelector('[data-testid="workspace-project-info-dialog"]'));
log(JSON.stringify(r, null, 1));
const ok = r.浮层 === 0 && r.选中 === 0 && r.缩放三次一致 && /60%/.test(String(r.缩放读数1)) && /805/.test(String(r.credits)) && !r.面板在 && !r.项目信息在 && (r.与基线完全一致 !== false);
log('\n收尾判定：', ok ? '✅ 干净' : '⛔ 不干净');
process.exit(ok ? 0 : 4);

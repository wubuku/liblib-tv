// 批次 105 · z 轮：量准右键菜单盒子 + 收尾（删两个自建节点 → 归位 → 核对）。
//
// h 轮的教训：我用「面积最大的浮层」去找菜单，结果**把整个 `body`（1280×720）当成菜单**，
// 于是 `items` 里混进了顶栏、时间线节点、别人的上传 toast……
// 读数能蒙对是因为 `innerText` 末尾正好带着菜单那一段，但这种「蒙对」绝不能当判据。
// ⇒ **找浮层要按内容定位（文本以「复制 ⌘ C」开头），不是按面积猜。**
//
// 本轮要删的**恰好两个**，都是本轮自建：
//   `node_p0brqdj8z0`（垃圾 mp4，永久 processing）
//   `node_kk93zz7qzx`（能播的靶子）
// 🔴 三重护栏：删前再确认目标仍 selected → 删后核对「本轮消失的 id」**恰好只有这两个**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const MINE = ['node_p0brqdj8z0', 'node_kk93zz7qzx'];

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    scale: ((t.match(/(\d+)%/) || [])[1]), editable: /Editable/.test(t),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).getAttribute
      ? document.querySelector('[data-testid="canvas-commerce-entry"]').getAttribute('aria-label') : null };
});

// ---- 1. 按**内容**定位菜单，量盒子 ----
const box = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return { x: r.x + r.width / 2, y: r.y + r.height / 4 };
}, 'node_kk93zz7qzx');
await p.mouse.move(box.x, box.y); await p.waitForTimeout(500);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1200);

out.menu = await p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('div,ul,section'));
  const m = all.find((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 60 || r.width > 600 || r.height < 60 || r.height > 900) return false;
    if (getComputedStyle(e).visibility === 'hidden') return false;
    const t = e.innerText.replace(/\s+/g, ' ').trim();
    return t.startsWith('复制 ⌘ C') && t.includes('删除 ⌫') && t.split('⌫').length === 2;
  });
  if (!m) return { found: false };
  const r = m.getBoundingClientRect();
  const rows = Array.from(m.querySelectorAll('button,[role=menuitem]')).map((e) => {
    const rr = e.getBoundingClientRect();
    return { text: e.innerText.replace(/\s+/g, ' ').trim(), w: Math.round(rr.width), h: Math.round(rr.height),
      disabled: e.getAttribute('aria-disabled') };
  }).filter((x) => x.text);
  return { found: true, w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y),
    rows, n: rows.length, text: m.innerText.replace(/\s+/g, ' ').trim() };
});
log('菜单盒子：', JSON.stringify(out.menu, null, 1));

await p.keyboard.press('Escape'); await p.waitForTimeout(800);
out.menuClosed = await p.evaluate(() => Array.from(document.querySelectorAll('div,ul,section'))
  .filter((e) => { const r = e.getBoundingClientRect(); const t = e.innerText.replace(/\s+/g, ' ').trim();
    return r.width > 60 && r.width < 600 && getComputedStyle(e).visibility !== 'hidden' && t.startsWith('复制 ⌘ C') && t.includes('删除 ⌫'); }).length);
log('Esc 之后仍打开的同款菜单数：', out.menuClosed);

// ---- 2. 收尾：先删自建节点 ----
out.start = await status();
log('\n删前状态：', JSON.stringify(out.start));
const idsBefore = await allIds();
out.idsBefore = idsBefore.length;
for (const id of MINE) if (!idsBefore.includes(id)) { log('🔴 目标不存在，中止：', id); writeFileSync(new URL('./_tmp-b105z.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }
log('两个自建节点都在 ✅');

for (const id of MINE) {
  const sel = await p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); return e ? e.classList.contains('selected') : null; }, id);
  log(`  ${id} 删前 selected =`, sel);
  if (!sel) { log('  🔴 不是选中态，先点一下'); }
  if (!sel) {
    const c = await p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 4 }; }, id);
    await p.mouse.move(c.x, c.y); await p.waitForTimeout(400); await p.mouse.click(c.x, c.y); await p.waitForTimeout(900);
  }
  const del = await p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 4 }; }, id);
  await p.mouse.move(del.x, del.y); await p.waitForTimeout(400);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1000);
  const hit = await p.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button,[role=menuitem]')).find((e) => /^删除/.test(e.innerText.trim()));
    if (!b) return null; const r = b.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2, t: b.innerText.trim() };
  });
  log('  删除项：', JSON.stringify(hit));
  if (hit) { await p.mouse.move(hit.x, hit.y); await p.waitForTimeout(350); await p.mouse.click(hit.x, hit.y); }
  await p.waitForTimeout(1500);
  const gone = !(await allIds()).includes(id);
  log(`  ${id} 已删除 =`, gone);
}

const idsAfter = await allIds();
out.idsAfter = idsAfter.length;
out.vanished = idsBefore.filter((x) => !idsAfter.includes(x));
out.appeared = idsAfter.filter((x) => !idsBefore.includes(x));
log('\n消失的 id：', JSON.stringify(out.vanished));
log('新出现的 id：', JSON.stringify(out.appeared));
out.vanishOk = out.vanished.length === 2 && MINE.every((x) => out.vanished.includes(x));
log('护栏：', out.vanishOk ? '✅ 恰好只有本轮两个' : '🔴 不对');

// ---- 3. 归位：缩放 60% + 选择工具 + 0 选中 ----
const tool = await p.evaluate(() => {
  const b = Array.from(document.querySelectorAll('button,[role=button]')).find((e) => /选择工具|抓手|画笔/.test(e.getAttribute('aria-label') || ''));
  return b ? { a: b.getAttribute('aria-label') } : null;
});
log('\n工具态探测：', JSON.stringify(tool));
if (tool && !/选择工具/.test(tool.a)) {
  const c = await p.evaluate(() => { const b = Array.from(document.querySelectorAll('button,[role=button]')).find((e) => /选择工具|抓手|画笔/.test(e.getAttribute('aria-label') || '')); const r = b.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y + r.height / 2 }; });
  await p.mouse.move(c.x, c.y); await p.waitForTimeout(300); await p.mouse.click(c.x, c.y); await p.waitForTimeout(600);
}
out.end = await status();
log('终态：', JSON.stringify(out.end));
out.clean = out.vanishOk && out.end.sel === '0' && out.end.scale === '60';
writeFileSync(new URL('./_tmp-b105z.json', import.meta.url), JSON.stringify(out, null, 1));
log('clean =', out.clean);
await b.close();

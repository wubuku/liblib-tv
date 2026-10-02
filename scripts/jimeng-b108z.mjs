// 批次 108 · z 轮：删掉本轮自建的空组，归位。
//
// 本轮自建且**必须清零**的东西：两个文本节点（已删）+ 一个组（还在，0 成员）。
// 删除顺序：**先删组**，再确认两个成员确实已经不在了。
// 收尾判据：状态行回到 **76 nodes**（本轮开工时的基线）、`0 selected`、
//   `Zoom options, 60%`、工具「选择工具」、积分 805。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
out.groupId = 'node_0ctj8mcr3m';
out.members = ['node_d6cn9z91w6', 'node_8vwsfmqc24'];
const G = out.groupId;
const save = () => writeFileSync(new URL('./_tmp-b108z.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => { const t = document.body.innerText;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const tb = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1], zoom: z ? z.getAttribute('aria-label') : null,
    tool: tb ? tb.getAttribute('aria-label') : null,
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') }; });
const domIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const groupInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const t = n.querySelector('[data-testid="group-title-chrome"]');
  const tr = t ? t.getBoundingClientRect() : null;
  const txt = n.innerText.replace(/\s+/g, ' ').trim();
  return { sel: n.classList.contains('selected'), text: txt.slice(0, 100),
    members: (txt.match(/(\d+) members?/) || [])[1] ?? null,
    title: tr ? { cx: Math.round(tr.x + tr.width / 2), cy: Math.round(tr.y + tr.height / 2) } : null };
}, G);
const spotNow = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect(); const c = [];
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 4)
    for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 4) {
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (el && (el === n || n.contains(el))) c.push({ x, y });
    }
  return { total: c.length, sample: c.slice(0, 4) };
}, id);

out.start = await status();
out.domBefore = (await domIds()).length;
log('起点状态行：', JSON.stringify(out.start), '｜.react-flow__node 计数：', out.domBefore);
out.mineLeft = (await domIds()).filter((x) => x === G || out.members.includes(x) || /resize-chrome/.test(x));
log('本轮遗留 id：', JSON.stringify(out.mineLeft));
save();

// ① 取消选中，免得浮层挡路
await p.mouse.click(8, 300); await p.waitForTimeout(1200);
log('\n取消选中后选中数 =', (await status()).sel);

// ② 选中组 → 右键 → 删除
const sp = await spotNow(G);
out.spot = sp;
log('组落点：', JSON.stringify({ total: sp.total }));
if (!sp.total) { log('🔴 无落点'); save(); await b.close(); process.exit(1); }
const pt = sp.sample[Math.floor(sp.sample.length / 2)];
await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(500);
await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500);
out.gSel = await groupInfo();
log('点组之后：', JSON.stringify(out.gSel));
if (!out.gSel.sel) { log('🔴 没选中，停止'); save(); await b.close(); process.exit(1); }

await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(450);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1400);
const del = await p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('div,ul,section')).find((x) => { const q = x.getBoundingClientRect();
    return q.width > 60 && q.width < 600 && q.height > 60 && getComputedStyle(x).visibility !== 'hidden'
      && (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith('复制 ⌘ C'); });
  if (!m) return { found: false, items: null };
  const items = Array.from(m.querySelectorAll('button,[role=menuitem]')).map((e) => e.innerText.replace(/\s+/g, ' ').trim());
  const btn = Array.from(m.querySelectorAll('button,[role=menuitem]')).find((e) => /^删除/.test(e.innerText.trim()));
  if (!btn) return { found: false, items };
  const q = btn.getBoundingClientRect();
  return { found: true, items, x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2) };
});
out.menu = del;
log('右键菜单：', JSON.stringify(del));
if (del.found) {
  await p.mouse.move(del.x, del.y); await p.waitForTimeout(400);
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2200);
  out.gone = !(await domIds()).includes(G);
  log('组已消失 =', out.gone, '｜状态行', JSON.stringify(await status()));
  if (!out.gone) {
    log('\n>>> 右键删除不奏效，改走 ⌘⇧G（批次 50 记过它能直接清掉空组）');
    const g2 = await keyGuard(p);
    log('keyGuard：', JSON.stringify(g2));
    if (g2.safe) {
      await p.keyboard.press('Meta+Shift+g');
      await p.waitForTimeout(2000);
      out.gone = !(await domIds()).includes(G);
      log('⌘⇧G 后组已消失 =', out.gone, '｜状态行', JSON.stringify(await status()));
    }
  }
} else {
  log('🔴 菜单里没有删除项，中止'); save(); await b.close(); process.exit(1);
}
save();

// ③ 归位
await p.mouse.click(8, 300); await p.waitForTimeout(1200);
const st = await status();
out.finalStatus = st;
log('\n最终状态行：', JSON.stringify(st));
if (!/60%/.test(st.zoom || '')) {
  log('>>> 缩放归位 60%（走批次 106 验过的输入框路径）');
  await p.click('[data-testid="canvas-zoom-percent"]').catch(() => {});
  await p.waitForTimeout(1400);
  await p.fill('[data-testid="canvas-zoom-percent-input"]', '').catch(() => {});
  await p.type('[data-testid="canvas-zoom-percent-input"]', '60', { delay: 200 });
  await p.waitForTimeout(400); await p.keyboard.press('Enter'); await p.waitForTimeout(2000);
  const a = await status(); await p.waitForTimeout(1300); const c = await status();
  out.restored = { a: a.zoom, b: c.zoom, ok: a.zoom === c.zoom && /60%/.test(a.zoom) };
  log('归位读数：', a.zoom, '/', c.zoom, out.restored.ok ? '✅' : '🔴');
}
out.final = await status();
out.domAfter = (await domIds()).length;
out.leftover = (await domIds()).filter((x) => x === G || out.members.includes(x) || /resize-chrome/.test(x));
log('\n最终：', JSON.stringify(out.final));
log('.react-flow__node 计数：', out.domBefore, '→', out.domAfter);
log('本轮遗留 id：', JSON.stringify(out.leftover));
out.clean = out.leftover.length === 0 && out.final.sel === '0' && /60%/.test(out.final.zoom || '')
  && out.final.tool === '选择工具' && out.final.nodes === '76';
log('clean =', out.clean, '（状态行回到开工基线 76 nodes）');
save();
await b.close();

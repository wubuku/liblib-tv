// 批次 105 · z4 轮：核对花名册 + 把缩放归位到 60%。
//
// 情况：z2 轮中止时画布 67 个节点、`node_p0brqdj8z0` 还在；z3 轮一上来就 `__err: gone`
// 且总数 66。⇒ 那个垃圾节点**在两轮之间被别人删掉了**（本项目共享画布，此刻画布上有
// 58 个他人音频节点，另一套会话正在活跃使用）。本轮只做两件事：
//   ① 把花名册整份读出来，确认**我自建的节点一个都不剩**、且没被牵连他人节点；
//   ② 把缩放从 50% 归位到 60%（z3 轮想缩到 40%，但那个下拉里**没有 40% 这一项**，
//      点完停在 50%）。按规矩归位要**回读验证、连读两次相同才算静止**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };

const roster = () => p.evaluate(() => {
  const t = document.body.innerText;
  return {
    n: Array.from(document.querySelectorAll('.react-flow__node')).length,
    sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1],
    scale: (t.match(/(\d+)%/) || [])[1],
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    mine: Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')).filter((i) => /p0brqdj8z0|kk93zz7qzx/.test(i)),
    byKind: {},
  };
});
const r0 = await roster();
for (const e of await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((x) => {
  const t = x.getAttribute('data-testid') || ''; return t.replace(/-(flow-node|simple-player).*$/, '');
}))) r0.byKind[e] = (r0.byKind[e] || 0) + 1;
out.before = r0;
log('归位前：', JSON.stringify({ n: r0.n, sel: r0.sel, scale: r0.scale, credits: r0.credits, mine: r0.mine, byKind: r0.byKind }, null, 1));

// ---- 缩放下拉里到底有哪些档位（顺手把 z3 轮「找不到 40%」这件事查实） ----
const btn = await p.evaluate(() => {
  const b = Array.from(document.querySelectorAll('button,[role=button]')).find((e) => /^\d+%$/.test((e.innerText || '').trim()) && e.getBoundingClientRect().width < 90);
  if (!b) return null; const q = b.getBoundingClientRect(); return { x: q.x + q.width / 2, y: q.y + q.height / 2, t: b.innerText.trim() };
});
log('\n缩放按钮：', JSON.stringify(btn));
let levels = null;
if (btn) {
  await p.mouse.click(btn.x, btn.y); await p.waitForTimeout(900);
  levels = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=menuitem],[role=option],li,div'))
    .map((e) => ({ t: (e.innerText || '').trim(), v: getComputedStyle(e).visibility, r: e.getBoundingClientRect() }))
    .filter((x) => /^\d{2,3}%$/.test(x.t) && x.r.width > 10 && x.r.height > 8 && x.v !== 'hidden')
    .map((x) => x.t));
  levels = Array.from(new Set(levels));
  log('下拉里的档位：', JSON.stringify(levels));
  const opt = await p.evaluate((tg) => {
    const o = Array.from(document.querySelectorAll('button,[role=menuitem],[role=option],li,div'))
      .filter((e) => (e.innerText || '').trim() === tg + '%')
      .map((e) => e.getBoundingClientRect()).filter((r) => r.width > 10 && r.height > 8)[0];
    if (!o) return null; return { x: o.x + o.width / 2, y: o.y + o.height / 2 };
  }, 60);
  if (opt) { await p.mouse.move(opt.x, opt.y); await p.waitForTimeout(350); await p.mouse.click(opt.x, opt.y); }
  else { log('🔴 找不到 60% 项，按 Esc'); await p.keyboard.press('Escape'); }
  await p.waitForTimeout(1600);
}
out.levels = levels;

const s1 = await p.evaluate(() => (document.body.innerText.match(/(\d+)%/) || [])[1]);
await p.waitForTimeout(1200);
const s2 = await p.evaluate(() => (document.body.innerText.match(/(\d+)%/) || [])[1]);
out.scaleBack = { s1, s2, ok: s1 === s2 && s1 === '60' };
log('\n缩放归位读数：', s1, '/', s2, out.scaleBack.ok ? '✅ 静止且为 60%' : '🔴 需重试');

// ---- 工具态 ----
out.tool = await p.evaluate(() => {
  const b = Array.from(document.querySelectorAll('button,[role=button]')).find((e) => /选择工具|抓手|画笔/.test(e.getAttribute('aria-label') || ''));
  return b ? b.getAttribute('aria-label') : null;
});
log('工具态：', out.tool);
out.end = await roster();
log('\n终态：', JSON.stringify({ n: out.end.n, sel: out.end.sel, scale: out.end.scale, credits: out.end.credits, mine: out.end.mine, byKind: out.end.byKind }, null, 1));
out.clean = out.end.sel === '0' && out.end.scale === '60' && out.end.mine.length === 0;
log('clean =', out.clean);
writeFileSync(new URL('./_tmp-b105z4.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

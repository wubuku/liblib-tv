// 批次 107 · z 轮：退出编辑态 → 删掉本轮自建的文本节点 → 归位。
//
// 🔴 本轮自建的只有一枚：`node_gmvz7secas`（`.md` 上传，积分 805→805）。
//   a 轮想建的时间线节点**没建成**（左栏「时间线」那行点下去没有新节点，
//   本轮不追这条，避免在共享画布上乱试）。
//
// 🔴 按批次 105 立的**第四道护栏**删除：点之前用 `elementFromPoint` 证明命中、
//   落点不在任何他人节点矩形内；点之后必须读到 `selected === true` 才继续。
//   画布此刻 ~77 个节点，可用落点极少 —— 拿不到就**中止，不猜、不硬删**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_gmvz7secas' };
const SELF = out.selfId;
const save = () => writeFileSync(new URL('./_tmp-b107z.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => { const t = document.body.innerText;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const tb = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1], zoom: z ? z.getAttribute('aria-label') : null,
    tool: tb ? tb.getAttribute('aria-label') : null,
    inEditor: !!document.querySelector('.tiptap.ProseMirror'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') }; });

out.start = await status();
out.idsBefore = (await allIds()).length;
log('起点：', JSON.stringify(out.start), '｜id 数', out.idsBefore);

// ---- 退出编辑态：点画布空白（不触发任何动作） ----
if (out.start.inEditor) {
  log('\n>>> 退出编辑态（Esc）');
  await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
  out.afterEsc = await status();
  log('Esc 后：', JSON.stringify(out.afterEsc));
  if (out.afterEsc.inEditor) {
    log('  Esc 没退出，改点画布空白');
    await p.mouse.click(60, 400); await p.waitForTimeout(1200);
    out.afterBlank = await status();
    log('  点空白后：', JSON.stringify(out.afterBlank));
  }
  save();
}

// ---- 第四道护栏：找安全落点 ----
out.spot = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e.getAttribute('data-id') !== i)
    .map((e) => { const q = e.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height }; })
    .filter((o) => o.w > 0 && o.h > 0);
  const cands = [];
  for (let fy = 0.15; fy <= 0.85; fy += 0.05) for (let fx = 0.1; fx <= 0.9; fx += 0.05) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
    const el = document.elementFromPoint(x, y);
    if (!el || !(el === n || n.contains(el))) continue;
    if (others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h)) continue;
    cands.push({ x: Math.round(x), y: Math.round(y) });
  }
  return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    others: others.length, total: cands.length, sample: cands.slice(0, 6) };
}, SELF);
log('\n落点诊断：', JSON.stringify(out.spot));
save();

if (out.spot.__err || !out.spot.total) {
  log('🔴 没有安全落点 —— 缩小画布让节点散开');
  // 用批次 106 验过的输入框路径退到 40%
  const cur = await status();
  if (!/40%/.test(cur.zoom || '')) {
    await p.click('[data-testid="canvas-zoom-percent"]').catch(() => {});
    await p.waitForTimeout(1200);
    await p.fill('[data-testid="canvas-zoom-percent-input"]', '').catch(() => {});
    await p.type('[data-testid="canvas-zoom-percent-input"]', '40', { delay: 200 });
    await p.waitForTimeout(400);
    await p.keyboard.press('Enter');
    await p.waitForTimeout(1800);
  }
  out.zoom40 = (await status()).zoom;
  log('缩放读数：', out.zoom40);
  out.spot2 = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e.getAttribute('data-id') !== i)
      .map((e) => { const q = e.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height }; });
    const cands = [];
    for (let fy = 0.15; fy <= 0.85; fy += 0.05) for (let fx = 0.1; fx <= 0.9; fx += 0.05) {
      const x = r.x + r.width * fx, y = r.y + r.height * fy;
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !(el === n || n.contains(el))) continue;
      if (others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h)) continue;
      cands.push({ x: Math.round(x), y: Math.round(y) });
    }
    return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, total: cands.length, sample: cands.slice(0, 6) };
  }, SELF);
  log('40% 下落点诊断：', JSON.stringify(out.spot2));
  out.spot = out.spot2.__err ? out.spot2 : out.spot2;
}
save();

const P = (out.spot && out.spot.sample && out.spot.sample[0]) || null;
if (!P) { log('🔴 仍无安全落点，**中止删除**（不猜、不硬删）'); save(); await b.close(); process.exit(1); }
log('\n用落点：', JSON.stringify(P));

// 点 → 必须读到 selected
await p.mouse.move(P.x, P.y); await p.waitForTimeout(500);
await p.mouse.click(P.x, P.y); await p.waitForTimeout(1300);
const sel = await p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); return e ? e.classList.contains('selected') : null; }, SELF);
out.selected = sel;
log('点击后 selected =', sel);
if (sel !== true) { log('🔴 没选中，**中止删除**'); save(); await b.close(); process.exit(1); }

// 右键 → 删除
await p.mouse.move(P.x, P.y); await p.waitForTimeout(450);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(280); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1200);
const del = await p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('div,ul,section')).find((x) => { const q = x.getBoundingClientRect();
    return q.width > 60 && q.width < 600 && q.height > 60 && getComputedStyle(x).visibility !== 'hidden'
      && (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith('复制 ⌘ C'); });
  if (!m) return null;
  const btn = Array.from(m.querySelectorAll('button,[role=menuitem]')).find((e) => /^删除/.test(e.innerText.trim()));
  if (!btn) return null;
  const q = btn.getBoundingClientRect();
  return { x: q.x + q.width / 2, y: q.y + q.height / 2, t: btn.innerText.replace(/\s+/g, ' ') };
});
log('删除项：', JSON.stringify(del));
if (!del) { log('🔴 菜单里没有删除项，**中止**'); save(); await b.close(); process.exit(1); }
await p.mouse.move(del.x, del.y); await p.waitForTimeout(400);
await p.mouse.click(del.x, del.y);
await p.waitForTimeout(2000);

const idsAfter = await allIds();
out.idsAfter = idsAfter.length;
out.vanished = out.idsBefore ? null : null;
out.gone = !idsAfter.includes(SELF);
out.end = await status();
log('\n节点数：', out.idsBefore, '→', out.idsAfter, '｜目标已消失 =', out.gone);
log('终态：', JSON.stringify(out.end));

// 归位缩放 60%（必要时走输入框路径）
if (!/60%/.test(out.end.zoom || '')) {
  log('\n>>> 缩放归位 60%');
  if (out.end.inEditor) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  await p.click('[data-testid="canvas-zoom-percent"]').catch(() => {});
  await p.waitForTimeout(1300);
  await p.fill('[data-testid="canvas-zoom-percent-input"]', '').catch(() => {});
  await p.type('[data-testid="canvas-zoom-percent-input"]', '60', { delay: 200 });
  await p.waitForTimeout(400);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(2000);
  const e1 = await status(); await p.waitForTimeout(1300); const e2 = await status();
  out.restored = { a: e1.zoom, b: e2.zoom, ok: e1.zoom === e2.zoom && /60%/.test(e1.zoom) };
  log('归位读数：', e1.zoom, '/', e2.zoom, out.restored.ok ? '✅' : '🔴');
}
out.final = await status();
log('\n最终：', JSON.stringify(out.final));
out.clean = out.gone && out.final.sel === '0' && /60%/.test(out.final.zoom || '') && out.final.tool === '选择工具';
log('clean =', out.clean);
save();
await b.close();

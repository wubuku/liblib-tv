// Batch BE4 —— BE3 收尾：修判据、补打乱、拿画布坐标复原。
//
// ⛔ BE3 踩了一个新的判据陷阱：`[...document.querySelectorAll('body *')]` 取 `innerText`
//    **会命中 `<script>`**。LibTV 是 Next.js 站点，`<script>` 里塞着整份 RSC flight payload，
//    **任何文案在里面都搜得到** —— 于是「是否保留此次整理结果？」被判成了「有」，
//    一次调用就吐出 65 KB 噪声，把后面的输出全冲掉了。
//    ✅ 判可见文案**必须先排掉 `script` / `style` / `noscript`**。
//
// ⛔ BE3 第二个 bug：`Object.keys(数组).slice(0,2)` 返回的是**下标 "0" "1"**，
//    不是节点 id，所以「打乱」一步根本没执行（两行都报「无可拖点」）。
//    于是 BE3 的「画布确实是乱的」那行是**空话** —— 乱不乱得由布局间距说了算，
//    不能由「我没拖动成功」反推。
//
// ⛔ BE3 第三个问题：它拿**屏幕坐标**当复原目标，而中途 `⌘0` 改过缩放。
//    ✅ 这一轮全程用**画布坐标**（节点 `transform: translate(Xpx,Ypx)`）当判据，
//    它与视口缩放/平移无关，跨缩放、跨会话都稳定。
//
// 这轮做三件事：
//   ① 先把画布**明确打乱**（用画布坐标确认确实乱了），再按 `⌥⇧F`；
//   ② 键盘按不到就点**底栏那枚「整理画布」按钮**，两条路都试；
//   ③ 复原：按画布坐标把每个节点拖回进场时的位置，**逐个回读**直到收敛。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchBE4';
const { browser, page } = await launch();

/** ⭐ 画布坐标。 */
const flowPos = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const t = getComputedStyle(n).transform;
  const m = /matrix\(([^)]+)\)/.exec(t || '');
  const p = m ? m[1].split(',').map(Number) : null;
  return { id: n.getAttribute('data-id'),
    name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12),
    x: p ? Math.round(p[4]) : null, y: p ? Math.round(p[5]) : null };
}));

/** 布局统计：几行、行内 x 间距有几种取值。间距只有一种取值才算整齐。 */
const stat = (list) => {
  const byRow = {};
  for (const n of list) (byRow[n.y] = byRow[n.y] || []).push(n);
  const rows = Object.keys(byRow).map(Number).sort((a, b) => a - b);
  const gaps = [];
  for (const y of rows) {
    const r = byRow[y].slice().sort((a, b) => a.x - b.x);
    for (let i = 1; i < r.length; i += 1) gaps.push(r[i].x - r[i - 1].x);
  }
  return { rows: rows.length, gaps, kinds: [...new Set(gaps)].length,
    regular: new Set(gaps).size <= 2 && gaps.length > 0 };
};

/** ⭐ 可见文案 —— **排掉 script/style/noscript**。 */
const findBar = (pg) => pg.evaluate(() => {
  const vis = [...document.querySelectorAll('body *')].filter((e) => {
    const t = e.tagName;
    return t !== 'SCRIPT' && t !== 'STYLE' && t !== 'NOSCRIPT' && t !== 'TEMPLATE';
  });
  const barTexts = [...new Set(vis.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => t && t.length < 60 && /是否保留此次整理结果/.test(t)))];
  const btns = [...document.querySelectorAll('button,[role="button"]')].map((e) => {
    const r = e.getBoundingClientRect();
    return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((e) => e.rect[2] > 0 && /^(还原|保留)$/.test(e.text));
  return { barTexts, btns };
});

async function nodePts(pg) {
  return pg.evaluate(() => {
    const res = {};
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const r = n.getBoundingClientRect();
      for (let fy = 0.2; fy <= 0.8; fy += 0.12) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === n) { res[n.getAttribute('data-id')] = { x, y }; break; }
      }
    }
    return res; });
}

/** 拖一个节点，目标是**画布坐标**目标点。内部换算成屏幕位移。 */
async function dragToFlow(pg, id, tx, ty) {
  const fp = await flowPos(pg);
  const cur = fp.find((n) => n.id === id);
  if (!cur) return { ok: false, err: 'no node' };
  const scale = await pg.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = v ? /scale\(([\d.]+)\)/.exec(v.style.transform || '') : null;
    return m ? +m[1] : null; });
  const scr = await pg.evaluate((nid) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height }; }, id);
  if (!scr || !scale) return { ok: false, err: 'no scale/screen' };
  // 节点屏幕左上角 = 画布坐标 × scale + 视口平移。视口平移由当前节点反推。
  const ox = scr.x - cur.x * scale, oy = scr.y - cur.y * scale;
  const wantX = tx * scale + ox, wantY = ty * scale + oy;
  const dx = wantX - scr.x, dy = wantY - scr.y;
  // 找一个独占点
  const pt = await pg.evaluate((nid) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.12) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === n) return { x, y };
    }
    return null; }, id);
  if (!pt) return { ok: false, err: 'no exclusive point' };
  await pg.mouse.move(pt.x, pt.y); await pg.mouse.down();
  for (let i = 1; i <= 12; i += 1) { await pg.mouse.move(pt.x + (dx * i) / 12, pt.y + (dy * i) / 12); await pg.waitForTimeout(55); }
  await pg.mouse.up(); await pg.waitForTimeout(1400);
  const after = (await flowPos(pg)).find((n) => n.id === id);
  return { ok: true, movedTo: after ? [after.x, after.y] : null, err: [Math.round(tx), Math.round(ty)] };
}

const btnRect = (pg, aria) => pg.evaluate((name) => {
  const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === name);
  if (!e) return { err: '没找到 ' + name };
  const r = e.getBoundingClientRect();
  return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
}, aria);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '修 findBar 的 script 噪声 + 修打乱的 id bug + 全程画布坐标' });

  const out = {};
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2200);

  const base = await flowPos();
  const s0 = stat(base);
  console.log('进场基线：', base.length, '个节点，', s0.rows, '行，间距', JSON.stringify(s0.gaps),
    '（不同取值', s0.kinds, '种 →', s0.regular ? '整齐' : '不整齐', '）');
  out.base = base; out.statBase = s0;

  // ═══ ① 明确打乱 —— 这次 id 从 flowPos 正确取
  console.log('\n--- ① 明确打乱 ---');
  const targets = base.slice(0, 3);
  for (let i = 0; i < targets.length; i += 1) {
    const t = targets[i];
    const r = await dragToFlow(page, t.id, t.x + 137 + i * 53, t.y - 111 + i * 79);
    console.log(`  ${t.id} ${r.ok ? `→ ${JSON.stringify(r.movedTo)}` : '✗ ' + r.err}`);
  }
  const messy = await flowPos();
  const sM = stat(messy);
  const changed = messy.filter((n) => { const b = base.find((x) => x.id === n.id); return b && (b.x !== n.x || b.y !== n.y); });
  console.log(`  打乱结果：画布坐标变化 ${changed.length} 个；${sM.rows} 行，间距种类 ${sM.kinds} → ${sM.regular ? '整齐' : '不整齐'}`);
  out.messy = { changed: changed.length, stat: sM, pos: messy };
  out.messyConfirmed = changed.length >= 2 && !sM.regular;
  console.log(`  ⭐ 乱已坐实：${out.messyConfirmed}`);
  if (out.messyConfirmed) {
    await shot(page, 'M-188-整理前-弄乱的画布.png');
    out.shot2 = 'M-188-整理前-弄乱的画布.png';
  }

  // ═══ ② 键盘 ⌥⇧F
  console.log('\n--- ② 键盘 Meta+Alt+F ---');
  await page.mouse.click(720, 300); await page.waitForTimeout(900);
  const bA = await flowPos();
  await page.keyboard.press('Meta+Alt+f'); await page.waitForTimeout(3400);
  await clearToasts(page); await page.waitForTimeout(700);
  const aA = await flowPos();
  const kChanged = aA.filter((n) => { const b = bA.find((x) => x.id === n.id); return b && (b.x !== n.x || b.y !== n.y); }).length;
  const barK = await findBar(page);
  const sK = stat(aA);
  console.log(`  画布坐标变化 ${kChanged} 个；确认条文案 ${JSON.stringify(barK.barTexts)}；按钮 ${JSON.stringify(barK.btns)}`);
  console.log(`  布局：${sK.rows} 行，间距 ${JSON.stringify(sK.gaps)}（${sK.kinds} 种 → ${sK.regular ? '整齐' : '仍不整齐'}）`);
  out.byKey = { changed: kChanged, bar: barK, stat: sK, pos: aA };

  // ═══ ③ 底栏按钮
  console.log('\n--- ③ 底栏「整理画布，Option+Shift+F」按钮 ---');
  const bB = await flowPos();
  const p = await btnRect(page, '整理画布，Option+Shift+F');
  if (p.err) { console.log('  ', p.err); out.byButton = p; }
  else {
    await page.mouse.move(p.x, p.y); await page.waitForTimeout(300);
    await page.mouse.click(p.x, p.y); await page.waitForTimeout(3400);
    await clearToasts(page); await page.waitForTimeout(700);
    const aB = await flowPos();
    const bChanged = aB.filter((n) => { const b = bB.find((x) => x.id === n.id); return b && (b.x !== n.x || b.y !== n.y); }).length;
    const barB = await findBar(page);
    const sB = stat(aB);
    console.log(`  画布坐标变化 ${bChanged} 个；确认条文案 ${JSON.stringify(barB.barTexts)}；按钮 ${JSON.stringify(barB.btns)}`);
    console.log(`  布局：${sB.rows} 行，间距 ${JSON.stringify(sB.gaps)}（${sB.kinds} 种 → ${sB.regular ? '整齐' : '仍不整齐'}）`);
    out.byButton = { changed: bChanged, bar: barB, stat: sB, pos: aB };
    if (bChanged > 0) {
      await shot(page, 'M-189-整理后.png');
      out.shot = 'M-189-整理后.png';
    }
  }

  // ═══ ④ 复原：按画布坐标拖回基线，最多两轮
  console.log('\n--- ④ 复原（按画布坐标）---');
  let rounds = 0;
  let drift = [];
  for (; rounds < 2; rounds += 1) {
    const cur = await flowPos();
    drift = cur.filter((n) => { const b = base.find((x) => x.id === n.id); return !b || Math.abs(b.x - n.x) > 6 || Math.abs(b.y - n.y) > 6; });
    if (!drift.length) break;
    console.log(`  第 ${rounds + 1} 轮：${drift.length} 个节点有偏差，开始拖回`);
    for (const d of drift) {
      const b = base.find((x) => x.id === d.id);
      if (!b) continue;
      const r = await dragToFlow(page, d.id, b.x, b.y);
      if (!r.ok) console.log(`    ${d.id} ✗ ${r.err}`);
    }
  }
  const fin = await flowPos();
  const still = fin.filter((n) => { const b = base.find((x) => x.id === n.id); return !b || Math.abs(b.x - n.x) > 6 || Math.abs(b.y - n.y) > 6; });
  console.log(`  ${rounds} 轮之后仍有偏差：${still.length} 个`);
  still.forEach((d) => { const b = base.find((x) => x.id === d.id);
    console.log(`    ${d.id} ${d.name} 现在 (${d.x},${d.y}) vs 基线 (${b.x},${b.y})`); });
  out.restore = { rounds, still: still.map((d) => { const b = base.find((x) => x.id === d.id);
    return { id: d.id, now: [d.x, d.y], base: [b.x, b.y] }; }), final: fin };
  out.restored = still.length === 0;
  const sF = stat(fin);
  console.log(`  复原后布局：${sF.rows} 行，间距 ${JSON.stringify(sF.gaps)}（${sF.kinds} 种）`);
  out.statFinal = sF;

  await logStep(B, {
    id: 'BE4-fix-criteria-restore-by-flow-coord',
    title: '修判据（排掉 script 噪声）+ 按画布坐标复原 + 钉死整理画布触不触发',
    target: 'BE3 两处判据坏了：findBar 命中 <script> 里的 RSC payload（一次吐 65KB 噪声）；'
      + 'Object.keys(数组).slice(0,2) 拿到的是下标不是 id，导致「打乱」根本没执行。'
      + '这轮全程用画布坐标（transform translate）当判据，它与视口缩放无关。',
    evidence: out,
    visible_text: JSON.stringify({ statBase: out.statBase, messy: { changed: out.messy?.changed, stat: out.messy?.stat },
      byKey: { changed: out.byKey?.changed, bar: out.byKey?.bar, stat: out.byKey?.stat },
      byButton: { changed: out.byButton?.changed, bar: out.byButton?.bar, stat: out.byButton?.stat },
      restored: out.restored, still: out.restore?.still }).slice(0, 3000),
    shot: out.shot || out.shot2,
  });
  console.log('\nBE4 完成');
} finally {
  await browser.close();
}

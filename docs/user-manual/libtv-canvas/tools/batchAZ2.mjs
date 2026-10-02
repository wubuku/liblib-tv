// Batch AZ2 —— 给 AZ1 的三处翻车补判据，重测。
//
// AZ1 的结果要**分类处理**：
//
// ✅ 真发现：「定位到节点」不是「移动某个节点」，是**平移整张画布**
//    （点行内小图标后六个节点全部 +594px，x 一起变），
//    而且顺带**改了缩放** —— 定位前节点 148×148，定位后 350×350。
//    这解释了为什么定位之后参数面板变得又大又挡手。
//
// ⚠️ 作废一：**图片节点参数条的 tooltip 全是底栏的。**
//    AZ1 那批按钮 rect 都在 y=747..779 —— **底栏工具条就压在 y≈745..770**。
//    我按 rect 算中心点去悬停，鼠标实际落在底栏按钮上，
//    于是读回 `移动` / `素材库` / `生成历史`（底栏三枚的真实名字）。
//    ⚠️ 这是 AX §25.1「点偏了」的**镜像版**：那次是坐标算出视口外，
//    这次是坐标**算对了、但那个点上压着别的东西**。
//    → 补的硬闸：**悬停/点击前验 `elementFromPoint(x,y).closest(button) === 目标按钮`**，
//      对不上就不读、记成「被底栏遮住」。
//
// ⚠️ 作废二：重名定位的「离中心最近」判据把 350×350 的导演台排到了前面。
//    → 改成**先按名字过滤出同名的候选，再在候选里排名**。
//
// 这轮做三件事：
// A. 图片节点参数条七枚 —— **先验落点归属**，并把面板挪到**底栏之上**再读 tooltip
// B. 重名「定位到节点」：第 1 行 vs 第 2 行，分别落到哪一个 `data-id`
// C. 顺带量准「定位到节点」对画布做了什么（pan / zoom 各多少）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAZ2';
const { browser, page } = await launch();

/** 底栏工具条顶边 —— 落点 y 超过它就悬停到别的东西了。 */
const TOOLBAR_TOP = 735;

async function hoverTooltip(cx, cy, waitMs = 1000) {
  await page.mouse.move(cx, cy);
  await page.waitForTimeout(waitMs);
  return page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"],[role="tooltip"]')]
    .filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; })
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter(Boolean));
}
const NOISE = /^(按 ESC 退出|新功能：.+)$/;
const clean = (l) => l.filter((t) => !NOISE.test(t));

/**
 * 悬停读 tooltip，但**先验落点归属**。
 * AX §25.1 的镜像版教训：坐标算对了，那个点上可能压着别的东西。
 * 这次直接要求 `elementFromPoint(x,y).closest('button,[role=button]')` 就是目标。
 */
async function hoverVerified(page, rect, label) {
  const x = Math.round(rect[0] + rect[2] / 2);
  const y = Math.round(rect[1] + rect[3] / 2);
  const owner = await page.evaluate(([px, py]) => {
    const e = document.elementFromPoint(px, py);
    if (!e) return { tag: null, owner: 'nothing' };
    const b = e.closest('button,[role="button"]');
    if (!b) return { tag: e.tagName, owner: 'not-a-button' };
    return { tag: e.tagName, owner: 'button',
      ownerText: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
      ownerAria: b.getAttribute('aria-label'),
      ownerFp: (() => { const s = b.querySelector('svg'); if (!s) return 'nosvg';
        const d = [...s.querySelectorAll('path')].map((z) => z.getAttribute('d') || '').filter(Boolean);
        return d.length ? d.sort((a, c) => c.length - a.length)[0].slice(0, 26) : 'svgonly'; })() };
  }, [x, y]);
  const looksRight = owner.owner === 'button'
    && (owner.ownerFp || '').startsWith(label.fp || '§');
  const blocked = y > TOOLBAR_TOP || owner.owner !== 'button';
  if (blocked) return { skipped: `落点在 (${x},${y})，${y > TOOLBAR_TOP ? '**压在底栏工具条上**' : '不是按钮'}`, owner };
  const tip = clean(await hoverTooltip(x, y));
  return { point: [x, y], owner, tip };
}

const roster = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
  return { id: n.getAttribute('data-id') || '?',
    cls: ((/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || '?'),
    name: (/^[^\s]+(?:\s+\d+)?/.exec(t) || [''])[0].slice(0, 14),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
}));

const scale = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  if (!v) return null;
  const m = /scale\(([\d.]+)\)/.exec(v.style.transform || '');
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(v.style.transform || '');
  return { scale: m ? +m[1] : null, tx: t ? +t[1] : null, ty: t ? +t[2] : null };
});

async function readBars() {
  return page.evaluate(() => {
    const n = document.querySelector('.react-flow__node.selected');
    if (!n) return { err: '没选中节点' };
    const panels = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter((o) => o.r.width >= 480 && o.r.height >= 100)
      .filter((o) => o.e.querySelectorAll('button,[role="button"]').length >= 3);
    if (!panels.length) return { err: '没找到参数面板' };
    const p = panels.sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height))[0];
    const fp = (x) => { const s = x.querySelector('svg'); if (!s) return 'nosvg';
      const d = [...s.querySelectorAll('path')].map((z) => z.getAttribute('d') || '').filter(Boolean);
      return d.length ? d.sort((a, b) => b.length - a.length)[0].slice(0, 30) : 'svgonly'; };
    const all = [...p.e.querySelectorAll('button,[role="button"]')].map((x) => { const q = x.getBoundingClientRect();
      return { text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), aria: x.getAttribute('aria-label'),
        fp: fp(x), disabled: x.disabled === true, cursor: getComputedStyle(x).cursor,
        rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; })
      .filter((b) => b.rect[2] > 0);
    const maxY = Math.max(...all.map((b) => b.rect[1] + b.rect[3]));
    const minY = Math.min(...all.map((b) => b.rect[1]));
    return { panelRect: [Math.round(p.r.x), Math.round(p.r.y), Math.round(p.r.width), Math.round(p.r.height)],
      panelText: (p.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      bottomBar: all.filter((b) => maxY - (b.rect[1] + b.rect[3]) <= 8),
      topToolBar: all.filter((b) => b.rect[1] - minY <= 4) };
  });
}

/** 借抽屉的「定位到节点」把目标拉到画面，再找一个**独占**的点击点。 */
async function locateAndSelect(pg, rowName) {
  const b = await pg.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => /资产管理/.test(x.getAttribute('aria-label') || x.getAttribute('title') || ''));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (!b) return { err: '没有资产管理按钮' };
  await pg.mouse.click(b.cx, b.cy); await pg.waitForTimeout(3000); await clearToasts(pg);
  const row = await pg.evaluate((nm) => {
    const e = [...document.querySelectorAll('body div,body section,body aside')]
      .find((x) => ((x.className || '') + '').includes('mantine-Drawer-content'));
    if (!e) return { err: '抽屉没开' };
    const rows = [...e.querySelectorAll('button,[role="button"]')].map((n) => { const r = n.getBoundingClientRect();
      return { aria: n.getAttribute('aria-label'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((b) => (b.aria || '').startsWith('定位到节点') && b.rect[2] > 200 && (b.aria || '').replace('定位到节点', '').trim() === nm);
    return rows.length ? rows[0] : { err: `没找到行「${nm}」` };
  }, rowName);
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(1500); // 先关抽屉，避免它挡着
  if (row.err) return row;
  // 关了抽屉坐标就变了，重开一次点完立刻关
  await pg.mouse.click(b.cx, b.cy); await pg.waitForTimeout(2600);
  const r2 = await pg.evaluate((nm) => {
    const e = [...document.querySelectorAll('body div,body section,body aside')]
      .find((x) => ((x.className || '') + '').includes('mantine-Drawer-content'));
    const rows = [...e.querySelectorAll('button,[role="button"]')].map((n) => { const r = n.getBoundingClientRect();
      return { aria: n.getAttribute('aria-label'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((b) => (b.aria || '').startsWith('定位到节点') && b.rect[2] > 200 && (b.aria || '').replace('定位到节点', '').trim() === nm);
    return rows.length ? rows[0] : null;
  }, rowName);
  await pg.mouse.click(r2.rect[0] + 40, r2.rect[1] + r2.rect[3] / 2);
  await pg.waitForTimeout(3600);
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(2000);
  await clearToasts(pg);
  return { clicked: r2.rect };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2000);
  await beginBatch(B, { note: '补 AZ1 三处翻车的判据：落点归属硬闸 + 同名候选内排名 + 量准 pan/zoom' });

  const out = {};

  // ═══ C（先做，成本最低）：定位到底改了画布什么
  console.log('--- AZ2 C 「定位到节点」对画布做了什么 ---');
  const s0 = await scale(); const r0 = await roster();
  console.log('定位前 scale:', JSON.stringify(s0));
  await locateAndSelect(page, '图片节点 2');
  const s1 = await scale(); const r1 = await roster();
  console.log('定位后 scale:', JSON.stringify(s1));
  out.locateEffect = { scaleBefore: s0, scaleAfter: s1,
    before: r0.slice(0, 4).map((n) => ({ id: n.id, rect: n.rect })),
    after: r1.slice(0, 4).map((n) => ({ id: n.id, rect: n.rect })) };

  // ═══ A：图片节点参数条 —— 先把面板挪到底栏之上
  console.log('\n--- AZ2 A 图片节点参数条（落点归属硬闸）---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  // 缩到 42% 左右，整块面板能进画面上部
  for (let i = 0; i < 3; i += 1) { await page.keyboard.press('Meta+-'); await page.waitForTimeout(500); }
  await fitView(page); await page.waitForTimeout(1600);
  const imgs = (await roster()).filter((n) => n.cls === 'image');
  console.log('图片节点:', JSON.stringify(imgs));
  let picked = null;
  for (const cand of imgs) {
    const pt = await page.evaluate((id) => {
      const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === id);
      if (!t) return { err: 'no node' };
      const r = t.getBoundingClientRect();
      for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === t) return { x, y };
      }
      return { err: 'no exclusive point' };
    }, cand.id);
    console.log(`  ${cand.id} →`, JSON.stringify(pt));
    if (pt.err) continue;
    await page.mouse.click(pt.x, pt.y);
    await page.waitForTimeout(3800);
    const sel = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { ok: false };
      const t = (n.innerText || '').replace(/\s+/g, ' ');
      return { ok: t.includes('图片节点'), id: n.getAttribute('data-id'), text: t.trim().slice(0, 50) };
    });
    console.log('   选中:', JSON.stringify(sel));
    if (sel.ok) { picked = sel; break; }
    await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  }
  out.picked = picked;
  if (!picked) console.log('  ⚠ 没选中');
  else {
    const bar = await readBars();
    if (bar.err) { console.log('  ⚠', bar.err); out.bars = { err: bar.err }; }
    else {
      console.log(`  面板=[${bar.panelRect}] 工具条 ${bar.topToolBar.length} / 参数条 ${bar.bottomBar.length}`);
      console.log(`  文案: ${bar.panelText.slice(0, 180)}`);
      const named = [];
      for (const b of bar.bottomBar) {
        const r = await hoverVerified(page, b.rect, { fp: b.fp });
        named.push({ rect: b.rect, text: b.text, aria: b.aria, fp: b.fp.slice(0, 24),
          disabled: b.disabled, cursor: b.cursor, ...r });
        console.log(`   [${String(b.rect).padEnd(20)}] ${(b.text || '-').padEnd(14)} aria=${(b.aria || '-').padEnd(8)} dis=${b.disabled ? 'Y' : 'n'} fp=${b.fp.slice(0, 18).padEnd(19)} ${r.skipped ? '⚠ ' + r.skipped : '→ ' + JSON.stringify(r.tip)}`);
      }
      out.bars = { panelRect: bar.panelRect, panelText: bar.panelText, bottom: named,
        toolBar: bar.topToolBar.map((b) => ({ rect: b.rect, text: b.text, fp: b.fp.slice(0, 20) })) };
      await shot(page, 'M-169-图片-参数条按钮命名.png');
      out.shot = 'M-169-图片-参数条按钮命名.png';
    }
  }

  // ═══ B：重名定位 —— 先按名字过滤候选，再在候选里排名
  console.log('\n--- AZ2 B 重名「定位到节点」---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await fitView(page); await page.waitForTimeout(1600);
  out.dup = {};
  for (const which of [0, 1]) {
    const pre = await roster();
    const cands = pre.filter((n) => n.name === '视频节点 3');
    if (cands.length < 2) { console.log(`第 ${which + 1} 行前：只找到 ${cands.length} 个「视频节点 3」`); continue; }
    console.log(`\n--- 点第 ${which + 1} 行 ---`);
    console.log('候选:', JSON.stringify(cands.map((c) => ({ id: c.id, rect: c.rect }))));
    await locateAndSelect(page, '视频节点 3');
    const post = await roster();
    const same = post.filter((n) => n.name === '视频节点 3');
    console.log('定位后同名节点:', JSON.stringify(same.map((c) => ({ id: c.id, rect: c.rect }))));
    const vis = (n) => n.rect[0] + n.rect[2] > 0 && n.rect[0] < 1440 && n.rect[1] + n.rect[3] > 60;
    const visible = same.filter(vis);
    console.log(`  定位后仍在视口内: ${visible.length} 个 →`,
      JSON.stringify(visible.map((v) => ({ id: v.id, rect: v.rect }))));
    // 判据：**只有它进了视口** / **它最靠近视口中心**，且只在同名候选里比
    const ranked = same.slice().sort((a, b2) =>
      Math.hypot(a.cx - 720, a.cy - 300) - Math.hypot(b2.cx - 720, b2.cy - 300));
    console.log('  同名候选里离中心最近:', JSON.stringify(ranked[0]));
    out.dup[`row${which + 1}`] = { before: cands.map((c) => ({ id: c.id, rect: c.rect })),
      after: same.map((c) => ({ id: c.id, rect: c.rect })),
      visibleIds: visible.map((v) => v.id), winner: ranked[0].id };
    if (which === 0) await shot(page, 'M-170-重名-定位到节点.png'), (out.shot2 = 'M-170-重名-定位到节点.png');
  }
  console.log('\n两行分别落到:', JSON.stringify({ r1: out.dup.row1 && out.dup.row1.winner, r2: out.dup.row2 && out.dup.row2.winner }));
  console.log('是不是同一个:', out.dup.row1 && out.dup.row2 && (out.dup.row1.winner === out.dup.row2.winner));

  await logStep(B, {
    id: 'AZ2-image-bar-verified', title: '图片节点参数条（落点归属硬闸）+ 重名定位 + 定位对画布的影响',
    target: '补 AZ1 三处翻车：①tooltip 被底栏工具条污染 —— 悬停前加 '
      + '`elementFromPoint(x,y).closest(button) === 目标` 硬闸；②重名排名没先按名字过滤；'
      + '③「定位到节点」到底改了画布什么。全只读。',
    evidence: out,
    visible_text: JSON.stringify({ picked: out.picked, bars: out.bars,
      dup: out.dup, locateEffect: out.locateEffect }).slice(0, 3500),
    shot: out.shot,
  });
  console.log('\nAZ2 完成');
} finally {
  await browser.close();
}

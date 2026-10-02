// Batch AZ —— 攻「图片节点始终选不中」+ 顺手坐实「定位到节点」在重名时选哪一个。
//
// AY3 留下的坑：图片节点两次都没选中成功，回读 `selectedType` 都是 `video`。
// AY3 当时的归因是「节点重叠，点到了压在上面的视频节点」，并发现两个图片候选
// 的 `hitPt` **全是 `null`**（5 个探测点全被别的元素挡住）。
//
// 这批换个思路解死结：
//   **别在画布上找目标，改用抽屉自己的「定位到节点」把它拉到视口中央。**
//   那枚按钮的既定行为（手册 M-37 已实测）就是「把节点拉回视口中央」，
//   正好是「制造一个不重叠的现场」需要的那一步 ——
//   ⭐ 用产品自己的功能给取证脚本铺路，比自己算坐标可靠。
//
// 三件事：
// A. 借「定位到节点」把图片节点拉到中央 → 选它 → **参数条全量清点 + tooltip 普查**
//    （回答悬而未决的那一问：图片节点到底有没有 `📄 提示词优化`、总共几枚）
// B. **重名时的「定位到节点」** —— 画布上确有两张都叫「视频节点 3」的卡片，
//    点第 1 行的「定位到节点」，看被拉到中央的是哪一张（按 `data-id` 认人）
// C. 抽屉每行**第三枚**小图标（SVG `M19.51.09a.9.9 0 0 1`，aria 也是
//    `定位到节点 XXX`）—— 它和整行点下去**是不是同一件事**？
//
// ⚠️ 全只读：不生成、不上传、不删除、不改名。「定位到节点」只改变视口位置。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAZ1';
const { browser, page } = await launch();

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

/** 画布上所有节点的「身份卡」：data-id + 名字 + 中心点。按 data-id 认人才靠得住。 */
const roster = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
  return { id: n.getAttribute('data-id') || '(无 data-id)',
    cls: ((/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || '?'),
    name: (/^[^\s]+(?:\s+\d+)?/.exec(t) || [''])[0].slice(0, 14),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
}));

/**
 * 找一个**只属于目标节点**的点击点。
 *
 * AY3 的教训：`elementFromPoint` 只回「落点是不是在某个节点里」，
 * 回不出「是哪一个」—— 三张节点叠着的时候全都通过，于是点到压着的那个。
 * 这里直接要求 **`elementFromPoint(...).closest('.react-flow__node') === 目标节点`**，
 * 在节点框内扫一张网格，逐点验证，拿到第一个通过的。
 */
async function exclusiveClickPoint(pg, nodeId) {
  return pg.evaluate((id) => {
    const target = [...document.querySelectorAll('.react-flow__node')]
      .find((n) => n.getAttribute('data-id') === id);
    if (!target) return { err: '找不到节点 ' + id };
    const r = target.getBoundingClientRect();
    const tried = [];
    for (let fy = 0.15; fy <= 0.9; fy += 0.15) {
      for (let fx = 0.04; fx <= 0.97; fx += 0.04) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const o = document.elementFromPoint(x, y);
        const owner = o ? o.closest('.react-flow__node') : null;
        tried.push([x, y, owner ? (owner.getAttribute('data-id') || '?') : 'none']);
        if (owner === target) return { x, y, tries: tried.length };
      }
    }
    return { err: '这个节点被完全盖住了，没有独占的点', tries: tried.length, sample: tried.slice(0, 8) };
  }, nodeId);
}

/** 开抽屉，返回「画布」标签下每一行的结构。 */
async function openDrawerRows() {
  const b = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => /资产管理/.test(x.getAttribute('aria-label') || x.getAttribute('title') || ''));
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (!b) return { err: '底栏没有「资产管理」' };
  await page.mouse.click(b.cx, b.cy);
  await page.waitForTimeout(3200); await clearToasts(page);
  return page.evaluate(() => {
    const e = [...document.querySelectorAll('body div,body section,body aside')]
      .find((x) => ((x.className || '') + '').includes('mantine-Drawer-content'));
    if (!e) return { err: '抽屉没打开' };
    const fp = (n) => { const s = n.querySelector('svg'); if (!s) return 'nosvg';
      const ds = [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').filter(Boolean);
      return ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 26) : 'svgonly'; };
  const btns = [...e.querySelectorAll('button,[role="button"]')].map((n) => { const r = n.getBoundingClientRect();
      return { text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
        aria: n.getAttribute('aria-label'), fp: fp(n),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((b) => b.rect[2] > 0 && b.rect[1] > 180 && b.rect[1] < 700);
    // 一行 = 整行（宽 >200）+ ⋯ + 定位小图标
    const rows = [];
    for (const b of btns) {
      if (!b.aria || !b.aria.startsWith('定位到节点')) continue;
      if (b.rect[2] > 200) rows.push({ name: b.aria.replace('定位到节点', '').trim(), rect: b.rect, fp: b.fp });
    }
    return { n: btns.length, rows };
  });
}

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
      const ds = [...s.querySelectorAll('path')].map((z) => z.getAttribute('d') || '').filter(Boolean);
      return ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 30) : 'svgonly'; };
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

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2000);
  await beginBatch(B, { note: '借「定位到节点」解开节点重叠 → 图片节点参数条；重名定位；行内第三枚图标' });

  const out = {};

  // ═══ A + B：开抽屉，取第一行「图片节点」
  console.log('--- AZ A/B 开抽屉 ---');
  const rows = await openDrawerRows();
  if (rows.err) throw new Error(rows.err);
  console.log('抽屉可点元素', rows.n, '行按钮', rows.rows.length);
  rows.rows.forEach((r, i) => console.log(`  行 ${i}: "${r.name}" rowBtn=[${r.rect}] fp=${r.fp}`));
  out.drawerRows = rows.rows.map((r) => ({ name: r.name, rect: r.rect, fp: r.fp }));

  const before = await roster();
  console.log('\n画布名册（按 data-id 认人）:');
  before.forEach((n) => console.log(`  ${n.id} ${n.cls.padEnd(6)} "${n.name}" rect=[${n.rect}] center=(${n.cx},${n.cy})`));
  out.rosterBefore = before;

  // ── A：定位第一行「图片节点 2」的那个
  const imgRow = rows.rows.find((r) => r.name.startsWith('图片节点'));
  if (!imgRow) throw new Error('抽屉里没有图片节点行');
  console.log(`\n点行按钮「定位到节点 ${imgRow.name}」 → [${imgRow.rect}]`);
  await page.mouse.click(imgRow.rect[0] + 40, imgRow.rect[1] + imgRow.rect[3] / 2); // 点整行左侧，避开右侧两枚
  await page.waitForTimeout(3600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1800); // 关抽屉，别挡着
  await clearToasts(page);
  const afterLocate = await roster();
  console.log('定位之后:');
  afterLocate.forEach((n) => console.log(`  ${n.id} "${n.name}" rect=[${n.rect}] center=(${n.cx},${n.cy})`));
  out.rosterAfterLocate = afterLocate;

  // 找出被拉到中央的那个（离 720,150 最近）
  const centered = afterLocate.slice().sort((a, b) =>
    Math.hypot(a.cx - 720, a.cy - 150) - Math.hypot(b.cx - 720, b.cy - 150))[0];
  console.log('离视口中心最近的是:', JSON.stringify(centered));
  out.centeredAfterLocate = centered;

  // 选它（用「独占点击点」，不是中心点 —— 中心点早被压着的节点抢走了）
  let picked = null;
  const imgNodes = afterLocate.filter((n) => n.cls === 'image');
  console.log(`\n画布上有 ${imgNodes.length} 个图片节点:`);
  imgNodes.forEach((n) => console.log(`  ${n.id} rect=[${n.rect}] center=(${n.cx},${n.cy})`));
  for (const cand of imgNodes) {
    const pt = await exclusiveClickPoint(page, cand.id);
    console.log(`  ${cand.id} 找独占点击点 →`, JSON.stringify(pt));
    if (pt.err) continue;
    await page.mouse.click(pt.x, pt.y);
    await page.waitForTimeout(3800);
    const sel = await page.evaluate((kw) => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { ok: false, why: '没选中' };
      const t = (n.innerText || '').replace(/\s+/g, ' ');
      return { ok: t.includes(kw), cls: n.getAttribute('data-id'),
        type: (/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || '?', text: t.trim().slice(0, 60) };
    }, '图片节点');
    console.log('   选中判定:', JSON.stringify(sel));
    if (sel.ok) { picked = { ...sel, point: [pt.x, pt.y] }; break; }
    await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  }
  out.picked = picked;
  if (!picked) {
    console.log('  ⚠ 还是没选中图片节点');
  } else {
    const bar = await readBars();
    if (bar.err) { console.log('  ⚠', bar.err); out.bars = { err: bar.err }; }
    else {
      console.log(`\n  ✅ 选中 ${picked.type} 面板=[${bar.panelRect}]`);
      console.log(`     面板文案: ${bar.panelText.slice(0, 200)}`);
      console.log(`     工具条 ${bar.topToolBar.length} 枚 / 参数条 ${bar.bottomBar.length} 枚`);
      const named = [];
      for (const b of bar.bottomBar) {
        const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
        const tip = (cx < 0 || cx > 1440) ? ['出视口'] : clean(await hoverTooltip(cx, cy, 950));
        named.push({ rect: b.rect, text: b.text, aria: b.aria, fp: b.fp.slice(0, 22), disabled: b.disabled, cursor: b.cursor, tip });
        console.log(`      [${String(b.rect).padEnd(20)}] ${(b.text || '-').padEnd(14)} aria=${(b.aria || '-').padEnd(8)} dis=${b.disabled ? 'Y' : 'n'} fp=${b.fp.slice(0, 18).padEnd(19)} → ${JSON.stringify(tip)}`);
      }
      const tn = bar.topToolBar.map((b) => ({ rect: b.rect, text: b.text, aria: b.aria, fp: b.fp.slice(0, 20), cursor: b.cursor }));
      console.log('      工具条:', JSON.stringify(tn));
      out.bars = { picked, panelRect: bar.panelRect, panelText: bar.panelText, bottom: named, toolBar: tn };
      await shot(page, 'M-169-图片-参数条按钮命名.png');
      out.shot = 'M-169-图片-参数条按钮命名.png';
    }
  }

  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  // ═══ B：重名时的「定位到节点」
  console.log('\n--- AZ B 重名定位 ---');
  const dup = before.filter((n) => n.name === '视频节点 3');
  console.log(`画布上叫「视频节点 3」的有 ${dup.length} 个:`, JSON.stringify(dup.map((d) => d.id)));
  out.dupVideoNodes = dup;
  if (dup.length >= 2) {
    const rows2 = await openDrawerRows();
    const vrows = (rows2.rows || []).filter((r) => r.name === '视频节点 3');
    console.log('抽屉里「视频节点 3」行数:', vrows.length, JSON.stringify(vrows.map((r) => r.rect)));
    out.dupRows = vrows.map((r) => r.rect);
    if (vrows.length >= 2) {
      const pre = await roster();
      const near = (id) => (pre.find((n) => n.id === id) || {});
      console.log('点**第 1 行**的「定位到节点」…');
      await page.mouse.click(vrows[0].rect[0] + 40, vrows[0].rect[1] + vrows[0].rect[3] / 2);
      await page.waitForTimeout(3800);
      await page.keyboard.press('Escape'); await page.waitForTimeout(1800); await clearToasts(page);
      const post = await roster();
      const best = post.slice().sort((a, b) => Math.hypot(a.cx - 720, a.cy - 150) - Math.hypot(b.cx - 720, b.cy - 150))[0];
      console.log('定位后离中心最近:', JSON.stringify(best));
      out.dupResult = { clickedRowIndex: 0, rows: vrows.length,
        beforeIds: dup.map((d) => ({ id: d.id, rect: d.rect })),
        landedOn: best, post: post.filter((n) => n.name === '视频节点 3').map((n) => ({ id: n.id, rect: n.rect })) };
      await shot(page, 'M-170-重名-定位到节点.png');
      out.shot2 = 'M-170-重名-定位到节点.png';
    }
  }

  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);

  // ═══ C：行内第三枚小图标 = 跟整行同一件事吗
  console.log('\n--- AZ C 行内第三枚图标 ---');
  const rows3 = await openDrawerRows();
  const r0 = (rows3.rows || [])[0];
  if (r0) {
    const icons = await page.evaluate((y) => {
      const e = [...document.querySelectorAll('body div,body section,body aside')]
        .find((x) => ((x.className || '') + '').includes('mantine-Drawer-content'));
      if (!e) return [];
      return [...e.querySelectorAll('button,[role="button"]')].map((n) => { const r = n.getBoundingClientRect();
        const s = n.querySelector('svg');
        const ds = s ? [...s.querySelectorAll('path')].map((z) => z.getAttribute('d') || '').filter(Boolean) : [];
        return { text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), aria: n.getAttribute('aria-label'),
          fp: ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 26) : (s ? 'svgonly' : 'nosvg'),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
      }).filter((b) => b.rect[3] > 0 && Math.abs(b.rect[1] - y) < 8);
    }, r0.rect[1] + 6);
    console.log(`第一行三枚:`, JSON.stringify(icons));
    const small = icons.find((b) => b.rect[2] <= 30 && (b.fp || '').startsWith('M19.51.09'));
    if (small) {
      const pre = await roster();
      await page.mouse.click(small.rect[0] + small.rect[2] / 2, small.rect[1] + small.rect[3] / 2);
      await page.waitForTimeout(3600);
      const mid = await roster();
      await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
      console.log('点这枚小图标前后节点位置变化:');
      pre.forEach((p) => { const m = mid.find((x) => x.id === p.id);
        if (m) console.log(`  ${p.id} [${p.rect}] → [${m.rect}] ${p.rect.join() !== m.rect.join() ? '动了' : '没动'}`); });
      out.rowIcon = { icon: small, before: pre.map((p) => ({ id: p.id, rect: p.rect })),
        after: mid.map((m) => ({ id: m.id, rect: m.rect })),
        moved: pre.filter((p) => { const m = mid.find((x) => x.id === p.id); return m && p.rect.join() !== m.rect.join(); }).map((p) => p.id) };
      console.log('  移动过的节点:', JSON.stringify(out.rowIcon.moved));
    } else console.log('  ⚠ 没找到那枚小图标');
  }

  await logStep(B, {
    id: 'AZ1-image-bar-and-dup-locate', title: '借「定位到节点」解开重叠 → 图片节点参数条；重名定位；行内小图标',
    target: 'AY3 图片节点两次都没选中（`hitPt` 全 null）。这轮**不自己算坐标**，改用产品自己的'
      + '「定位到节点」把目标拉到视口中央制造干净现场 —— 用产品功能给取证脚本铺路。'
      + '顺带实测画布上两张同名「视频节点 3」时，点第 1 行会定位到哪一个。全只读。',
    evidence: out,
    visible_text: JSON.stringify({ picked: out.picked, bars: out.bars,
      dup: out.dupResult, rowIcon: out.rowIcon && { moved: out.rowIcon.moved } }).slice(0, 3500),
    shot: out.shot,
  });
  console.log('\nAZ1 完成');
} finally {
  await browser.close();
}

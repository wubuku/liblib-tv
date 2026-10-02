// Batch BC1 —— 补最后两个节点类型的覆盖缺口 + 验摄像机开关。
//
// 覆盖盘点到这一步：视频 / 图片 / 音频 / 文本 / 智能剪辑 五类参数条都逐枚清点过，
// **只剩「逐帧拉片」和「导演台」两类从没点开过参数面板** —— 九类节点里唯一的两块空白。
//
// 三件事：
// A. 逐帧拉片 节点参数条
// B. 导演台 节点参数条
// C. 摄像机面板的「关闭」开关 —— 手册写的是「它的作用应该是…，具体影响没验 📖」。
//    这轮**打开它 → 读面板变化 → 关回去**，并**逐字确认复原**。
//    ⚠️ 它会写进节点参数，所以必须记下原值并在最后复原。
//
// 判据沿用已经换过血的那几版：
//   · 悬停读 tooltip 前**先验落点归属**（AZ：坐标对 ≠ 落点归你）
//   · 点选项/按钮一律用 Playwright `getByText`（BB2：别硬猜 DOM 结构）
//   · 选节点用**独占网格点** + 回读 innerText 一致性闸（AY3/AZ2）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBC1';
const { browser, page } = await launch();

const TOOLBAR_TOP = 735;

async function hoverTooltip(cx, cy, waitMs = 900) {
  await page.mouse.move(cx, cy);
  await page.waitForTimeout(waitMs);
  return page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"],[role="tooltip"]')]
    .filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; })
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean));
}
const NOISE = /^(按 ESC 退出|新功能：.+)$/;
const clean = (l) => l.filter((t) => !NOISE.test(t));

async function hoverVerified(pg, rect) {
  if (!rect || rect.length < 4 || !rect.every((v) => Number.isFinite(v))) {
    return { skipped: `按钮 rect 不完整（${JSON.stringify(rect)}），不悬停`, owner: null };
  }
  const x = Math.round(rect[0] + rect[2] / 2), y = Math.round(rect[1] + rect[3] / 2);
  const owner = await pg.evaluate(([px, py]) => {
    const e = document.elementFromPoint(px, py);
    if (!e) return { kind: 'nothing' };
    const b = e.closest('button,[role="button"]');
    return b ? { kind: 'button', text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18), aria: b.getAttribute('aria-label') }
      : { kind: 'not-button', tag: e.tagName };
  }, [x, y]);
  if (y > TOOLBAR_TOP || owner.kind !== 'button') {
    return { skipped: `落点 (${x},${y}) ${y > TOOLBAR_TOP ? '压在底栏工具条上' : owner.kind}`, owner };
  }
  return { point: [x, y], owner, tip: clean(await hoverTooltip(x, y)) };
}

const listNodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
  return { id: n.getAttribute('data-id') || '?', prefix: (n.getAttribute('data-id') || '?').split('-')[0],
    cls: ((/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || '?'),
    name: (/^[^\s]+(?:\s+\d+)?/.exec(t) || [''])[0].slice(0, 14),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }));

async function exclusivePoint(pg, id) {
  return pg.evaluate((nid) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, id);
}

/** 按 data-id 前缀 + 名字关键字选中节点，带一致性闸。 */
async function selectNode(pg, prefix, nameKw) {
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(700);
  await pg.mouse.click(80, 120); await pg.waitForTimeout(900);
  await fitView(pg); await pg.waitForTimeout(1800);
  for (const c of (await listNodes()).filter((n) => n.prefix === prefix && (!nameKw || n.name.includes(nameKw)))) {
    const pt = await exclusivePoint(pg, c.id);
    if (pt.err) { console.log(`  ${c.id} → ${pt.err}`); continue; }
    await pg.mouse.click(pt.x, pt.y); await pg.waitForTimeout(3800);
    const sel = await pg.evaluate((id) => {
      const n = document.querySelector('.react-flow__node.selected');
      return n && n.getAttribute('data-id') === id
        ? { ok: true, id, text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) } : { ok: false }; }, c.id);
    console.log(`  ${c.id} 点(${pt.x},${pt.y}) → ${JSON.stringify(sel)}`);
    if (sel.ok) return sel;
    await pg.keyboard.press('Escape'); await pg.waitForTimeout(800);
  }
  return { err: `没选中 prefix=${prefix} name∋${nameKw}` };
}

async function readBars() {
  return page.evaluate(() => {
    const n = document.querySelector('.react-flow__node.selected');
    if (!n) return { err: '没选中节点' };
    const panels = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter((o) => o.r.width >= 480 && o.r.height >= 100)
      .filter((o) => o.e.querySelectorAll('button,[role="button"]').length >= 3);
    if (!panels.length) return { err: '没找到参数面板（≥480 宽且 ≥3 个可点元素）' };
    const p = panels.sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height))[0];
    const fp = (x) => { const s = x.querySelector('svg'); if (!s) return 'nosvg';
      const d = [...s.querySelectorAll('path')].map((z) => z.getAttribute('d') || '').filter(Boolean);
      return d.length ? d.sort((a, b) => b.length - a.length)[0].slice(0, 30) : 'svgonly'; };
    const all = [...p.e.querySelectorAll('button,[role="button"]')].map((x) => { const q = x.getBoundingClientRect();
      return { text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: x.getAttribute('aria-label'),
        fp: fp(x), disabled: x.disabled === true, cursor: getComputedStyle(x).cursor,
        rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; })
      .filter((b) => b.rect[2] > 0);
    const maxY = Math.max(...all.map((b) => b.rect[1] + b.rect[3]));
    const minY = Math.min(...all.map((b) => b.rect[1]));
    return { panelRect: [Math.round(p.r.x), Math.round(p.r.y), Math.round(p.r.width), Math.round(p.r.height)],
      panelText: (p.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
      allCount: all.length,
      bottomBar: all.filter((b) => maxY - (b.rect[1] + b.rect[3]) <= 8),
      topToolBar: all.filter((b) => b.rect[1] - minY <= 4) };
  });
}

async function surveyBars(label) {
  const bar = await readBars();
  if (bar.err) {
    // ⚠️ 「没找到参数面板」有两种可能：(a) 它确实没有；(b) 它有但不符合我的形状条件。
    //    要分清，就得把选中节点里**所有**可点元素原样 dump 出来。
    console.log(`  ⚠ ${label}: ${bar.err} —— 下面把该节点里全部可点元素 dump 出来，用来看是 (a) 还是 (b)`);
    const all = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没选中' };
      const r = n.getBoundingClientRect();
      const fp = (x) => { const s = x.querySelector('svg'); if (!s) return 'nosvg';
        const d = [...s.querySelectorAll('path')].map((z) => z.getAttribute('d') || '').filter(Boolean);
        return d.length ? d.sort((a, b) => b.length - a.length)[0].slice(0, 26) : 'svgonly'; };
      const btns = [...n.querySelectorAll('button,[role="button"],input,textarea,[contenteditable="true"]')].map((x) => { const q = x.getBoundingClientRect();
        return { tag: x.tagName, text: (x.innerText || x.value || '').replace(/\s+/g, ' ').trim().slice(0, 18),
          aria: x.getAttribute('aria-label'), ph: x.placeholder || '', type: x.type || '', fp: fp(x),
          disabled: x.disabled === true, cursor: getComputedStyle(x).cursor,
          rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; })
        .filter((b) => b.rect[2] > 0);
      // 顺便找找有没有任何「宽 ≥480 的容器」——用来判断是不是形状条件卡住了
      const wide = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
        .filter((o) => o.r.width >= 300 && o.r.height >= 20)
        .map((o) => ({ cls: (o.e.className || '').toString().slice(0, 40),
          rect: [Math.round(o.r.x), Math.round(o.r.y), Math.round(o.r.width), Math.round(o.r.height)],
          nBtn: o.e.querySelectorAll('button,[role="button"]').length,
          outside: o.r.x < r.x - 2 || o.r.x + o.r.width > r.x + r.width + 2,
          text: (o.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80) }))
        .sort((a, b) => b.nBtn - a.nBtn).slice(0, 5);
      return { nodeRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        nBtns: btns.length, btns, wide };
    });
    console.log('  节点尺寸:', JSON.stringify(all.nodeRect), '| 可点元素', all.nBtns, '个');
    all.btns.forEach((b, i) => console.log(`   [${String(i).padStart(2)}] ${b.tag.padEnd(8)} [${String(b.rect).padEnd(20)}] ${(b.text || '-').padEnd(18)} aria=${(b.aria || '-').padEnd(12)} cur=${(b.cursor || '-').padEnd(11)} fp=${b.fp.slice(0, 18)}`));
    console.log('  该节点里比卡片更宽的容器:', JSON.stringify(all.wide));
    return { noPanel: bar.err, nodeRect: all.nodeRect, nBtns: all.nBtns, btns: all.btns, wide: all.wide };
  }
  console.log(`\n${label} 面板=[${bar.panelRect}] 可点 ${bar.allCount} 枚（工具条 ${bar.topToolBar.length} / 参数条 ${bar.bottomBar.length}）`);
  console.log(`  面板文案: ${bar.panelText.slice(0, 260)}`);
  const rows = [];
  for (const b of [...bar.topToolBar, ...bar.bottomBar]) {
    const r = await hoverVerified(page, b.rect);
    rows.push({ rect: b.rect, text: b.text, aria: b.aria, fp: b.fp.slice(0, 24),
      disabled: b.disabled, cursor: b.cursor, ...r });
    console.log(`   [${String(b.rect).padEnd(20)}] ${(b.text || '-').padEnd(16)} aria=${(b.aria || '-').padEnd(8)} dis=${b.disabled ? 'Y' : 'n'} ${r.skipped ? '⚠ ' + r.skipped : '→ ' + JSON.stringify(r.tip)}`);
  }
  await shot(page, `${label.startsWith('逐帧') ? 'M-175' : 'M-176'}-${label}-参数条.png`);
  return { panelRect: bar.panelRect, panelText: bar.panelText, nTool: bar.topToolBar.length,
    nBottom: bar.bottomBar.length, rows,
    shot: `${label.startsWith('逐帧') ? 'M-175' : 'M-176'}-${label}-参数条.png` };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2000);
  await beginBatch(B, { note: '补逐帧拉片/导演台两类节点的参数条覆盖缺口 + 验摄像机「关闭」开关' });

  const out = {};
  const rost = await listNodes();
  console.log('画布名册:'); rost.forEach((n) => console.log(`  ${n.id} ${n.prefix}- ${n.cls} "${n.name}" [${n.rect}]`));
  out.roster = rost.map((n) => ({ id: n.id, prefix: n.prefix, cls: n.cls, name: n.name }));

  // ═══ A：逐帧拉片（data-id 前缀 b-）
  console.log('\n--- BC1 A 逐帧拉片 ---');
  const shotSel = await selectNode(page, 'b', '逐帧拉片');
  console.log('选中:', JSON.stringify(shotSel));
  out.shot = shotSel.err ? { err: shotSel.err } : await surveyBars('逐帧拉片');

  // ═══ B：导演台（前缀 n-）
  console.log('\n--- BC1 B 导演台 ---');
  const dirSel = await selectNode(page, 'n', '导演台');
  console.log('选中:', JSON.stringify(dirSel));
  out.director = dirSel.err ? { err: dirSel.err } : await surveyBars('导演台');

  // ═══ C：摄像机「关闭」开关 —— 打开 → 读变化 → 关回去
  console.log('\n--- BC1 C 摄像机「关闭」开关 ---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  const imgSel = await selectNode(page, 'i', '图片节点');
  console.log('图片节点:', JSON.stringify(imgSel));
  if (imgSel.err) { out.camera = { err: imgSel.err }; }
  else {
    const bar0 = await readBars();
    if (bar0.err) throw new Error('图片节点参数面板读不到: ' + bar0.err);
    // ⭐ 按**指纹**找摄像机按钮（`fp === nosvg`），不硬编码下标 —— 硬编码会随面板构成变化而错位
    const camIdx = bar0.bottomBar.findIndex((b) => b.fp === 'nosvg');
    console.log('  参数条:', JSON.stringify(bar0.bottomBar.map((b) => ({ t: b.text, aria: b.aria, fp: b.fp.slice(0, 12) }))));
    console.log('  摄像机按钮下标:', camIdx);
    const camTip0 = await hoverVerified(page, bar0.bottomBar[camIdx].rect);
    console.log('  摄像机按钮悬停（开关关着时）:', JSON.stringify(camTip0.tip || camTip0.skipped));
    const camBtn = bar0.bottomBar[camIdx];

    // 用 Playwright getByText 打开摄像机面板（BB2 的教训）
    await page.mouse.click(camBtn.rect[0] + camBtn.rect[2] / 2, camBtn.rect[1] + camBtn.rect[3] / 2);
    await page.waitForTimeout(2400); await clearToasts(page);
    const panel = await page.getByText('摄像机', { exact: true }).first()
      .waitFor({ state: 'visible', timeout: 6000 }).then(() => true).catch(() => false);
    console.log('  摄像机面板打开:', panel);
    const before = await page.evaluate(() => {
      const sw = [...document.querySelectorAll('button,[role="switch"],[class*="Switch"],[class*="Toggle"]')]
        .filter((e) => { const t = (e.innerText || '').trim(); const r = e.getBoundingClientRect();
          return /关闭|开启|启用/.test(t) && r.width > 0 && r.height > 0; })
        .map((e) => { const r = e.getBoundingClientRect();
          return { text: (e.innerText || '').trim(), aria: e.getAttribute('aria-label'),
            role: e.getAttribute('role'), ariaChecked: e.getAttribute('aria-checked'),
            dataChecked: e.getAttribute('data-checked'),
            cls: (e.className || '').toString().slice(0, 60),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
      return { switches: sw, text: (document.body.innerText || '').replace(/\s+/g, ' ').match(/摄像机[^]{0,220}/)?.[0] || '' };
    });
    console.log('  开关读数:', JSON.stringify(before.switches));
    console.log('  面板片段:', before.text.slice(0, 200));
    await shot(page, 'M-177-摄像机-开关关闭.png');
    out.camera = { btnTip: camTip0.tip, panelOpen: panel, before };

    if (before.switches.length) {
      const sw0 = before.switches[0];
      // 用 Playwright 点开关
      const swLoc = page.getByText(sw0.text, { exact: true }).first();
      await swLoc.click({ timeout: 5000 }).catch((e) => console.log('  点开关失败:', e.message.slice(0, 80)));
      await page.waitForTimeout(2600); await clearToasts(page);
      const after = await page.evaluate(() => [...document.querySelectorAll('button,[role="switch"],[class*="Switch"],[class*="Toggle"]')]
        .filter((e) => { const t = (e.innerText || '').trim(); const r = e.getBoundingClientRect();
          return /关闭|开启|启用/.test(t) && r.width > 0 && r.height > 0; })
        .map((e) => ({ text: (e.innerText || '').trim(), ariaChecked: e.getAttribute('aria-checked'),
          dataChecked: e.getAttribute('data-checked'),
          rect: (({x: bx, y: by, width: bw, height: bh}) => [bx, by, bw, bh])(e.getBoundingClientRect()) })));
      console.log('  ⬆️ 打开开关后:', JSON.stringify(after));
      await shot(page, 'M-178-摄像机-开关打开.png');
      out.camera.afterOpen = after;
      out.camera.shotOpen = 'M-178-摄像机-开关打开.png';

      // 再读一次按钮悬停提示 —— 提示里会写当前状态
      const camTip1 = await hoverVerified(page, bar0.bottomBar[camIdx].rect);
      console.log('  开关打开后按钮悬停:', JSON.stringify(camTip1.tip || camTip1.skipped));
      out.camera.tipAfterOpen = camTip1.tip || camTip1.skipped;

      // ✅ 关回去
      await page.mouse.click(camBtn.rect[0] + camBtn.rect[2] / 2, camBtn.rect[1] + camBtn.rect[3] / 2);
      await page.waitForTimeout(1600);
      const panelOpen2 = await page.getByText('摄像机', { exact: true }).first()
        .count().catch(() => 0);
      if (panelOpen2) {
        const swNow = await page.evaluate(() => [...document.querySelectorAll('button,[role="switch"],[class*="Switch"],[class*="Toggle"]')]
          .filter((e) => { const t = (e.innerText || '').trim(); const r = e.getBoundingClientRect();
            return /关闭|开启|启用/.test(t) && r.width > 0 && r.height > 0; })
          .map((e) => ({ text: (e.innerText || '').trim(), rect: (({x: bx, y: by, width: bw, height: bh}) => [bx, by, bw, bh])(e.getBoundingClientRect()) })));
        if (swNow.length) {
          await page.getByText(swNow[0].text, { exact: true }).first().click({ timeout: 5000 })
            .catch((e) => console.log('  关回去失败:', e.message.slice(0, 80)));
          await page.waitForTimeout(2400); await clearToasts(page);
          const back = await page.evaluate(() => [...document.querySelectorAll('button,[role="switch"],[class*="Switch"],[class*="Toggle"]')]
            .filter((e) => { const t = (e.innerText || '').trim(); const r = e.getBoundingClientRect();
              return /关闭|开启|启用/.test(t) && r.width > 0 && r.height > 0; })
            .map((e) => ({ text: (e.innerText || '').trim(), ariaChecked: e.getAttribute('aria-checked'),
              dataChecked: e.getAttribute('data-checked') })));
          out.camera.afterRestore = back;
          console.log('  ✅ 关回去后:', JSON.stringify(back));
        }
      }
      await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
    }
  }

  await logStep(B, {
    id: 'BC1-shot-director-camera', title: '逐帧拉片/导演台参数条 + 摄像机开关开关验证',
    target: '九类节点里**只剩逐帧拉片和导演台两类参数条从没点开过** —— 本批补这块覆盖缺口。'
      + '摄像机「关闭」开关**打开→读→关回去并确认复原**（会写节点参数，所以必须复原）。'
      + '点开关用 Playwright `getByText`，悬停读 tooltip 前先验落点归属。',
    evidence: out,
    visible_text: JSON.stringify({ shot: out.shot, director: out.director, camera: out.camera }).slice(0, 3500),
    shot: (out.shot && out.shot.shot) || (out.director && out.director.shot),
  });
  console.log('\nBC1 完成');
} finally {
  await browser.close();
}

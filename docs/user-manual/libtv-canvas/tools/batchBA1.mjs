// Batch BA —— 补完 AZ 没测成的四件事，全只读。
//
// AZ2 留下的坑与机会：
//   ① 重名「定位到节点」**第 2 行没测成** —— 点完第 1 行之后另一个同名节点
//      **移出了视口**，`roster()` 只返回视口内节点，于是第 2 轮只找到 1 个候选。
//      这正是「视口内读不到节点 ≠ 节点不存在」那条老坑的又一次现身。
//      ✅ 这轮的修法：**先 `⌘0` 把所有节点收进视口，再点某一行**，
//      并且**把画布缩放也记下来**（AZ2 发现定位会顺手改成 100%，那是干扰项）。
//   ② **智能剪辑节点**的参数条从没清点过 —— 前四类（视频/图片/音频/文本）都做了，
//      第五类漏了。这是一处**覆盖缺口**，不是新功能。
//   ③ **预设工作流 11 项**此前只读过名字，没读过结构。这轮只读：
//      hover 每一条读 tooltip、读每条的 DOM（是否 disabled、有没有描述文字、
//      有没有分组标题），**一条都不点**（点了会往画布加东西）。
//   ④ **摄像机面板的「关闭」开关** —— 只读它的 DOM 结构和当前值，
//      **不开关**（它会写进节点配置）。
//
// ⚠️ 安全边界：不点生成、不点预设、不点开关、不上传、不删除、不派发任务。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBA1';
const { browser, page } = await launch();

const TOOLBAR_TOP = 735;

async function hoverTooltip(cx, cy, waitMs = 950) {
  await page.mouse.move(cx, cy);
  await page.waitForTimeout(waitMs);
  return page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"],[role="tooltip"]')]
    .filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; })
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean));
}
const NOISE = /^(按 ESC 退出|新功能：.+)$/;
const clean = (l) => l.filter((t) => !NOISE.test(t));

/** 悬停读 tooltip，**先验落点归属**（AZ 的教训：rect 对 ≠ 落点归你）。 */
async function hoverVerified(pg, rect) {
  const x = Math.round(rect[0] + rect[2] / 2), y = Math.round(rect[1] + rect[3] / 2);
  const owner = await pg.evaluate(([px, py]) => {
    const e = document.elementFromPoint(px, py);
    if (!e) return { kind: 'nothing' };
    const b = e.closest('button,[role="button"]');
    if (!b) return { kind: 'not-button', tag: e.tagName };
    return { kind: 'button', text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
      aria: b.getAttribute('aria-label') };
  }, [x, y]);
  if (y > TOOLBAR_TOP || owner.kind !== 'button') {
    return { skipped: `落点 (${x},${y}) ${y > TOOLBAR_TOP ? '**压在底栏工具条上**' : owner.kind}`, owner };
  }
  return { point: [x, y], owner, tip: clean(await hoverTooltip(x, y)) };
}

const roster = () => pg => pg; // 占位，避免误用

const listNodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
  return { id: n.getAttribute('data-id') || '?',
    cls: ((/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || '?'),
    name: (/^[^\s]+(?:\s+\d+)?/.exec(t) || [''])[0].slice(0, 14),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
    inView: r.x + r.width > 0 && r.x < 1440 && r.y + r.height > 60 && r.y < 810 };
}));

const scaleNow = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  if (!v) return null;
  const m = /scale\(([\d.]+)\)/.exec(v.style.transform || '');
  return m ? +m[1] : null;
});

/** 在节点框内扫网格，找一个**独占**的点击点（AZ2 的收口判据）。 */
async function exclusivePoint(pg, nodeId) {
  return pg.evaluate((id) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === id);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, nodeId);
}

async function selectNodeByName(pg, keyword) {
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(700);
  await fitView(pg); await pg.waitForTimeout(1600);
  for (const cand of (await listNodes()).filter((n) => n.name.includes(keyword))) {
    const pt = await exclusivePoint(pg, cand.id);
    if (pt.err) { console.log(`  ${cand.id} → ${pt.err}`); continue; }
    await pg.mouse.click(pt.x, pt.y);
    await pg.waitForTimeout(3600);
    const sel = await pg.evaluate((kw) => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { ok: false, why: '没选中' };
      const t = (n.innerText || '').replace(/\s+/g, ' ');
      return { ok: t.includes(kw), id: n.getAttribute('data-id'), type: (/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || '?' };
    }, keyword);
    console.log(`  ${cand.id} 点(${pt.x},${pt.y}) → ${JSON.stringify(sel)}`);
    if (sel.ok) return sel;
    await pg.keyboard.press('Escape'); await pg.waitForTimeout(800);
  }
  return { err: `没选中「${keyword}」` };
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

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2000);
  await beginBatch(B, { note: '重名定位第2行（先 fitView）+ 智能剪辑参数条 + 预设 11 项只读清点 + 摄像机开关只读' });

  const out = {};

  // ═══ A：重名「定位到节点」—— 每轮之前先 ⌘0，把候选收进视口
  console.log('--- BA A 重名「定位到节点」 ---');
  out.dup = {};
  for (const rowIdx of [0, 1]) {
    await page.keyboard.press('Escape'); await page.waitForTimeout(800);
    await page.mouse.click(80, 120); await page.waitForTimeout(900);
    await fitView(page); await page.waitForTimeout(1800);          // ← 关键：先把候选都收进视口
    const pre = await listNodes();
    const cands = pre.filter((n) => n.name === '视频节点 3');
    console.log(`\n第 ${rowIdx + 1} 行前：候选 ${cands.length} 个`,
      JSON.stringify(cands.map((c) => ({ id: c.id, rect: c.rect, inView: c.inView }))));
    if (cands.length < 2) { console.log('  ⚠ 候选不足，跳过'); continue; }

    // 开抽屉 → 点第 rowIdx 行
    const b = await page.evaluate(() => {
      const e = [...document.querySelectorAll('button,[role="button"]')]
        .find((x) => /资产管理/.test(x.getAttribute('aria-label') || x.getAttribute('title') || ''));
      if (!e) return null; const r = e.getBoundingClientRect();
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
    await page.mouse.click(b.cx, b.cy); await page.waitForTimeout(2800); await clearToasts(page);
    const rows = await page.evaluate(() => {
      const e = [...document.querySelectorAll('body div,body section,body aside')]
        .find((x) => ((x.className || '') + '').includes('mantine-Drawer-content'));
      if (!e) return [];
      return [...e.querySelectorAll('button,[role="button"]')].map((n) => { const r = n.getBoundingClientRect();
        return { aria: n.getAttribute('aria-label'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
        .filter((x) => (x.aria || '').startsWith('定位到节点') && x.rect[2] > 200
          && (x.aria || '').replace('定位到节点', '').trim() === '视频节点 3'); });
    console.log(`  抽屉里「视频节点 3」共 ${rows.length} 行`);
    if (!rows[rowIdx]) { console.log('  ⚠ 没有第 ' + (rowIdx + 1) + ' 行'); await page.keyboard.press('Escape'); await page.waitForTimeout(1200); continue; }
    await page.mouse.click(rows[rowIdx].rect[0] + 40, rows[rowIdx].rect[1] + rows[rowIdx].rect[3] / 2);
    await page.waitForTimeout(3600);
    await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
    await clearToasts(page);
    const post = await listNodes();
    const sc = await scaleNow();
    const same = post.filter((n) => n.name === '视频节点 3');
    console.log('  定位后 scale =', sc);
    console.log('  同名节点:', JSON.stringify(same.map((c) => ({ id: c.id, rect: c.rect, inView: c.inView }))));
    // 判据：**只在这两个同名候选里比**，看谁被平移进了视口中心
    const vis = same.filter((n) => n.inView);
    const near = same.slice().sort((a, c) => Math.hypot(a.cx - 720, a.cy - 300) - Math.hypot(c.cx - 720, c.cy - 300));
    console.log(`  在视口内: ${vis.length} 个 → ${JSON.stringify(vis.map((v) => v.id))}`);
    console.log(`  同名候选里离中心最近: ${near[0].id} ${JSON.stringify(near[0].rect)}`);
    out.dup[`row${rowIdx + 1}`] = { scaleAfter: sc,
      before: cands.map((c) => ({ id: c.id, rect: c.rect })),
      after: same.map((c) => ({ id: c.id, rect: c.rect, inView: c.inView })),
      visibleIds: vis.map((v) => v.id), winner: near[0].id };
    if (rowIdx === 0) { await shot(page, 'M-171-重名-定位-第1行.png'); out.shot = 'M-171-重名-定位-第1行.png'; }
  }
  const w1 = out.dup.row1 && out.dup.row1.winner, w2 = out.dup.row2 && out.dup.row2.winner;
  console.log(`\n结论：第 1 行 → ${w1}；第 2 行 → ${w2}；${w1 && w2 ? (w1 === w2 ? '**两行落到同一个**' : '**两行落到不同的**') : '数据不全'}`);
  out.dupVerdict = { row1: w1, row2: w2, same: w1 === w2 };

  // ═══ B：智能剪辑节点参数条（补第五类节点）
  console.log('\n--- BA B 智能剪辑节点参数条 ---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  await fitView(page); await page.waitForTimeout(1600);
  const clip = await selectNodeByName(page, '智能剪辑');
  console.log('智能剪辑选中:', JSON.stringify(clip));
  out.clip = { sel: clip };
  if (clip.err) console.log('  ⚠', clip.err);
  else {
    const bar = await readBars();
    if (bar.err) { console.log('  ⚠', bar.err); out.clip.bar = { err: bar.err }; }
    else {
      console.log(`  面板=[${bar.panelRect}] 文案="${bar.panelText.slice(0, 160)}"`);
      console.log(`  工具条 ${bar.topToolBar.length} / 参数条 ${bar.bottomBar.length}`);
      const named = [];
      for (const b of bar.bottomBar) {
        const r = await hoverVerified(page, b.rect);
        named.push({ rect: b.rect, text: b.text, aria: b.aria, fp: b.fp.slice(0, 22), disabled: b.disabled, cursor: b.cursor, ...r });
        console.log(`   [${String(b.rect).padEnd(20)}] ${(b.text || '-').padEnd(14)} aria=${(b.aria || '-').padEnd(8)} dis=${b.disabled ? 'Y' : 'n'} ${r.skipped ? '⚠ ' + r.skipped : '→ ' + JSON.stringify(r.tip)}`);
      }
      out.clip.bar = { panelRect: bar.panelRect, panelText: bar.panelText, bottom: named,
        toolBar: bar.topToolBar.map((b) => ({ rect: b.rect, text: b.text, aria: b.aria, fp: b.fp.slice(0, 20) })) };
      console.log('  工具条:', JSON.stringify(out.clip.bar.toolBar));
      await shot(page, 'M-172-智能剪辑-参数条.png');
      out.shot2 = 'M-172-智能剪辑-参数条.png';
    }
  }

  // ═══ C：预设工作流 11 项只读清点 —— 一条都不点
  console.log('\n--- BA C 预设工作流 11 项（只读，不点）---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  await fitView(page); await page.waitForTimeout(1600);
  const imgSel = await selectNodeByName(page, '图片节点');
  out.presetSel = imgSel;
  if (imgSel.err) console.log('  ⚠ 没能选中图片节点:', imgSel.err);
  else {
    const pre = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没选中' };
      const btn = [...n.querySelectorAll('button,[role="button"]')].find((b) => b.getAttribute('aria-label') === '预设');
      if (!btn) return { err: '面板里没有 aria=预设 那枚' };
      const r = btn.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    });
    console.log('  预设按钮:', JSON.stringify(pre));
    if (pre.err) { out.preset = { err: pre.err }; }
    else {
      const pt = await hoverVerified(page, pre.rect);
      console.log('  落点校验:', JSON.stringify(pt));
      await page.mouse.click(pt.point[0], pt.point[1]); // 这枚是打开选择器，不是应用某一项 —— 安全
      await page.waitForTimeout(2600);
      await clearToasts(page);
      const panel = await page.evaluate(() => {
        const cands = [...document.querySelectorAll('body div,body section,body aside')].map((e) => {
          const r = e.getBoundingClientRect();
          const cs = getComputedStyle(e);
          if (r.width < 300 || r.height < 200) return null;
          if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity <= 0.05) return null;
          if (r.x + r.width < 0 || r.x > 1440) return null;
          const btns = [...e.querySelectorAll('button,[role="button"]')].filter((b) => { const q = b.getBoundingClientRect(); return q.width > 0; });
          return { cls: (e.className || '').toString().slice(0, 50),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            pos: cs.position, z: cs.zIndex, nBtn: btns.length,
            text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 600) }; }).filter(Boolean);
        return cands.sort((a, b) => b.nBtn - a.nBtn).slice(0, 3);
      });
      console.log('  预设选择器候选:', JSON.stringify(panel).slice(0, 1600));
      // 逐条读：文字、是否 disabled、有没有副标题、悬停提示
      const items = await page.evaluate(() => {
        const sel = [...document.querySelectorAll('body *')]
          .filter((e) => { const t = (e.innerText || '').trim();
            return /^(调度故事板|故事板|25宫格连贯分镜|剧情推演四宫格|画面推演|人像质感调节|电影级光影校正|720全景|多机位九宫格|角色脸部三视图|角色设定图|角色三视图|场景设定图|产品设定图)/.test(t)
              && t.length < 30 && e.children.length < 6; });
        const seen = new Set(); const out = [];
        for (const e of sel) {
          const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
          if (seen.has(t)) continue; seen.add(t);
          const r = e.getBoundingClientRect();
          const btn = e.closest('button,[role="button"]');
          out.push({ text: t, tag: e.tagName, isButton: !!btn,
            title: e.getAttribute('title'), aria: e.getAttribute('aria-label'),
            disabled: btn ? btn.disabled === true : false,
            cursor: getComputedStyle(e).cursor,
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
        }
        return out.sort((a, b) => a.rect[1] - b.rect[1] || a.rect[0] - b.rect[0]);
      });
      console.log(`\n  读到 ${items.length} 条:`);
      items.forEach((it, i) => console.log(`   ${String(i).padStart(2)} [${String(it.rect).padEnd(20)}] ${it.tag.padEnd(6)} btn=${it.isButton ? 'Y' : 'n'} dis=${it.disabled ? 'Y' : 'n'} cur=${it.cursor.padEnd(8)} "${it.text}"`));
      const tips = [];
      for (const it of items.filter((x) => x.rect[2] > 0).slice(0, 12)) {
        const r = await hoverVerified(page, it.rect);
        tips.push({ text: it.text, ...r });
        console.log(`   悬停「${it.text}」→ ${r.skipped ? '⚠ ' + r.skipped : JSON.stringify(r.tip)}`);
      }
      out.preset = { btnRect: pre.rect, panel: panel.slice(0, 2), items, tips };
      await shot(page, 'M-173-预设工作流-只读.png');
      out.shot3 = 'M-173-预设工作流-只读.png';
      await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
    }
  }

  await logStep(B, {
    id: 'BA1-dup-locate-clip-preset', title: '重名定位两行 + 智能剪辑参数条 + 预设 11 项只读清点',
    target: 'A 每轮之前先 `⌘0` 把同名候选都收进视口（AZ2 就是因为另一个被移出视口而没测成第 2 行）；'
      + 'B 补上第五类节点（智能剪辑）的参数条清点；C 预设工作流 11 项**逐条读 DOM 与 tooltip，一条都不点**。'
      + '全部 tooltip 读取前都验过落点归属（AZ 的教训）。',
    evidence: out,
    visible_text: JSON.stringify({ dup: out.dupVerdict, clip: out.clip, preset: out.preset }).slice(0, 3500),
    shot: out.shot,
  });
  console.log('\nBA1 完成');
} finally {
  await browser.close();
}

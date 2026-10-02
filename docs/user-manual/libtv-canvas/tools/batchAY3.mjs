// Batch AY3 —— 补 AY2 作废的两份读数 + 摸清抽屉「资产」页 + 给最后一枚按钮定性。
//
// AY2 挖到的（本批要坐实的）：
//   `📄`（SVG M10.26 1.67…）   = **提示词优化**   ← 点下去不弹面板，弹
//                                  「提示词为空，请输入内容后点击」
//   `M15.52 7.2…`             = **翻译提示词**   ← 手册此前完全没这枚
//   文本节点参数条只有 3 枚： `GVLM 3.1` / 翻译提示词 / 一枚 tooltip 写
//                              **「请输入提示词」**的
//   抽屉顶部四枚： `搜索节点` / `筛选：全部` / `所有评级` / `展示设置`
//   抽屉底部一行： `共 11 节点`
//
// ⚠️ AY2 的两份读数**作废**，本批重做：
//   图片节点和音频节点选中后读出来的 `selectedType` **都是 `video`**，
//   参数条文案也是视频那套（`全能参考` / `16:9 · 720P · 5s · 1个 · 135`）。
//   原因：**节点重叠，点到了压在上面的视频节点**。
//   → 教训升级：光「断言选中的是哪一类」还不够（那条在 AX 立过），
//     **必须断言选中的那一类跟我要找的关键词一致**，不一致就是没点到目标。
//     否则「我点到了某个节点」会被当成「我点到了我以为的那个节点」。
//
// 三件事：
// A. 图片 / 音频 节点参数条 tooltip 普查（带一致性闸）
// B. 抽屉「资产」页（AY2 只找到 `画布` 是 BUTTON，`资产` 不是按钮元素，
//    判据要改成按文案找任何标签）
// C. 最后一枚无 tooltip 按钮**是什么** ——
//    **先读 `disabled` / `aria-disabled` / `cursor`，能定性就定性；**
//    若它可点而我又不能点（可能是触发生成），就**在提示词里临时打几个字**
//    再悬停读 tooltip，读完还原 —— **打字是本地编辑，不触发生成**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAY3';
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

/** 提示词/新手引导气泡的噪声，普查结果里要剔掉。 */
const NOISE = /^(按 ESC 退出|新功能：.+|提示词为空，请输入内容后点击)$/;
const clean = (list) => list.filter((t) => !NOISE.test(t));

/**
 * 选中某个关键词的节点 —— **带一致性闸**。
 * 判定标准从 AY2 的教训来：点完必须回读 `.selected` 的 innerText，
 * **确认它真的包含关键词**，否则换下一个候选重试。
 */
async function selectNode(pg, keyword, typeHint) {
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(700);
  await pg.mouse.click(80, 120); await pg.waitForTimeout(1000); // 先取消选中
  await fitView(pg); await pg.waitForTimeout(1500);
  // 把所有候选排好序：先按「elementFromPoint 命中自己」筛，再按离中心距离
  const cands = await pg.evaluate((kw) => {
    const out = [];
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(kw)) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 40 || r.x + r.width > 1400 || r.y < 80 || r.y + r.height > 780) continue;
      const probes = [[0.5, 0.5], [0.5, 0.25], [0.5, 0.75], [0.3, 0.5], [0.7, 0.5]];
      let hitPt = null;
      for (const [fx, fy] of probes) {
        const x = r.x + r.width * fx, y = r.y + r.height * fy;
        const o = document.elementFromPoint(x, y);
        if (o && n.contains(o)) { hitPt = [Math.round(x), Math.round(y)]; break; }
      }
      out.push({ rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        d: Math.hypot(r.x + r.width / 2 - 720, r.y - 150), hitPt,
        text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) });
    }
    return out.sort((a, b) => (b.hitPt ? 1 : 0) - (a.hitPt ? 1 : 0) || a.d - b.d);
  }, keyword);
  if (!cands.length) return { err: `视口里找不到「${keyword}」节点` };
  console.log(`  候选 ${cands.length} 个:`, JSON.stringify(cands.slice(0, 4)));

  for (const c of cands.slice(0, 4)) {
    const pt = c.hitPt || [c.cx, c.cy];
    await pg.mouse.click(pt[0], pt[1]);
    await pg.waitForTimeout(3600);
    const sel = await pg.evaluate((kw) => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { ok: false, why: '没选中任何节点' };
      const t = (n.innerText || '').replace(/\s+/g, ' ');
      return { ok: t.includes(kw), type: (/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || '?',
        text: t.trim().slice(0, 50) };
    }, keyword);
    console.log(`   点 [${pt}] → ok=${sel.ok} type=${sel.type} text="${sel.text}"`);
    if (sel.ok) return { rect: c.rect, cx: c.cx, cy: c.cy, selectedType: sel.type, match: sel.text };
    await pg.keyboard.press('Escape'); await pg.waitForTimeout(800);
  }
  return { err: `点了 ${Math.min(4, cands.length)} 个候选，选中的都不是「${keyword}」（多为节点重叠）`, tried: cands.length, typeHint };
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
    const fp = (e) => { const s = e.querySelector('svg'); if (!s) return 'nosvg';
      const ds = [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').filter(Boolean);
      return ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 34) : 'svgonly'; };
    const btns = [...p.e.querySelectorAll('button,[role="button"]')].map((e) => { const q = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), aria: e.getAttribute('aria-label'),
        fp: fp(e), disabled: e.disabled === true || e.getAttribute('aria-disabled') === 'true',
        cursor: cs.cursor, rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
    }).filter((b) => b.rect[2] > 0);
    if (!btns.length) return { err: '面板里没有按钮' };
    const maxY = Math.max(...btns.map((b) => b.rect[1] + b.rect[3]));
    const minY = Math.min(...btns.map((b) => b.rect[1]));
    return { panelRect: [Math.round(p.r.x), Math.round(p.r.y), Math.round(p.r.width), Math.round(p.r.height)],
      panelText: (p.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      bottomBar: btns.filter((b) => maxY - (b.rect[1] + b.rect[3]) <= 8),
      topToolBar: btns.filter((b) => b.rect[1] - minY <= 4) };
  });
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '补 AY2 作废的图片/音频读数 + 抽屉资产页 + 最后一枚按钮定性' });

  const out = {};

  // ═══ B. 抽屉「资产」页（先做，因为它要先开抽屉）
  console.log('--- AY3 B 抽屉「资产」页 ---');
  const openBtn = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => /资产管理/.test(x.getAttribute('aria-label') || x.getAttribute('title') || ''));
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (openBtn) {
    await page.mouse.click(openBtn.cx, openBtn.cy);
    await page.waitForTimeout(3200); await clearToasts(page);
    out.drawerText = await page.evaluate(() => {
      const e = [...document.querySelectorAll('body div,body section,body aside')]
        .find((x) => ((x.className || '') + '').includes('mantine-Drawer-content'));
      return e ? (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500) : 'no-drawer'; });
    console.log('抽屉全文:', out.drawerText);

    // 按文案找 tab，不限标签
    out.tabCands = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].map((n) => {
        const r = n.getBoundingClientRect();
        return { tag: n.tagName, text: (n.innerText || '').trim(), cls: (n.className || '').toString().slice(0, 46),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cursor: getComputedStyle(n).cursor,
          inDrawer: !!n.closest('[class*="Drawer-content"]') }; });
      return all.filter((n) => (n.text === '画布' || n.text === '资产') && n.rect[2] > 0 && n.rect[2] < 120 && n.inDrawer);
    });
    console.log('tab 候选（不限标签）:', JSON.stringify(out.tabCands));
    const assetTab = (out.tabCands || []).find((t) => t.text === '资产');
    if (assetTab) {
      await page.mouse.click(assetTab.rect[0] + assetTab.rect[2] / 2, assetTab.rect[1] + assetTab.rect[3] / 2);
      await page.waitForTimeout(3400); await clearToasts(page);
      out.assetPage = await page.evaluate(() => {
        const e = [...document.querySelectorAll('body div,body section,body aside')]
          .find((x) => ((x.className || '') + '').includes('mantine-Drawer-content'));
        if (!e) return { err: '切 tab 后抽屉不见了' };
        const nodes = [...e.querySelectorAll('button,[role="button"],input,a,[role="tab"]')].map((n) => {
          const r = n.getBoundingClientRect();
          return { tag: n.tagName, text: (n.innerText || n.value || '').replace(/\s+/g, ' ').trim().slice(0, 18),
            aria: n.getAttribute('aria-label'), title: n.getAttribute('title'), type: n.type || '',
            ph: n.placeholder || '', cursor: getComputedStyle(n).cursor,
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
          .filter((n) => n.rect[2] > 0);
        const r = e.getBoundingClientRect();
        return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 800), n: nodes.length, nodes: nodes.slice(0, 40) };
      });
      console.log('\n资产页:', JSON.stringify(out.assetPage).slice(0, 2200));
      await shot(page, 'M-167-资产管理-资产页.png');
      out.shot = 'M-167-资产管理-资产页.png';
      // 顶部按钮 tooltip
      out.assetTips = [];
      for (const n of (out.assetPage.nodes || []).filter((x) => x.rect[1] < 200).slice(0, 12)) {
        const cx = n.rect[0] + n.rect[2] / 2, cy = n.rect[1] + n.rect[3] / 2;
        const tip = (cx < 0 || cx > 1440) ? ['出视口'] : clean(await hoverTooltip(cx, cy, 900));
        out.assetTips.push({ rect: n.rect, text: n.text, aria: n.aria, tip });
        console.log(`  [${n.rect}] ${n.tag} text=${(n.text || '-').padEnd(14)} aria=${(n.aria || '-').padEnd(14)} → ${JSON.stringify(tip)}`);
      }
    } else console.log('  ⚠ 没找到「资产」');
  } else console.log('  ⚠ 底栏没有「资产管理」');

  await page.keyboard.press('Escape'); await page.waitForTimeout(2000); await clearToasts(page);

  // ═══ A. 图片 / 音频 参数条 tooltip（带一致性闸）
  console.log('\n--- AY3 A 图片/音频参数条 ---');
  out.bars = {};
  for (const kw of ['图片节点', '音频节点']) {
    const sel = await selectNode(page, kw);
    console.log(`\n[${kw}]`, JSON.stringify(sel));
    if (sel.err) { out.bars[kw] = { err: sel.err }; continue; }
    const bar = await readBars();
    if (bar.err) { console.log('  ⚠', bar.err); out.bars[kw] = { sel, err: bar.err }; continue; }
    console.log(`  选中类型=${sel.selectedType} 面板=[${bar.panelRect}] 文案="${bar.panelText.slice(0, 120)}"`);
    const named = [];
    for (const b of bar.bottomBar) {
      const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
      const tip = (cx < 0 || cx > 1440) ? ['出视口'] : clean(await hoverTooltip(cx, cy, 900));
      named.push({ rect: b.rect, text: b.text, fp: b.fp.slice(0, 24), disabled: b.disabled, cursor: b.cursor, tip });
      console.log(`   [${String(b.rect).padEnd(20)}] ${(b.text || '-').padEnd(14)} dis=${b.disabled ? 'Y' : 'n'} cur=${(b.cursor || '-').padEnd(12)} fp=${b.fp.slice(0, 18).padEnd(20)} → ${JSON.stringify(tip)}`);
    }
    const tn = bar.topToolBar.map((b) => ({ rect: b.rect, text: b.text, fp: b.fp.slice(0, 20), cursor: b.cursor, disabled: b.disabled }));
    out.bars[kw] = { sel, selectedType: sel.selectedType, panelRect: bar.panelRect,
      panelText: bar.panelText, bottom: named, toolBar: tn };
    console.log('   工具条:', JSON.stringify(tn));
  }

  // ═══ C. 最后一枚按钮定性（视频节点）
  console.log('\n--- AY3 C 最后一枚按钮定性 ---');
  const vsel = await selectNode(page, '视频节点');
  console.log('视频节点选中:', JSON.stringify(vsel));
  out.last = { sel: vsel };
  if (!vsel.err) {
    const bar = await readBars();
    if (bar.err) { out.last.err = bar.err; console.log('  ⚠', bar.err); }
    else {
      const last = bar.bottomBar[bar.bottomBar.length - 1];
      const prev = bar.bottomBar[bar.bottomBar.length - 2];
      out.last.panel = { rect: bar.panelRect, text: bar.panelText.slice(0, 200), n: bar.bottomBar.length };
      out.last.btn = last;
      console.log('  参数条最后一枚:', JSON.stringify(last));
      console.log('  倒数第二枚:', JSON.stringify(prev));
      const cx = last.rect[0] + last.rect[2] / 2, cy = last.rect[1] + last.rect[3] / 2;
      const tipEmpty = clean(await hoverTooltip(cx, cy, 1400));
      out.last.tipWhenEmpty = tipEmpty;
      console.log('  提示词为空时悬停 tooltip:', JSON.stringify(tipEmpty));

      // 临时打几个字再悬停 —— **打字是本地编辑，不触发生成**
      const ta = await page.evaluate(() => {
        const n = document.querySelector('.react-flow__node.selected');
        const t = n && n.querySelector('textarea,[contenteditable="true"]');
        if (!t) return null;
        t.scrollIntoView({ block: 'center' });
        const r = t.getBoundingClientRect();
        return { tag: t.tagName, x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
          text: (t.value || t.innerText || '').slice(0, 40) }; });
      out.last.textarea = ta;
      if (ta && ta.text === '') {
        await page.mouse.click(ta.x, ta.y); await page.waitForTimeout(600);
        await page.keyboard.type('猫在窗台上打盹', { delay: 60 });
        await page.waitForTimeout(1800);
        const afterType = await page.evaluate(() => {
          const n = document.querySelector('.react-flow__node.selected');
          const t = n && n.querySelector('textarea,[contenteditable="true"]');
          return t ? (t.value || t.innerText || '').slice(0, 40) : null; });
        out.last.afterType = afterType;
        console.log('  打字后 textarea:', JSON.stringify(afterType));
        const b2 = await readBars();
        if (!b2.err) {
          const l2 = b2.bottomBar[b2.bottomBar.length - 1];
          const t2 = clean(await hoverTooltip(l2.rect[0] + l2.rect[2] / 2, l2.rect[1] + l2.rect[3] / 2, 1400));
          out.last.tipWhenFilled = t2;
          out.last.btnFilled = l2;
          console.log('  有提示词时悬停 tooltip:', JSON.stringify(t2), '| disabled=', l2.disabled, 'cursor=', l2.cursor);
          await shot(page, 'M-168-视频-参数条按钮命名.png');
          out.last.shot = 'M-168-视频-参数条按钮命名.png';
        }
        // 还原提示词，避免污染用户的画布
        await page.keyboard.press('Meta+a'); await page.keyboard.press('Backspace');
        await page.waitForTimeout(1200);
        const restored = await page.evaluate(() => {
          const n = document.querySelector('.react-flow__node.selected');
          const t = n && n.querySelector('textarea,[contenteditable="true"]');
          return t ? (t.value || t.innerText || '') : null; });
        out.last.restored = restored;
        console.log('  还原后 textarea:', JSON.stringify(restored));
      } else console.log('  textarea 已有内容，不打字');
    }
  }

  await logStep(B, {
    id: 'AY3-bars-assets-last-button', title: '图片/音频参数条（带一致性闸）+ 抽屉资产页 + 最后一枚按钮定性',
    target: 'AY2 的图片/音频读数**作废**（选中的是压在上面的视频节点，`selectedType` 读出 `video`）。'
      + '本轮选中后**回读 `.selected` 的 innerText 确认它真的含目标关键词**，不一致就换候选重试 —— '
      + '只断言「选中了一类」不够，要断言「选中的是**我以为的那一类**」。'
      + '最后一枚按钮**不点**：先读 disabled/cursor，再临时打几个字悬停读 tooltip，读完还原。',
    evidence: out,
    visible_text: JSON.stringify({ bars: out.bars, assetPage: out.assetPage, last: out.last }).slice(0, 3500),
    shot: out.shot,
  });
  console.log('\nAY3 完成');
} finally {
  await browser.close();
}

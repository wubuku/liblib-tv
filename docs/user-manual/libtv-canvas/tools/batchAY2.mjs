// Batch AY2 —— 把「资产管理抽屉顶部那一层」读出来 + 给**所有无文字按钮**正名。
//
// AY1 的两半结果：
//
// ① 视频节点那枚 `📄`（SVG `M10.26 1.67c.32 0 .57.25.57.57v.35`）= **提示词优化**。
//    点下去不弹面板，弹顶部提示「**提示词为空，请输入内容后点击**」——
//    也就是说它是**有前置条件的**，提示词没填就拒绝干活。
//    （AW2 当初读到 `newPanels: []` 是 `diffPanels` API 用错时的读数，没有判别力。）
//
// ② 资产管理抽屉判据**又选窄了一层**。抽屉本体是 `mantine-Drawer-content`
//    `[0,0,320,810]`，含 41 个按钮；我的规则「取最内层」挑中的是
//    `mantine-ScrollArea-content` `[0,182,319,520]` 的 33 个 ——
//    **顶部那层（`画布`/`资产` 两个 tab、`所有评级` 筛选）根本没进来。**
//    → 教训：**「取最内层」和「取最外层」一样是凭空的**。抽屉容器要用
//      **文案锚点**反查（内容里同时出现「所有评级」+「画布」+「资产」），
//      而不是按 class 或嵌套深浅挑。
//
// 这批做三件事：
//
// A. **抽屉顶部控件**（用文案锚点定位 Drawer-content，整层清点 + 分区归类）
// B. **切到「资产」tab**（纯导航，不写数据）看资产列表长什么样
// C. **参数条 tooltip 普查** —— 对视频/图片/音频/文本四种节点底部参数条上的
//    **每一个**按钮 hover，读取 Mantine Tooltip 的官方名字。
//    ⭐ 这是本批最有价值的手段：**无文字、无 aria 的按钮，hover 一下就有官方名**，
//      而且**不点击**——不会触发生成、不会写账户、不会跳页面。
//      之前好几批是靠 SVG path 反推语义（`📄` 反推了三轮才对），
//      有 tooltip 还去猜就是白白冒险。
//
// ⚠️ 安全边界（不变）：不点任何会生成 / 上传 / 创建 / 删除 / 发布的东西；
//    悬停读 tooltip 是纯只读。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAY2';
const { browser, page } = await launch();

/** 悬停并读 Mantine Tooltip 的文字 —— **不点击**。 */
async function hoverTooltip(cx, cy, waitMs = 1100) {
  await page.mouse.move(cx, cy);
  await page.waitForTimeout(waitMs);
  const t = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[class*="Tooltip-tooltip"],[role="tooltip"]')]
      .filter((e) => { const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; });
    return els.map((e) => ({ rect: [Math.round(e.getBoundingClientRect().x), Math.round(e.getBoundingClientRect().y),
      Math.round(e.getBoundingClientRect().width), Math.round(e.getBoundingClientRect().height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) }));
  });
  return t;
}

/** 找到当前选中的参数面板，并列出底部参数条（y 最大那一行）上的按钮。 */
async function bottomBar() {
  return page.evaluate(() => {
    const n = document.querySelector('.react-flow__node.selected');
    if (!n) return { err: '没选中节点' };
    const type = (/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || 'unknown';
    const panels = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter((o) => o.r.width >= 480 && o.r.height >= 100)
      .filter((o) => o.e.querySelectorAll('button,[role="button"]').length >= 3);
    if (!panels.length) return { err: '没找到参数面板' };
    const p = panels.sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height))[0];
    const fp = (e) => { const s = e.querySelector('svg'); if (!s) return 'nosvg';
      const ds = [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').filter(Boolean);
      return ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 34) : 'svgonly'; };
    const btns = [...p.e.querySelectorAll('button,[role="button"]')].map((e) => { const q = e.getBoundingClientRect();
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), aria: e.getAttribute('aria-label'),
        fp: fp(e), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
    }).filter((b) => b.rect[2] > 0);
    if (!btns.length) return { err: '面板里没有按钮' };
    // 参数条 = y 最大的一行（底部），容差 6px
    const maxY = Math.max(...btns.map((b) => b.rect[1] + b.rect[3]));
    const bar = btns.filter((b) => maxY - (b.rect[1] + b.rect[3]) <= 8);
    const barY = Math.max(...bar.map((b) => b.rect[1] + b.rect[3]));
    // 工具条 = y 最小的一行（顶部）
    const minY = Math.min(...btns.map((b) => b.rect[1]));
    const tool = btns.filter((b) => b.rect[1] - minY <= 4);
    return { type, panelRect: [Math.round(p.r.x), Math.round(p.r.y), Math.round(p.r.width), Math.round(p.r.height)],
      panelText: (p.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      bottomBar: bar.map((b) => ({ ...b, rect: b.rect })),
      topToolBar: tool.map((b) => ({ ...b, rect: b.rect })),
      nBottom: bar.length, nTool: tool.length, barY };
  });
}

/** 把某类节点拖到画面中间并选中它。 */
async function selectNode(pg, keyword) {
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(700);
  await pg.mouse.click(80, 120); await pg.waitForTimeout(1200); // 先取消选中，否则面板盖住节点
  await fitView(pg); await pg.waitForTimeout(1500);
  const hit = await pg.evaluate((kw) => {
    let best = null;
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(kw)) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 40 || r.x + r.width > 1400 || r.y < 80 || r.y + r.height > 780) continue;
      const d = Math.hypot(r.x + r.width / 2 - 720, r.y - 150);
      if (!best || d < best.d) best = { d, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return best;
  }, keyword);
  if (!hit) return { err: `视口里找不到「${keyword}」节点` };
  if (Math.abs(hit.rect[0] + hit.rect[2] / 2 - 720) > 40 || Math.abs(hit.rect[1] - 150) > 40) {
    const dx = Math.round(720 - (hit.rect[0] + hit.rect[2] / 2));
    const dy = Math.round(150 - hit.rect[1]);
    await pg.mouse.move(hit.cx, hit.cy); await pg.mouse.down();
    for (let i = 1; i <= 16; i += 1) { await pg.mouse.move(hit.cx + (dx * i) / 16, hit.cy + (dy * i) / 16); await pg.waitForTimeout(70); }
    await pg.mouse.up(); await pg.waitForTimeout(2200);
  }
  const now = await pg.evaluate((kw) => {
    let best = null;
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(kw)) continue;
      const r = n.getBoundingClientRect();
      const d = Math.abs(r.x + r.width / 2 - 720);
      if (!best || d < best.d) best = { d, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return best;
  }, keyword);
  if (!now || now.d > 200) return { err: `拖完「${keyword}」还是不在画面中间（偏离 ${now ? now.d : 'n/a'}px）` };
  await pg.mouse.click(now.cx, now.cy);
  await pg.waitForTimeout(4000);
  const sel = await pg.evaluate(() => {
    const n = document.querySelector('.react-flow__node.selected');
    if (!n) return 'none';
    return (/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || 'unknown';
  });
  return { ...now, selectedType: sel };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '抽屉顶部控件 + 资产 tab + 参数条 tooltip 普查（悬停只读，不点生成）' });

  const out = {};

  // ═══ A. 抽屉顶部控件：用文案锚点反查，不用 class 也不用嵌套深浅
  console.log('--- AY2 A 资产管理抽屉 ---');
  const openBtn = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => /资产管理/.test(x.getAttribute('aria-label') || x.getAttribute('title') || ''));
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (!openBtn) throw new Error('底栏没有「资产管理」按钮');
  await page.mouse.click(openBtn.cx, openBtn.cy);
  await page.waitForTimeout(3200);
  await clearToasts(page);

  // 文案锚点：内容里同时有「所有评级」和「资产」的祖先层，且靠左、宽度 300~400
  const drawerAnchor = await page.evaluate(() => {
    const cands = [];
    for (const e of document.querySelectorAll('body div,body section,body aside')) {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t.includes('所有评级')) continue;
      const r = e.getBoundingClientRect();
      if (r.x > 60 || r.width > 420 || r.width < 260 || r.height < 500) continue;
      if (e.closest('.react-flow')) continue;
      cands.push({ cls: (e.className || '').toString().slice(0, 64), tag: e.tagName,
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        depth: (() => { let d = 0, p = e; while ((p = p.parentElement)) d += 1; return d; })(),
        nBtn: [...e.querySelectorAll('button,[role="button"]')].length, head: t.slice(0, 120) });
    }
    return cands.sort((a, b) => b.depth - a.depth);
  });
  console.log('含「所有评级」且靠左的祖先层:');
  drawerAnchor.forEach((c) => console.log(`  depth=${c.depth} ${c.tag} [${c.rect}] btn=${c.nBtn} ${c.cls}\n     "${c.head}"`));
  out.drawerAnchor = drawerAnchor;

  const box = drawerAnchor[0];
  if (box) {
    const dump = await page.evaluate((cls) => {
      const e = [...document.querySelectorAll('body div,body section,body aside')]
        .find((x) => ((x.className || '') + '').startsWith(cls) && (x.innerText || '').includes('所有评级'));
      if (!e) return { err: '锚点回查失败' };
      const fp = (n) => { const s = n.querySelector('svg'); if (!s) return 'nosvg';
        const ds = [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').filter(Boolean);
        return ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 30) : 'svgonly'; };
      const nodes = [...e.querySelectorAll('button,[role="button"],input,a,[role="tab"],select')].map((n) => {
        const r = n.getBoundingClientRect();
        return { tag: n.tagName, text: (n.innerText || n.value || '').replace(/\s+/g, ' ').trim().slice(0, 18),
          aria: n.getAttribute('aria-label'), title: n.getAttribute('title'), role: n.getAttribute('role'),
          type: n.type || '', ph: n.placeholder || '', fp: fp(n),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cursor: getComputedStyle(n).cursor };
      }).filter((n) => n.rect[2] > 0 && n.rect[3] > 0);
      const r = e.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 900), n: nodes.length, nodes };
    }, box.cls);
    out.drawer = dump;
    if (dump.err) console.log('  ⚠', dump.err);
    else {
      console.log(`\n抽屉 [${dump.rect}] 共 ${dump.n} 个可交互元素:`);
      dump.nodes.forEach((n, i) => console.log(
        ` [${String(i).padStart(2)}] [${String(n.rect).padEnd(20)}] ${n.tag.padEnd(6)} role=${(n.role || '-').padEnd(6)} text=${(n.text || '-').padEnd(18)} aria=${(n.aria || '-').padEnd(16)} cur=${(n.cursor || '-').padEnd(8)} fp=${n.fp.slice(0, 20)}`));
      console.log('\n抽屉全文:', dump.text.slice(0, 700));
      await shot(page, 'M-165-资产管理抽屉.png');
      out.shot = 'M-165-资产管理抽屉.png';
    }

    // 悬停给顶部无文字按钮读 tooltip（只读）
    console.log('\n抽屉顶部按钮 tooltip 普查（hover，不点击）:');
    out.drawerTooltips = [];
    const topBtns = (dump.nodes || []).filter((n) => n.rect[1] < 190 && n.rect[2] > 0);
    for (const t of topBtns.slice(0, 14)) {
      const cx = t.rect[0] + t.rect[2] / 2, cy = t.rect[1] + t.rect[3] / 2;
      if (cx < 0 || cx > 1440 || cy < 0 || cy > 810) { out.drawerTooltips.push({ ...t, tip: '出视口不悬停' }); continue; }
      const tip = await hoverTooltip(cx, cy);
      const one = { text: t.text, aria: t.aria, rect: t.rect, fp: t.fp.slice(0, 18), tip: tip.map((x) => x.text) };
      out.drawerTooltips.push(one);
      console.log(`  [${t.rect}] text=${(t.text || '-').padEnd(10)} → tooltip: ${JSON.stringify(one.tip)}`);
    }

    // ═══ B. 切到「资产」tab —— 纯导航
    console.log('\n--- AY2 B 抽屉里的 tab ---');
    out.tabs = await page.evaluate(() => {
      const cands = [...document.querySelectorAll('body *')].filter((n) => {
        const t = (n.innerText || '').trim();
        return t === '画布' || t === '资产'; })
        .map((n) => { const r = n.getBoundingClientRect();
          return { tag: n.tagName, text: (n.innerText || '').trim(), cls: (n.className || '').toString().slice(0, 50),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], cursor: getComputedStyle(n).cursor }; })
        .filter((n) => n.rect[2] > 0 && n.rect[0] < 60);
      return cands.slice(0, 12);
    });
    console.log('tab 候选:', JSON.stringify(out.tabs));
    const assetTab = (out.tabs || []).find((t) => t.text === '资产' && t.rect[2] >= 20);
    if (assetTab) {
      await page.mouse.click(assetTab.rect[0] + assetTab.rect[2] / 2, assetTab.rect[1] + assetTab.rect[3] / 2);
      await page.waitForTimeout(3200);
      await clearToasts(page);
      out.assetTab = await page.evaluate(() => {
        const t = [...document.querySelectorAll('body div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
          .filter((o) => o.r.x < 40 && o.r.width > 250 && o.r.height > 500 && (o.e.innerText || '').includes('所有评级'))
          .sort((a, b) => b.r.width - a.r.width)[0];
        if (!t) return { err: '切 tab 后没找到抽屉' };
        const fps = [...t.e.querySelectorAll('button,[role="button"],input')].map((n) => { const r = n.getBoundingClientRect();
          return { text: (n.innerText || n.value || '').replace(/\s+/g, ' ').trim().slice(0, 14),
            aria: n.getAttribute('aria-label'), ph: n.placeholder || '', type: n.type || '',
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
        }).filter((n) => n.rect[2] > 0);
        return { text: (t.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 800), n: fps.length, nodes: fps.slice(0, 30) };
      });
      console.log('切到「资产」后:', JSON.stringify(out.assetTab).slice(0, 900));
      await shot(page, 'M-167-资产管理-资产页.png');
      out.shot2 = 'M-167-资产管理-资产页.png';
    } else {
      console.log('  ⚠ 没找到可点的「资产」tab');
    }
  }

  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await clearToasts(page);

  // ═══ C. 参数条 tooltip 普查：四种节点
  console.log('\n--- AY2 C 参数条 tooltip 普查 ---');
  out.bars = {};
  for (const kw of ['视频节点', '图片节点', '音频节点', '文本节点']) {
    const sel = await selectNode(page, kw);
    console.log(`\n[${kw}] 选中结果:`, JSON.stringify(sel));
    if (sel.err) { out.bars[kw] = { err: sel.err }; continue; }
    const bar = await bottomBar();
    if (bar.err) { console.log('  ⚠', bar.err); out.bars[kw] = { err: bar.err, sel }; continue; }
    console.log(`  选中类型=${bar.type} 面板=[${bar.panelRect}] 工具条 ${bar.nTool} 枚 / 参数条 ${bar.nBottom} 枚`);
    const named = [];
    for (const b of bar.bottomBar) {
      const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
      if (cx < 0 || cx > 1440 || cy < 0 || cy > 810) { named.push({ ...b, tip: '出视口不悬停' }); continue; }
      const tip = await hoverTooltip(cx, cy, 950);
      named.push({ rect: b.rect, text: b.text, fp: b.fp.slice(0, 24), tip: tip.map((x) => x.text) });
      console.log(`   [${String(b.rect).padEnd(20)}] text=${(b.text || '-').padEnd(12)} fp=${b.fp.slice(0, 18).padEnd(20)} → ${JSON.stringify(tip.map((x) => x.text))}`);
    }
    out.bars[kw] = { sel, type: bar.type, panelRect: bar.panelRect, panelText: bar.panelText,
      toolBar: bar.topToolBar.map((b) => ({ rect: b.rect, text: b.text, fp: b.fp.slice(0, 20) })), bottom: named };
    // 工具条也读一遍 tooltip
    const tn = [];
    for (const b of bar.topToolBar) {
      if (b.text) { tn.push({ rect: b.rect, text: b.text, tip: [b.text] }); continue; }
      const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
      if (cx < 0 || cx > 1440 || cy < 0 || cy > 810) { tn.push({ rect: b.rect, text: b.text, tip: '出视口' }); continue; }
      const tip = await hoverTooltip(cx, cy, 950);
      tn.push({ rect: b.rect, text: b.text, fp: b.fp.slice(0, 20), tip: tip.map((x) => x.text) });
    }
    out.bars[kw].toolTips = tn;
    console.log('   工具条:', JSON.stringify(tn));
  }
  await shot(page, 'M-168-参数条对比.png');
  out.shot3 = 'M-168-参数条对比.png';

  await logStep(B, {
    id: 'AY2-drawer-top-and-tooltips', title: '抽屉顶部控件 + 资产 tab + 四类节点参数条 tooltip 普查',
    target: '**全只读**：抽屉容器用「含『所有评级』且靠左」的文案锚点反查（AY1 用嵌套深浅挑挑窄了一层）；'
      + '参数条按钮一律 **hover 读 Mantine Tooltip**，不点击 —— 无文字按钮能拿到官方名字，'
      + '又不触发生成 / 写账户 / 跳页面',
    evidence: out,
    visible_text: JSON.stringify({ drawer: out.drawer && out.drawer.text, tabs: out.tabs,
      assetTab: out.assetTab && out.assetTab.text, bars: out.bars }).slice(0, 3500),
    shot: out.shot,
  });
  console.log('\nAY2 完成');
} finally {
  await browser.close();
}

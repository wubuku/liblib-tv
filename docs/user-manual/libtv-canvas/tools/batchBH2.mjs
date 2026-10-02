// Batch BH2 — 三个「读不到 ≠ 不存在」的补正 + 手册缺口。
//
// BH1 那张评级截图直接推翻了两条我们自己的结论：
//
// 1. ⭐ **评级筛选的六档，每档右侧都有一个橙色五角星图标** ——
//    而 `innerText` 只读得到 `1` `2` `3` `4` `5`，
//    **因为星形是 SVG、没有文字**。
//    §30「读不到不等于不存在」的又一个实例：
//    这也是为什么 BG1/BG2 用文字正则扫星级是行不通的 ——
//    整个星级 UI **一个文字都没有**，只有图标。
//
// 2. ⭐⭐ **连接口在节点旁边是可见的「⊕」圆圈** ——
//    BG3 说「端口元素 0×0、伪元素 content:none」并据此写成
//    「真正可点的套在里面那个 80×80 透明圆」，
//    但那张截图里 `innerHTML` **被我截断在 160 字**，
//    **没看到那个 80×80 的圆里其实画着可见的标记**。
//    这一轮把 `innerHTML` 完整读出来，把这件事说准。
//
// 3. ⭐ **节点卡片上「尝试：」后面的快捷选项，手册只零散记了几个**。
//    BH1 的 aria 全量清单把它们一次性捞全了 —— 每类节点各 1~4 个，
//    这是用户点开节点第一眼就能用上的信息。
//
// 4. **`智能引用 AutoLink`** —— 选中图片/视频节点时新出现的 aria，
//    手册**完全没记过**。这轮读它的悬停提示与点击后的效果。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBH2';
const { browser, page } = await launch();

async function exclusivePoint(pg, id) {
  return pg.evaluate((nid) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.12) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, id);
}

/** ⭐ 连接口的完整 innerHTML（不截断）+ 内部每个可见元素的尺寸。 */
const handleFull = (pg, nodeId, handleId) => pg.evaluate(([nid, hid]) => {
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
  if (!n) return { err: 'no node' };
  const e = [...n.querySelectorAll('[data-handleid]')].find((x) => x.getAttribute('data-handleid') === hid);
  if (!e) return { err: 'no handle' };
  const box = e.getBoundingClientRect();
  // 内层那个 80×80 的圆
  const inner = [...e.querySelectorAll('div')].map((c) => {
    const r = c.getBoundingClientRect();
    const cs = getComputedStyle(c);
    return { w: Math.round(r.width), h: Math.round(r.height),
      radius: cs.borderRadius, border: cs.border, bg: cs.backgroundColor,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  // 圆里画的东西（svg / 伪元素）
  const svgs = [...e.querySelectorAll('svg')].map((s) => {
    const r = s.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height), fill: s.getAttribute('fill'),
      pathLen: (s.innerHTML.match(/d="([^"]{0,60})/g) || []).length,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  const pe = getComputedStyle(e, '::before');
  const pe2 = getComputedStyle(e, '::after');
  return { outerRect: [Math.round(box.x), Math.round(box.y), Math.round(box.width), Math.round(box.height)],
    fullHtml: e.innerHTML, inner, svgs,
    before: { content: pe.content, w: pe.width, h: pe.height, bg: pe.backgroundColor, border: pe.border },
    after: { content: pe2.content, w: pe2.width, h: pe2.height, bg: pe2.backgroundColor, border: pe2.border } };
}, [nodeId, handleId]);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '连接口完整 innerHTML / 评级星形图标 / 尝试：选项全清单 / 智能引用 AutoLink' });

  const out = {};
  await page.mouse.move(720, 260); await page.waitForTimeout(800);

  // ═══ 1. 连接口：完整读，不截断
  console.log('--- BH2-1 连接口完整结构 ---');
  const h = await handleFull(page, 'i-9nlG6HdjK2', 'target');
  console.log(`  外层盒子：${JSON.stringify(h.outerRect)}`);
  console.log(`  内层 div：${JSON.stringify(h.inner)}`);
  console.log(`  里面的 svg：${JSON.stringify(h.svgs)}`);
  console.log(`  ::before ${JSON.stringify(h.before)}`);
  console.log(`  ::after  ${JSON.stringify(h.after)}`);
  console.log(`  完整 innerHTML（${h.fullHtml.length} 字）：`);
  console.log(`    ${h.fullHtml}`);
  out.handle = h;

  // ═══ 2. 评级下拉：星形图标逐档读
  console.log('\n--- BH2-2 评级六档的星形图标 ---');
  const dm = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '资产管理');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (dm) {
    await page.mouse.click(dm.x, dm.y); await page.waitForTimeout(2500);
    const rp = await page.evaluate(() => {
      const e = [...document.querySelectorAll('button,[role="button"]')]
        .find((x) => /评级/.test(x.getAttribute('aria-label') || ''));
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
    if (rp) {
      await page.mouse.click(rp.x, rp.y); await page.waitForTimeout(2200);
      // ⭐ 每一行：文字 + 里面的 svg（星形）
      const rows = await page.evaluate(() => {
        const ok = (e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName);
        const seen = new Set(); const out2 = [];
        for (const e of document.querySelectorAll('div,li,button')) {
          if (!ok(e)) continue;
          const r = e.getBoundingClientRect();
          if (r.width < 40 || r.height < 10 || r.height > 50 || r.x < 60 || r.x > 300 || r.y < 140) continue;
          const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
          if (!/^(所有评级|[1-5])$/.test(t)) continue;
          const k = `${Math.round(r.x)},${Math.round(r.y)}`;
          if (seen.has(k)) continue; seen.add(k);
          const svgs = [...e.querySelectorAll('svg')].map((s) => {
            const q = s.getBoundingClientRect();
            return { w: Math.round(q.width), h: Math.round(q.height), fill: s.getAttribute('fill'),
              cls: (s.getAttribute('class') || '').slice(0, 40) }; });
          out2.push({ text: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            cursor: getComputedStyle(e).cursor, svgs, html: e.innerHTML.slice(0, 120) });
        }
        return out2.sort((a, b) => a.rect[1] - b.rect[1]);
      });
      console.log(`  读到 ${rows.length} 档：`);
      for (const r of rows) {
        console.log(`    [${r.rect}] "${r.text}" cursor=${r.cursor} svg=${r.svgS ? '' : ''}${JSON.stringify(r.svgs)}`);
      }
      out.ratings = rows;
      await shot(page, 'M-198-评级筛选-六档.png');
      out.shot = 'M-198-评级筛选-六档.png';
      // ⭐ 顺带验一件事：选「1★」之后列表剩几行
      const one = rows.find((r) => r.text === '1');
      if (one) {
        const beforeRows = await page.evaluate(() =>
          [...document.querySelectorAll('*')]
            .filter((e) => (e.innerText || '').trim().startsWith('定位到节点') && e.getBoundingClientRect().height > 20).length);
        await page.mouse.click(one.rect[0] + one.rect[2] / 2, one.rect[1] + one.rect[3] / 2);
        await page.waitForTimeout(2200);
        const afterRows = await page.evaluate(() =>
          [...document.querySelectorAll('*')]
            .filter((e) => (e.innerText || '').trim().startsWith('定位到节点') && e.getBoundingClientRect().height > 20).length);
        const btnNow = await page.evaluate(() => {
          const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => /评级/.test(x.getAttribute('aria-label') || ''));
          return e ? (e.innerText || '').trim() : null; });
        console.log(`  选「1★」：列表行数 ${beforeRows} → ${afterRows}；按钮正文变成 "${btnNow}"`);
        out.ratingFilter = { before: beforeRows, after: afterRows, btnText: btnNow };
        // 复原
        const all = await page.evaluate(() => {
          const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => /评级/.test(x.getAttribute('aria-label') || ''));
          if (!e) return null; const r = e.getBoundingClientRect();
          return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
        if (all) {
          await page.mouse.click(all.x, all.y); await page.waitForTimeout(2000);
          const back = await page.evaluate(() => [...document.querySelectorAll('*')]
            .filter((e) => (e.innerText || '').trim().startsWith('定位到节点') && e.getBoundingClientRect().height > 20).length);
          const rst = await page.evaluate(() => {
            const e = [...document.querySelectorAll('button,[role="button"]')].find((x) => /评级/.test(x.getAttribute('aria-label') || ''));
            if (!e) return null; const r = e.getBoundingClientRect();
            return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
          if (rst) { await page.mouse.click(rst.x, rst.y); await page.waitForTimeout(2000);
            const opt = await page.evaluate(() => [...document.querySelectorAll('div,li,button')]
              .filter((e) => (e.innerText || '').trim() === '所有评级' && e.getBoundingClientRect().height > 20)
              .map((e) => { const r = e.getBoundingClientRect();
                return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; })[0]);
            if (opt) { await page.mouse.click(opt.x, opt.y); await page.waitForTimeout(2000); }
          }
          const finalRows = await page.evaluate(() =>
            [...document.querySelectorAll('*')]
              .filter((e) => (e.innerText || '').trim().startsWith('定位到节点') && e.getBoundingClientRect().height > 20).length);
          console.log(`  复原「所有评级」后：列表 ${finalRows} 行`);
          out.ratingFilter.restored = finalRows;
        }
      }
      await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
    }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  }

  // ═══ 3. 「尝试：」快捷选项的完整清单
  console.log('\n--- BH2-3 节点卡片「尝试：」选项全清单 ---');
  const tries = {};
  for (const n of (await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((x) => ({ id: x.getAttribute('data-id'),
      name: ((x.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 10) }))))) {
    const info = await page.evaluate((nid) => {
      const el = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
      if (!el) return null;
      // 找「尝试：」那个标签，然后读它同一区域里的可点项
      const label = [...el.querySelectorAll('*')]
        .find((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().startsWith('尝试：'));
      const box = el.getBoundingClientRect();
      // 该节点内所有小尺寸可点元素（快捷选项通常是这个尺寸）
      const items = [...el.querySelectorAll('button,[role="button"],[class*="cursor-pointer"],div')]
        .map((e) => { const r = e.getBoundingClientRect();
          return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            cursor: getComputedStyle(e).cursor, tag: e.tagName,
            aria: e.getAttribute('aria-label') }; })
        .filter((x) => x.text && x.text.length < 24 && x.rect[2] > 0 && x.rect[3] > 0
          && x.rect[3] < 40 && x.rect[1] > box.y && x.rect[1] < box.y + box.height
          && x.cursor === 'pointer' && !/尝试/.test(x.text));
      // 去重（父子同文）
      const uniq = []; const seen = new Set();
      for (const it of items) { const k = it.text; if (seen.has(k)) continue; seen.add(k); uniq.push(it); }
      return { hasLabel: !!label, items: uniq };
    }, n.id);
    tries[n.name + ' / ' + n.id] = info;
    console.log(`  ${n.name}（${n.id}）：「尝试：」标签 ${info?.hasLabel ? '有' : '无'}；可点项 ${info?.items.length} 个`);
    (info?.items || []).forEach((i) => console.log(`     [${i.rect}] "${i.text}" ${i.tag}${i.aria ? ` aria=${i.aria}` : ''}`));
  }
  out.tries = tries;

  // ═══ 4. 「智能引用 AutoLink」
  console.log('\n--- BH2-4 智能引用 AutoLink ---');
  const pt = await exclusivePoint(page, 'i-9nlG6HdjK2');
  if (pt.err) { console.log(' ', pt.err); out.autolink = { err: pt.err }; }
  else {
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(2400);
    const al = await page.evaluate(() => {
      const e = [...document.querySelectorAll('button,[role="button"]')]
        .find((x) => /AutoLink/.test(x.getAttribute('aria-label') || ''));
      if (!e) return { err: '没找到 AutoLink 按钮' };
      const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cursor: getComputedStyle(e).cursor, disabled: e.disabled === true,
        html: e.innerHTML.slice(0, 200) }; });
    console.log(`  按钮：${JSON.stringify(al)}`);
    if (!al.err) {
      // 悬停读 tooltip
      await page.mouse.move(al.rect[0] + al.rect[2] / 2, al.rect[1] + al.rect[3] / 2);
      await page.waitForTimeout(1600);
      const tip = await page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
        .filter((t) => !/按 ESC 退出|^新功能/.test(t)));
      console.log(`  悬停提示：${JSON.stringify(tip)}`);
      out.autolink = { btn: al, tip };
    } else out.autolink = al;
    await shot(page, 'M-199-智能引用-AutoLink.png');
    out.shot2 = 'M-199-智能引用-AutoLink.png';
  }

  await logStep(B, {
    id: 'BH2-handle-fullhtml-rating-stars-tries',
    title: '连接口完整 innerHTML / 评级星形图标 / 「尝试：」全清单 / 智能引用 AutoLink',
    target: 'BH1 的评级截图推翻了两条我们自己的结论：① 评级每档右侧有橙色五角星，'
      + '而 innerText 只读到数字 —— 整个星级 UI 一个文字都没有，只有图标；'
      + '② 连接口旁边的 ⊕ 圆圈是可见的，BG3 把 innerHTML 截断在 160 字所以没看到。'
      + '这轮把 innerHTML 完整读出来，并顺手捞全节点卡片「尝试：」快捷选项与「智能引用 AutoLink」。',
    evidence: out,
    visible_text: JSON.stringify({
      handle: { outer: out.handle?.outerRect, inner: out.handle?.inner, svgs: out.handle?.svgs,
        before: out.handle?.before, after: out.handle?.after, htmlLen: out.handle?.fullHtml?.length },
      ratings: out.ratings?.map((r) => ({ text: r.text, svgs: r.svgs, cursor: r.cursor })),
      ratingFilter: out.ratingFilter,
      tries: Object.fromEntries(Object.entries(out.tries || {}).map(([k, v]) => [k, v?.items?.map((i) => i.text)])),
      autolink: { aria: out.autolink?.btn?.aria, rect: out.autolink?.btn?.rect, cursor: out.autolink?.btn?.cursor, tip: out.autolink?.tip } }).slice(0, 3500),
    shot: out.shot2,
  });
  console.log('\nBH2 完成');
} finally {
  await browser.close();
}

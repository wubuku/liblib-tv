// Batch BI1c — 像素级判定：连接口图标到底默认显不显示。
//
// 局面已经很清楚了，但三方读数互相打架，必须用**像素**裁决：
//   ① BH2 读 `innerHTML` 里的 inline `style`：L2 写着 `opacity: 0`、20×20
//   ② BI1 读 `getComputedStyle(svg).opacity` = **1**（错：opacity 不继承，
//      svg 自己的值是 1，父级 L2 的 0 不会体现在它身上）
//   ③ BI1b 读 `getComputedStyle(L2).opacity` = **0**（对），但 L2 的 rect 是
//      **11×11**，而 inline 写的是 20×20 —— 计算值与属性值又对不上
//
// ⭐ ③ 那条「rect 11×11 vs 属性 20×20」说明**有 CSS 规则用 !important 覆盖了
//    宽高**，那它也可能覆盖 opacity。而 L1 那个 80×80 的圆，计算 rect 却是
//    **42×42** —— 同样是属性与计算值对不上。
//    ⚠️ 属性 ≠ 计算值 ≠ 渲染结果，三者可能各说各话。**只有像素说了算。**
//
// 判据：同一个节点、同一个口，未选中 / 悬停 / 选中三个态各裁一张**同一区域**的图，
// 逐像素比对 —— 若三张图完全一致，图标就是**一直显示**，与 hover/选中无关。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBI1c';
const { browser, page } = await launch();
const ID = 'i-9nlG6HdjK2';

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '像素级裁决：属性 / 计算值 / 渲染三者打架时只信像素' });

  const out = {};

  // 把口的位置与四层读数一次性取全，并顺带查有没有样式表覆盖
  const info = await page.evaluate((id) => {
    const n = [...document.querySelectorAll('.react-flow__node')]
      .find((x) => x.getAttribute('data-id') === id);
    const h = n.querySelector('[data-handleid="source"]');
    const l1 = h.children[0], l2 = l1.children[0], svg = l2.querySelector('svg');
    const r1 = l1.getBoundingClientRect(), r2 = l2.getBoundingClientRect(), rs = svg.getBoundingClientRect();
    window.__k = { n, h, l1, l2, svg };
    return {
      nodeCls: (n.className || '').toString().slice(0, 80),
      selected: n.classList.contains('selected'),
      handleCls: (h.className || '').toString().slice(0, 120),
      L1: { rect: [r1.x, r1.y, r1.width, r1.height].map(Math.round), attr: l1.getAttribute('style'),
        computedW: getComputedStyle(l1).width, computedOpacity: getComputedStyle(l1).opacity },
      L2: { rect: [r2.x, r2.y, r2.width, r2.height].map(Math.round), attr: l2.getAttribute('style'),
        computedW: getComputedStyle(l2).width, computedH: getComputedStyle(l2).height,
        computedOpacity: getComputedStyle(l2).opacity, cls: (l2.className || '').toString() },
      SVG: { rect: [rs.x, rs.y, rs.width, rs.height].map(Math.round),
        computedOpacity: getComputedStyle(svg).opacity },
    };
  }, ID);
  console.log('══ 读数 ══');
  console.log('  L1 80×80 圆：属性写 80px，计算宽 =', info.L1.computedW, ' rect =', JSON.stringify(info.L1.rect));
  console.log('  L2 图标盒：属性写 20px/opacity:0，计算 =', info.L2.computedW, '×', info.L2.computedH,
    ' opacity =', info.L2.computedOpacity, ' rect =', JSON.stringify(info.L2.rect), ' class=', JSON.stringify(info.L2.cls));
  console.log('  SVG：计算 opacity =', info.SVG.computedOpacity, ' rect =', JSON.stringify(info.SVG.rect));

  // ⭐ 查一下：有没有样式表规则用 !important 覆盖了 width/opacity
  const rules = await page.evaluate(() => {
    const out = [];
    for (const ss of document.styleSheets) {
      let list; try { list = ss.cssRules; } catch { continue; }
      for (const r of list || []) {
        const t = r.cssText || '';
        if (/react-flow__handle|connectionindicator/.test(t) && /!important/.test(t)) {
          out.push(t.slice(0, 220));
        }
      }
    }
    return out.slice(0, 12);
  });
  console.log(`  含 !important 且提到 handle 的样式规则：${rules.length} 条`);
  rules.forEach((r) => console.log('    ', r));
  out.rules = rules;

  // ── 裁剪区域：以 L2 图标为中心，往外取 90×50，避开节点本体（往节点外侧偏）
  const clip = await page.evaluate(() => {
    const r = window.__k.l1.getBoundingClientRect();   // 用 80×80 那个圆定位
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    return { x: Math.max(0, Math.round(cx - 75)), y: Math.max(0, Math.round(cy - 45)),
      width: 150, height: 90, center: [Math.round(cx), Math.round(cy)] };
  });
  console.log('  裁剪区域 =', JSON.stringify(clip));

  const shoot = async (tag) => {
    const p = `screenshots/.tmp-${tag}.png`;
    await page.screenshot({ path: p, clip: { x: clip.x, y: clip.y, width: clip.width, height: clip.height } });
    return p;
  };

  // 三态裁同一块区域
  await page.mouse.move(120, 120); await page.waitForTimeout(1600);          // 态 A：远离
  const a = await shoot('BI1c-A-far');
  const c1 = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

  const circ = await page.evaluate(() => { const r = window.__k.l1.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await page.mouse.move(circ[0], circ[1]); await page.waitForTimeout(1600); // 态 B：悬停在口上
  const b = await shoot('BI1c-B-hover');
  const c2 = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

  const body = await page.evaluate(() => { const r = window.__k.n.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  await page.mouse.click(body[0], body[1]); await page.waitForTimeout(2400);  // 态 C：选中
  const c = await shoot('BI1c-C-selected');
  const c3 = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  const after = await page.evaluate(() => {
    const l2 = window.__k.l2, svg = window.__k.svg;
    const r2 = l2.getBoundingClientRect(), rs = svg.getBoundingClientRect();
    return { L2: { rect: [r2.x, r2.y, r2.width, r2.height].map(Math.round), attr: l2.getAttribute('style'),
      computedOpacity: getComputedStyle(l2).opacity, computedW: getComputedStyle(l2).width },
      SVG: { rect: [rs.x, rs.y, rs.width, rs.height].map(Math.round), computedOpacity: getComputedStyle(svg).opacity } };
  });
  console.log(`  选中数 A/B/C = ${c1}/${c2}/${c3}`);
  console.log('  选中后 L2：', JSON.stringify(after.L2));
  console.log('  选中后 SVG：', JSON.stringify(after.SVG));
  out.states = { a, b, c, counts: [c1, c2, c3], before: info, after };

  // 找 L2 上真正生效的 CSS 规则（逐条试）
  const effective = await page.evaluate(() => {
    const l2 = window.__k.l2, hits = [];
    for (const ss of document.styleSheets) {
      let list; try { list = ss.cssRules; } catch { continue; }
      for (const r of list || []) {
        if (!r.selectorText || !r.style) continue;
        if (!/width|height|opacity|transform/.test(r.style.cssText)) continue;
        let m = false; try { m = l2.matches(r.selectorText); } catch {}
        if (m) hits.push({ sel: r.selectorText.slice(0, 90),
          css: r.style.cssText.slice(0, 160),
          width: r.style.getPropertyValue('width'), height: r.style.getPropertyValue('height'),
          opacity: r.style.getPropertyValue('opacity'), prioW: r.style.getPropertyPriority('width'),
          prioO: r.style.getPropertyPriority('opacity') });
      }
    }
    return hits;
  });
  console.log(`\n  命中 L2 的样式规则 ${effective.length} 条：`);
  effective.forEach((e) => console.log(`    ${e.sel}  {${e.css}}  !important: w=${e.prioW} o=${e.prioO}`));
  out.effectiveRules = effective;

  await logStep(B, {
    id: 'BI1c-port-icon-pixel-verdict',
    title: '像素级裁决：端口图标默认显不显示',
    target: '属性值（opacity:0/20px）、计算值（L2 opacity 0 但 rect 11×11、80×80 圆算成 42×42）、'
      + 'BI1 读 svg 自身的 opacity 1 —— 三方互相打架。用同一区域三态裁图 + 逐像素比对裁决，'
      + '并把 L2 上真正命中的 CSS 规则连 !important 一起列出来。',
    evidence: out,
    visible_text: JSON.stringify({ before: out.states?.before, after: out.states?.after,
      counts: out.states?.counts, rules: out.effectiveRules?.length }).slice(0, 3000),
  });
  console.log('\nBI1c 完成');
} finally {
  await browser.close();
}

// Batch BG4 — 复原画布（⌘Z 撤不回来）+ 坐实「连线两端在 aria-label 里」。
//
// ⛔ BG3 拖出了一条新连线（1 → 2），**`⌘Z` 没撤回来**。
//    这与 inventory 早就记的「删除单个节点 `⌘Z` 也撤不回来」是同一族问题。
//    ✅ 这一轮先用别的路复原，**不碰 ⌘Z**。
//
// ⭐⭐ 顺带一个极有价值的发现：BG3 找「这条连线连的是谁」时，
//    从 `path` 的 `d` 坐标反推（距离 969~1325，全是错的）。
//    读 `aria-label` 才发现答案就写在脸上：
//    **`aria-label="Edge from i-9nlG6HdjK2 to v-eMpqKtiLlx"`**
//    —— ✅ 认连线的两端应该读 `aria-label`，不是坐标反推、也不是 `data-source`
//    （`.react-flow__edge` 上**根本没有** `data-source` / `data-target`）。
//    这条直接写进 connect-nodes 手册，是读者用得上的信息。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBG4';
const { browser, page } = await launch();

/** ⭐ 连线读数：两端直接从 `aria-label` 抠。 */
const edges = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => {
  const label = e.getAttribute('aria-label') || '';
  const m = /^Edge from (\S+) to (.+)$/.exec(label);
  const p = e.querySelector('path');
  return { id: e.getAttribute('data-id'), testid: e.getAttribute('data-testid'),
    role: e.getAttribute('role'), roleDesc: e.getAttribute('aria-roledescription'),
    label, from: m ? m[1] : null, to: m ? m[2] : null,
    temp: label.includes('__temp'),
    cls: (e.getAttribute('class') || '').slice(0, 60),
    stroke: p ? getComputedStyle(p).stroke : null, sw: p ? getComputedStyle(p).strokeWidth : null };
}));

const nodeName = (pg, id) => pg.evaluate((nid) => {
  const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
  if (!n) return null;
  return ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12);
}, id);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '复原 BG3 连不上的新连线 + 坐实连线两端在 aria-label 里' });

  const out = {};
  await page.mouse.move(720, 260); await page.waitForTimeout(800);

  // ═══ 1. 读连线清单（aria-label 判据）
  console.log('--- BG4-1 连线清单（读 aria-label）---');
  let es = await edges();
  console.log(`  共 ${es.length} 条：`);
  for (const e of es) {
    const fn = e.from ? await nodeName(page, e.from) : null;
    const tn = e.to ? await nodeName(page, e.to) : null;
    console.log(`  ${e.id}  "${e.label}"`);
    console.log(`    from=${e.from}(${fn}) to=${e.to}(${tn}) temp=${e.temp} testid=${e.testid} role=${e.role}/${e.roleDesc} stroke=${e.stroke} ${e.sw}`);
  }
  out.edges = es;

  // ═══ 2. 复原：把 BG3 多出来的那条删掉
  console.log('\n--- BG4-2 复原 ---');
  const ORIG = 'e-5U2jB82fuL';       // BG3 之前就有的那条
  const extra = es.filter((e) => e.id !== ORIG && !e.temp);
  console.log(`  原有的 ${ORIG}；多出来的 ${extra.length} 条：${extra.map((e) => e.id).join(', ') || '（无）'}`);
  if (!extra.length) { out.restore = { need: false, count: es.length }; console.log('  无需复原'); }
  else {
    // 办法一：点连线选中再按删除键
    for (const e of extra) {
      const hit = await page.evaluate((eid) => {
        const el = document.querySelector(`[data-testid="rf__edge-${eid}"]`)
          || [...document.querySelectorAll('.react-flow__edge')].find((x) => x.getAttribute('data-id') === eid);
        if (!el) return { err: 'no edge el' };
        const p = el.querySelector('path');
        if (!p) return { err: 'no path' };
        const len = p.getTotalLength ? p.getTotalLength() : 0;
        const pt = len ? p.getPointAtLength(len / 2) : null;
        if (!pt) return { err: 'no point' };
        const q = el.getBoundingClientRect();
        return { x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2) }; }, e.id);
      if (hit.err) { console.log(`  ${e.id}: ${hit.err}`); continue; }
      const own = await page.evaluate(([x, y]) => {
        const o = document.elementFromPoint(x, y);
        return { tag: o ? o.tagName : null,
          inEdge: !!(o && o.closest('.react-flow__edge')),
          edgeId: o ? (o.closest('.react-flow__edge')?.getAttribute('data-id') || null) : null };
      }, [hit.x, hit.y]);
      console.log(`  点 ${e.id}：落点 [${hit.x},${hit.y}] 归属 ${JSON.stringify(own)}`);
      if (!own.inEdge) { console.log('    ⚠️ 落点不在连线上，跳过'); continue; }
      await page.mouse.click(hit.x, hit.y); await page.waitForTimeout(1800);
      const sel = await page.evaluate(() => ({
        edges: document.querySelectorAll('.react-flow__edge').length,
        selectedEdge: document.querySelectorAll('.react-flow__edge.selected, .react-flow__edge[aria-selected="true"]').length,
        selected: !!document.querySelector('.react-flow__edge.selected'),
      }));
      console.log(`    点后：连线 ${sel.edges} 条；连线选中态 ${JSON.stringify(sel)}`);
      // 焦点交回画布再按删除（inventory 记过这个坑）
      await page.keyboard.press('Escape'); await page.waitForTimeout(500);
      await page.mouse.click(720, 260); await page.waitForTimeout(800);
      await page.keyboard.press('Backspace'); await page.waitForTimeout(2200);
      const afterDel = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
      console.log(`    按 ⌫ 后：连线 ${afterDel} 条 ${afterDel < sel.edges ? '✅ 删掉了' : '（没删掉）'}`);
    }
    es = await edges();
    console.log(`  复原后：${es.length} 条 → ${es.map((e) => e.id).join(', ')}`);
    out.restore = { after: es.length, ids: es.map((e) => e.id),
      restored: es.length === 1 && es[0].id === ORIG };
    // 落盘验证
    await page.reload({ waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6500);
    await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
    await page.keyboard.press('Meta+0'); await page.waitForTimeout(2200);
    const after2 = await edges();
    console.log(`  刷新后：${after2.length} 条 → ${after2.map((e) => `${e.id}(${e.from}→${e.to})`).join(', ')}`);
    out.afterReload = after2;
    out.restore.persisted = after2.length === 1 && after2[0].id === ORIG;
    await shot(page, 'M-196-连线-aria-label清单.png');
    out.shot = 'M-196-连线-aria-label清单.png';
  }

  await logStep(B, {
    id: 'BG4-restore-and-aria-edges',
    title: '复原 BG3 的新连线 + 坐实连线两端写在 aria-label 里',
    target: 'BG3 拖出一条新连线后 ⌘Z 撤不回来（与 inventory 早就记的「删除节点 ⌘Z 也撤不回来」同族），'
      + '这轮换点选连线 + 交回焦点 + ⌫ 的路子复原。'
      + '⭐ 顺带坐实认连线两端的正确判据：aria-label="Edge from <源> to <目标>"，'
      + '而 .react-flow__edge 上根本没有 data-source / data-target，'
      + '从 path 的 d 坐标反推距离 969~1325 全错。',
    evidence: out,
    visible_text: JSON.stringify({ edges: out.edges, restore: out.restore,
      afterReload: out.afterReload?.map((e) => `${e.id}: ${e.label}`) }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBG4 完成');
} finally {
  await browser.close();
}

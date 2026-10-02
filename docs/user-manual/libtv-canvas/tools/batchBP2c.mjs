// Batch BP2c — 把「资产管理」弹窗读透 + 给每次探测加一个能自证的「弹窗已关」守卫。
//
// ⛔ 先认自己刚犯的错（BP2b 的判据污染）：
//   BP2b 依次点了「更多操作 / 创建 / 筛选 / 搜索 / 批量操作」，每次点完按 Escape 再点下一个。
//   但 M-254 证明**「更多操作」打开的是一整个全屏「资产管理」弹窗**，
//   而**按 Escape 并没有关掉它** —— 于是：
//     · 「创建」那一轮的 `新增浮层=0` 是因为弹窗已经开着、基线里已经有了，**不是**因为「创建」没反应；
//     · 两轮都出现「创建主体」是**同一块残留画面**，不是两个入口各自的产物。
//   ⇒ **回退动作必须独立复核**（BN5 立过）。下面 `assertClosed()` 不相信 Escape，
//     它用三个互相独立的证据判定「真的关了」：
//       ① 全屏 Modal 容器数 = 0
//       ② 弹窗标题「资产管理」不再出现在 DOM 可见层里
//       ③ ⭐ **elementFromPoint 打中抽屉里的「创建」按钮**（阳性对照：
//          真能点到才算关；点不到说明还有东西盖在上面）
//
// 本轮全部只读：⛔ 不建主体、不传文件、不删东西、不改名。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBP2c';
const { browser, page } = await launch();

const clickAria = async (label, wait = 2400) => {
  const p = await page.evaluate((l) => {
    const hits = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .map((x) => ({ x, r: x.getBoundingClientRect() }))
      .filter(({ x, r }) => x.getAttribute('aria-label') === l && r.width >= 4 && r.height >= 4);
    if (!hits.length) return null;
    const r = hits[0].r;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, label);
  if (!p) return { executed: false, note: `找不到可见的 aria-label=${label}` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};
const clickText = async (txt, wait = 2600, minW = 0) => {
  const p = await page.evaluate(([t, mw]) => {
    const seen = new Set();
    for (const e of document.querySelectorAll('div,button,span,li,a')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4 || r.width < mw) continue;
      const k = `${Math.round(r.x)}@${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k);
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    } return null; }, [txt, minW]);
  if (!p) return { executed: false, note: `找不到文字「${txt}」` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};

/**
 * ⭐ 「弹窗真的关了吗」—— 不相信 Escape，用三个独立证据判。
 * @param {{probe?:[number,number]}} opts probe 点用来做阳性对照（默认打「创建」按钮中心）
 */
const assertClosed = async ({ probe = null } = {}) => {
  // ① 全屏 Modal 容器  ② 标题还在不在  ③ elementFromPoint 打不打得中抽屉
  const st = await page.evaluate((pv) => {
    const big = [...document.querySelectorAll('div,section')]
      .filter((e) => { const r = e.getBoundingClientRect();
        return r.width > 900 && r.height > 500 && getComputedStyle(e).visibility !== 'hidden'; })
      .filter((e) => /Modal|Dialog|Drawer/.test((e.className || '').toString()))
      .map((e) => ({ cls: (e.className || '').toString().slice(0, 60),
        title: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }));
    const title = [...document.querySelectorAll('div,h1,h2,span')]
      .filter((e) => (e.innerText || '').trim() === '资产管理' && e.getBoundingClientRect().width > 0).length;
    let hit = null;
    if (pv) {
      const el = document.elementFromPoint(pv[0], pv[1]);
      let chain = []; for (let e = el, i = 0; e && i < 4; e = e.parentElement, i++) {
        chain.push(`${e.tagName}.${(e.className || '').toString().split(' ')[0]}`); }
      hit = { chain, isInModal: !!el?.closest('.mantine-Modal-root,[class*=Modal]') };
    }
    return { modals: big, titleCount: title, probeHit: hit };
  }, probe);
  const closed = st.modals.length === 0 && st.titleCount === 0
    && (!st.probeHit || !st.probeHit.isInModal);
  return { closed, ...st };
};

/** 关弹窗：先 Escape，不行点 ✕，最后**必须** assertClosed 自证。 */
const closeAll = async (probe) => {
  const tries = [];
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  tries.push({ how: 'Escape', ...(await assertClosed({ probe })) });
  if (!tries[0].closed) {
    const x = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button[aria-label="关闭"],button[aria-label="Close"],button')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 8 && r.height > 8; })
        .find((e) => /^[✕×xX]$/.test((e.innerText || '').trim()) || /关闭|Close/.test(e.getAttribute('aria-label') || ''));
      if (!b) return null; const r = b.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (x) { await page.mouse.click(x[0], x[1]); await page.waitForTimeout(1200); tries.push({ how: '✕', at: x, ...(await assertClosed({ probe })) }); }
    else tries.push({ how: '✕-找不到', ...(await assertClosed({ probe })) });
  }
  if (!tries[tries.length - 1].closed) await page.mouse.click(1400, 800); // 点最右下角空白
  tries.push({ how: '收尾复核', ...(await assertClosed({ probe })) });
  return tries;
};

const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(900); };

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '读透「资产管理」弹窗；每次探测前后都用 assertClosed 自证「弹窗真的关了」' });
  const out = {};

  await clickAria('资产管理', 2800);
  await clickText('资产', 2600, 20);
  // 阳性对照点：抽屉里「创建」按钮的中心
  const probe = [219, 162];
  const g0 = await assertClosed({ probe });
  out.guard0 = g0;
  console.log(`═══ 守卫自检（进资产页后）═══ closed=${g0.closed} 弹窗容器=${g0.modals.length} 标题数=${g0.titleCount}`);
  console.log(`  elementFromPoint(${probe}) → ${JSON.stringify(g0.probeHit)}`);
  console.log(`  ⭐ 阳性对照：这条链里出现 Modal 的话，说明「守卫本身失效」，后面全部结论作废`);

  const S = await page.evaluate(() => {
    const d = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
      return r.x < 40 && r.width > 250 && r.width < 380 && r.height > 300; })
      .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
    return { text: (d?.innerText || '').replace(/\s+/g, ' ').trim(),
      rows: [...(d?.querySelectorAll('*') || [])].filter((e) => {
          const r = e.getBoundingClientRect();
          return r.y > 180 && r.y < 300 && r.height >= 20 && r.height <= 60 && r.x < 30; })
        .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
          cls: (e.className || '').toString().slice(0, 40),
          svg: e.querySelectorAll('svg').length, aria: e.getAttribute('aria-label') })) };
  });
  out.drawer = S;
  console.log(`\n═══ 抽屉现状 ═══\n  ${S.text}`);
  console.log(`  行内件：${JSON.stringify(S.rows)}`);

  // ── ① 「管理」到底开什么？用 fingerprint 差集 + 守卫
  console.log(`\n═══ ① 点抽屉头部的「管理」 ═══`);
  const b1 = await fingerprint(page);
  const mg = await clickAria('资产管理', 2600);
  const a1 = await fingerprint(page);
  const f1 = diffPanels(b1, a1).slice(0, 4).map((p) => ({ area: p.area, all: p.all.slice(0, 300), buttons: p.buttons.slice(0, 16) }));
  out.manageClick = { ...mg, fresh: f1 };
  console.log(`  executed=${mg.executed}｜新增浮层 ${f1.length} 个`);
  f1.forEach((f, i) => console.log(`   ${i + 1}. area=${f.area} 文案=${JSON.stringify(f.all)}\n      按钮=${JSON.stringify(f.buttons)}`));
  await shot(page, 'M-255-资产管理弹窗-从管理进入.png');
  const ga = await assertClosed({ probe });
  console.log(`  守卫：closed=${ga.closed} 弹窗容器=${ga.modals.length} 标题数=${ga.titleCount} probe命中Modal=${ga.probeHit?.isInModal}`);
  out.afterManageGuard = ga;

  // ── ② 读透弹窗：侧栏项 + 标签页 + 内容
  if (!ga.closed) {
    const M = await page.evaluate(() => {
      const root = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
          return r.width > 800 && r.height > 500; })
        .sort((a, b) => b.getBoundingClientRect().area - a.getBoundingClientRect().area)[0];
      if (!root) return { err: 'no root' };
      const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      const at = (e) => { const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; };
      return {
        text: (root.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 600),
        side: [...root.querySelectorAll('div,button,a,li')].filter(vis)
          .filter((e) => { const r = e.getBoundingClientRect(); return r.x < 420 && r.width > 60 && r.height >= 24 && r.height <= 60 && e.children.length <= 2; })
          .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), at: at(e),
            sel: getComputedStyle(e).backgroundColor })).filter((x) => x.t)
          .filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.at[1] === v.at[1]) === i),
        tabs: [...root.querySelectorAll('div,button,li,span')].filter(vis)
          .filter((e) => { const r = e.getBoundingClientRect();
            return r.x > 420 && r.y > 150 && r.y < 320 && r.height >= 24 && r.height <= 48
              && r.width >= 30 && r.width <= 140 && e.children.length === 0; })
          .map((e) => ({ t: (e.innerText || '').trim(), at: at(e),
            bg: getComputedStyle(e).backgroundColor, color: getComputedStyle(e).color }))
          .filter((x) => x.t).filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.at[1] === v.at[1]) === i),
        allButtons: [...root.querySelectorAll('button,[role="button"]')].filter(vis)
          .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
            aria: e.getAttribute('aria-label'), at: at(e) })),
      };
    });
    out.modal = M;
    console.log(`\n═══ ② 弹窗读数 ═══\n  全文：${M.text}`);
    console.log(`  侧栏：${JSON.stringify(M.side)}`);
    console.log(`  标签：${JSON.stringify(M.tabs)}`);
    console.log(`  按钮：${JSON.stringify(M.allButtons)}`);
  }

  const cl1 = await closeAll(probe);
  out.close1 = cl1;
  console.log(`\n  ⭐ 关弹窗尝试：${JSON.stringify(cl1.map((c) => ({ how: c.how, closed: c.closed, modals: c.modals.length, title: c.titleCount })))}`);
  out.escapeAloneWorks = cl1.find((c) => c.how === 'Escape')?.closed ?? null;
  console.log(`  ⭐⭐ 单按 Escape 能关掉吗？ ${out.escapeAloneWorks ? '✅ 能' : '❌ 不能 —— BP2b 的污染就是这么来的'}`);

  // ── ③ 「创建」在干净状态下重测（BP2b 那轮作废）
  console.log(`\n═══ ③ 「创建」在干净状态下重测 ═══`);
  const b3 = await fingerprint(page);
  const cr = await clickAria('创建', 2400);
  const a3 = await fingerprint(page);
  const f3 = diffPanels(b3, a3).slice(0, 4).map((p) => ({ area: p.area, all: p.all.slice(0, 300), buttons: p.buttons.slice(0, 16) }));
  out.createClean = { ...cr, fresh: f3 };
  console.log(`  executed=${cr.executed}｜新增浮层 ${f3.length} 个`);
  f3.forEach((f, i) => console.log(`   ${i + 1}. area=${f.area} 文案=${JSON.stringify(f.all)}\n      按钮=${JSON.stringify(f.buttons)}`));
  await shot(page, 'M-256-资产页-创建下拉.png');
  const g3 = await assertClosed({ probe });
  console.log(`  守卫：closed=${g3.closed} 标题数=${g3.titleCount} probe命中Modal=${g3.probeHit?.isInModal}`);
  await closeAll(probe);

  // ── ④ 上传归因：expectFileChooser 读 chooser.element()
  console.log(`\n═══ ④ 上传归因 ═══`);
  const upItems = [];
  const b4 = await fingerprint(page);
  await clickAria('创建', 2000);
  const a4 = await fingerprint(page);
  for (const f of diffPanels(b4, a4)) {
    const item = f.buttons.filter((t) => /上传/.test(t));
    if (item.length) upItems.push(...item);
  }
  console.log(`  「创建」下拉里的上传项：${JSON.stringify(upItems)}`);
  out.uploadItems = upItems;
  let accept = null;
  for (const item of [...new Set(upItems)]) {
    const p = await page.evaluate((t) => {
      for (const e of document.querySelectorAll('div,button,li,span')) {
        if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 20 || r.height < 10) continue;
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; } return null; }, item);
    if (!p) { console.log(`  「${item}」这轮找不到坐标`); continue; }
    const fc = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 5000 }).catch(() => null),
      page.mouse.click(p[0], p[1]),
    ]).then((r) => r[0]);
    if (!fc) { console.log(`  点「${item}」→ filechooser 没弹`); out[`fc_${item}`] = { fired: false }; continue; }
    const el = fc.element();
    accept = { item, accept: await el.getAttribute('accept'), multiple: await el.getAttribute('multiple'),
      outer: (await el.evaluate((e) => e.outerHTML)).slice(0, 260) };
    out[`fc_${item}`] = accept;
    console.log(`  ⭐ 点「${item}」→ filechooser 弹了，accept=${JSON.stringify(accept.accept)} multiple=${JSON.stringify(accept.multiple)}`);
    await esc();
  }
  out.uploadAccept = accept;
  if (!accept) console.log(`  ⛔ 没归因到任何 accept（本轮无法确认「上传资产」支持哪些格式）`);
  await closeAll(probe);

  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  const gEnd = await assertClosed({ probe });
  out.final = { nodes: finalN, guard: gEnd };
  console.log(`\n═══ 收尾：视口内节点 ${finalN}，守卫 closed=${gEnd.closed}（本轮零写操作）═══`);

  await logStep(B, {
    id: 'BP2c-asset-modal-guard',
    title: '⭐「更多操作」开的是全屏「资产管理」弹窗；Escape 关不掉它，BP2b 后三轮判据全污染',
    target: 'M-254 证明「更多操作」打开的不是菜单而是整个「资产管理」弹窗。'
      + '但 BP2b 每轮点完只按 Escape 就继续下一轮，而**Escape 并不能关掉这个弹窗** —— '
      + '于是「创建」那轮报的 `新增浮层=0` 不是「没反应」，是基线里已经有了。'
      + '本轮立 `assertClosed()`：① 全屏 Modal 容器数 ② 标题「资产管理」是否还在 DOM '
      + '③ **elementFromPoint 打不打得中抽屉的「创建」按钮**（阳性对照），'
      + '每个探测前后各自证一次；同时读透弹窗（侧栏 / 标签页 / 按钮），'
      + '并用 expectFileChooser 归因「上传资产」的 accept。⛔ 不建主体、不传文件、不删不改。',
    evidence: out,
    visible_text: JSON.stringify({
      守卫自检: out.guard0, 抽屉: out.drawer,
      点管理后的新增浮层: out.manageClick?.fresh, 点管理后守卫: out.afterManageGuard,
      弹窗全文: out.modal?.text, 弹窗侧栏: out.modal?.side, 弹窗标签: out.modal?.tabs,
      关闭尝试: out.close1?.map((c) => ({ how: c.how, closed: c.closed })),
      单按Escape能否关闭: out.escapeAloneWorks,
      创建下拉_干净态: out.createClean?.fresh, 创建下拉里的上传项: out.uploadItems,
      上传归因: out.uploadAccept, 收尾: out.final }).slice(0, 3200),
    shot: 'M-255-资产管理弹窗-从管理进入.png',
  });
  console.log('\nBP2c 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

// Batch BP2g — ⛔ 先查账户，再重做被 Escape 打断的三件事。
//
// ⚠️ BP2f 结尾的复核读到「待分类资产」在可见 DOM 里出现 0 次。
//    两种可能，**必须分开**：① Escape 把**整个抽屉**关了（东西还在，只是没显示）
//                        ② 那个分类真被删了。
//    判据：重新打开抽屉再数一次 —— 「可见 DOM 出现次数」和「重新打开后还在不在」不是一回事。
//    ⇒ 这正是「判显隐要读把它设成 0 的那个祖先」的另一种用法：**别拿「当前看不见」当「不存在」。**
//
// ⭐ BP2f 后半段全废的根因：`esc()` 不只关菜单，**它把抽屉也关了** —— 于是 ④「创建」
//   和 ⑤「可灵主体库」都 executed=false。⇒ 本轮加 `enterDrawer()`：**每一步之前都确认抽屉开着**，
//   不开着就重新开，并把这层自证写进证据里。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBP2g';
const { browser, page } = await launch();

const visIn = (e) => { const r = e.getBoundingClientRect();
  return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
const clickAria = async (label, wait = 2200) => {
  const p = await page.evaluate((l) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .find((x) => x.getAttribute('aria-label') === l && x.getBoundingClientRect().width >= 4
        && x.getBoundingClientRect().height >= 4);
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, label);
  if (!p) return { executed: false, note: `找不到可见的 aria-label=${label}` };
  await page.mouse.click(p[0], p[1]); await page.waitForTimeout(wait);
  return { executed: true, at: p };
};
const cands = (txt, minW = 6) => page.evaluate(([t, mw]) => {
  const out = []; const seen = new Set();
  for (const e of document.querySelectorAll('div,button,span,li,a')) {
    if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
    const r = e.getBoundingClientRect();
    if (r.width < mw || r.height < 6) continue;
    if (getComputedStyle(e).visibility === 'hidden') continue;
    const k = `${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)}`;
    if (seen.has(k)) continue; seen.add(k);
    out.push({ at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], tag: e.tagName }); }
  return out; }, [txt, minW]);
const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1400); };

/** ⭐ 抽屉开没开：判据 = 「共 N 节点」这行字在可见 DOM 里（它在抽屉底部，抽屉关了就看不见）。 */
const drawerOpen = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const foot = [...document.querySelectorAll('div,span')].filter((e) => vis(e)
    && /^共 \d+ 节点$/.test((e.innerText || '').trim())).length;
  const assetName = [...document.querySelectorAll('div,span')]
    .filter((e) => vis(e) && (e.innerText || '').trim() === '待分类资产').length;
  return { drawerOpen: foot > 0, footCount: foot, assetNameVisible: assetName };
});
/** 每一步之前都确认抽屉开着；没开就重开，并记录这层自证。 */
const enterDrawer = async (log) => {
  let d = await drawerOpen();
  if (!d.drawerOpen) {
    await clickAria('资产管理', 2600);
    d = await drawerOpen();
    log?.push({ reopened: true, ...d });
  } else log?.push({ reopened: false, ...d });
  return d;
};
/** 打开资产行菜单（点 •••），并**验证 8 项同时可见**才算开成。 */
const openRowMenu = async () => {
  const more = await clickAria('更多操作', 1800);
  const want = ['添加到Agent', '添加到画布', '更改图标', '新建子文件夹', '移动到', '下载', '重命名', '删除'];
  const seen = await page.evaluate((w) => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    return w.filter((t) => [...document.querySelectorAll('div,span,button,li')]
      .some((e) => (e.innerText || '').replace(/\s+/g, ' ').trim() === t && vis(e)
        && e.getBoundingClientRect().height < 60)); }, want);
  const pts = await page.evaluate((w) => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    const o = {};
    for (const t of w) {
      const e = [...document.querySelectorAll('div,span')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === t && vis(x)
        && x.getBoundingClientRect().height < 60);
      if (!e) { o[t] = null; continue; }
      let row = e; for (let i = 0; i < 4 && row.parentElement; i++) { row = row.parentElement;
        const r = row.getBoundingClientRect(); if (r.height > 26 && r.height < 56 && r.width > 100 && r.width < 320) break; }
      const r = row.getBoundingClientRect();
      o[t] = { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }
    return o; }, want);
  return { click: more, seen, allSeen: seen.length === want.length, pts };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '⛔ 先查分类是否还在；enterDrawer 每步自证；删除只读确认框' });
  const out = {};

  // ── ① ⛔ 账户状态复核
  console.log(`═══ ① 账户状态复核（关着抽屉时） ═══\n  ${JSON.stringify(await drawerOpen())}`);
  const trace = [];
  await clickAria('资产管理', 2800);
  await clickAria('资产', 2000);
  const t0 = await cands('资产', 20);
  if (t0[0]) { await page.mouse.click(t0[0].at[0], t0[0].at[1]); await page.waitForTimeout(2400); }
  const st = await drawerOpen(); out.account = st; out.trace = trace;
  console.log(`  进「资产」页后：${JSON.stringify(st)}`);
  const drawerText = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const d = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
      return vis(e) && r.x < 40 && r.width > 250 && r.width < 380 && r.height > 300; })
      .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
    return (d?.innerText || '').replace(/\s+/g, ' ').trim(); });
  out.drawerText = drawerText;
  console.log(`  ⭐⭐ 抽屉全文：${JSON.stringify(drawerText)}`);
  console.log(`  ⭐⭐ 结论：分类${st.assetNameVisible > 0 ? '**还在** ✅（BP2f 那次是抽屉被 Escape 关了）' : '**不见了** ⛔ 需要处理'}`);
  await shot(page, 'M-265-资产页-账户状态复核.png');

  // ── ② 删除确认框：只读，⛔ 取消后必须复核分类还在
  console.log(`\n═══ ② 「删除」的确认框 ═══`);
  const mm = await openRowMenu(); out.menu = { seen: mm.seen, allSeen: mm.allSeen };
  console.log(`  菜单打开：allSeen=${mm.allSeen}｜可见 ${mm.seen.length}/8：${JSON.stringify(mm.seen)}`);
  console.log(`  「删除」坐标：${JSON.stringify(mm.pts['删除'])}`);
  if (mm.pts['删除']) {
    const base = await fingerprint(page);
    await page.mouse.click(mm.pts['删除'].at[0], mm.pts['删除'].at[1]);
    await page.waitForTimeout(2200);
    const dlg = await page.evaluate(() => {
      const vis = (e) => { const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
      const cs = [...document.querySelectorAll('div,section')].filter(vis)
        .map((e) => { const r = e.getBoundingClientRect();
          return { e, r, t: (e.innerText || '').replace(/\s+/g, ' ').trim() }; })
        .filter((x) => /删除|该文件夹|无法|确认/.test(x.t) && x.t.length < 240 && x.r.width > 220 && x.r.height > 80)
        .sort((a, b) => a.t.length - b.t.length);
      const best = cs[0];
      if (!best) return { found: false, tried: cs.length };
      return { found: true, text: best.t.slice(0, 220),
        rect: [Math.round(best.r.x), Math.round(best.r.y), Math.round(best.r.width), Math.round(best.r.height)],
        buttons: [...best.e.querySelectorAll('button,[role="button"]')].filter(vis).map((e) => {
          const r = e.getBoundingClientRect();
          return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), aria: e.getAttribute('aria-label'),
            at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
            color: getComputedStyle(e).color, bg: getComputedStyle(e).backgroundColor }; }) }; });
    const fresh = diffPanels(base, await fingerprint(page)).slice(0, 3)
      .map((p) => ({ area: p.area, all: p.all.slice(0, 220), buttons: p.buttons.slice(0, 10) }));
    out.deleteDialog = { ...dlg, fresh };
    console.log(`  确认框 found=${dlg.found}：${JSON.stringify(dlg.text)}`);
    console.log(`  框内按钮：${JSON.stringify(dlg.buttons)}`);
    if (!dlg.found) fresh.forEach((f, i) => console.log(`   浮层${i + 1} area=${f.area} ${JSON.stringify(f.all)} 按钮=${JSON.stringify(f.buttons)}`));
    if (dlg.found) await shot(page, 'M-262-删除文件夹-确认框.png');
    const cancel = (dlg.buttons || []).find((b) => /取消/.test(b.t || ''));
    if (cancel) { await page.mouse.click(cancel.at[0], cancel.at[1]); out.cancelClicked = cancel; console.log(`  ⛔ 已点「取消」@${JSON.stringify(cancel.at)}`); }
    else { await esc(); console.log('  ⛔ 没有「取消」→ Escape'); }
    await page.waitForTimeout(1400);
    const after = await enterDrawer(out.trace);
    const afterText = await page.evaluate(() => {
      const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      const d = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
        return vis(e) && r.x < 40 && r.width > 250 && r.width < 380 && r.height > 300; })
        .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
      return (d?.innerText || '').replace(/\s+/g, ' ').trim(); });
    out.afterCancel = { state: after, text: afterText };
    console.log(`  ⭐ 取消后复核：${JSON.stringify(after)}｜抽屉=${JSON.stringify(afterText)}`);
    console.log(`  ⭐⭐ 分类还在吗？ ${after.assetNameVisible > 0 ? '✅ 还在（删除已被取消）' : '⛔ 不在了'}`);
    if (after.drawerOpen) await shot(page, 'M-266-取消删除之后.png');
  }

  // ── ③ 上传归因（每步先确认抽屉开着）
  console.log(`\n═══ ③ 「上传资产」归因 ═══`);
  await enterDrawer(out.trace);
  await page.evaluate(() => { window.__fc = [];
    document.addEventListener('click', (e) => { const t = e.target;
      if (t && t.tagName === 'INPUT' && t.type === 'file') window.__fc.push({ accept: t.getAttribute('accept'), multiple: t.getAttribute('multiple') }); }, true); });
  const cr = await clickAria('创建', 2200);
  const ups = await cands('上传资产', 30);
  console.log(`  「创建」executed=${cr.executed}｜「上传资产」候选 ${ups.length} 个`);
  const tries = [];
  for (const [i, u] of ups.entries()) {
    if (i > 0) { await enterDrawer(out.trace); await clickAria('创建', 2000); }
    const base = await fingerprint(page);
    const fcP = page.waitForEvent('filechooser', { timeout: 4500 }).catch(() => null);
    await page.mouse.click(u.at[0], u.at[1]);
    const fc = await fcP; await page.waitForTimeout(1600);
    const hits = await page.evaluate(() => window.__fc);
    const fresh = diffPanels(base, await fingerprint(page)).slice(0, 3)
      .map((p) => ({ area: p.area, all: p.all.slice(0, 200), buttons: p.buttons.slice(0, 10) }));
    const t = { idx: i, at: u.at, rect: u.rect, chooserFired: !!fc, clickHits: hits, fresh };
    if (fc) { t.accept = await fc.element().getAttribute('accept'); t.multiple = await fc.element().getAttribute('multiple'); }
    tries.push(t);
    console.log(`  候选${i + 1} @${JSON.stringify(u.at)} rect=${JSON.stringify(u.rect)} → chooser=${t.chooserFired ? '✅' : '❌'} fileInput点击=${hits.length} 新增浮层=${fresh.length}`);
    if (t.accept) console.log(`     ⭐⭐ accept=${JSON.stringify(t.accept)} multiple=${JSON.stringify(t.multiple)}`);
    if (hits.length) console.log(`     ⭐ fileInput accept=${JSON.stringify(hits[0].accept)} multiple=${JSON.stringify(hits[0].multiple)}`);
    fresh.forEach((f, k) => console.log(`     浮层${k + 1} area=${f.area} ${JSON.stringify(f.all)} 按钮=${JSON.stringify(f.buttons)}`));
    if (i === 0) { await shot(page, 'M-263-点上传资产之后.png'); t.shot = 'M-263-点上传资产之后.png'; }
    await esc();
  }
  out.uploadTries = tries;
  const hit = tries.find((t) => t.accept || (t.clickHits || []).length);
  out.uploadAccept = hit ? { accept: hit.accept ?? hit.clickHits[0].accept, multiple: hit.multiple ?? hit.clickHits[0].multiple, viaIdx: hit.idx } : null;
  console.log(`  ⭐⭐ 上传归因：${JSON.stringify(out.uploadAccept)}`);

  // ── ④ 可灵主体库标签筛选
  console.log(`\n═══ ④ 可灵主体库标签 ═══`);
  await enterDrawer(out.trace);
  const mg = await clickAria('资产管理', 2600);
  console.log(`  点「管理」executed=${mg.executed}`);
  const bodyOf = () => page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const t = [...document.querySelectorAll('div,h1,h2,span')].find((e) => (e.innerText || '').trim() === '资产管理' && vis(e));
    if (!t) return null;
    let root = t; for (let i = 0; i < 8 && root.parentElement; i++) { root = root.parentElement;
      const r = root.getBoundingClientRect(); if (r.width > 500 && r.height > 350) break; }
    const rr = root.getBoundingClientRect();
    return { text: (root.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
      tabs: [...root.querySelectorAll('div,button,li,span')].filter((e) => { const r = e.getBoundingClientRect();
          return vis(e) && e.children.length === 0 && r.height >= 24 && r.height <= 44 && r.width >= 28 && r.width <= 120
            && r.y > rr.y + 40 && r.y < rr.y + 210; })
        .map((e) => ({ t: (e.innerText || '').trim(), bg: getComputedStyle(e).backgroundColor,
          at: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; })() }))
        .filter((x) => x.t).filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.at[1] === v.at[1]) === i) }; });
  const lib = await clickText2('可灵主体库');
  const b0 = await bodyOf();
  console.log(`  点「可灵主体库」executed=${lib.executed}`);
  console.log(`  正文：${b0?.text}`);
  console.log(`  标签行：${JSON.stringify(b0?.tabs)}`);
  out.kling = { click: lib, body0: b0 };
  if (b0?.tabs?.length) {
    const probes = [];
    for (const t of b0.tabs) {
      await page.mouse.click(t.at[0], t.at[1]); await page.waitForTimeout(1800);
      const b = await bodyOf();
      probes.push({ tab: t.t, bg: t.bg, body: b?.text });
      console.log(`   【${t.t}】→ ${JSON.stringify(b?.text?.slice(0, 120))}`);
    }
    out.klingTabs = probes;
    const sigs = [...new Set(probes.map((p) => p.body))];
    out.klingTabDistinguish = sigs.length;
    console.log(`  ⭐ ${probes.length} 个标签给出 ${sigs.length} 种正文 ${sigs.length > 1 ? '✅ 各不相同 → 确实在筛' : '❌ 全一样'}`);
    await shot(page, 'M-264-可灵主体库-标签筛选.png');
  }

  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.final = { nodes: finalN };
  console.log(`\n═══ 收尾：节点 ${finalN}；本轮未确认任何删除、未传文件 ═══`);

  async function clickText2(t) { const c = await cands(t, 40);
    if (!c[0]) return { executed: false, note: `找不到「${t}」` };
    await page.mouse.click(c[0].at[0], c[0].at[1]); await page.waitForTimeout(2200);
    return { executed: true, at: c[0].at }; }

  await logStep(B, {
    id: 'BP2g-account-state-and-delete-dialog',
    title: '⛔ 复核分类是否还在 + 删除确认框 + 上传归因 + 可灵主体库标签',
    target: 'BP2f 结尾复核读到「待分类资产」在可见 DOM 里出现 0 次，但**「当前看不见」不等于「不存在」** —— '
      + 'Escape 会把**整个抽屉**一起关掉（BP2f ④⑤ 全部 executed=false 就是这个原因）。'
      + '本轮：① 先重开抽屉数一次，分清「被删了」和「被关掉了」；'
      + '② 加 `enterDrawer()`，每一步之前都确认抽屉开着，把这层自证写进证据；'
      + '③ 打开行菜单（**验证 8 项同时可见**才算开成）后点「删除」，只读确认框文案再取消，并复核分类还在；'
      + '④ 上传归因；⑤ 可灵主体库标签筛选用「正文是否随标签变」做判别式。'
      + '⛔ 不确认删除、不传文件、不建主体、不改名。',
    evidence: out,
    visible_text: JSON.stringify({
      账户复核: out.account, 抽屉全文: out.drawerText,
      抽屉自证轨迹: out.trace, 菜单可见项: out.menu?.seen, 菜单全开: out.menu?.allSeen,
      删除确认框: out.deleteDialog?.text, 框内按钮: out.deleteDialog?.buttons,
      新增浮层: out.deleteDialog?.fresh?.map((f) => f.all),
      点了取消: out.cancelClicked?.t, 取消后: out.afterCancel,
      上传尝试: out.uploadTries?.map((t) => ({ idx: t.idx, at: t.at, chooser: t.chooserFired, hits: t.clickHits, fresh: t.fresh?.map((f) => f.all) })),
      上传归因: out.uploadAccept,
      可灵主体库正文: out.kling?.body0?.text, 标签行: out.kling?.body0?.tabs,
      各标签正文: out.klingTabs?.map((p) => `${p.tab}:${p.body?.slice(0, 80)}`),
      标签正文不同值数: out.klingTabDistinguish, 收尾: out.final }).slice(0, 3600),
    shot: 'M-265-资产页-账户状态复核.png',
  });
  console.log('\nBP2g 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

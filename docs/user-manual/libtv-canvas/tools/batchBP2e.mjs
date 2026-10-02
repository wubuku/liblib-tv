// Batch BP2e — 「管理」与「更多操作」是不是同一个弹窗？落点一样吗？里面有什么可点的？
//
// 守卫修正（第三次）：`[class*="Modal-root"]` 会命中 `mantine-Drawer-content` 的祖先链，
// 于是抽屉自己被判成「没关掉的弹窗」。**结论：放弃「数弹窗容器」，只用 `titleCount`**
// —— 标题「资产管理」是弹窗独有的锚点，抽屉里没有这个字；它归零 = 弹窗没了。
// 「assetNameCount」同样归零 = 连它带出来的资产数据也卸载了。两条互相独立。
//
// M-255 已确证弹窗结构：
//   资产管理 │ 侧栏〔个人资产库 ✓选中〕〔可灵主体库〕 │ 主区〔个人资产库〕 🔍 ⚟ ≡ 〔+ 新建〕
//             │ 内容：📁 待分类资产 / 2026-10-02
//   而 M-254 里从行上「更多操作」进来，**选中的是「可灵主体库」** —— ⚠️ 两条路由落点可能不同，
//   本轮用 bg 色判定「哪一项被选中」，而不是靠肉眼。
//
// ⛔ 本轮只读：不建文件夹、不传文件、不建主体、不删不改名、不上传。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBP2e';
const { browser, page } = await launch();

const clickAria = async (label, wait = 2400) => {
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
/** 点一个「同名多候选」里第 idx 个的点，逐个候选都能单独指名，不猜。 */
const clickTextNth = async (txt, idx = 0, wait = 2200, minW = 0) => {
  const cands = await page.evaluate(([t, mw]) => {
    const out = []; const seen = new Set();
    for (const e of document.querySelectorAll('div,button,span,li,a')) {
      if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 6 || r.height < 6 || r.width < mw) continue;
      const k = `${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)}`;
      if (seen.has(k)) continue; seen.add(k);
      out.push({ at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        tag: e.tagName, kids: e.children.length }); }
    return out; }, [txt, minW]);
  if (!cands[idx]) return { executed: false, note: `「${txt}」没有第 ${idx + 1} 个候选（共 ${cands.length}）` };
  await page.mouse.click(cands[idx].at[0], cands[idx].at[1]); await page.waitForTimeout(wait);
  return { executed: true, at: cands[idx].at, rect: cands[idx].rect, candCount: cands.length };
};

/** ⭐ 修好的守卫：只看两个**互不相关**的锚点是否归零。 */
const guard = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const cnt = (t) => [...document.querySelectorAll('div,h1,h2,span')]
    .filter((e) => (e.innerText || '').trim() === t && vis(e)).length;
  return { titleCount: cnt('资产管理'), assetNameCount: cnt('待分类资产'),
    modalOpen: cnt('资产管理') > 0 };
});
const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1500); };

/** ⭐ 从标题锚点读弹窗 + 判哪一项侧栏被选中（读 bg，不用肉眼）。 */
const readModal = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const title = [...document.querySelectorAll('div,h1,h2,span')]
    .find((e) => (e.innerText || '').trim() === '资产管理' && vis(e));
  if (!title) return { found: false };
  let root = title;
  for (let i = 0; i < 8 && root.parentElement; i++) { root = root.parentElement;
    const r = root.getBoundingClientRect(); if (r.width > 500 && r.height > 350) break; }
  const rr = root.getBoundingClientRect();
  const at = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; };
  const dedup = (a) => a.filter((v, i, x) => x.findIndex((y) => y.t === v.t && y.at[0] === v.at[0] && y.at[1] === v.at[1]) === i);
  const leaves = (pred) => dedup([...root.querySelectorAll('div,button,li,span')].filter(vis)
    .map((e) => ({ e, r: e.getBoundingClientRect() })).filter(({ e, r }) => r.width >= 4 && r.height >= 4 && pred(r, e))
    .map(({ e }) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
      at: at(e), kids: e.children.length,
      bg: getComputedStyle(e).backgroundColor,
      aria: e.getAttribute('aria-label') })).filter((x) => x.t || x.aria));
  return { found: true, rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
    text: (root.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
    side: leaves((r, e) => r.x < rr.x + 40 && r.width > 70 && r.height >= 24 && r.height <= 56 && e.children.length <= 3),
    tabRow: leaves((r, e) => r.x > rr.x + 340 && r.y > rr.y + 40 && r.y < rr.y + 210
      && r.height >= 24 && r.height <= 44 && r.width >= 28 && r.width <= 120 && e.children.length === 0),
    buttons: [...root.querySelectorAll('button,[role="button"]')].filter(vis)
      .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
        aria: e.getAttribute('aria-label'), at: at(e) })),
  };
});
/** 被选中的侧栏项 = 背景色不是透明的。 */
const picked = (side) => (side || []).filter((s) => s.bg && !/rgba\(0, 0, 0, 0\)|transparent/.test(s.bg))
  .map((s) => `${s.t}(bg=${s.bg})`);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '两条路由开同一个弹窗？落点一样吗？hover 有没有删除入口？' });
  const out = {};

  await clickAria('资产管理', 2800);
  await clickTextNth('资产', 0, 2600, 20);
  const g0 = await guard(); out.guard0 = g0;
  console.log(`═══ 守卫自检 ═══ modalOpen=${g0.modalOpen} titleCount=${g0.titleCount} assetNameCount=${g0.assetNameCount}`);
  console.log(`  ${g0.titleCount === 0 && g0.assetNameCount === 0 ? '✅ 守卫干净（两个锚点都归零）' : '⛔ 守卫不可信'}`);

  // ── ① 路由 A：抽屉头部「管理」
  const rA = await clickAria('资产管理', 2600);
  const gA = await guard(); const mA = await readModal(); out.routeA = { click: rA, guard: gA, modal: mA };
  console.log(`\n═══ ① 路由 A：点头部「管理」 ═══\n  executed=${rA.executed}｜modalOpen=${gA.modalOpen}`);
  if (mA.found) {
    console.log(`  弹窗 rect=${JSON.stringify(mA.rect)} 全文：${mA.text}`);
    console.log(`  侧栏：${JSON.stringify(mA.side)}`);
    console.log(`  ⭐ 选中的侧栏项：${JSON.stringify(picked(mA.side))}`);
    console.log(`  顶部标签行：${JSON.stringify(mA.tabRow)}`);
    console.log(`  按钮：${JSON.stringify(mA.buttons)}`);
  } else console.log('  ⛔ 弹窗没开');
  await shot(page, 'M-255-资产管理弹窗-从管理进入.png');
  await esc();
  const gA2 = await guard(); console.log(`  Escape 后：modalOpen=${gA2.modalOpen} titleCount=${gA2.titleCount} assetNameCount=${gA2.assetNameCount}`);
  out.routeA.afterEscape = gA2;
  out.escapeClosesModal = gA2.modalOpen === false;

  // ── ② 路由 B：行上的「更多操作」
  const rB = await clickAria('更多操作', 2600);
  const gB = await guard(); const mB = await readModal(); out.routeB = { click: rB, guard: gB, modal: mB };
  console.log(`\n═══ ② 路由 B：点行上「更多操作」 ═══\n  executed=${rB.executed}｜modalOpen=${gB.modalOpen}`);
  if (mB.found) {
    console.log(`  弹窗 rect=${JSON.stringify(mB.rect)} 全文：${mB.text}`);
    console.log(`  侧栏：${JSON.stringify(mB.side)}`);
    console.log(`  ⭐ 选中的侧栏项：${JSON.stringify(picked(mB.side))}`);
    console.log(`  顶部标签行：${JSON.stringify(mB.tabRow)}`);
  } else console.log('  ⛔ 弹窗没开');
  await shot(page, 'M-258-资产管理弹窗-从更多操作进入.png');
  out.sameModal = mA.found && mB.found && JSON.stringify(mA.rect) === JSON.stringify(mB.rect);
  out.sameLanding = JSON.stringify(picked(mA.side)) === JSON.stringify(picked(mB.side));
  console.log(`\n  ⭐⭐ 两条路由开的是同一个弹窗吗？ ${out.sameModal ? '✅ 是' : '❌ 否'}（rect 逐字比对）`);
  console.log(`  ⭐⭐ 两条路由落点相同吗？ ${out.sameLanding ? '✅ 相同 → ' + JSON.stringify(picked(mB.side)) : '❌ 不同'}`);

  // ── ③ ⭐ hover「待分类资产」卡片：找删除 / 重命名入口
  console.log(`\n═══ ③ hover「待分类资产」卡片 ═══`);
  const card = await page.evaluate(() => {
    for (const e of document.querySelectorAll('div,span')) {
      if ((e.innerText || '').trim() !== '待分类资产') continue;
      const r = e.getBoundingClientRect();
      if (r.width < 10 || r.height < 8) continue;
      let n = e; for (let i = 0; i < 5 && n.parentElement; i++) {
        n = n.parentElement; const rr = n.getBoundingClientRect();
        if (rr.width > 120 && rr.height > 100) break; }
      const rr = n.getBoundingClientRect();
      return { at: [Math.round(rr.x + rr.width / 2), Math.round(rr.y + rr.height / 2)],
        rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)] }; }
    return null; });
  console.log(`  卡片：${JSON.stringify(card)}`);
  const hover = { before: null, after: null, shot: null };
  if (card) {
    await page.mouse.move(card.at[0], card.at[1]); await page.waitForTimeout(1400);
    hover.before = await page.evaluate((c) => {
      const el = document.elementFromPoint(c[0], c[1]);
      let n = el; for (let i = 0; i < 6 && n; i++, n = n.parentElement) {
        if (n.getBoundingClientRect().width > 120 && n.getBoundingClientRect().height > 100) {
          return [...n.querySelectorAll('button,[role="button"],[aria-label]')]
            .filter((b) => { const r = b.getBoundingClientRect(); return r.width > 2 && r.height > 2; })
            .map((b) => ({ t: (b.innerText || '').trim().slice(0, 12), aria: b.getAttribute('aria-label'),
              op: getComputedStyle(b).opacity,
              at: (() => { const r = b.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; })() })); } }
      return null; }, card.at);
    await shot(page, 'M-259-待分类资产卡片-hover.png');
    hover.shot = 'M-259-待分类资产卡片-hover.png';
    console.log(`  hover 后卡片内的可交互件：${JSON.stringify(hover.before)}`);
    out.hover = hover;
  }

  // ── ④ 弹窗工具条四个按钮各开什么
  console.log(`\n═══ ④ 弹窗工具条 ═══`);
  const bar = [];
  for (const label of ['新建', '搜索', '批量操作', '筛选']) {
    const base = await fingerprint(page);
    const r = await clickAria(label, 2200);
    const after = await fingerprint(page);
    const fresh = diffPanels(base, after).slice(0, 3).map((p) => ({ area: p.area, all: p.all.slice(0, 160), buttons: p.buttons.slice(0, 12) }));
    bar.push({ label, ...r, fresh });
    console.log(`  【${label}】executed=${r.executed}${r.note ? '（' + r.note + '）' : ''} → 新增浮层 ${fresh.length}：${JSON.stringify(fresh.map((f) => f.all))}`);
    if (label === '新建' && fresh.length) await shot(page, 'M-260-资产管理弹窗-新建下拉.png');
    await esc();
  }
  out.toolbar = bar;
  console.log(`  ⭐ 哪个没反应？ ${JSON.stringify(bar.filter((b) => !b.executed || !b.fresh.length).map((b) => b.label))}`);

  // ── ⑤ ⭐ 全弹窗搜「删除 / 重命名 / 移除」字样
  const danger = await page.evaluate(() => {
    const body = document.body.innerText || '';
    return { 删除: (body.match(/删除/g) || []).length, 重命名: (body.match(/重命名/g) || []).length,
      移除: (body.match(/移除/g) || []).length, 移动: (body.match(/移动到|移到/g) || []).length }; });
  out.dangerWords = danger;
  console.log(`\n═══ ⑤ 全页危险词出现次数 ═══ ${JSON.stringify(danger)}`);

  const gEnd = await guard();
  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.final = { nodes: finalN, guard: gEnd };
  console.log(`\n═══ 收尾：节点 ${finalN}，modalOpen=${gEnd.modalOpen}（本轮零写操作）═══`);

  await logStep(B, {
    id: 'BP2e-two-routes-into-asset-modal',
    title: '⭐「管理」和「更多操作」开的是同一个弹窗，但落点可能不同；卡片 hover 无删除入口',
    target: 'M-255 与 M-254 两张截图看起来是同一个「资产管理」弹窗，但**选中的侧栏项不一样**：'
      + '从「管理」进来选中「个人资产库」，从「更多操作」进来看着像「可灵主体库」。'
      + '本轮不用肉眼，改成读 `backgroundColor` 判「哪一项被选中」，并逐字比对两条路由的弹窗 rect，'
      + '回答「是不是同一个弹窗、落点是否相同」；同时 hover「待分类资产」卡片找删除/重命名入口，'
      + '并点名弹窗工具条的 搜索 / 批量操作 / 筛选 / 新建。'
      + '守卫第三次修正：**放弃数弹窗容器**（`[class*=Modal-root]` 会命中 `mantine-Drawer-content` 的祖先链），'
      + '只用两个互不相关的锚点 —— 标题「资产管理」和资产名「待分类资产」—— 是否同时归零。'
      + '⛔ 不建文件夹、不传文件、不建主体、不删不改名。',
    evidence: out,
    visible_text: JSON.stringify({
      守卫自检: out.guard0,
      路由A管理: { executed: out.routeA?.click?.executed, modalOpen: out.routeA?.guard?.modalOpen,
        全文: out.routeA?.modal?.text, 侧栏: out.routeA?.modal?.side,
        选中: picked(out.routeA?.modal?.side), 顶部标签行: out.routeA?.modal?.tabRow },
      Escape后: out.routeA?.afterEscape, Escape能关弹窗: out.escapeClosesModal,
      路由B更多操作: { executed: out.routeB?.click?.executed, modalOpen: out.routeB?.guard?.modalOpen,
        全文: out.routeB?.modal?.text, 侧栏: out.routeB?.modal?.side,
        选中: picked(out.routeB?.modal?.side) },
      同一个弹窗: out.sameModal, 落点相同: out.sameLanding,
      hover卡片内可交互件: out.hover?.before,
      工具条: out.toolbar?.map((b) => `${b.label}:${b.executed ? '执行' : '没找到'}/浮层${b.fresh.length}${b.fresh.length ? JSON.stringify(b.fresh[0].all) : ''}`),
      危险词: out.dangerWords, 收尾: out.final }).slice(0, 3600),
    shot: 'M-258-资产管理弹窗-从更多操作进入.png',
  });
  console.log('\nBP2e 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

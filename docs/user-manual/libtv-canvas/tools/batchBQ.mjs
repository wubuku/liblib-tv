// Batch BQ — 把资产页剩下的 📖 一次扫干净。
//
// BP 留下的 📖 一共五个，本轮逐个点名：
//   ① 「请选择文件夹」下拉列什么        —— 读选项文本
//   ② 「请选择标签」下拉列什么          —— 读选项文本
//   ③ 「可灵主体库」六个标签到底筛不筛   —— 判别式改成**点完回读每个标签自己的 backgroundColor**，
//                                          看选中态有没有转移（BP2g 用的「正文变没变」在空库上失效）
//   ④ 「创建主体」点开是什么表单        —— 只读，不提交
//   ⑤ 「批量操作」勾选模式能勾什么      —— 有分类了，至少能看清勾选态长什么样
//
// ⭐ BP 留下的三条硬纪律，本轮继续用：
//   · `enterDrawer()` **验 → 没开就重试 → 再验**，前置不成立就**响亮地抛**，别让后面静默空转；
//   · 进抽屉后**必须显式切到「资产」标签页**（BP2h 忘了这步，后面全废）；
//   · 判「是否全部满足」之前**先确认集合非空**（BP2h 的 `0/0 ✅` 是空集恒真的教训）。
//
// ⛔ 本轮只读：不传文件、不提交表单、不建主体、不新建文件夹、不新建标签、不删除。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBQ';
const { browser, page } = await launch();

/** ⭐ 同名 aria 全部枚举，按 preferX 挑（BP2i 的教训：`.find()` 取到的是底栏那个）。 */
const findAria = (label) => page.evaluate((l) => [...document.querySelectorAll('button,[role="button"],[aria-label]')]
  .filter((x) => x.getAttribute('aria-label') === l)
  .map((x) => { const r = x.getBoundingClientRect();
    return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      visible: r.width >= 4 && r.height >= 4 }; }), label);
const clickAria = async (label, wait = 2200, preferX = null) => {
  const vis = (await findAria(label)).filter((a) => a.visible);
  if (!vis.length) return { executed: false, note: `找不到可见的 aria-label=${label}` };
  const pick = preferX == null ? vis[0] : (vis.find((a) => a.at[0] < preferX) || vis[0]);
  await page.mouse.click(pick.at[0], pick.at[1]); await page.waitForTimeout(wait);
  return { executed: true, at: pick.at, hits: vis.length };
};
const cands = (txt, minW = 6) => page.evaluate(([t, mw]) => {
  const out = []; const seen = new Set();
  for (const e of document.querySelectorAll('div,button,span,li,a')) {
    if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== t) continue;
    const r = e.getBoundingClientRect();
    if (r.width < mw || r.height < 6 || getComputedStyle(e).visibility === 'hidden') continue;
    const k = `${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)}`;
    if (seen.has(k)) continue; seen.add(k);
    out.push({ at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }); }
  return out; }, [txt, minW]);
const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1400); };

const drawerOpen = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  return { open: [...document.querySelectorAll('div,span')].filter((e) => vis(e)
    && /^共 \d+ 节点$/.test((e.innerText || '').trim())).length > 0,
    assetName: [...document.querySelectorAll('div,span')].filter((e) => vis(e)
      && (e.innerText || '').trim() === '待分类资产').length }; });
const drawerText = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const d = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
      return vis(e) && r.x < 40 && r.width > 250 && r.width < 380 && r.height > 300; })
    .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
  return (d?.innerText || '').replace(/\s+/g, ' ').trim(); });
const trace = [];
const enterDrawer = async () => {
  for (let i = 0; i < 3; i += 1) {
    const d = await drawerOpen();
    if (d.open) { trace.push({ round: i + 1, ok: true, ...d }); return { ok: true }; }
    await clickAria('资产管理', 2600, 40);
    trace.push({ round: i + 1, ok: false, ...d });
  }
  return { ok: false };
};
/** 进抽屉 + **显式切到「资产」页** + 复核。 */
const onAssetPage = async () => {
  const d = await enterDrawer();
  if (!d.ok) return { ok: false, why: '抽屉没打开' };
  const tab = await cands('资产', 20);
  if (!tab[0]) return { ok: false, why: '抽屉里找不到「资产」标签' };
  await page.mouse.click(tab[0].at[0], tab[0].at[1]); await page.waitForTimeout(2400);
  const txt = await drawerText();
  return { ok: /资产/.test(txt) && /待分类资产|暂无资产/.test(txt), text: txt };
};
const must = (c, msg) => { if (!c) { console.log(`⛔ 前置条件不成立：${msg}`); console.log(`   轨迹：${JSON.stringify(trace)}`); throw new Error(msg); } };
/** 从标题锚点读「资产管理」弹窗。 */
const readModal = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const t = [...document.querySelectorAll('div,h1,h2,span')].find((e) => (e.innerText || '').trim() === '资产管理' && vis(e));
  if (!t) return { found: false };
  let root = t; for (let i = 0; i < 8 && root.parentElement; i++) { root = root.parentElement;
    const r = root.getBoundingClientRect(); if (r.width > 500 && r.height > 350) break; }
  const rr = root.getBoundingClientRect();
  const at = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; };
  return { found: true, rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
    text: (root.innerText || '').replace(/\s+/g, ' ').trim(),
    side: [...root.querySelectorAll('div,button')].filter(vis)
      .map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter(({ r, e }) => r.x < rr.x + 40 && r.width > 70 && r.height >= 24 && r.height <= 56 && e.children.length <= 3)
      .map(({ e }) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), at: at(e),
        bg: getComputedStyle(e).backgroundColor }))
      .filter((x) => x.t).filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.at[1] === v.at[1]) === i),
    // 顶部标签行：右半、靠上、横向一排的小元素
    tabs: [...root.querySelectorAll('div,button,li,span')].filter(vis)
      .map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter(({ r, e }) => r.x > rr.x + 340 && r.y > rr.y + 40 && r.y < rr.y + 210
        && r.height >= 24 && r.height <= 44 && r.width >= 28 && r.width <= 120 && e.children.length === 0)
      .map(({ e }) => ({ t: (e.innerText || '').trim(), at: at(e), bg: getComputedStyle(e).backgroundColor }))
      .filter((x) => x.t).filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.at[1] === v.at[1]) === i),
    buttons: [...root.querySelectorAll('button,[role="button"]')].filter(vis)
      .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
        aria: e.getAttribute('aria-label'), at: at(e) })) };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '扫干净资产页剩余 📖：两个下拉 / 六个标签 / 创建主体表单 / 批量操作' });
  const out = {};

  // ═══ ①② 上传面板的两个下拉
  const p0 = await onAssetPage(); out.assetPage = p0;
  must(p0.ok, `进「资产」页失败：${p0.why || ''} 实际抽屉=${p0.text}`);
  console.log(`═══ 资产页就位：${JSON.stringify(p0.text)} ═══`);

  const up = await clickAria('创建', 2000);
  const upItems = await cands('上传资产', 30);
  must(up.executed && upItems[0], '打不开「创建 → 上传资产」');
  await page.mouse.click(upItems[0].at[0], upItems[0].at[1]); await page.waitForTimeout(2200);
  const panelOk = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return [...document.querySelectorAll('div,span')].filter((e) => vis(e)
      && (e.innerText || '').trim() === '上传资产').length; });
  console.log(`\n═══ ①② 上传面板里的两个下拉（标题命中 ${panelOk}）═══`);
  out.panelTitleCount = panelOk;
  const dds = {};
  for (const label of ['请选择文件夹', '请选择标签']) {
    const base = await fingerprint(page);
    const c = await cands(label, 60);
    if (!c[0]) { console.log(`  【${label}】找不到`); dds[label] = { found: false }; continue; }
    await page.mouse.click(c[0].at[0], c[0].at[1]); await page.waitForTimeout(2000);
    const fresh = diffPanels(base, await fingerprint(page)).slice(0, 4)
      .map((p) => ({ area: p.area, all: p.all.slice(0, 200), buttons: p.buttons.slice(0, 12) }));
    // ⭐ 另外直接读「下拉里自己冒出来的叶子文本」，不只靠 DOM 差集
    const opts = await page.evaluate(() => {
      const vis = (e) => { const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
      return [...document.querySelectorAll('div,li,span')].filter(vis)
        .map((e) => { const r = e.getBoundingClientRect();
          return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), kids: e.children.length,
            w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) }; })
        .filter((x) => x.kids === 0 && x.t && x.t.length <= 16 && x.w > 40 && x.w < 340 && x.h >= 16 && x.h <= 44)
        .filter((x) => x.y > 240) // 下拉出现在表单下方，只收 y 更大的
        .map((x) => `${x.t}@${x.x},${x.y}`)
        .filter((v, i, a) => a.indexOf(v) === i).slice(0, 16); });
    dds[label] = { at: c[0].at, fresh, opts };
    console.log(`  【${label}】@${JSON.stringify(c[0].at)} → 浮层 ${fresh.length} 个`);
    fresh.forEach((f, i) => console.log(`     ${i + 1}. area=${f.area} ${JSON.stringify(f.all)} 按钮=${JSON.stringify(f.buttons)}`));
    console.log(`     新冒出的叶子文本：${JSON.stringify(opts)}`);
    if (label === '请选择文件夹' && (fresh.length || opts.length)) await shot(page, 'M-267-上传-选择文件夹下拉.png');
    await esc();
  }
  out.dropdowns = dds;
  await esc(); await esc();

  // ═══ ③ 可灵主体库六个标签：判别式 = 选中态有没有转移
  console.log(`\n═══ ③ 可灵主体库六个标签（判别式＝选中态 bg 转移）═══`);
  must((await onAssetPage()).ok, '第 ③ 段进资产页失败');
  const mg = await clickAria('资产管理', 2600, 340);
  must(mg.executed, '打不开「资产管理」弹窗');
  const lib = await cands('可灵主体库', 40);
  must(lib[0], '弹窗里找不到侧栏「可灵主体库」');
  await page.mouse.click(lib[0].at[0], lib[0].at[1]); await page.waitForTimeout(2200);
  const m0 = await readModal();
  console.log(`  弹窗正文：${m0.text}`);
  console.log(`  标签行：${JSON.stringify(m0.tabs)}`);
  const sel = (ts) => (ts || []).filter((x) => !/rgba\(0, 0, 0, 0\)|transparent/.test(x.bg)).map((x) => x.t);
  console.log(`  ⭐ 初始选中：${JSON.stringify(sel(m0.tabs))}`);
  out.kling = { modalText: m0.text, tabs0: m0.tabs, picked0: sel(m0.tabs) };
  const probes = [];
  if (m0.tabs.length) {
    for (const t of m0.tabs) {
      await page.mouse.click(t.at[0], t.at[1]); await page.waitForTimeout(1600);
      const now = await readModal();
      const pickedNow = sel(now.tabs);
      probes.push({ clicked: t.t, pickedAfter: pickedNow, bodyChanged: now.text !== m0.text });
      console.log(`   点「${t.t}」→ 选中 ${JSON.stringify(pickedNow)} ${pickedNow.length === 1 && pickedNow[0] === t.t ? '✅ 转移到自己' : '❌ 没转移'}`);
    }
  }
  out.kling.probes = probes;
  // ⭐ 空集陷阱：先确认集合非空，再谈「是否全部满足」
  out.kling.VERDICT = probes.length === 0
    ? '⛔ 无效：一个标签都没读到（0 候选），本轮结论作废'
    : (probes.every((p) => p.pickedAfter.length === 1 && p.pickedAfter[0] === p.clicked)
      ? `✅ ${probes.length}/${probes.length} 个标签点击后选中态都转移到了自己 —— 标签是真的`
      : `⚠️ ${probes.filter((p) => p.pickedAfter.length === 1 && p.pickedAfter[0] === p.clicked).length}/${probes.length} 个转移了`);
  console.log(`  ⭐⭐ ${out.kling.VERDICT}`);
  if (probes.length) await shot(page, 'M-268-可灵主体库-点标签之后.png');

  // ═══ ④ 「创建主体」点开是什么表单（只读，不提交）
  console.log(`\n═══ ④ 「创建主体」点开是什么 ═══`);
  const mk = await cands('创建主体', 40);
  if (!mk[0]) { console.log('  ⛔ 找不到「创建主体」'); out.createSubject = { found: false }; }
  else {
    const base = await fingerprint(page);
    await page.mouse.click(mk[0].at[0], mk[0].at[1]); await page.waitForTimeout(2400);
    const fresh = diffPanels(base, await fingerprint(page)).slice(0, 4)
      .map((p) => ({ area: p.area, all: p.all.slice(0, 300), buttons: p.buttons.slice(0, 14) }));
    const form = await page.evaluate(() => {
      const vis = (e) => { const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
      return { dialogs: [...document.querySelectorAll('[role="dialog"]')].filter(vis)
          .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200)),
        inputs: [...document.querySelectorAll('input,textarea')].filter(vis)
          .map((e) => ({ type: e.type, ph: e.placeholder, val: (e.value || '').slice(0, 30) })) }; });
    out.createSubject = { found: true, fresh, ...form };
    console.log(`  新增浮层 ${fresh.length} 个`);
    fresh.forEach((f, i) => console.log(`   ${i + 1}. area=${f.area} ${JSON.stringify(f.all)}\n      按钮=${JSON.stringify(f.buttons)}`));
    console.log(`  role=dialog：${JSON.stringify(form.dialogs)}`);
    console.log(`  可见输入框：${JSON.stringify(form.inputs)}`);
    if (fresh.length || form.dialogs.length) await shot(page, 'M-269-创建主体-表单.png');
  }
  await esc(); await esc();

  // ═══ ⑤ 批量操作勾选态
  console.log(`\n═══ ⑤ 批量操作 ═══`);
  const ap = await onAssetPage();
  console.log(`  回资产页：${JSON.stringify(ap)}`);
  if (ap.ok) {
    const bo = await clickAria('批量操作', 2000);
    const after = await page.evaluate(() => {
      const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      const d = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
          return vis(e) && r.x < 40 && r.width > 250 && r.width < 380 && r.height > 300; })
        .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
      return { text: (d?.innerText || '').replace(/\s+/g, ' ').trim(),
        checks: [...document.querySelectorAll('[role="checkbox"],input[type="checkbox"]')].filter(vis).length }; });
    console.log(`  executed=${bo.executed}${bo.note ? '（' + bo.note + '）' : ''} → ${JSON.stringify(after)}`);
    out.batchMode = { click: bo, ...after };
    if (/已选择/.test(after.text || '')) await shot(page, 'M-270-批量操作-勾选模式.png');
  }

  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  const endState = await drawerOpen();
  out.final = { nodes: finalN, state: endState };
  console.log(`\n═══ 收尾：节点 ${finalN}｜资产行仍可见=${endState.assetName > 0}（本轮零写操作）═══`);

  await logStep(B, {
    id: 'BQ-asset-page-open-questions',
    title: '⭐ 扫干净资产页剩下的 📖：两个下拉 / 六个标签判别式 / 创建主体表单 / 批量操作',
    target: 'BP 留下五个 📖。本轮：① 读「请选择文件夹」「请选择标签」两个下拉的选项；'
      + '② ⭐ 可灵主体库六个标签，判别式从「正文变没变」换成**「点完回读每个标签自己的 '
      + 'backgroundColor，看选中态有没有转移」** —— BP2g 那个判别式在**空库**上必然失效，'
      + '正文只有「创建主体」一个按钮，六种结果一样并不说明标签是坏的；'
      + '③ 点「创建主体」读表单（只读不提交）；④ 批量操作勾选态。'
      + '沿用 BP 立的三条纪律：`enterDrawer()` 验-重试-再验且前置不成立就**响亮地抛**；'
      + '进抽屉后**显式切到「资产」标签页**；判「是否全部满足」前**先确认集合非空**。'
      + '⛔ 不传文件、不提交表单、不建主体、不新建文件夹/标签、不删除。',
    evidence: out,
    visible_text: JSON.stringify({
      资产页: out.assetPage,
      面板标题命中: out.panelTitleCount,
      文件夹下拉: out.dropdowns?.['请选择文件夹'],
      标签下拉: out.dropdowns?.['请选择标签'],
      可灵主体库正文: out.kling?.modalText, 标签初值: out.kling?.tabs0, 初始选中: out.kling?.picked0,
      逐标签选中态: out.kling?.probes?.map((p) => `${p.clicked}→${JSON.stringify(p.pickedAfter)}`),
      标签判定: out.kling?.VERDICT,
      创建主体: out.createSubject, 批量操作: out.batchMode, 收尾: out.final }).slice(0, 3600),
    shot: 'M-267-上传-选择文件夹下拉.png',
  });
  console.log('\nBQ 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

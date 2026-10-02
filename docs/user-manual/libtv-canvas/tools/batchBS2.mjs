// Batch BS2 — 资产行菜单里剩下的四个动作，点开各是什么。
//
// BP2f 只 hover 展开过菜单，没点过里面任何一项。BR/BQ 又把页面推到了「有分类」的状态，
// 于是这四项终于可以点名了：
//   ① 添加到Agent   —— 资产抽屉里也有同名项（节点侧栏的 `⋯→添加到Agent` 已经验过，
//                       **资产这条是不是同一个机制**，之前一直存疑）
//   ② 添加到画布
//   ③ 新建子文件夹   —— ⚠️ 写账户数据：只点开看有没有输入框，⛔ 不提交、不命名
//   ④ 移动到 › 的子菜单 —— 列出哪些目标文件夹
//
// ⭐ 沿用 BQ/BR 立的三条：
//   · 前置条件不成立就 `must()` 响亮地抛，别让后面静默空转；
//   · 同名 aria 全部枚举再挑，别 `.find()` 取第一个；
//   · ⭐⭐ 输出「✅ n/n」之前先报覆盖率 —— n 要等于界面上一共有几个。
//
// ⛔ 本轮只读：不提交任何写操作 —— 不建子文件夹、不传文件、不发送、不派发。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBS2';
const { browser, page } = await launch();

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
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      tag: e.tagName, kids: e.children.length }); }
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
const onAssetPage = async () => {
  for (let i = 0; i < 3; i += 1) {
    const d = await drawerOpen();
    if (d.open) {
      const tab = await cands('资产', 20);
      if (!tab[0]) return { ok: false, why: '找不到「资产」标签' };
      await page.mouse.click(tab[0].at[0], tab[0].at[1]); await page.waitForTimeout(2400);
      const txt = await drawerText();
      return /资产/.test(txt) && /待分类资产|暂无资产/.test(txt)
        ? { ok: true, text: txt } : { ok: false, why: `切标签后抽屉=${txt}` };
    }
    await clickAria('资产管理', 2600, 40);
    trace.push({ round: i + 1, opened: false });
  }
  return { ok: false, why: '抽屉没打开' };
};
const must = (c, msg) => { if (!c) { console.log(`⛔ 前置不成立：${msg}｜轨迹 ${JSON.stringify(trace)}`); throw new Error(msg); } };

const MENU8 = ['添加到Agent', '添加到画布', '更改图标', '新建子文件夹', '移动到', '下载', '重命名', '删除'];
/** 打开八项菜单，并**验证 8 项同时可见**才算开成（BP2g 的做法）。 */
const openMenu = async () => {
  const more = await clickAria('更多操作', 1800);
  if (!more.executed) return { opened: false, note: more.note, coverage: '0/8', seen: [], pts: {} };
  const seen = await page.evaluate((w) => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    return w.filter((t) => [...document.querySelectorAll('div,span,button,li')]
      .some((e) => (e.innerText || '').replace(/\s+/g, ' ').trim() === t && vis(e)
        && e.getBoundingClientRect().height < 60)); }, MENU8);
  const pts = await page.evaluate((w) => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    const o = {};
    for (const t of w) {
      const e = [...document.querySelectorAll('div,span')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === t
        && vis(x) && x.getBoundingClientRect().height < 60);
      if (!e) { o[t] = null; continue; }
      let row = e; for (let i = 0; i < 4 && row.parentElement; i++) { row = row.parentElement;
        const r = row.getBoundingClientRect();
        if (r.height > 26 && r.height < 56 && r.width > 100 && r.width < 340) break; }
      const r = row.getBoundingClientRect();
      o[t] = { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }
    return o; }, MENU8);
  return { opened: seen.length === MENU8.length, seen, pts, coverage: `${seen.length}/${MENU8.length}` };
};

/**
 * ⭐ 读可见输入框。**before / after 必须调用同一个函数** ——
 * BS 第一轮 before 少取了 `at` 字段，两边 JSON 必然不等，
 * 于是「新增输入框 ✅」恒为真，输出了一个假阳性。
 */
const readInputs = () => page.evaluate(() => [...document.querySelectorAll('input,textarea')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { ph: e.placeholder, val: (e.value || '').slice(0, 24),
      at: [Math.round(r.x), Math.round(r.y)] }; }));

/**
 * ⭐ 「菜单关掉了」这件事本身会让正文变短 —— 菜单八项加起来大约 40 个字。
 * 所以 bodyLen 为负时，要先减掉这个基线再判断「有没有发生别的事」。
 */
const MENU_TEXT_LEN = (() => {
  try { return MENU8.join(' ').length; } catch { return null; }
})();

/** ⭐ 通用探测：点菜单某一项 → DOM 差集 + 可见输入框 + 抽屉/画布两侧文本变化。 */
const probeItem = async (label) => {
  const m = await openMenu();
  must(m.opened, `菜单没打开（读到 ${m.coverage}）`);
  must(m.pts[label], `菜单里没有「${label}」`);
  const before = {
    drawer: await drawerText(),
    bodyLen: await page.evaluate(() => document.body.innerText.length),
    // ⭐⭐ before / after 必须取**完全相同**的字段，否则 JSON 永远不等、
    //    「新增输入框」会恒为 true —— BS 第一轮就报了个假的「新增输入框 ✅」。
    inputs: await readInputs(),
    nodes: await page.evaluate(() => document.querySelectorAll('.react-flow__node').length),
    fp: await fingerprint(page),
  };
  const fcP = page.waitForEvent('filechooser', { timeout: 3500 }).catch(() => null);
  await page.mouse.click(m.pts[label].at[0], m.pts[label].at[1]);
  const fc = await fcP;
  await page.waitForTimeout(2400);
  const after = {
    drawer: await drawerText(),
    bodyLen: await page.evaluate(() => document.body.innerText.length),
    inputs: await readInputs(),
    nodes: await page.evaluate(() => document.querySelectorAll('.react-flow__node').length),
    fp: await fingerprint(page),
  };
  const fresh = diffPanels(before.fp, after.fp).slice(0, 5)
    .map((p) => ({ area: p.area, all: p.all.slice(0, 260), buttons: p.buttons.slice(0, 14) }));
  const delta = after.bodyLen - before.bodyLen;
  return { label, menuCoverage: m.coverage, at: m.pts[label].at,
    chooserFired: !!fc, menuTextLen: MENU_TEXT_LEN,
    // ⭐ 正文变短 ≈ 菜单消失；扣掉这个基线后仍是 0 → 「除了菜单关掉，什么都没发生」
    netOfMenu: delta + (delta < 0 ? Math.abs(MENU_TEXT_LEN || 0) : 0),
    drawerChanged: before.drawer !== after.drawer,
    bodyLenDelta: after.bodyLen - before.bodyLen,
    nodesDelta: after.nodes - before.nodes,
    newInputs: JSON.stringify(after.inputs) !== JSON.stringify(before.inputs),
    inputs: after.inputs, fresh };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '资产行菜单四个动作逐个点名（不提交任何写操作）' });
  const out = {};

  const p0 = await onAssetPage(); out.assetPage = p0;
  must(p0.ok, `进资产页失败：${p0.why || ''}`);
  console.log(`═══ 资产页就位：${JSON.stringify(p0.text)} ═══`);

  // 菜单覆盖率先自证一次
  const m0 = await openMenu();
  console.log(`  菜单自检：读到 ${m0.coverage} → ${JSON.stringify(m0.seen)}`);
  out.menuSelfCheck = { coverage: m0.coverage, seen: m0.seen };
  must(m0.opened, `菜单八项没读全（${m0.coverage}）`);
  await esc();

  // ── 逐项点名
  const probes = [];
  for (const label of ['添加到Agent', '添加到画布', '新建子文件夹']) {
    console.log(`\n═══ 点「${label}」 ═══`);
    // ⭐ 每项之前重新确认「抽屉开着 + 在资产页」—— BS 第一轮第二项就是这么断的：
    //    上一项点完连按两个 esc，把整个抽屉关掉了。
    const here = await onAssetPage();
    must(here.ok, `第「${label}」项前资产页不在位：${here.why || ''}`);
    const r = await probeItem(label);
    probes.push(r);
    console.log(`  filechooser=${r.chooserFired ? '✅' : '❌'}｜抽屉文案变=${r.drawerChanged ? '✅' : '—'}`
      + `｜正文长度 ${r.bodyLenDelta >= 0 ? '+' : ''}${r.bodyLenDelta}`
      + `（菜单文字基线 ${r.menuTextLen}，扣除后净变化 ${r.netOfMenu}）`
      + `｜节点 ${r.nodesDelta >= 0 ? '+' : ''}${r.nodesDelta}`
      + `｜新增输入框=${r.newInputs ? '✅' : '—'}`);
    const inert = r.netOfMenu === 0 && !r.drawerChanged && r.nodesDelta === 0 && !r.newInputs && !r.fresh.length;
    console.log(`  ⭐ 判定：${inert ? '**除了菜单关掉，什么都没发生**' : '**发生了别的事，见下面**'}`);
    r.inert = inert;
    console.log(`  当前输入框：${JSON.stringify(r.inputs)}`);
    console.log(`  新增浮层 ${r.fresh.length} 个：`);
    r.fresh.forEach((f, i) => console.log(`    ${i + 1}. area=${f.area} ${JSON.stringify(f.all)}\n       按钮=${JSON.stringify(f.buttons)}`));
    if (r.fresh.length) await shot(page, `M-272-资产菜单-${label}.png`);
    await esc(); await esc();
  }
  out.probes = probes;
  out.coverage = { probed: probes.length, expected: 3,
    names: probes.map((p) => p.label) };
  out.VERDICT = probes.length === 0 ? '⛔ 一项都没点到'
    : (probes.length < 3 ? `⚠️ 只点了 ${probes.length}/3 项` : `✅ 三项全部点到`);
  console.log(`\n  ⭐ 覆盖率：${out.coverage.probed}/${out.coverage.expected}｜${out.VERDICT}`);

  // ── 「移动到 ›」子菜单
  console.log(`\n═══ 「移动到 ›」的子菜单 ═══`);
  const m1 = await openMenu();
  must(m1.opened, '菜单没打开');
  must(m1.pts['移动到'], '菜单里没有「移动到」');
  await page.mouse.move(m1.pts['移动到'].at[0], m1.pts['移动到'].at[1]);
  await page.waitForTimeout(1800);
  const sub = await page.evaluate((r) => {
    const vis = (e) => { const b = e.getBoundingClientRect();
      return b.width > 0 && b.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    // 子菜单在「移动到」那一行的**右侧**
    return [...document.querySelectorAll('div,li,span,button')].filter(vis)
      .map((e) => { const b = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), kids: e.children.length,
          x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) }; })
      .filter((x) => x.t && x.t.length <= 16 && x.kids === 0 && x.w > 40 && x.w < 340 && x.h >= 16 && x.h <= 44)
      .filter((x) => x.x > r[0] && Math.abs(x.y - r[1]) < 220)   // 右侧且纵向大致对齐
      .map((x) => `${x.t}@${x.x},${x.y}[${x.w}x${x.h}]`)
      .filter((v, i, a) => a.indexOf(v) === i).slice(0, 16); }, m1.pts['移动到'].rect);
  out.moveToSub = { at: m1.pts['移动到'].at, items: sub };
  console.log(`  悬停「移动到」后右侧出现：${JSON.stringify(sub)}`);
  if (sub.length) await shot(page, 'M-273-资产菜单-移动到子菜单.png');
  await esc();

  // ── 收尾：账户必须原样
  await esc();
  const st = await drawerOpen(); const txt = await drawerText();
  const nodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.final = { state: st, text: txt, nodes };
  console.log(`\n═══ 收尾：抽屉=${JSON.stringify(txt)}｜节点 ${nodes}｜分类仍可见=${st.assetName > 0} ═══`);
  out.accountIntact = /待分类资产/.test(txt) && nodes === 11;
  console.log(`  ⭐ 账户与画布原样？ ${out.accountIntact ? '✅ 是' : '❌ 否'}`);

  await logStep(B, {
    id: 'BS2-asset-row-menu-four-actions',
    title: '资产行菜单四个动作逐个点名（不提交任何写操作）',
    target: 'BP2f 只展开过菜单没点过任何一项。本轮逐个点 `添加到Agent` / `添加到画布` / `新建子文件夹`，'
      + '每次都用四条判据同时汇报：① DOM 差集里有没有新浮层 ② 抽屉全文变没变 ③ 正文长度差 '
      + '④ 可见输入框数变没变，另加画布节点数差（防「添加到画布」真建了节点）。'
      + '并悬停 `移动到 ›` 读它右侧的子菜单列出哪些目标文件夹。'
      + '⭐ 菜单开成与否先自证：**八项同时可见**才算开成，并报 `读到 n/8`。'
      + '⛔ 不提交任何写操作 —— 不建子文件夹、不传文件、不发送、不派发。',
    evidence: out,
    visible_text: JSON.stringify({
      资产页: out.assetPage, 菜单自检: out.menuSelfCheck,
      逐项: out.probes?.map((p) => ({ 项: p.label, chooser: p.chooserFired,
        抽屉变: p.drawerChanged, 正文Δ: p.bodyLenDelta, 扣菜单基线后: p.netOfMenu, inert: p.inert, 节点Δ: p.nodesDelta,
        新输入框: p.newInputs, 输入框: p.inputs, 新浮层: p.fresh?.map((f) => f.all) })),
      覆盖率: out.coverage, 判定: out.VERDICT,
      移动到子菜单: out.moveToSub, 收尾: out.final,
      账户画布原样: out.accountIntact }).slice(0, 3600),
    shot: 'M-273-资产菜单-移动到子菜单.png',
  });
  console.log('\nBS 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

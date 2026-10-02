// Batch BR — 补 BQ 的两处缺口。
//
// ⛔ 先认 BQ 自己犯的**第五次同款错误，而且这次更隐蔽**：
//   BQ 的标签判据要求 `r.x > 弹窗左边界 + 340`，而弹窗左边界是 72 ——
//   于是 `全部`(x=354) 和 `人物`(x=416) **被自己的边界滤掉了**，
//   六个标签只读到 4 个，可判据照样输出「✅ 4/4 —— 标签是真的」。
//   ⭐⭐ **结论为真、覆盖面被静默削掉一半，比直接报错更难发现。**
//   修法：**先「报总数」再「判真假」** —— 覆盖了几个必须和界面上一共有几个一起报；
//        判别式只用相对坐标（同一条 y 带内），不用任何绝对 x 阈值。
//
// 本轮三件事：
//   ① 重开上传面板，点「请选择标签」读选项（BQ 那轮 esc 把整个面板关掉了）
//   ② 六个标签重测：**不设绝对 x 边界**，改成「和已知标签同一 y 带、宽 28~120、叶子节点」
//   ③ 「创建主体」换更宽的候选重试，确认它到底开不开东西
//
// ⛔ 只读：不传文件、不提交、不建主体、不删除。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBR';
const { browser, page } = await launch();

const findAria = (label) => page.evaluate((l) => [...document.querySelectorAll('button,[role="button"],[aria-label]')]
  .filter((x) => x.getAttribute('aria-label') === l)
  .map((x) => { const r = x.getBoundingClientRect();
    return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
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
    && /^共 \d+ 节点$/.test((e.innerText || '').trim())).length > 0 }; });
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
      if (/资产/.test(txt) && /待分类资产|暂无资产/.test(txt)) return { ok: true, text: txt };
      return { ok: false, why: `切标签后抽屉=${txt}` };
    }
    await clickAria('资产管理', 2600, 40);
    trace.push({ round: i + 1, opened: false });
  }
  return { ok: false, why: '抽屉没打开' };
};
const must = (c, msg) => { if (!c) { console.log(`⛔ 前置不成立：${msg}｜轨迹 ${JSON.stringify(trace)}`); throw new Error(msg); } };
/** 打开上传面板。 */
const openPanel = async () => {
  const cr = await clickAria('创建', 2000);
  const up = await cands('上传资产', 30);
  if (!up[0]) return { ok: false, why: `下拉里没有「上传资产」（创建 executed=${cr.executed}）` };
  await page.mouse.click(up[0].at[0], up[0].at[1]); await page.waitForTimeout(2200);
  const n = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return [...document.querySelectorAll('div,span')].filter((e) => vis(e)
      && (e.innerText || '').trim() === '上传资产').length; });
  return { ok: n > 0, titleHits: n };
};
/** ⭐ 标签行：**不设任何绝对 x 边界**，改成「与已知标签同一 y 带」来圈定。 */
const readTabs = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  const t = [...document.querySelectorAll('div,h1,h2,span')].find((e) => (e.innerText || '').trim() === '资产管理' && vis(e));
  if (!t) return { found: false };
  let root = t; for (let i = 0; i < 8 && root.parentElement; i++) { root = root.parentElement;
    const r = root.getBoundingClientRect(); if (r.width > 500 && r.height > 350) break; }
  // ⭐ 第一步：找出「标签带」的 y —— 主区工具条那一行下方、靠左的一排小元素
  const all = [...root.querySelectorAll('div,button,li,span')].filter(vis)
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter(({ r, e }) => e.children.length === 0 && r.height >= 24 && r.height <= 44
      && r.width >= 28 && r.width <= 120 && (e.innerText || '').trim());
  if (!all.length) return { found: true, text: (root.innerText || '').replace(/\s+/g, ' ').trim(), tabs: [] };
  // 标签带的 y = 出现次数最多的那一行（六个标签里五个透明，一个选中，但 y 相同）
  const byY = {};
  for (const x of all) { const k = Math.round(x.r.y / 4) * 4; byY[k] = (byY[k] || 0) + 1; }
  const bandY = Number(Object.keys(byY).sort((a, b) => byY[b] - byY[a])[0]);
  const band = all.filter(({ r }) => Math.abs(r.y - bandY) <= 6)
    .map(({ e, r }) => ({ t: (e.innerText || '').trim(), bg: getComputedStyle(e).backgroundColor,
      at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }))
    .filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.at[0] === v.at[0]) === i)
    .sort((a, b) => a.at[0] - b.at[0]);
  return { found: true, bandY, text: (root.innerText || '').replace(/\s+/g, ' ').trim(), tabs: band }; });

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '补 BQ 两处缺口：标签下拉 + 六标签全覆盖（去掉绝对 x 边界）' });
  const out = {};

  // ── ① 「请选择标签」下拉
  console.log(`═══ ① 「请选择标签」下拉 ═══`);
  const p0 = await onAssetPage(); out.assetPage = p0;
  must(p0.ok, `进资产页失败：${p0.why || ''}`);
  console.log(`  资产页：${JSON.stringify(p0.text)}`);
  const pn = await openPanel();
  must(pn.ok, `上传面板没开：${pn.why || ''}（标题命中 ${pn.titleHits}）`);
  console.log(`  上传面板就位（标题命中 ${pn.titleHits}）`);
  const tagSel = await cands('请选择标签', 60);
  console.log(`  「请选择标签」候选 ${tagSel.length} 个：${JSON.stringify(tagSel)}`);
  if (!tagSel[0]) { out.tagDropdown = { found: false }; }
  else {
    const base = await fingerprint(page);
    await page.mouse.click(tagSel[0].at[0], tagSel[0].at[1]); await page.waitForTimeout(2200);
    const fresh = diffPanels(base, await fingerprint(page)).slice(0, 4)
      .map((p) => ({ area: p.area, all: p.all.slice(0, 200), buttons: p.buttons.slice(0, 14) }));
    const opts = await page.evaluate(() => {
      const vis = (e) => { const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
      const panel = [...document.querySelectorAll('div')].filter(vis)
        .map((e) => { const r = e.getBoundingClientRect();
          return { e, r, t: (e.innerText || '').replace(/\s+/g, ' ').trim() }; })
        .filter((x) => /请选择标签/.test(x.t) && x.r.width > 200 && x.t.length < 40)
        .sort((a, b) => a.t.length - b.t.length)[0];
      if (!panel) return null;
      const pr = panel.r;
      return [...document.querySelectorAll('div,li,span,button')].filter(vis)
        .map((e) => { const r = e.getBoundingClientRect();
          return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), kids: e.children.length,
            w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y),
            inPanel: r.x > pr.x - 30 && r.x < pr.x + 320 && r.y > pr.y }; })
        .filter((x) => x.inPanel && x.kids === 0 && x.t && x.t.length <= 16 && x.w > 30 && x.w < 340 && x.h >= 16 && x.h <= 44)
        .map((x) => `${x.t}@${x.x},${x.y}`)
        .filter((v, i, a) => a.indexOf(v) === i).slice(0, 16); });
    out.tagDropdown = { at: tagSel[0].at, fresh, opts };
    console.log(`  → 浮层 ${fresh.length} 个`);
    fresh.forEach((f, i) => console.log(`     ${i + 1}. area=${f.area} ${JSON.stringify(f.all)} 按钮=${JSON.stringify(f.buttons)}`));
    console.log(`     选项：${JSON.stringify(opts)}`);
    if ((fresh.length || (opts || []).length)) await shot(page, 'M-271-上传-选择标签下拉.png');
  }
  await esc(); await esc();

  // ── ② 六个标签全覆盖
  console.log(`\n═══ ② 可灵主体库标签（去掉绝对 x 边界，按 y 带圈定）═══`);
  must((await onAssetPage()).ok, '第 ② 段进资产页失败');
  const mg = await clickAria('资产管理', 2600, 340);
  must(mg.executed, '打不开「资产管理」弹窗');
  const lib = await cands('可灵主体库', 40);
  must(lib[0], '找不到侧栏「可灵主体库」');
  await page.mouse.click(lib[0].at[0], lib[0].at[1]); await page.waitForTimeout(2200);
  const m0 = await readTabs();
  const sel = (ts) => (ts || []).filter((x) => !/rgba\(0, 0, 0, 0\)|transparent/.test(x.bg)).map((x) => x.t);
  console.log(`  标签带 y=${m0.bandY}｜读到 ${m0.tabs.length} 个：${JSON.stringify(m0.tabs.map((t) => `${t.t}${t.bg === 'rgba(0, 0, 0, 0)' ? '' : '*'}@${t.at[0]}`))}`);
  console.log(`  ⭐ 初始选中：${JSON.stringify(sel(m0.tabs))}`);
  out.tabs = { bandY: m0.bandY, all: m0.tabs, picked0: sel(m0.tabs) };
  const probes = [];
  for (const t of m0.tabs) {
    await page.mouse.click(t.at[0], t.at[1]); await page.waitForTimeout(1600);
    const now = await readTabs();
    const p = sel(now.tabs);
    probes.push({ clicked: t.t, pickedAfter: p, moved: p.length === 1 && p[0] === t.t });
    console.log(`   点「${t.t}」→ 选中 ${JSON.stringify(p)} ${p.length === 1 && p[0] === t.t ? '✅' : '❌'}`);
  }
  out.probes = probes;
  // ⭐⭐ 覆盖率必须和结论一起报 —— 「4/4 通过」不等于「六个都测了」
  const expected = 6;
  out.coverage = { read: m0.tabs.length, expected,
    names: m0.tabs.map((t) => t.t) };
  const movedN = probes.filter((p) => p.moved).length;
  out.VERDICT = m0.tabs.length === 0
    ? '⛔ 无效：一个标签都没读到'
    : (m0.tabs.length < expected
      ? `⚠️ 覆盖不全：界面上一共 ${expected} 个标签，只读到 ${m0.tabs.length} 个（缺 ${JSON.stringify(
        ['全部', '人物', '场景', '道具', '特效', '其他'].filter((n) => !m0.tabs.some((t) => t.t === n)))}）`
      : (movedN === probes.length
        ? `✅ 六个标签全覆盖，且 ${movedN}/${probes.length} 点击后选中态都转移到了自己`
        : `⚠️ ${movedN}/${probes.length} 转移了`));
  console.log(`  ⭐⭐ ${out.VERDICT}`);
  if (m0.tabs.length >= expected) await shot(page, 'M-268-可灵主体库-点标签之后.png');

  // ── ③ 「创建主体」换宽候选重试
  console.log(`\n═══ ③ 「创建主体」 ═══`);
  const mk = await cands('创建主体', 20);
  console.log(`  候选 ${mk.length} 个：${JSON.stringify(mk)}`);
  if (!mk.length) out.createSubject = { found: false };
  else {
    const base = await fingerprint(page);
    const beforeTexts = await page.evaluate(() => document.body.innerText.length);
    await page.mouse.click(mk[0].at[0], mk[0].at[1]); await page.waitForTimeout(2600);
    const fresh = diffPanels(base, await fingerprint(page)).slice(0, 4)
      .map((p) => ({ area: p.area, all: p.all.slice(0, 240), buttons: p.buttons.slice(0, 12) }));
    const now = await readTabs();
    const inputs = await page.evaluate(() => {
      const vis = (e) => { const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
      return [...document.querySelectorAll('input,textarea')].filter(vis)
        .map((e) => ({ type: e.type, ph: e.placeholder, val: (e.value || '').slice(0, 24),
          at: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; })() })); });
    out.createSubject = { cands: mk, fresh, bodyLenBefore: beforeTexts,
      bodyLenAfter: await page.evaluate(() => document.body.innerText.length),
      modalText: now.text, inputs };
    console.log(`  正文长度 ${beforeTexts} → ${out.createSubject.bodyLenAfter}`);
    console.log(`  新增浮层 ${fresh.length}：${JSON.stringify(fresh.map((f) => f.all))}`);
    console.log(`  弹窗正文：${now.text}`);
    console.log(`  可见输入框：${JSON.stringify(inputs)}`);
    if (fresh.length) await shot(page, 'M-269-创建主体-表单.png');
  }
  await esc(); await esc();

  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.final = { nodes: finalN };
  console.log(`\n═══ 收尾：节点 ${finalN}（本轮零写操作）═══`);

  await logStep(B, {
    id: 'BR-tag-dropdown-and-full-tab-coverage',
    title: '⭐⭐ 六标签全覆盖复测：BQ 的绝对 x 边界把「全部」「人物」滤掉了，结论对但覆盖面少一半',
    target: 'BQ 的标签判据要求 `r.x > 弹窗左边界 + 340`，而弹窗左边界是 72 —— '
      + '**`全部`(x=354) 和 `人物`(x=416) 被自己的边界滤掉**，六个标签只读到 4 个，'
      + '判据却照样输出「✅ 4/4 —— 标签是真的」。'
      + '⭐⭐ **结论为真、覆盖面被静默削掉一半，比直接报错更难发现。** '
      + '修法两条：① 判别式只用相对坐标（同一条 y 带内），不设任何绝对 x 阈值；'
      + '② **先报覆盖率、再判真假**，覆盖了几个必须和界面上一共有几个一起报。'
      + '本轮另补 BQ 漏掉的「请选择标签」下拉（BQ 那轮 esc 把整个面板关掉了），'
      + '并用更宽的候选重试「创建主体」。⛔ 只读。',
    evidence: out,
    visible_text: JSON.stringify({
      资产页: out.assetPage, 标签下拉: out.tagDropdown,
      标签带y: out.tabs?.bandY, 读到的标签: out.tabs?.all?.map((t) => `${t.t}:${t.bg}@${t.at[0]}`),
      初始选中: out.tabs?.picked0,
      逐标签: out.probes?.map((p) => `${p.clicked}→${JSON.stringify(p.pickedAfter)}${p.moved ? '✅' : '❌'}`),
      覆盖率: out.coverage, 判定: out.VERDICT,
      创建主体: out.createSubject, 收尾: out.final }).slice(0, 3400),
    shot: 'M-271-上传-选择标签下拉.png',
  });
  console.log('\nBR 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

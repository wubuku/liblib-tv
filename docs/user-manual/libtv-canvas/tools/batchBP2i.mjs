// Batch BP2i — 重跑 BP2h：前置条件必须响亮失败 + 修掉「空集让真值判断恒真」。
//
// ⭐⭐ M-263 一张图就答掉了挂了好几批的 📖「上传资产支持哪些格式」——
//   面板底部白纸黑字：`支持的文件格式 🖼 jpg/jpeg/png ▶ mp4 🔊 mp3` + `单个文件大小不超过 20MB`。
//   而 BP1 从 DOM 读到的 `accept=".jpg,.jpeg,.png,.mp4,.mp3"` 与这行字**逐字吻合** ——
//   两个互相独立的来源对上了，这是本轮最硬的一条。
//   ⇒ 不必再纠结「哪个 file input 属于上传」，**界面自己写着答案**。
//
// 本轮全部只读：⛔ 不选真文件、不提交表单、不建主体、不传任何东西。
//   ① 点左侧虚线框 `+` → 这次 filechooser **应该**会弹，把 accept 真正归因到它
//   ② 「请选择文件夹」下拉列什么   ③ 「请选择标签」下拉列什么
//   ④ 没填必填项时「保存」是不是禁用的（读 disabled / pointer-events / 颜色，别只看"点了没反应"）
//   ⑤ ⭐ 可灵主体库 6 个标签：BP2g 用「正文是否变」做判别式，得到「6 个标签 1 种正文」，
//      **但那个库是空的**（正文只有「创建主体」一个按钮）—— **判别式失效 ≠ 标签无效**。
//      本轮换判别式：**点击后回读每个标签自己的 backgroundColor，看选中态有没有转移**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBP2i';
const { browser, page } = await launch();

/**
 * ⭐⭐ BP2h2 的硬教训：`aria-label="资产管理"` 在页面上**命中两个元素** ——
 *   底栏左下角那个「打开素材库侧栏」的开关，和抽屉内部的「管理」按钮。
 *   `.find()` 只取第一个，于是点到的是 [61,778]（底栏），不是抽屉里的「管理」。
 * 修法：先枚举所有命中并报告，再按 `preferX`（优先落在 x < 这个数的，即抽屉区域）挑一个。
 */
const findAria = (label) => page.evaluate((l) => {
  return [...document.querySelectorAll('button,[role="button"],[aria-label]')]
    .filter((x) => x.getAttribute('aria-label') === l)
    .map((x) => { const r = x.getBoundingClientRect();
      return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        visible: r.width >= 4 && r.height >= 4,
        cls: (x.className || '').toString().slice(0, 40) }; }); }, label);
const clickAria = async (label, wait = 2200, preferX = null) => {
  const all = await findAria(label);
  const vis = all.filter((a) => a.visible);
  if (!vis.length) return { executed: false, note: `找不到可见的 aria-label=${label}`, allHits: all };
  const pick = preferX == null ? vis[0] : (vis.find((a) => a.at[0] < preferX) || vis[0]);
  await page.mouse.click(pick.at[0], pick.at[1]); await page.waitForTimeout(wait);
  return { executed: true, at: pick.at, hits: vis.length, allHits: all, pickedBy: preferX == null ? '第一个' : 'preferX' };
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
    && /^共 \d+ 节点$/.test((e.innerText || '').trim())).length > 0 }; });
/**
 * ⭐ BP2h 的教训：`enterDrawer()` 调一次「管理」就返回，**没验证抽屉真的开了**，
 * 于是后面 ④⑤ 全部静默空转，最后还打出 `0/0 ✅ 标签是真的`。
 * 修法：**验 → 没开就重试 → 再验**，最多 3 轮；返回 ok 供调用方**响亮地失败**。
 */
const enterDrawer = async (log) => {
  for (let i = 0; i < 3; i += 1) {
    const d = await drawerOpen();
    if (d.open) { log?.push({ round: i + 1, ok: true, ...d }); return { ok: true, rounds: i + 1, ...d }; }
    const r = await clickAria('资产管理', 2600, 40);
    log?.push({ round: i + 1, ok: false, click: r, ...d });
  }
  const d = await drawerOpen();
  return { ok: d.open, rounds: 3, exhausted: true, ...d };
};
/** 前置条件不成立就立刻抛，别让后面静默空转。 */
const must = (cond, msg, log) => { if (!cond) { console.log(`⛔ 前置条件不成立：${msg}`); console.log(`   轨迹：${JSON.stringify(log)}`); throw new Error(msg); } };

/** 打开「上传资产」面板，返回面板内可交互件。 */
const openUpload = async () => {
  const cr = await clickAria('创建', 2000);
  const up = await cands('上传资产', 30);
  if (!up[0]) return { opened: false, create: cr };
  await page.mouse.click(up[0].at[0], up[0].at[1]); await page.waitForTimeout(2200);
  const panel = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    const t = [...document.querySelectorAll('div,h1,h2,span')].find((e) => (e.innerText || '').trim() === '上传资产' && vis(e));
    if (!t) return { found: false };
    let root = t; for (let i = 0; i < 8 && root.parentElement; i++) { root = root.parentElement;
      const r = root.getBoundingClientRect(); if (r.width > 500 && r.height > 300) break; }
    const rr = root.getBoundingClientRect();
    return { found: true, rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
      text: (root.innerText || '').replace(/\s+/g, ' ').trim(),
      items: [...root.querySelectorAll('button,[role="button"],div,span')].filter(vis)
        .map((e) => { const r = e.getBoundingClientRect();
          return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
            aria: e.getAttribute('aria-label'), kids: e.children.length,
            at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            disabled: e.disabled === true || e.getAttribute('aria-disabled') === 'true',
            pe: getComputedStyle(e).pointerEvents, op: getComputedStyle(e).opacity,
            color: getComputedStyle(e).color, bg: getComputedStyle(e).backgroundColor,
            border: getComputedStyle(e).borderStyle, svg: e.querySelectorAll('svg').length }; })
        .filter((x) => x.at[0] > rr.x && x.at[0] < rr.x + rr.width && x.at[1] > rr.y && x.at[1] < rr.y + rr.height)
        .filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.at[0] === v.at[0] && y.at[1] === v.at[1]) === i) }; });
  return { opened: true, create: cr, panel };
};
/** ⭐ 虚线框 = 找 borderStyle 为 dashed 且面积最大的那个元素。 */
const dropZone = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 40 && r.height > 40 && getComputedStyle(e).visibility !== 'hidden'; };
  const ds = [...document.querySelectorAll('div,section,label')].filter(vis)
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter(({ r, e }) => r.width > 150 && r.height > 150
      && /dashed|dotted/.test(getComputedStyle(e).borderTopStyle)
      && e.querySelectorAll('input[type="file"]').length > 0)
    .sort((a, b) => b.r.width * b.r.height - a.r.width * a.r.height);
  const best = ds[0];
  if (!best) {
    // 兜底：面板里最大的、含 file input 的方块
    const alt = [...document.querySelectorAll('div,section,label')]
      .map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter(({ r, e }) => r.width > 200 && r.height > 200 && e.querySelectorAll('input[type="file"]').length > 0)
      .sort((a, b) => b.r.width * b.r.height - a.r.width * a.r.height)[0];
    if (!alt) return null;
    return { at: [Math.round(alt.r.x + alt.r.width / 2), Math.round(alt.r.y + alt.r.height / 2)],
      rect: [Math.round(alt.r.x), Math.round(alt.r.y), Math.round(alt.r.width), Math.round(alt.r.height)],
      via: '含file input的最大方块', border: getComputedStyle(alt.e).borderTopStyle,
      suspicious: alt.r.width > 1200 };
  }
  return { at: [Math.round(best.r.x + best.r.width / 2), Math.round(best.r.y + best.r.height / 2)],
    rect: [Math.round(best.r.x), Math.round(best.r.y), Math.round(best.r.width), Math.round(best.r.height)],
    via: '虚线框', border: getComputedStyle(best.e).borderTopStyle }; });

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '上传面板读透（不选真文件）+ 可灵主体库标签用选中态转移做判别式' });
  const out = {};

  const trace = []; out.trace = trace;
  const d0 = await enterDrawer(trace);
  out.enterDrawer = d0;
  must(d0.ok, '进「资产」抽屉失败（3 轮都没打开）', trace);
  // ⭐ BP2h/BP2h2 的第二个漏：进抽屉后**忘了切到「资产」标签页**，于是在「画布」页找「上传资产」。
  out.ariaAssetMgmt = await findAria('资产管理');
  console.log(`\n═══ aria-label="资产管理" 的全部命中（${out.ariaAssetMgmt.length}）═══`);
  out.ariaAssetMgmt.forEach((h, i) => console.log(`   ${i + 1}. ${JSON.stringify(h)}`));
  const tab = await cands('资产', 20);
  must(tab[0], '抽屉里找不到「资产」标签', trace);
  out.assetTab = tab[0];
  await page.mouse.click(tab[0].at[0], tab[0].at[1]); await page.waitForTimeout(2400);
  const onAssetTab = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const d = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
      return vis(e) && r.x < 40 && r.width > 250 && r.width < 380 && r.height > 300; })
      .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
    return (d?.innerText || '').replace(/\s+/g, ' ').trim(); });
  out.onAssetTab = onAssetTab;
  console.log(`  ⭐ 已切到「资产」页：${JSON.stringify(onAssetTab)}`);
  must(/资产/.test(onAssetTab) && /待分类资产|暂无资产/.test(onAssetTab), '没切到「资产」标签页', trace);
  // ── ① 打开上传面板
  const up = await openUpload(); out.uploadPanel = up;
  must(up.opened, '「创建 → 上传资产」没打开面板', trace);
  console.log(`═══ ① 「上传资产」面板（opened=${up.opened}）═══`);
  if (up.panel?.found) {
    console.log(`  rect=${JSON.stringify(up.panel.rect)}`);
    console.log(`  全文：${up.panel.text}`);
    console.log(`  面板内可交互件：`);
    (up.panel.items || []).filter((i) => i.t || i.aria).forEach((i) =>
      console.log(`    ${JSON.stringify(i.t || i.aria).padEnd(12)} at=${JSON.stringify(i.at)} rect=${JSON.stringify(i.rect)} disabled=${i.disabled} pe=${i.pe} op=${i.op} border=${i.border} svg=${i.svg}`));
  } else console.log(`  ⛔ 面板没开`);

  // ── ② ⭐ 点虚线框 → filechooser 归因
  console.log(`\n═══ ② 点虚线框「+」，filechooser 归因 ═══`);
  const dz = await dropZone(); out.dropZone = dz;
  console.log(`  虚线框：${JSON.stringify(dz)}`);
  console.log(`  ⚠️ suspicious=${dz?.suspicious ? '是（兜底抓到了整页，说明面板根本没开）' : '否'}`);
  must(dz && !dz.suspicious, '虚线框定位不可信（抓到整页）', trace);
  if (dz) {
    await page.evaluate(() => { window.__fc2 = [];
      document.addEventListener('click', (e) => { const t = e.target;
        if (t && t.tagName === 'INPUT' && t.type === 'file') window.__fc2.push({ accept: t.getAttribute('accept'), multiple: t.getAttribute('multiple') }); }, true); });
    const fcP = page.waitForEvent('filechooser', { timeout: 6000 }).catch(() => null);
    await page.mouse.click(dz.at[0], dz.at[1]);
    const fc = await fcP; await page.waitForTimeout(1200);
    const hits = await page.evaluate(() => window.__fc2);
    const acc = fc ? await fc.element().getAttribute('accept') : null;
    const mul = fc ? await fc.element().getAttribute('multiple') : null;
    const html = fc ? (await fc.element().evaluate((e) => e.outerHTML)).slice(0, 240) : null;
    out.dropZoneClick = { chooserFired: !!fc, accept: acc, multiple: mul, html, clickHits: hits };
    console.log(`  filechooser=${fc ? '✅ 弹了' : '❌ 没弹'}｜accept=${JSON.stringify(acc)}｜multiple=${JSON.stringify(mul)}`);
    console.log(`  html：${html}`);
    if (hits.length) console.log(`  捕获到的 file input：${JSON.stringify(hits)}`);
    if (fc) console.log(`  ⭐⭐ 归因确认：点虚线框弹出的 file input accept = ${JSON.stringify(acc)}`);
  }

  // ── ③ 两个下拉各列什么
  console.log(`\n═══ ③ 「请选择文件夹」/「请选择标签」下拉 ═══`);
  const dds = {};
  for (const label of ['请选择文件夹', '请选择标签']) {
    const base = await fingerprint(page);
    const c = await cands(label, 60);
    if (!c[0]) { console.log(`  【${label}】找不到`); dds[label] = { found: false }; continue; }
    await page.mouse.click(c[0].at[0], c[0].at[1]); await page.waitForTimeout(2000);
    const fresh = diffPanels(base, await fingerprint(page)).slice(0, 4)
      .map((p) => ({ area: p.area, all: p.all.slice(0, 200), buttons: p.buttons.slice(0, 12) }));
    dds[label] = { at: c[0].at, fresh };
    console.log(`  【${label}】@${JSON.stringify(c[0].at)} → 新增浮层 ${fresh.length}`);
    fresh.forEach((f, i) => console.log(`     ${i + 1}. area=${f.area} ${JSON.stringify(f.all)} 按钮=${JSON.stringify(f.buttons)}`));
    if (label === '请选择文件夹' && fresh.length) await shot(page, 'M-267-上传-选择文件夹下拉.png');
    await esc();
  }
  out.dropdowns = dds;

  // ── ④ 「保存」禁不禁用（空提交）
  console.log(`\n═══ ④ 空状态下「保存」的状态 ═══`);
  const save = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const b = [...document.querySelectorAll('button')].filter(vis).find((e) => (e.innerText || '').trim() === '保存');
    if (!b) return { found: false };
    const s = getComputedStyle(b);
    const r = b.getBoundingClientRect();
    return { found: true, disabledProp: b.disabled === true, ariaDisabled: b.getAttribute('aria-disabled'),
      pointerEvents: s.pointerEvents, opacity: s.opacity, color: s.color, bg: s.backgroundColor,
      cls: (b.className || '').toString().slice(0, 90),
      at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  console.log(`  ${JSON.stringify(save)}`);
  out.saveBtn = save;
  if (save.found) {
    await page.mouse.click(save.at[0], save.at[1]); await page.waitForTimeout(1800);
    const afterClick = await page.evaluate(() => {
      const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      return { toasts: [...document.querySelectorAll('div,span')].filter((e) => vis(e)
          && (e.innerText || '').trim().length > 0 && (e.innerText || '').trim().length < 40)
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
        .filter((t) => /请选择|不能为空|必填|请上传|至少/.test(t))
        .filter((v, i, a) => a.indexOf(v) === i).slice(0, 8) }; });
    console.log(`  ⭐ 空提交后的校验提示：${JSON.stringify(afterClick.toasts)}`);
    out.emptySubmit = afterClick;
  }
  await esc(); await esc();

  // ── ⑤ ⭐ 可灵主体库标签：改用「选中态转移」做判别式
  console.log(`\n═══ ⑤ 可灵主体库 6 个标签（判别式＝选中态 bg 有没有转移）═══`);
  const t5 = await enterDrawer(trace);
  must(t5.ok, '第 ⑤ 段进抽屉失败', trace);
  await clickAria('资产管理', 2600, 340); // preferX=340 → 优先点抽屉里那个「管理」
  const lib = await cands('可灵主体库', 40);
  must(lib[0], '弹窗里找不到侧栏「可灵主体库」', trace);
  if (lib[0]) { await page.mouse.click(lib[0].at[0], lib[0].at[1]); await page.waitForTimeout(2200); }
  const readTabs = () => page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const t = [...document.querySelectorAll('div,h1,h2,span')].find((e) => (e.innerText || '').trim() === '资产管理' && vis(e));
    if (!t) return null;
    let root = t; for (let i = 0; i < 8 && root.parentElement; i++) { root = root.parentElement;
      const r = root.getBoundingClientRect(); if (r.width > 500 && r.height > 350) break; }
    const rr = root.getBoundingClientRect();
    return { text: (root.innerText || '').replace(/\s+/g, ' ').trim(),
      tabs: [...root.querySelectorAll('div,button,li,span')].filter((e) => { const r = e.getBoundingClientRect();
          return vis(e) && e.children.length === 0 && r.height >= 24 && r.height <= 44 && r.width >= 28 && r.width <= 120
            && r.y > rr.y + 40 && r.y < rr.y + 210; })
        .map((e) => ({ t: (e.innerText || '').trim(), bg: getComputedStyle(e).backgroundColor,
          at: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; })() }))
        .filter((x) => x.t).filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.at[1] === v.at[1]) === i) }; });
  const t0 = await readTabs();
  console.log(`  初始标签：${JSON.stringify(t0?.tabs)}`);
  const sel = (ts) => (ts || []).filter((x) => !/rgba\(0, 0, 0, 0\)|transparent/.test(x.bg)).map((x) => x.t);
  console.log(`  ⭐ 初始选中：${JSON.stringify(sel(t0?.tabs))}`);
  const probes = [];
  if (t0?.tabs?.length) {
    for (const t of t0.tabs) {
      await page.mouse.click(t.at[0], t.at[1]); await page.waitForTimeout(1600);
      const now = await readTabs();
      const pickedNow = sel(now?.tabs);
      probes.push({ clicked: t.t, pickedAfter: pickedNow, bodyChanged: now?.text !== t0?.text });
      console.log(`   点「${t.t}」→ 选中变成 ${JSON.stringify(pickedNow)} ${pickedNow.length === 1 ? '✅ 转移了' : '❌ 没转移'}`);
    }
  }
  out.klingTabs = { initial: t0?.tabs, initialPicked: sel(t0?.tabs), probes };
  const moved = probes.filter((p) => p.pickedAfter.length === 1 && p.pickedAfter[0] === p.clicked);
  out.klingTabs.movedCount = moved.length;
  out.klingTabs.total = probes.length;
  // ⭐⭐ 空集陷阱：`moved.length >= probes.length - 1` 在 probes 为空时**恒为真**，
  //    于是「一个都没点」也能打出「✅ 标签是真的」（BP2h 就这么误报过一次）。
  //    判「是否全部满足」之前，**必须先确认集合非空**。
  out.klingTabs.VERDICT = probes.length === 0
    ? '⛔ 无效：标签一个都没读到（0 候选），本轮结论作废'
    : (moved.length === probes.length
      ? `✅ ${moved.length}/${probes.length} 个标签点击后选中态都转移到了自己`
      : `⚠️ 只转移了 ${moved.length}/${probes.length} 个`);
  console.log(`  ⭐⭐ ${out.klingTabs.VERDICT}`);
  await shot(page, 'M-264-可灵主体库-标签筛选.png');
  await esc();

  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.final = { nodes: finalN };
  console.log(`\n═══ 收尾：节点 ${finalN}；本轮未选真文件、未提交、未建主体 ═══`);

  await logStep(B, {
    id: 'BP2i-upload-panel-and-kling-tabs',
    title: '⭐⭐ 上传资产支持 jpg/jpeg/png・mp4・mp3，单个 ≤20MB —— 界面自己写着；标签用选中态转移判定',
    target: 'M-263 一张图就答掉了挂了好几批的 📖「上传资产支持哪些格式」：面板底部写着'
      + '`支持的文件格式 🖼 jpg/jpeg/png ▶ mp4 🔊 mp3` 和 `单个文件大小不超过 20MB`，'
      + '而 BP1 从 DOM 读到的 `accept=".jpg,.jpeg,.png,.mp4,.mp3"` 与这行字逐字吻合 —— '
      + '两个互相独立的来源对上了。**不必再纠结哪个 file input 属于上传，界面自己写着答案。**'
      + '本轮：① 点左侧虚线框 `+` 把 filechooser 真正归因到它；② 读「请选择文件夹 / 请选择标签」两个下拉；'
      + '③ 读空状态下「保存」是否禁用（`disabled` / `pointer-events` / 颜色，而不是只看点了没反应）；'
      + '④ ⭐ BP2g 用「正文是否变」做判别式得到「6 个标签 1 种正文」，**但那个库是空的**（正文只有「创建主体」）—— '
      + '**判别式失效 ≠ 标签无效**；本轮改用「点击后回读每个标签自己的 backgroundColor，看选中态有没有转移」。'
      + '⛔ 不选真文件、不提交表单、不建主体、不传任何东西。',
    evidence: out,
    visible_text: JSON.stringify({
      面板全文: out.uploadPanel?.panel?.text,
      面板件: out.uploadPanel?.panel?.items?.filter((i) => i.t || i.aria)
        ?.slice(0, 14).map((i) => `${i.t || i.aria}@${JSON.stringify(i.at)}`),
      虚线框: out.dropZone,
      点虚线框: out.dropZoneClick,
      文件夹下拉: out.dropdowns?.['请选择文件夹']?.fresh?.map((f) => ({ all: f.all, buttons: f.buttons })),
      标签下拉: out.dropdowns?.['请选择标签']?.fresh?.map((f) => ({ all: f.all, buttons: f.buttons })),
      保存按钮状态: out.saveBtn, 空提交校验: out.emptySubmit,
      可灵主体库标签初值: out.klingTabs?.initial, 初始选中: out.klingTabs?.initialPicked,
      逐标签选中态: out.klingTabs?.probes?.map((p) => `${p.clicked}→${JSON.stringify(p.pickedAfter)}`),
      抽屉轨迹: out.trace, 进抽屉结果: out.enterDrawer,
      管理按钮全部命中: out.ariaAssetMgmt, 资产页正文: out.onAssetTab,
      标签判定: out.klingTabs?.VERDICT, 收尾: out.final }).slice(0, 3600),
    shot: 'M-263-点上传资产之后.png',
  });
  console.log('\nBP2h 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

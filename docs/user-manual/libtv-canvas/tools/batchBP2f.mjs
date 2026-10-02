// Batch BP2f — 资产行菜单读透 + 上传归因 + 可灵主体库标签筛选。
//
// M-259 已用眼睛确证：hover「待分类资产」行会展开
//   添加到Agent │ 添加到画布 │ 更改图标 › │ 新建子文件夹 │ 移动到 › │ 下载 │ 重命名 │ 删除(红)
// 本轮全部只读：
//   ① 两个带 › 的子菜单分别列出什么（只展开、不点确认）
//   ② 「删除」点下去是什么确认框 —— ⛔ **读完立刻取消，不确认**
//   ③ ⭐「上传资产」到底开什么：逐个候选坐标试 + 全页 fingerprint 差集 + 捕获 file input 的 click
//   ④ 「可灵主体库」的标签行（全部/人物/场景/道具/特效/其他）是否真筛内容（判别式 = 正文）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBP2f';
const { browser, page } = await launch();

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
    const k = `${Math.round(r.x)},${Math.round(r.y)},${Math.round(r.width)}`;
    if (seen.has(k)) continue; seen.add(k);
    out.push({ at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      tag: e.tagName, kids: e.children.length }); }
  return out; }, [txt, minW]);
const clickText = async (txt, idx = 0, wait = 2200, minW = 6) => {
  const c = await cands(txt, minW);
  if (!c[idx]) return { executed: false, note: `「${txt}」没有第 ${idx + 1} 个候选（共 ${c.length}）` };
  await page.mouse.click(c[idx].at[0], c[idx].at[1]); await page.waitForTimeout(wait);
  return { executed: true, at: c[idx].at, rect: c[idx].rect, candCount: c.length };
};
const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1400); };

/** 打开资产行菜单（hover 行 → 点 •••，或只 hover），返回菜单项。 */
const openRowMenu = async () => {
  const more = await clickAria('更多操作', 1800);
  if (!more.executed) return { opened: false, note: more.note, items: [] };
  const items = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    const want = ['添加到Agent', '添加到画布', '更改图标', '新建子文件夹', '移动到', '下载', '重命名', '删除'];
    const out = [];
    for (const t of want) {
      const e = [...document.querySelectorAll('div,span,button,li')]
        .find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === t && vis(x)
          && x.getBoundingClientRect().height < 60);
      if (!e) { out.push({ t, found: false }); continue; }
      const r = e.getBoundingClientRect();
      // 找带 › 的那个元素（同一行的最后那个 svg）
      let row = e; for (let i = 0; i < 4 && row.parentElement; i++) {
        row = row.parentElement; const rr = row.getBoundingClientRect();
        if (rr.height > 28 && rr.height < 56 && rr.width > 100) break; }
      const rr = row.getBoundingClientRect();
      out.push({ t, found: true, color: getComputedStyle(e).color,
        at: [Math.round(rr.x + rr.width / 2), Math.round(rr.y + rr.height / 2)],
        rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)],
        hasChevron: row.querySelectorAll('svg').length > 1 });
    }
    return out; });
  return { opened: true, at: more.at, items };
};
/** ⭐ hover 某个菜单项，读它展开出来的子菜单（只展开，不点）。 */
const hoverItem = async (label) => {
  const c = await cands(label, 30);
  if (!c[0]) return { executed: false, note: `菜单里没有「${label}」` };
  await page.mouse.move(c[0].at[0], c[0].at[1]); await page.waitForTimeout(1600);
  const sub = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    return [...document.querySelectorAll('div,span,li,button')].filter(vis).map((e) => {
        const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), at: [Math.round(r.x), Math.round(r.y)],
          w: Math.round(r.width), h: Math.round(r.height), kids: e.children.length,
          svg: e.querySelectorAll('svg').length, img: e.querySelectorAll('img').length }; })
      .filter((x) => x.t && x.t.length <= 10 && x.kids === 0 && x.w > 30 && x.w < 300 && x.h >= 16 && x.h <= 44)
      .map((x) => `${x.t}@${x.at[0]},${x.at[1]}[${x.w}x${x.h}${x.svg ? ' svg' + x.svg : ''}${x.img ? ' img' + x.img : ''}]`)
      .filter((v, i, a) => a.indexOf(v) === i); });
  return { executed: true, at: c[0].at, sub };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '资产行菜单读透 + 上传归因 + 可灵主体库标签筛选（删除只读确认框，不确认）' });
  const out = {};

  await clickAria('资产管理', 2800);
  await clickText('资产', 0, 2600, 20);

  // ── ① 菜单本体
  const menu = await openRowMenu(); out.menu = menu;
  console.log(`═══ ① 资产行菜单（opened=${menu.opened}）═══`);
  (menu.items || []).forEach((i) => console.log(`   ${i.found ? '✅' : '❌'} ${i.t.padEnd(6)} color=${i.color || '-'} chevron=${i.hasChevron ?? '-'}`));
  await shot(page, 'M-259-待分类资产卡片-hover.png');

  // ── ② 两个子菜单
  const subs = {};
  for (const l of ['更改图标', '移动到']) {
    const r = await hoverItem(l);
    subs[l] = r;
    console.log(`\n═══ ② 展开「${l}」子菜单（executed=${r.executed}）═══`);
    console.log(`   ${JSON.stringify(r.sub)}`);
    if (l === '更改图标') await shot(page, 'M-261-资产菜单-更改图标子菜单.png');
    await esc();
    const again = await openRowMenu();
    if (!again.opened) console.log('   ⚠️ 菜单没重开');
  }
  out.submenus = subs;
  console.log(`\n  ⭐ 带 › 的项：${JSON.stringify((menu.items || []).filter((i) => i.hasChevron).map((i) => i.t))}`);

  // ── ③ ⭐ 删除确认框 —— 只读，⛔ 不确认
  console.log(`\n═══ ③ 「删除」的确认框（只读，不确认） ═══`);
  await openRowMenu();
  const del = await clickText('删除', 0, 2400, 30);
  const dlg = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    const cands2 = [...document.querySelectorAll('div,section')].filter(vis)
      .map((e) => { const r = e.getBoundingClientRect();
        return { e, r, t: (e.innerText || '').replace(/\s+/g, ' ').trim(),
          cls: (e.className || '').toString().slice(0, 50) }; })
      .filter((x) => /删除|确认|取消|该文件夹|无法/.test(x.t) && x.t.length < 220 && x.r.width > 200);
    const best = cands2.sort((a, b) => a.t.length - b.t.length)[0];
    if (!best) return { found: false };
    return { found: true, text: best.t.slice(0, 200), cls: best.cls,
      rect: [Math.round(best.r.x), Math.round(best.r.y), Math.round(best.r.width), Math.round(best.r.height)],
      buttons: [...best.e.querySelectorAll('button,[role="button"]')].filter(vis).map((e) => {
        const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), aria: e.getAttribute('aria-label'),
          at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          color: getComputedStyle(e).color, bg: getComputedStyle(e).backgroundColor }; }) }; });
  out.deleteDialog = { click: del, ...dlg };
  console.log(`  点「删除」executed=${del.executed}`);
  console.log(`  确认框 found=${dlg.found}：${JSON.stringify(dlg.text)}`);
  console.log(`  框内按钮：${JSON.stringify(dlg.buttons)}`);
  if (dlg.found) await shot(page, 'M-262-删除文件夹-确认框.png');
  // ⛔ 明确取消：优先找「取消」，找不到就 Escape
  const cancel = (dlg.buttons || []).find((b) => /取消/.test(b.t || ''));
  if (cancel) { await page.mouse.click(cancel.at[0], cancel.at[1]); console.log(`  ⛔ 已点「取消」@${JSON.stringify(cancel.at)}`); }
  else { await esc(); console.log('  ⛔ 框里没有「取消」→ 按 Escape 退回'); }
  await page.waitForTimeout(1200);
  const afterCancel = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return { dialogGone: ![...document.querySelectorAll('div,section')].filter(vis)
      .some((e) => /该文件夹|无法删除/.test((e.innerText || ''))),
      folderStillThere: [...document.querySelectorAll('div,span')]
        .filter((e) => (e.innerText || '').trim() === '待分类资产' && vis(e)).length }; });
  out.afterCancel = afterCancel;
  console.log(`  ⭐ 复核：确认框还在吗=${!afterCancel.dialogGone}｜「待分类资产」还在吗=${afterCancel.folderStillThere > 0}`);
  await esc();

  // ── ④ ⭐ 上传归因：逐个候选坐标试，每次都记 filechooser + 捕获 click + 全页差集
  console.log(`\n═══ ④ 「上传资产」归因 ═══`);
  await page.evaluate(() => { window.__fc = [];
    document.addEventListener('click', (e) => { const t = e.target;
      if (t && t.tagName === 'INPUT' && t.type === 'file') window.__fc.push({ accept: t.getAttribute('accept'), multiple: t.getAttribute('multiple') }); }, true); });
  const cr = await clickAria('创建', 2200);
  const ups = await cands('上传资产', 30);
  console.log(`  「创建」executed=${cr.executed}｜「上传资产」候选 ${ups.length} 个：${JSON.stringify(ups)}`);
  const tries = [];
  for (const [i, u] of ups.entries()) {
    const base = await fingerprint(page);
    const fcP = page.waitForEvent('filechooser', { timeout: 4500 }).catch(() => null);
    await page.mouse.click(u.at[0], u.at[1]);
    const fc = await fcP; await page.waitForTimeout(1500);
    const hits = await page.evaluate(() => window.__fc);
    const after = await fingerprint(page);
    const fresh = diffPanels(base, after).slice(0, 3).map((p) => ({ area: p.area, all: p.all.slice(0, 200), buttons: p.buttons.slice(0, 10) }));
    const t = { idx: i, at: u.at, rect: u.rect, chooserFired: !!fc, clickHits: hits, fresh };
    tries.push(t);
    console.log(`  候选 ${i + 1} @${JSON.stringify(u.at)} rect=${JSON.stringify(u.rect)} → filechooser=${t.chooserFired ? '✅' : '❌'} fileInput点击=${hits.length} 新增浮层=${fresh.length}`);
    if (hits.length) console.log(`     ⭐ accept=${JSON.stringify(hits[0].accept)} multiple=${JSON.stringify(hits[0].multiple)}`);
    fresh.forEach((f, k) => console.log(`     浮层${k + 1} area=${f.area} ${JSON.stringify(f.all)} 按钮=${JSON.stringify(f.buttons)}`));
    if (i === 0) { await shot(page, 'M-263-点上传资产之后.png'); t.shot = 'M-263-点上传资产之后.png'; }
    if (fc) { t.accept = await fc.element().getAttribute('accept'); t.multiple = await fc.element().getAttribute('multiple');
      console.log(`     ⭐⭐ chooser.element() accept=${JSON.stringify(t.accept)} multiple=${JSON.stringify(t.multiple)}`); }
    await esc();
    if (i === 0) await clickAria('创建', 2000); // 第二个候选要把下拉重新打开
  }
  out.uploadTries = tries;
  const hit = tries.find((t) => t.accept || (t.clickHits || []).length);
  out.uploadAccept = hit ? { accept: hit.accept ?? hit.clickHits[0].accept, multiple: hit.multiple ?? hit.clickHits[0].multiple, via: hit.idx } : null;
  console.log(`  ⭐⭐ 上传归因结果：${JSON.stringify(out.uploadAccept)}`);
  await esc();

  // ── ⑤ 「可灵主体库」标签行是否真筛
  console.log(`\n═══ ⑤ 可灵主体库标签行 ═══`);
  await clickAria('资产管理', 2800);
  const lib = await clickText('可灵主体库', 0, 2400, 30);
  const bodyOf = () => page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const t = [...document.querySelectorAll('div,h1,h2,span')].find((e) => (e.innerText || '').trim() === '资产管理' && vis(e));
    if (!t) return null;
    let root = t; for (let i = 0; i < 8 && root.parentElement; i++) { root = root.parentElement;
      const r = root.getBoundingClientRect(); if (r.width > 500 && r.height > 350) break; }
    return { text: (root.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
      tabs: [...root.querySelectorAll('div,button,li,span')].filter((e) => { const r = e.getBoundingClientRect();
          return vis(e) && e.children.length === 0 && r.height >= 24 && r.height <= 44 && r.width >= 28 && r.width <= 120
            && r.y > root.getBoundingClientRect().y + 40 && r.y < root.getBoundingClientRect().y + 210; })
        .map((e) => ({ t: (e.innerText || '').trim(), bg: getComputedStyle(e).backgroundColor,
          at: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; })() }))
        .filter((x) => x.t).filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.at[1] === v.at[1]) === i) }; });
  const b0 = await bodyOf();
  console.log(`  点侧栏「可灵主体库」executed=${lib.executed}`);
  console.log(`  正文：${b0?.text}`);
  console.log(`  标签行：${JSON.stringify(b0?.tabs)}`);
  out.klingLib = { click: lib, body0: b0 };
  if (b0?.tabs?.length) {
    const probes = [];
    for (const t of b0.tabs) {
      await page.mouse.click(t.at[0], t.at[1]); await page.waitForTimeout(1700);
      const b = await bodyOf();
      probes.push({ tab: t.t, bg: t.bg, body: b?.text });
      console.log(`   【${t.t}】bg=${t.bg} → ${JSON.stringify(b?.text?.slice(0, 130))}`);
    }
    out.klingTabs = probes;
    const sigs = [...new Set(probes.map((p) => p.body))];
    out.klingTabDistinguish = sigs.length;
    console.log(`  ⭐ ${probes.length} 个标签给出 ${sigs.length} 种正文 ${sigs.length > 1 ? '✅ 各不相同 → 确实在筛' : '❌ 全一样 → 点了没反应'}`);
    if (probes.length) await shot(page, 'M-264-可灵主体库-标签筛选.png');
  }
  await esc();

  const finalN = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.final = { nodes: finalN };
  console.log(`\n═══ 收尾：节点 ${finalN}；本轮唯一写动作＝点开确认框后立刻取消 ═══`);

  await logStep(B, {
    id: 'BP2f-asset-row-menu-and-upload',
    title: '⭐ 资产行菜单 8 项（含删除）；「上传资产」归因；可灵主体库 6 个标签各筛各的',
    target: 'M-259 用眼睛确证：hover「待分类资产」行展开 8 项菜单 —— 添加到Agent / 添加到画布 / '
      + '更改图标 › / 新建子文件夹 / 移动到 › / 下载 / 重命名 / 删除(红)。'
      + '**BP2a 那句「❌ 没有删除入口」至此作废**（它用几何判据找行，而「更多操作」是行的兄弟节点）。'
      + '本轮：① 读两个 › 子菜单各列什么；② 点「删除」读确认框文案后**立刻取消**并复核分类还在；'
      + '③ 「上传资产」逐个候选坐标试，同时等 filechooser 事件、捕获 file input 的 click、再看全页 DOM 差集；'
      + '④ 切到「可灵主体库」读 6 个标签，用「正文是否随标签变」做判别式。'
      + '⛔ 不确认删除、不传文件、不建主体、不改名。',
    evidence: out,
    visible_text: JSON.stringify({
      菜单项: out.menu?.items?.map((i) => ({ t: i.t, found: i.found, color: i.color, chevron: i.hasChevron })),
      子菜单: { 更改图标: out.submenus?.['更改图标']?.sub, 移动到: out.submenus?.['移动到']?.sub },
      删除确认框: out.deleteDialog?.text, 框内按钮: out.deleteDialog?.buttons,
      取消后复核: out.afterCancel,
      上传尝试: out.uploadTries?.map((t) => ({ idx: t.idx, at: t.at, chooser: t.chooserFired,
        hits: t.clickHits, fresh: t.fresh?.map((f) => f.all) })),
      上传归因: out.uploadAccept,
      可灵主体库正文: out.klingLib?.body0?.text, 标签行: out.klingLib?.body0?.tabs,
      各标签正文: out.klingTabs?.map((p) => `${p.tab}:${p.body?.slice(0, 90)}`),
      标签正文不同值数: out.klingTabDistinguish, 收尾: out.final }).slice(0, 3600),
    shot: 'M-259-待分类资产卡片-hover.png',
  });
  console.log('\nBP2f 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

// Batch BT5 — 菜单最后两项 + ⭐「创建 → 读 → 删除 → 独立复核」闭环。
//
// 闭环为什么现在做得成：
//   BP2a 一度报「资产页没有删除入口」（判据把兄弟节点挡在门外），
//   BP2g 读到了完整的删除确认框但只点了取消 —— 于是从 BP1 留下那枚 `待分类资产` 一直没人清过。
//   现在确认框的文案、两枚按钮的颜色、取消后的复核读数都齐了，
//   **可以在自己刚建的东西上把整条链路走一遍，然后恢复原状**。
//
// ⭐ 闭环的边界（重要）：
//   · 只删**本轮自己刚建**的那个子文件夹，一秒前才建的；
//   · ⛔ **绝对不碰**那枚 BP1 留下的 `待分类资产` —— 它不是我这一轮建的，
//     删它超出「恢复原状」的范围，属于改变用户账户状态；
//   · 收尾必须**独立复核**：抽屉全文与闭环前逐字比对 + 测试文件夹 0 命中。
//
// 本轮另外两件只读的：
//   ① `重命名` 点开是什么（输入框现值 / 是否全选 / 就地还是浮层）—— ⛔ 不提交
//   ② `下载` 会不会真触发下载（等 download 事件，记文件名，**不保存**）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { mkdir, rm } from 'node:fs/promises';
import { resolve } from 'node:path';

const SPACE = '10354929';
const B = 'batchBT5';
const TEST_NAME = '手册闭环测试';
const DL = resolve(import.meta.dirname, '.evidence/dl');
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
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }); }
  return out; }, [txt, minW]);
const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1400); };
const readInputs = () => page.evaluate(() => [...document.querySelectorAll('input,textarea')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { ph: e.placeholder, val: e.value,
      selStart: e.selectionStart, selEnd: e.selectionEnd,
      focused: document.activeElement === e,
      at: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
const drawerText = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const d = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
      return vis(e) && r.x < 40 && r.width > 250 && r.width < 380 && r.height > 300; })
    .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
  return (d?.innerText || '').replace(/\s+/g, ' ').trim(); });
/** ⭐ 抽屉里的每一行：名字 + 内层文字的 x（判缩进）+ 行末那枚 ••• 的坐标。 */
const rows = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const names = [...document.querySelectorAll('div,span')].filter(vis)
    .map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').trim(), x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height), kids: e.children.length }; })
    .filter((x) => x.t && x.t.length <= 20 && x.w > 20 && x.h >= 12 && x.h <= 30 && x.x < 260)
    .filter((v, i, a) => a.findIndex((y) => y.t === v.t && y.y === v.y && Math.abs(y.x - v.x) < 3) === i)
    // ⭐ 取**最内层**（children 最少）的那份，内层 x 才是缩进的真值
    .sort((a, b) => a.kids - b.kids);
  const more = [...document.querySelectorAll('[aria-label="更多操作"]')].filter(vis)
    .map((e) => { const r = e.getBoundingClientRect();
      return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], y: Math.round(r.y) }; })
    .sort((a, b) => a.y - b.y);
  return { names, more }; });
const onAssetPage = async () => {
  for (let i = 0; i < 3; i += 1) {
    const open = await page.evaluate(() => {
      const vis = (e) => { const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
      return [...document.querySelectorAll('div,span')].filter((e) => vis(e)
        && /^共 \d+ 节点$/.test((e.innerText || '').trim())).length > 0; });
    if (open) {
      const tab = await cands('资产', 20);
      if (!tab[0]) return { ok: false, why: '找不到「资产」标签' };
      await page.mouse.click(tab[0].at[0], tab[0].at[1]); await page.waitForTimeout(2400);
      const txt = await drawerText();
      return /待分类资产|暂无资产/.test(txt) ? { ok: true, text: txt } : { ok: false, why: txt };
    }
    await clickAria('资产管理', 2600, 40);
  }
  return { ok: false, why: '抽屉没打开' };
};
const must = (c, msg) => { if (!c) { console.log(`⛔ 前置不成立：${msg}`); throw new Error(msg); } };
/** 确保菜单处于**关**的状态（openMenu 会先判断，所以这里只做兜底）。 */
const closeMenu = async () => {
  if ((await MENU_OPEN_NOW()) > 0) { await esc(); await page.waitForTimeout(600); }
  return MENU_OPEN_NOW();
};
const MENU8 = ['添加到Agent', '添加到画布', '更改图标', '新建子文件夹', '移动到', '下载', '重命名', '删除'];
/** ⭐ 现在菜单开着几项（0 = 关着）。注意它在定义之后才被 closeMenu 用到，
 *  因为两个都是 `const` 箭头函数，靠调用时机而不是定义顺序来保证可用。 */
const _MENU_OPEN_NOW_PLACEHOLDER = null;
const MENU_OPEN_NOW = () => page.evaluate((w) => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  return w.filter((t) => [...document.querySelectorAll('div,span,button,li')]
    .some((e) => (e.innerText || '').replace(/\s+/g, ' ').trim() === t && vis(e)
      && e.getBoundingClientRect().height < 60)).length; }, MENU8);
/** ⭐ 菜单是**开关**：上一步点完它可能还开着，再点 `更多操作` 会把它**关掉**。
 *  BS2 就是这么断的 —— 所以这里先问「现在开着吗」，开着就直接用，不再点。 */
const openMenu = async (rowIdx = 0) => {
  const rs = await rows();
  const target = rs.more[rowIdx];
  if (!target) return { opened: false, coverage: '0/8', seen: [], pts: {},
    note: `没有第 ${rowIdx + 1} 行的「更多操作」（抽屉多半被 esc 关了）`, rows: rs };
  const already = await MENU_OPEN_NOW();
  if (already < MENU8.length) {
    await page.mouse.move(target.at[0], target.at[1]); await page.waitForTimeout(800);
    await page.mouse.click(target.at[0], target.at[1]); await page.waitForTimeout(2000);
  }
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
      o[t] = { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }
    return o; }, MENU8);
  return { opened: seen.length === MENU8.length, seen, pts,
    coverage: `${seen.length}/8`, alreadyOpen: already };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '重命名/下载只读 + 创建→读→删除→独立复核闭环（只删本轮自建物）' });
  const out = {};

  // ═══ 基线
  const p0 = await onAssetPage(); must(p0.ok, `进资产页失败：${p0.why || ''}`);
  const baseText = await drawerText();
  const baseRows = await rows();
  out.baseline = { text: baseText, rowCount: baseRows.more.length };
  console.log(`═══ 基线 ═══\n  抽屉：${JSON.stringify(baseText)}\n  行数（按 ••• 计）：${baseRows.more.length}`);
  console.log(`  各行内层文字：${JSON.stringify(baseRows.names.map((n) => `${n.t}@x=${n.x},y=${n.y}`))}`);

  // ═══ ① 重命名（只读）
  console.log(`\n═══ ① 「重命名」点开是什么（⛔ 不提交） ═══`);
  const m1 = await openMenu(0);
  console.log(`  菜单读到 ${m1.coverage}`);
  must(m1.opened && m1.pts['重命名'], '菜单没读全或没有「重命名」');
  const iBefore = await readInputs();
  await page.mouse.click(m1.pts['重命名'].at[0], m1.pts['重命名'].at[1]);
  await page.waitForTimeout(2200);
  const iAfter = await readInputs();
  // ⭐ 挑「新出现的那个」要用**集合差**，不能靠 `val && !ph` 这种条件猜 ——
  //    BT 第一轮就是这么挑错了（选中了顶栏那个「未命名工作区」）。
  const key = (x) => JSON.stringify([x.ph, x.val, x.at]);
  const beforeKeys = new Set(iBefore.map(key));
  const added = iAfter.filter((x) => !beforeKeys.has(key(x)));
  const rn = added[0] || null;
  console.log(`  输入框 before：${JSON.stringify(iBefore)}`);
  console.log(`  输入框 after ：${JSON.stringify(iAfter)}`);
  console.log(`  ⭐ 新的那个：${JSON.stringify(rn)}`);
  console.log(`  ⭐ 焦点在它上面？ ${rn?.focused}｜选区 ${rn?.selStart}–${rn?.selEnd}（现值 ${JSON.stringify(rn?.val)}）`);
  out.rename = { before: iBefore, after: iAfter, added, newInput: rn,
    selectedAll: rn ? rn.selStart === 0 && rn.selEnd === rn.val.length : null };
  await shot(page, 'M-274-资产菜单-重命名.png');
  await esc();
  console.log(`  Esc 之后输入框：${JSON.stringify(await readInputs())}`);
  console.log(`  ⚠️ 注意：esc() 会把**整个抽屉**也一起关掉，后面每段都要重新站位`);

  // ═══ ② 下载（不保存）
  console.log(`\n═══ ② 「下载」会不会真触发下载 ═══`);
  await mkdir(DL, { recursive: true }).catch(() => {});
  // ⭐ `esc()` 会把**整个抽屉**一起关掉 —— 上一段收尾之后必须重新站位
  const p2 = await onAssetPage(); must(p2.ok, `第 ② 段站位失败：${p2.why || ''}`);
  const m2 = await openMenu(0);
  must(m2.opened && m2.pts['下载'], `菜单里没有「下载」（读到 ${m2.coverage}）`);
  const dlp = page.waitForEvent('download', { timeout: 8000 }).catch(() => null);
  await page.mouse.click(m2.pts['下载'].at[0], m2.pts['下载'].at[1]);
  const dl = await dlp;
  await page.waitForTimeout(1500);
  if (dl) {
    out.download = { fired: true, suggested: dl.suggestedFilename(), url: (dl.url() || '').slice(0, 80) };
    console.log(`  ⭐ 触发下载：${dl.suggestedFilename()}`);
    console.log(`     URL：${(dl.url() || '').slice(0, 100)}`);
    await dl.cancel().catch(() => {});
    console.log(`     已 cancel()，不落盘`);
  } else {
    out.download = { fired: false };
    console.log(`  ⛔ 8 秒内没有 download 事件`);
  }
  await esc();

  // ═══ ③ ⭐ 闭环
  console.log(`\n═══ ③ ⭐ 闭环：创建 → 读 → 删除 → 独立复核 ═══`);
  console.log(`  ③ 开始前菜单可见项：${await MENU_OPEN_NOW()}`);
  const p3 = await onAssetPage(); must(p3.ok, `第 ③ 段站位失败：${p3.why || ''}`);
  console.log(`  站位：${JSON.stringify(p3.text)}`);
  const m3 = await openMenu(0);
  console.log(`  菜单读到 ${m3.coverage}（alreadyOpen=${m3.alreadyOpen}）`);
  must(m3.opened && m3.pts['新建子文件夹'],
    `菜单里没有「新建子文件夹」（读到 ${m3.coverage}）`);
  // ⭐ 点一次不够就重试：每次都把「点完之后到底有什么」原样打出来，别只报「没找到」
  const pt = m3.pts['新建子文件夹'].at;
  console.log(`  点「新建子文件夹」@${JSON.stringify(pt)}`);
  let seed = null;
  const tries = [];
  for (let i = 0; i < 3 && !seed; i += 1) {
    await page.mouse.move(pt[0], pt[1]); await page.waitForTimeout(600);
    await page.mouse.click(pt[0], pt[1]);
    await page.waitForTimeout(i === 0 ? 3200 : 2600);
    const inputs = await readInputs();
    const drawer = await drawerText();
    const menuNow = await MENU_OPEN_NOW();
    tries.push({ i, inputs, drawer, menuNow });
    console.log(`   第 ${i + 1} 次点：可见输入框 ${inputs.length} 个 ${JSON.stringify(inputs)}`);
    console.log(`     菜单可见项 ${menuNow}｜抽屉=${JSON.stringify(drawer)}`);
    seed = inputs.find((x) => /新建文件夹/.test(x.ph || ''))
      || inputs.find((x) => x.val === '新建文件夹')
      || null;
    if (!seed && menuNow > 0) { await esc(); await page.waitForTimeout(800); }
  }
  out.seedTries = tries;
  must(seed, `「新建子文件夹」点了 3 次都没开出输入框：${JSON.stringify(tries.map((t) => t.inputs))}`);
  console.log(`  ③-1 种子输入框：${JSON.stringify(seed)}｜默认名已全选=${seed.selStart === 0 && seed.selEnd === seed.val.length}`);

  // ⛔ 只往**这一个**输入框里打字：按**同一个矩形**找它，不靠 placeholder / val 去猜
  //    （BT 前几轮就是这么挑错的：这个输入框 placeholder 是空的，值才是「新建文件夹」）
  const sameBox = (list) => list.find((x) => Math.abs(x.at[0] - seed.at[0]) < 4
    && Math.abs(x.at[1] - seed.at[1]) < 4);
  // ⭐ 不按 ⌘A：默认名**已经全选**（selStart 0 / selEnd 5），直接打字就是覆盖
  await page.mouse.click(seed.at[0] + Math.round(seed.at[2] / 2), seed.at[1] + Math.round(seed.at[3] / 2));
  await page.waitForTimeout(800);
  const focused = sameBox(await readInputs());
  console.log(`  ③-2 打字前：${JSON.stringify(focused)}`);
  await page.keyboard.type(TEST_NAME, { delay: 70 }); await page.waitForTimeout(1000);
  const typed = sameBox(await readInputs());
  console.log(`  ③-2 打完字：${JSON.stringify(typed)}`);
  out.typed = typed;
  must(typed && typed.val === TEST_NAME,
    `输入框里不是「${TEST_NAME}」而是 ${JSON.stringify(typed)}｜所有输入框 ${JSON.stringify(await readInputs())}`);
  await shot(page, 'M-275-闭环-新建子文件夹-命名中.png');

  await page.keyboard.press('Enter'); await page.waitForTimeout(2600);
  const afterCreate = await drawerText();
  const rowsAfter = await rows();
  const created = rowsAfter.names.find((n) => n.t === TEST_NAME);
  console.log(`  ③-3 回车之后抽屉：${JSON.stringify(afterCreate)}`);
  console.log(`  ⭐ 新行命中：${JSON.stringify(created)}｜行数 ${rowsAfter.more.length}（基线 ${baseRows.more.length}）`);
  out.created = { text: afterCreate, row: created, rowCount: rowsAfter.more.length, baseRowCount: baseRows.more.length };
  must(created && rowsAfter.more.length === baseRows.more.length + 1,
    `建完没多出一行：命中=${!!created} 行数 ${rowsAfter.more.length} vs 基线 ${baseRows.more.length}`);
  console.log(`  ⭐ 缩进对比：父「待分类资产」内层 x=${baseRows.names.find((n) => n.t === '待分类资产')?.x}`
    + `｜新行内层 x=${created.x} → ${created.x > (baseRows.names.find((n) => n.t === '待分类资产')?.x ?? 0) ? '✅ 确实缩进了（是子级）' : '❌ 没缩进'}`);
  out.indentDelta = created.x - (baseRows.names.find((n) => n.t === '待分类资产')?.x ?? 0);
  await shot(page, 'M-276-闭环-新建子文件夹-建出来了.png');

  // ③-4 删掉**自己刚建的这一个**
  const rowIdx = rowsAfter.more.findIndex((m) => Math.abs(m.y - created.y) < 24);
  console.log(`  ③-4 要删的是第 ${rowIdx + 1} 行（y=${rowsAfter.more[rowIdx]?.y}，新行 y=${created.y}）`);
  must(rowIdx >= 0, '找不到刚建那一行的「更多操作」');
  const m4 = await openMenu(rowIdx);
  must(m4.opened && m4.pts['删除'], `第 ${rowIdx + 1} 行的菜单没读全（${m4.coverage}）`);
  await page.mouse.click(m4.pts['删除'].at[0], m4.pts['删除'].at[1]);
  await page.waitForTimeout(2400);
  const dlg = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    const c = [...document.querySelectorAll('div,section')].filter(vis)
      .map((e) => { const r = e.getBoundingClientRect();
        return { e, r, t: (e.innerText || '').replace(/\s+/g, ' ').trim() }; })
      .filter((x) => /删除|不可恢复/.test(x.t) && x.t.length < 240 && x.r.width > 220 && x.r.height > 80)
      .sort((a, b) => a.t.length - b.t.length)[0];
    if (!c) return { found: false };
    return { found: true, text: c.t.slice(0, 200),
      buttons: [...c.e.querySelectorAll('button,[role="button"]')].filter(vis).map((e) => {
        const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12),
          bg: getComputedStyle(e).backgroundColor,
          at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }) }; });
  out.deleteDialog = dlg;
  console.log(`  确认框：${JSON.stringify(dlg.text)}`);
  console.log(`  框内按钮：${JSON.stringify(dlg.buttons)}`);
  await shot(page, 'M-277-闭环-删除确认框.png');
  const yes = (dlg.buttons || []).find((b) => /^删除$/.test(b.t || ''));
  must(dlg.found && yes, `确认框里找不到红字「删除」：${JSON.stringify(dlg.buttons)}`);
  await page.mouse.click(yes.at[0], yes.at[1]);
  await page.waitForTimeout(2800);
  out.deleteClicked = yes;
  console.log(`  ⭐ 已点红字「删除」@${JSON.stringify(yes.at)}`);

  // ③-5 ⭐ 独立复核：必须**重新打开**抽屉再数，不能只看当前画面
  await esc();
  const p5 = await onAssetPage();
  const afterText = await drawerText();
  const rowsEnd = await rows();
  const leftover = rowsEnd.names.filter((n) => n.t === TEST_NAME).length;
  const restored = afterText === baseText && leftover === 0
    && rowsEnd.more.length === baseRows.more.length;
  out.restored = { page: p5.ok, text: afterText, baseText, sameText: afterText === baseText,
    leftover, rowCount: rowsEnd.more.length, baseRowCount: baseRows.more.length, restored };
  console.log(`\n  ③-5 独立复核（重新打开抽屉后）：`);
  console.log(`     抽屉：${JSON.stringify(afterText)}`);
  console.log(`     与基线逐字相同？ ${afterText === baseText ? '✅' : '❌'}`);
  console.log(`     「${TEST_NAME}」残留：${leftover} 处 ${leftover === 0 ? '✅' : '❌'}`);
  console.log(`     行数 ${rowsEnd.more.length} vs 基线 ${baseRows.more.length} ${rowsEnd.more.length === baseRows.more.length ? '✅' : '❌'}`);
  console.log(`  ⭐⭐ 账户是否回到闭环开始前？ ${restored ? '✅ 是' : '❌ 否'}`);
  await shot(page, 'M-278-闭环-删除之后.png');

  const nodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  out.final = { nodes, restored };
  console.log(`\n═══ 收尾：视口内节点 ${nodes}（视口虚拟化，真实数量看抽屉的「共 N 节点」）｜账户复原=${restored} ═══`);

  await logStep(B, {
    id: 'BT5-asset-rename-download-and-create-delete-loop',
    title: '⭐ 重命名/下载只读 + 「创建→读→删除→独立复核」闭环跑通，账户回到原状',
    target: 'BP2a 一度报「没有删除入口」，BP2g 读到确认框却只点了取消 —— '
      + '从 BP1 留下那枚 `待分类资产` 起就没人把整条链路走通过。'
      + '本轮补上：`新建子文件夹` → 打字 → 回车 → 读到新行（并验证它**确实缩进**在父分类下）'
      + '→ 对**这一行**点 `删除` → 确认框 → 点红字 `删除` → **重新打开抽屉**独立复核'
      + '（抽屉全文与闭环前逐字相同 + 测试名 0 残留 + 行数回到基线）。'
      + '⭐ 边界：⛔ 只删本轮自己刚建的那一个，**绝不碰** BP1 留下的 `待分类资产`。'
      + '另两项只读：`重命名` 开出的输入框现值与选区、`下载` 是否真触发 download 事件（记文件名后 cancel）。',
    evidence: out,
    visible_text: JSON.stringify({
      基线: out.baseline,
      重命名: { 新增输入框: out.rename?.added, 新输入框: out.rename?.newInput, 是否全选: out.rename?.selectedAll },
      下载: out.download,
      闭环: { 建名尝试: out.seedTries, 种子输入框: out.typed, 建完抽屉: out.created?.text,
        新行: out.created?.row, 缩进差: out.indentDelta,
        确认框: out.deleteDialog?.text, 框内按钮: out.deleteDialog?.buttons,
        复核: out.restored }, 收尾: out.final }).slice(0, 3400),
    shot: 'M-276-闭环-新建子文件夹-建出来了.png',
  });
  console.log('\nBT 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 4).join('\n'));
} finally {
  await browser.close();
}

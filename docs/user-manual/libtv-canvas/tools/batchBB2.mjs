// Batch BB2 —— 只做一件事：**验掉我在正文里写的、但没验过的那条建议**。
//
// BB1 的问题：读下拉的判据和点选项的判据用了**两套不同的选择器**。
//   读：`[role="option"],[role="menuitem"],li,button,[class*="Select-option"]` → 读到 18 项
//   点：`[role="option"],li,button`                                  → 一个都找不到
// 差的是 **`[class*="Select-option"]`** —— 这些选项是普通 div，不是 option/li/button。
//
// ⚠️ 这已经是「同一个概念写两遍判据」的第三次翻车
//    （前两次：AW 的 `diffPanels`、AZ 的 tooltip 收集范围）。
//    教训：**读和点必须共用同一个选择器常量**，
//    写两遍就等于埋一个「读得到、点不到」的雷。
//
// 这轮只验：换模型 → 15 条预设里哪些变亮 → **换回原模型并逐字确认复原**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBB2';
const { browser, page } = await launch();

/** ⭐ 唯一的选项选择器 —— 读和点都只认它（BB1 的教训）。 */
const OPT_SEL = '[role="option"],[role="menuitem"],[class*="Select-option"],[class*="Combobox-option"],[class*="Option"],li';
const DROPDOWN_SEL = '[role="listbox"],[role="menu"],.mantine-Select-dropdown,.mantine-Popover-dropdown,[class*="Popover-dropdown"],[class*="Select-dropdown"],[class*="Combobox-dropdown"]';

const optsNow = () => page.evaluate((sel) => [...document.querySelectorAll(sel)]
  .filter((e) => { const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      selected: e.getAttribute('data-selected') === 'true' || e.getAttribute('aria-selected') === 'true',
      disabled: e.getAttribute('data-disabled') === 'true' || e.getAttribute('aria-disabled') === 'true' }; })
  .filter((o) => o.text), OPT_SEL);

const listNodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
  return { id: n.getAttribute('data-id') || '?', prefix: (n.getAttribute('data-id') || '?').split('-')[0],
    name: (/^[^\s]+(?:\s+\d+)?/.exec(t) || [''])[0].slice(0, 14),
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }));

async function exclusivePoint(pg, id) {
  return pg.evaluate((nid) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, id);
}

const panelState = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没选中节点' };
  const panels = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width >= 480 && o.r.height >= 100)
    .filter((o) => o.e.querySelectorAll('button,[role="button"]').length >= 3);
  if (!panels.length) return { err: '没找到参数面板' };
  const p = panels.sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height))[0];
  const all = [...p.e.querySelectorAll('button,[role="button"]')].map((x) => { const q = x.getBoundingClientRect();
    return { text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: x.getAttribute('aria-label'),
      rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; })
    .filter((b) => b.rect[2] > 0);
  const maxY = Math.max(...all.map((b) => b.rect[1] + b.rect[3]));
  const bottom = all.filter((b) => maxY - (b.rect[1] + b.rect[3]) <= 8);
  const preset = all.find((b) => b.aria === '预设');
  return { modelBtn: bottom[0], specBtn: bottom[1], presetBtn: preset || null,
    bottomTexts: bottom.map((b) => b.text) };
});

/** 打开预设选择器，数 15 条各自的 cursor。 */
async function presetCursors() {
  const ps = await panelState();
  if (ps.err || !ps.presetBtn) return { err: ps.err || '没有预设按钮' };
  await page.mouse.click(ps.presetBtn.rect[0] + ps.presetBtn.rect[2] / 2, ps.presetBtn.rect[1] + ps.presetBtn.rect[3] / 2);
  await page.waitForTimeout(2400); await clearToasts(page);
  const rows = await page.evaluate(() => {
    const items = [...document.querySelectorAll('button')].filter((e) => {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      return t.length > 3 && t.length < 60 && /调度故事板|宫格|推演|质感|光影|全景|九宫格|三视图|设定图|画面推演|故事板/.test(t)
        && !/尝试|资产管理|素材库|工具箱/.test(t); });
    const seen = new Set(); const out = [];
    for (const e of items) {
      const full = (e.innerText || '').replace(/\s+/g, ' ').trim();
      // ⚠️ 不能按「首词」当 key ——「画面推演 - 3秒后」和「- 5秒前」首词相同，
      //    按首词去重会把 15 条并成 14 条（BB2 第一轮就这么数错的）。按整段去重。
      if (seen.has(full)) continue; seen.add(full);
      const r = e.getBoundingClientRect();
      const m = /^(.*?)(?:\s{2,}|\s(?=[^\s]{2,12}(?:生成|调节|校正|图|分镜|动作|状态|拆解)))/.exec(full);
      out.push({ name: (m ? m[1] : full).trim().slice(0, 20), desc: full.slice(0, 60),
        cursor: getComputedStyle(e).cursor, ariaDisabled: e.getAttribute('aria-disabled'),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
    return out;
  });
  return { n: rows.length, clickable: rows.filter((r) => r.cursor === 'pointer').map((r) => r.name), rows };
}

/**
 * 换模型 —— 全部交给 Playwright 的 locator，按**文案**找，不认 role / class。
 *
 * BB2 前三轮的教训链：
 *   ① 手搓遍历读下拉（选择器 A）能读到 18 项
 *   ② 手搓遍历点选项（选择器 B）一个都找不到 —— 两套选择器
 *   ③ 改成共用选择器 C 之后，**点按钮三次下拉都不开**（落点确认命中按钮）
 * → 到这一步已经不该继续猜 DOM 结构了。
 *   §17 的老教训在这里再次生效：**能用手搓 DOM 遍历解决的，别用手搓遍历**。
 *   这里反过来用：**能交给 Playwright 文本定位的，别自己找结构**。
 *   `getByText` 对 role / class / 层级都不敏感，还会自己等元素出现。
 */
async function switchModel(targetPrefix) {
  const ps = await panelState();
  if (ps.err) return { err: ps.err };
  const x = Math.round(ps.modelBtn.rect[0] + 20);
  const y = Math.round(ps.modelBtn.rect[1] + ps.modelBtn.rect[3] / 2);
  await page.mouse.click(x, y);
  // 不用固定 sleep，用 Playwright 等「下拉里的第一个已知选项文案」出现
  const known = page.getByText(/^Lib Image 2\.5 Fast/).first();
  try {
    await known.waitFor({ state: 'visible', timeout: 6000 });
  } catch {
    // 没等到就把当前页面上所有「像下拉」的容器打出来，供下一轮判断
    const dump = await page.evaluate(() => [...document.querySelectorAll('[class*="dropdown"],[class*="Dropdown"]')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
      .map((e) => ({ cls: (e.className || '').toString().slice(0, 50),
        rect: (({x: bx, y: by, width: bw, height: bh}) => [bx, by, bw, bh])(e.getBoundingClientRect()),
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80) })));
    return { err: '点了模型按钮之后下拉没出现', dump };
  }
  const opts = page.locator('[class*="Select-option"],[role="option"],li,button')
    .filter({ hasText: /./ }).first();
  // 按文案精确找目标项
  const item = page.getByText(new RegExp('^' + targetPrefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))).last();
  const n = await item.count();
  if (!n) { await page.keyboard.press('Escape'); await page.waitForTimeout(800); return { err: `下拉里没有以「${targetPrefix}」开头的项` }; }
  const itemText = (await item.innerText()).replace(/\s+/g, ' ').trim().slice(0, 40);
  console.log(`  选中「${itemText}」`);
  await item.click({ timeout: 5000 });
  await page.waitForTimeout(3400); await clearToasts(page);
  const now = await panelState();
  void opts;
  return { clicked: itemText, nowModel: now.modelBtn ? now.modelBtn.text : null };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2000);
  await beginBatch(B, { note: '专项：验掉正文里「换模型预设就变亮」这条未验证的建议，验完换回原值' });

  const out = {};
  // 选中图片节点
  let picked = null;
  for (const c of (await listNodes()).filter((n) => n.prefix === 'i' && n.name.includes('图片节点'))) {
    const pt = await exclusivePoint(page, c.id);
    if (pt.err) { console.log(`  ${c.id} → ${pt.err}`); continue; }
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(3800);
    const ok = await page.evaluate((id) => {
      const n = document.querySelector('.react-flow__node.selected');
      return n ? n.getAttribute('data-id') === id : false; }, c.id);
    console.log(`  ${c.id} → ${ok}`);
    if (ok) { picked = c.id; break; }
    await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  }
  if (!picked) throw new Error('没能选中图片节点');
  console.log('选中:', picked);

  const ps0 = await panelState();
  const ORIGINAL = (ps0.modelBtn || {}).text;
  console.log('\n原模型:', ORIGINAL);

  // 1) 换模型前
  const before = await presetCursors();
  console.log(`\n【换模型前】${before.n || 0} 条，可点 ${(before.clickable || []).length} 条`);
  if (!before.err) before.rows.forEach((r) => console.log(`   ${r.cursor === 'pointer' ? '✅' : '⛔'} ${r.name.padEnd(12)} ${r.desc}`));
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  out.before = before;

  // 2) 换成 Lib Image（提示里点名支持的那个）
  const TARGET = 'Lib Image';
  console.log(`\n换成「${TARGET}」…`);
  const sw = await switchModel(TARGET);
  console.log('  结果:', JSON.stringify(sw));
  out.switched = sw;

  if (sw.nowModel) {
    const after = await presetCursors();
    console.log(`\n【换模型后 · 当前模型 "${sw.nowModel}"】${after.n || 0} 条，可点 ${(after.clickable || []).length} 条`);
    if (!after.err) after.rows.forEach((r) => console.log(`   ${r.cursor === 'pointer' ? '✅' : '⛔'} ${r.name.padEnd(12)} ${r.desc}`));
    out.after = after;
    out.verdict = { model: sw.nowModel,
      becameClickable: (after.clickable || []).filter((x) => !(before.clickable || []).includes(x)),
      stillBlocked: (after.rows || []).filter((r) => r.cursor !== 'pointer').map((r) => r.name) };
    console.log('\n⭐ 变亮的:', JSON.stringify(out.verdict.becameClickable));
    console.log('   仍然灰的:', JSON.stringify(out.verdict.stillBlocked));
    await shot(page, 'M-174-换模型后预设.png');
    out.shot = 'M-174-换模型后预设.png';
    await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

    // 3) ✅ 换回原模型
    console.log(`\n换回「${ORIGINAL}」…`);
    const back = await switchModel(ORIGINAL);
    console.log('  结果:', JSON.stringify(back));
    out.restored = back;
    console.log(`  ${back.nowModel && ORIGINAL && back.nowModel.trim() === ORIGINAL.trim() ? '✅ 已复原' : '⚠ 未确认复原'}`);
    const backCheck = await presetCursors();
    out.afterRestore = { n: backCheck.n, clickable: backCheck.clickable };
    console.log(`  复原后可点条数回到 ${(backCheck.clickable || []).length}（换之前是 ${(before.clickable || []).length}）`);
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }

  await logStep(B, {
    id: 'BB2-verify-model-swap', title: '验证「换模型后预设会变亮」这条正文建议',
    target: '**BB1 自己的判据翻车**：读下拉用 `[role=option],[role=menuitem],li,button,[class*=Select-option]` '
      + '读到 18 项，点选项用 `[role=option],li,button` 一个都找不到 —— 少写了 `[class*="Select-option"]`，'
      + '这些选项是普通 div。**读和点必须共用同一个选择器常量**。'
      + '本轮换模型 → 数 15 条的 cursor → **换回原值并逐字确认复原**。',
    evidence: out,
    visible_text: JSON.stringify({ before: out.before && { n: out.before.n, clickable: out.before.clickable },
      switched: out.switched, after: out.after && { n: out.after.n, clickable: out.after.clickable },
      verdict: out.verdict, restored: out.restored }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBB2 完成');
} finally {
  await browser.close();
}

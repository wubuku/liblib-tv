// Batch BS3 — 补上「移动到 ›」的子菜单，并确认账户没被动过。
//
// BS2 的三连 `esc()` 之后，BS2 结尾想读「移动到」子菜单时菜单开不出来 ——
// 因为 `新建子文件夹` 开出来的**行内输入框还开着**，整个抽屉处于「正在新建」状态。
// ⭐ 这是个必须收尾的状态：它不是写操作，但会挡住后面的点击。
// 本轮：① 进资产页先确认抽屉状态干净（没有悬着的输入框）；② 读「移动到 ›」子菜单；
//      ③ **最后独立复核账户**：分类还在、层级没变、画布节点没变。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBS3';
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
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }); }
  return out; }, [txt, minW]);
const esc = async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1400); };
const readInputs = () => page.evaluate(() => [...document.querySelectorAll('input,textarea')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { ph: e.placeholder, val: (e.value || '').slice(0, 24), at: [Math.round(r.x), Math.round(r.y)] }; }));
const drawerText = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const d = [...document.querySelectorAll('div')].filter((e) => { const r = e.getBoundingClientRect();
      return vis(e) && r.x < 40 && r.width > 250 && r.width < 380 && r.height > 300; })
    .sort((a, b) => b.getBoundingClientRect().height - a.getBoundingClientRect().height)[0];
  return (d?.innerText || '').replace(/\s+/g, ' ').trim(); });
const MENU8 = ['添加到Agent', '添加到画布', '更改图标', '新建子文件夹', '移动到', '下载', '重命名', '删除'];

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600); await esc();
  await beginBatch(B, { note: '补「移动到 ›」子菜单 + 独立复核账户' });
  const out = {};

  await clickAria('资产管理', 2800, 40);
  const tab = await cands('资产', 20);
  if (tab[0]) { await page.mouse.click(tab[0].at[0], tab[0].at[1]); await page.waitForTimeout(2400); }
  const t0 = await drawerText();
  const i0 = await readInputs();
  out.start = { drawer: t0, inputs: i0 };
  console.log(`═══ 起点 ═══\n  抽屉：${JSON.stringify(t0)}\n  可见输入框：${JSON.stringify(i0)}`);
  const hanging = i0.filter((x) => /新建|重命名/.test(x.ph || ''));
  console.log(`  ⚠️ 悬着的「新建/重命名」输入框：${hanging.length} 个 ${JSON.stringify(hanging)}`);
  out.hangingInputs = hanging;
  if (hanging.length) { await esc(); console.log(`  → 已按 Esc 收尾`); }
  console.log(`  收尾后输入框：${JSON.stringify(await readInputs())}`);

  // ── 「移动到 ›」子菜单
  console.log(`\n═══ 「移动到 ›」的子菜单 ═══`);
  const more = await clickAria('更多操作', 1800);
  console.log(`  点「更多操作」executed=${more.executed}${more.note ? '（' + more.note + '）' : ''}`);
  const seen = await page.evaluate((w) => {
    const vis = (e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
    return w.filter((t) => [...document.querySelectorAll('div,span,button,li')]
      .some((e) => (e.innerText || '').replace(/\s+/g, ' ').trim() === t && vis(e)
        && e.getBoundingClientRect().height < 60)); }, MENU8);
  console.log(`  菜单读到 ${seen.length}/8`);
  out.menu = { coverage: `${seen.length}/8`, seen, click: more };
  if (seen.length < 8) { console.log(`  ⛔ 菜单没读全，本段作废`); out.moveTo = { invalid: true, seen }; }
  else {
    const mv = (await cands('移动到', 60))[0];
    const r = await page.evaluate((pt) => {
        const vis = (e) => { const b = e.getBoundingClientRect();
          return b.width > 0 && b.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
        return [...document.querySelectorAll('div,li,span,button')].filter(vis)
          .map((e) => { const b = e.getBoundingClientRect();
            return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), kids: e.children.length,
              x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height),
              aria: e.getAttribute('aria-label') }; })
          .filter((x) => x.kids === 0 && x.t && x.t.length <= 16 && x.w > 40 && x.w < 340 && x.h >= 16 && x.h <= 44)
          .filter((x) => x.x > pt[0] && x.y > pt[1] - 40 && x.y < pt[1] + 220)
          .map((x) => `${x.t}@${x.x},${x.y}[${x.w}x${x.h}]`)
          .filter((v, i, a) => a.indexOf(v) === i).slice(0, 16); }, mv.rect);
    console.log(`  悬停「移动到」@${JSON.stringify(mv.at)} 后右侧出现：${JSON.stringify(r)}`);
    out.moveTo = { at: mv.at, items: r };
    if (r.length) await shot(page, 'M-273-资产菜单-移动到子菜单.png');
    console.log(`  ⭐ ${r.length ? '子菜单有内容' : '右侧没有任何东西冒出来 —— 这一项的 › 可能不成立'}`);
  }
  await esc();

  // ── 独立复核账户
  await esc();
  const endI = await readInputs();
  await clickAria('资产管理', 2600, 40);
  const tab2 = await cands('资产', 20);
  if (tab2[0]) { await page.mouse.click(tab2[0].at[0], tab2[0].at[1]); await page.waitForTimeout(2400); }
  const t1 = await drawerText();
  const nodes = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  const names = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return [...document.querySelectorAll('div,span')].filter((e) => vis(e)
      && /^(待分类资产|未命名工作区)$/.test((e.innerText || '').trim()))
      .map((e) => (e.innerText || '').trim()); });
  out.end = { drawer: t1, inputs: endI, nodes, names };
  console.log(`\n═══ 收尾复核 ═══\n  抽屉：${JSON.stringify(t1)}\n  输入框：${JSON.stringify(endI)}\n  节点 ${nodes}｜分类名命中 ${JSON.stringify(names)}`);
  const intact = t0 === t1 && nodes === 11 && endI.filter((x) => /新建|重命名/.test(x.ph || '')).length === 0;
  out.accountIntact = intact;
  console.log(`  ⭐ 与起点一致？ ${intact ? '✅ 是（抽屉文案逐字相同、无悬空输入框、节点 11）' : '❌ 否'}`);

  await logStep(B, {
    id: 'BS3-move-to-submenu-and-account-review',
    title: '⭐「移动到 ›」子菜单 + 账户独立复核',
    target: 'BS2 点完「新建子文件夹」之后，行内输入框还开着，挡住了后面的点击 —— '
      + '这不是写操作，但**属于必须收尾的状态**。本轮：'
      + '① 进资产页先检查有没有悬着的「新建/重命名」输入框，有就 Esc 收尾并复核；'
      + '② 悬停 `移动到 ›` 读它右侧的子菜单；'
      + '③ ⭐ **独立复核账户**：抽屉全文与起点逐字比对、悬空输入框归零、节点数不变。',
    evidence: out,
    visible_text: JSON.stringify({
      起点: out.start, 悬空输入框: out.hangingInputs,
      菜单覆盖: out.menu?.coverage, 菜单读到: out.menu?.seen,
      移动到子菜单: out.moveTo, 收尾: out.end, 账户原样: out.accountIntact }).slice(0, 2600),
    shot: 'M-273-资产菜单-移动到子菜单.png',
  });
  console.log('\nBS3 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message);
} finally {
  await browser.close();
}

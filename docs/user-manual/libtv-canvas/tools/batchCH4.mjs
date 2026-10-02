// Batch CH-4：那两个**无文字的图标**才是模式切换器 —— 顺带测「改名后故事板跟不跟着变」。
//
// CH-3 的结论：画布 2 的页面文本里**既没有「工作流」也没有「故事板」**（两个都 false）。
// 翻 `M-29-故事板模式-有内容.png`（来自**画布 43**，已进故事板态）——
// 它的顶栏是「画布 43 ▾ | `⊞` `⊟` | …」，**同样没有那两个字**。
// ⭐ 而 `A4a-mode-workflow.png`（画布 1）里那个「工作流」标签，是**另一个画布**上的东西
//    （这个工作区里有画布 43~63 等几十个），**不能拿来当同一画布的对照**。
//
// ⇒ 假设：切换器是顶栏那两个**没有文字的图标**（`⊞` / `⊟`），
//   `storyboard-mode.md` 写的「顶栏中间有一个切换开关：`工作流` | `故事板`」**形态写错了**。
//   验证法：先 **hover 读 tooltip**（认名字），再点其中一个，看是否真的切到故事板。
//
// 顺带回答 CH-2 没测到的问题：**改名后，故事板里列的名字跟不跟着变？**
//
// ⚠️ 复原：改回 `视频节点 3` + 两轮独立刷新复核 + 切回工作流。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const VID = 'v-eMpqKtiLlx';
const ORIG_NAME = '视频节点 3';
const TMP = 'CH故事板改名';

const { browser, page } = await launch();
const out = {};

await open(page, URL_);
await closePromos(page);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(5000);
await closePromos(page);
await page.waitForTimeout(1000);

const readTips = () => page.evaluate(() => {
  const grab = (sel) => [...document.querySelectorAll(sel)].map((e) => (e.innerText || e.textContent || '').trim()).filter((t) => t && t.length < 60);
  return { role: grab('[role="tooltip"]'), mantine: grab('[class*="Tooltip"]') };
});
const findBlank = () => page.evaluate(() => {
  for (const [x, y] of [[720, 90], [1300, 170], [720, 690], [200, 370], [1240, 630], [80, 190], [1360, 390]]) {
    const el = document.elementFromPoint(x, y);
    if (el && !el.closest('.react-flow__node') && !el.closest('button,[role="button"]') && !el.closest('input,[contenteditable="true"]')) return { x, y };
  }
  return null;
});
const settle = async () => {
  const b = await findBlank();
  await page.mouse.click(b.x, b.y);
  await page.waitForTimeout(600);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2400);
};
const titleXY = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return null;
  for (const el of node.querySelectorAll('*')) {
    if (!(el.className || '').toString().includes('cursor-text')) continue;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), 文字: (el.innerText || '').trim() };
  }
  return null;
}, nid);
const nodeTitle = (nid) => titleXY(nid).then((t) => (t ? t.文字 : null));
const selectNode = async (nid) => {
  const c = await page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }, nid);
  if (!c) return false;
  await page.mouse.click(c.cx, c.cy);
  await page.waitForTimeout(1700);
  return page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    return !!el && el.className.includes('selected');
  }, nid);
};
const rename = async (nid, name) => {
  const t = await titleXY(nid);
  if (!t) return { ok: false, why: '找不到标题' };
  await page.mouse.dblclick(t.cx, t.cy);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+a');
  await page.waitForTimeout(250);
  await page.keyboard.type(name, { delay: 22 });
  await page.waitForTimeout(700);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1500);
  return { ok: true, 改完: await nodeTitle(nid) };
};

// ── ① 顶栏里所有无文字的图标按钮，逐个 hover 认名字 ──
//    （阳性对照：先 hover 一枚名字已知的，比如画布下拉本身，它应该会提示点什么）
out.顶栏图标 = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const out = [];
  for (const b of document.querySelectorAll('button,[role="button"]')) {
    if (!vis(b)) continue;
    const r = b.getBoundingClientRect();
    if (r.y > 90) continue;                     // 只要顶栏那一行
    const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    out.push({ 文字: t, aria: b.getAttribute('aria-label'), title: b.getAttribute('title'), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`, 路径头: d.slice(0, 26) });
  }
  return out;
});
console.log('顶栏可点元素：');
for (const e of out.顶栏图标) console.log(`   [${e.cx},${e.cy}] ${e.尺寸} 文字="${e.文字}" aria=${e.aria} title=${e.title} 路径=${e.路径头}`);

out.悬停认名 = [];
for (const e of out.顶栏图标) {
  if (e.文字) { out.悬停认名.push({ 文字: e.文字, 气泡: '(有文字，不用悬停)' }); continue; }
  await page.mouse.move(5, 400);
  await page.waitForTimeout(300);
  const b0 = await readTips();
  await page.mouse.move(e.cx, e.cy);
  await page.waitForTimeout(1200);
  await page.mouse.move(e.cx + 1, e.cy);
  await page.waitForTimeout(1000);
  const b1 = await readTips();
  const neu = b1.role.filter((t) => !b0.role.includes(t)).concat(b1.mantine.filter((t) => !b0.mantine.includes(t)));
  out.悬停认名.push({ 位置: [e.cx, e.cy], 尺寸: e.尺寸, 路径: e.路径头, 气泡: neu });
  console.log(`   悬停 [${e.cx},${e.cy}] → ${JSON.stringify(neu)}`);
}
await page.mouse.move(5, 400);
await page.waitForTimeout(500);
await shot(page, 'M-321-顶栏图标-悬停认名.png', { clip: { x: 0, y: 0, width: 900, height: 140 } });

// ── ② 改名 ──
await settle();
if (!await selectNode(VID)) { console.log('!! 没选中'); await browser.close(); process.exit(1); }
out.改名 = await rename(VID, TMP);
console.log('\n改名 =', JSON.stringify(out.改名.改完));

// ── ③ 挨个点那些无文字图标，看哪个能把页面切成故事板 ──
out.试切 = [];
const 无文字 = out.顶栏图标.filter((e) => !e.文字);
for (const e of 无文字) {
  const before = await page.evaluate(() => ({ 节点: document.querySelectorAll('.react-flow__node').length, 文本: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 120) }));
  await page.mouse.click(e.cx, e.cy);
  await page.waitForTimeout(2600);
  const after = await page.evaluate(() => ({ 节点: document.querySelectorAll('.react-flow__node').length, 文本: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 200), 画布: document.querySelector('.react-flow') ? '有' : '无' }));
  const 变了 = before.节点 !== after.节点 || before.文本 !== after.文本;
  out.试切.push({ 位置: [e.cx, e.cy], 路径: e.路径头, 变了, 之前: before, 之后: after });
  console.log(`点 [${e.cx},${e.cy}] 路径=${e.路径头} 变了=${变了} 节点${before.节点}→${after.节点}`);
  if (变了) {
    out.切到故事板 = { 用的图标: e, 之后: after };
    out.故事板里有新名字 = await page.evaluate((n) => (document.body.innerText || '').includes(n), TMP);
    out.故事板里有原名 = await page.evaluate((n) => (document.body.innerText || '').includes(n), ORIG_NAME);
    console.log(`   ⭐ 故事板里出现新名「${TMP}」= ${out.故事板里有新名字}；出现原名「${ORIG_NAME}」= ${out.故事板里有原名}`);
    await shot(page, 'M-322-改名后在故事板里.png', { clip: { x: 0, y: 0, width: 1440, height: 700 } });
    // 点同一个图标切回去
    await page.mouse.click(e.cx, e.cy);
    await page.waitForTimeout(2600);
    out.切回后 = await page.evaluate(() => ({ 节点: document.querySelectorAll('.react-flow__node').length }));
    console.log(`   点同一个图标切回，节点数 = ${out.切回后.节点}`);
    break;
  }
}

// ── ④ 复原 ──
await settle();
if (await selectNode(VID)) { out.复原 = await rename(VID, ORIG_NAME); console.log('\n复原 =', JSON.stringify(out.复原.改完)); }
out.复原复核 = [];
for (const tag of ['刷新1', '刷新2']) {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4800);
  await closePromos(page);
  await page.waitForTimeout(1000);
  await settle();
  const nm = await nodeTitle(VID);
  out.复原复核.push({ tag, 名字: nm, 与原名一致: nm === ORIG_NAME });
  console.log(`  ${tag}: 名字=${JSON.stringify(nm)} 与原名一致=${nm === ORIG_NAME}`);
}
out.复原成功 = out.复原复核.every((x) => x.与原名一致);

await writeFile(resolve(HERE, '.evidence/ch4-icon-mode-switch.json'), JSON.stringify(out, null, 2));
console.log('\n=== 复原成功 =', out.复原成功, '===');
await browser.close();

// Batch CH-0：**节点能不能重命名** —— 手册里完全没提过这个功能。
//
// ⭐ 线索是 CG 顺手读到的一行 class：
//     `text-[13px] cursor-text pointer-events-a…`  ← `cursor-text` 是**文本编辑光标**
// 画布本身能重命名（`manage-canvases.md` 第 4 步），**节点却没有** —— 是没这功能，还是没写？
// 而且画布上**有两个都叫「视频节点 3」的节点**（`v-eMpqKtiLlx` / `v-v2hlWY4Br3`），
// 自动命名撞车 ⇒ 如果能改名，就正好是解法。
//
// ⚠️ 三条纪律（CA 那次误删的学费）：
//   ① **只动 `v-eMpqKtiLlx` 这一个 id**，绝不按位置/顺序认目标；
//   ② 改名之前**先把原名逐字存下来**，脚本末尾**无条件**改回；
//   ③ 改回之后**两轮独立刷新复核**才算数（打字即存盘这件事本手册已经吃过亏）。
//
// 阶段设计成「先探查、后改名」：探查阶段零风险，读到什么算什么；
// 确认能进编辑态才进入改名阶段。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const VID = 'v-eMpqKtiLlx';
const NEW_NAME = 'CH临时改名测试';

const { browser, page } = await launch();
const out = { phases: [] };
const log = (tag, data) => { out.phases.push({ tag, ...data }); console.log(`\n### ${tag}\n` + JSON.stringify(data, null, 2).slice(0, 1600)); };

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

const findBlank = () => page.evaluate(() => {
  for (const [x, y] of [[720, 90], [1300, 170], [720, 690], [200, 370], [1240, 630], [80, 190], [1360, 390]]) {
    const el = document.elementFromPoint(x, y);
    if (el && !el.closest('.react-flow__node') && !el.closest('button,[role="button"]') && !el.closest('input,[contenteditable="true"]')) return { x, y };
  }
  return null;
});
const blank = await findBlank();
await page.mouse.click(blank.x, blank.y);
await page.waitForTimeout(800);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2400);

// 节点标题在**节点本体**里，不在浮层卡片里 —— 按 class 找「最像标题」的那一个
const titleInfo = () => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  // 标题栏是那层 292x23 的小浮层；从它的祖先链上找带 cursor-text 的元素
  const cands = [...node.querySelectorAll('*')]
    .filter((el) => (el.className || '').toString().includes('cursor-text'))
    .map((el) => {
      const r = el.getBoundingClientRect();
      return {
        tag: el.tagName.toLowerCase(),
        cls: (el.className || '').toString().slice(0, 70),
        文字: (el.innerText || el.textContent || '').trim(),
        矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        contenteditable: el.getAttribute('contenteditable'),
        是input: el.tagName === 'INPUT',
        父: (el.parentElement ? el.parentElement.tagName.toLowerCase() : ''),
      };
    });
  const all = [...node.querySelectorAll('input,textarea,[contenteditable="true"]')].map((el) => ({
    tag: el.tagName.toLowerCase(), ce: el.getAttribute('contenteditable'),
    value: el.value !== undefined ? el.value : (el.innerText || '').trim().slice(0, 30),
  }));
  return { cursorText候选: cands, 可编辑元素: all, 节点全部文字: (node.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) };
}, VID);

log('选中前', await titleInfo());

// 选中节点
const c = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!el) return null;
  const b = el.getBoundingClientRect();
  return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
}, VID);
await page.mouse.move(c.cx, c.cy);
await page.waitForTimeout(400);
await page.mouse.click(c.cx, c.cy);
await page.waitForTimeout(1800);
const sel = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  return { selected: !!el && el.className.includes('selected') };
}, VID);
if (!sel.selected) { console.log('!! 没选中'); await browser.close(); process.exit(1); }

// 拿到标题坐标
const t = await page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  for (const el of node.querySelectorAll('*')) {
    if (!(el.className || '').toString().includes('cursor-text')) continue;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), 文字: (el.innerText || '').trim() };
  }
  return null;
}, VID);
out.标题 = t;
if (!t) { console.log('!! 找不到标题'); await browser.close(); process.exit(1); }
console.log('原名 =', JSON.stringify(t.文字));

// ── 阶段 1：单击标题，看会不会直接进编辑 ──
await page.mouse.click(t.cx, t.cy);
await page.waitForTimeout(1200);
log('单击标题后', await titleInfo());

// ── 阶段 2：双击标题 ──
await page.mouse.dblclick(t.cx, t.cy);
await page.waitForTimeout(1400);
const afterDbl = await titleInfo();
log('双击标题后', afterDbl);
await shot(page, 'M-318-双击节点标题之后.png', { clip: { x: 0, y: 0, width: 1440, height: 700 } });

const 可编辑 = afterDbl.可编辑元素.length > 0 || afterDbl.cursorText候选.some((x) => x.contenteditable === 'true' || x.是input);
out.能进编辑态 = 可编辑;
console.log('\n=== 能进编辑态 =', 可编辑, '===');

if (!可编辑) {
  console.log('!! 双击没进编辑态 —— 可能是别的手势（右键菜单？），本轮到此为止，不改名');
  await writeFile(resolve(HERE, '.evidence/ch0-rename-probe.json'), JSON.stringify(out, null, 2));
  await browser.close();
  process.exit(0);
}

// ── 阶段 3：改名 ──
await page.keyboard.press('Meta+a');
await page.waitForTimeout(250);
await page.keyboard.type(NEW_NAME, { delay: 25 });
await page.waitForTimeout(900);
const typing = await titleInfo();
log('打字后', typing);
await page.keyboard.press('Enter');
await page.waitForTimeout(1500);
out.改名后 = await titleInfo();
log('回车后', out.改名后);

// ── 阶段 4：刷新两轮，复核落盘 ──
out.复核 = [];
for (const tag of ['刷新1', '刷新2']) {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4800);
  await closePromos(page);
  await page.waitForTimeout(1000);
  const b = await findBlank();
  await page.mouse.click(b.x, b.y);
  await page.waitForTimeout(600);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2400);
  const cc = await page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }, VID);
  if (cc) { await page.mouse.click(cc.cx, cc.cy); await page.waitForTimeout(1600); }
  const now = await titleInfo();
  out.复核.push({ tag, 名字: (now.cursorText候选[0] || {}).文字, 节点文字: now.节点全部文字 });
  console.log(`${tag} 名字 =`, JSON.stringify((now.cursorText候选[0] || {}).文字));
}

// ── 阶段 5：无条件改回原名 ──
out.原名 = t.文字;
console.log('\n=== 复原：改回', JSON.stringify(t.文字), '===');
const t2 = await page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  for (const el of node.querySelectorAll('*')) {
    if (!(el.className || '').toString().includes('cursor-text')) continue;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }
  return null;
}, VID);
if (t2) {
  await page.mouse.dblclick(t2.cx, t2.cy);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+a');
  await page.waitForTimeout(250);
  await page.keyboard.type(t.文字, { delay: 25 });
  await page.waitForTimeout(800);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(1500);
}
out.改回后 = await titleInfo();
console.log('改回后 =', JSON.stringify((out.改回后.cursorText候选[0] || {}).文字));

// 改回后再两轮刷新复核
out.复原复核 = [];
for (const tag of ['复原刷新1', '复原刷新2']) {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4800);
  await closePromos(page);
  await page.waitForTimeout(1000);
  const b = await findBlank();
  await page.mouse.click(b.x, b.y);
  await page.waitForTimeout(600);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2400);
  const cc = await page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }, VID);
  if (cc) { await page.mouse.click(cc.cx, cc.cy); await page.waitForTimeout(1600); }
  const now = await titleInfo();
  const nm = (now.cursorText候选[0] || {}).文字;
  out.复原复核.push({ tag, 名字: nm, 与原名一致: nm === t.文字 });
  console.log(`${tag} 名字 =`, JSON.stringify(nm), ' 与原名一致 =', nm === t.文字);
}
out.复原成功 = out.复原复核.every((x) => x.与原名一致);

await writeFile(resolve(HERE, '.evidence/ch0-rename-probe.json'), JSON.stringify(out, null, 2));
console.log('\n=== 复原成功 =', out.复原成功, '===');
await browser.close();

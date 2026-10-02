// Batch CH-2：只测一件事 —— **节点改名后，故事板里列的名字跟不跟着变**。
//
// CH-1 那一轮没测到：切换开关的文字是「工作流 / 故事板」，但它**不是 `<button>`**，
// 用 `button,[role=button]` 扫不到 ⇒ 整段 `if` 跳过了。
// ✅ AUDIT 里早就写过这条教训：「**点按钮要向上找真正的可点祖先**，不要点文字叶子」。
//    本轮先找出那个元素是什么，再从它往上找能点的那一层。
//
// 复原：改回 `视频节点 3` + 两轮独立刷新复核。
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
const nodeTitle = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return null;
  for (const el of node.querySelectorAll('*')) {
    if (!(el.className || '').toString().includes('cursor-text')) continue;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) return (el.innerText || el.textContent || '').trim();
  }
  return null;
}, nid);
const titleXY = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return null;
  for (const el of node.querySelectorAll('*')) {
    if (!(el.className || '').toString().includes('cursor-text')) continue;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }
  return null;
}, nid);
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

// ① 那个切换开关到底是什么
out.开关探查 = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const hits = [];
  for (const el of document.querySelectorAll('*')) {
    if (!vis(el)) continue;
    if (el.children.length !== 0) continue;                 // 只要叶子（真正的文字）
    const t = (el.innerText || '').trim();
    if (t !== '故事板' && t !== '工作流') continue;
    const chain = [];
    for (let a = el; a && a !== document.body && chain.length < 4; a = a.parentElement) {
      const r = a.getBoundingClientRect();
      chain.push({ tag: a.tagName.toLowerCase(), cls: (a.className || '').toString().slice(0, 56), cursor: getComputedStyle(a).cursor, 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}` });
    }
    hits.push({ 文字: t, 矩形: (() => { const r = el.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(), 往上: chain });
  }
  return hits;
});
console.log('开关探查 =', JSON.stringify(out.开关探查, null, 2).slice(0, 2000));

// ② 改名
await settle();
if (!await selectNode(VID)) { console.log('!! 没选中'); await browser.close(); process.exit(1); }
out.改名 = await rename(VID, TMP);
console.log('\n改名 =', JSON.stringify(out.改名.改完));

// ③ 切到故事板
const sw = out.开关探查.find((h) => h.文字 === '故事板');
if (sw) {
  const [sx, sy] = sw.矩形;
  await page.mouse.click(sx + Math.round(sw.矩形[2] / 2), sy + Math.round(sw.矩形[3] / 2));
  await page.waitForTimeout(2800);
  out.切后是故事板 = await page.evaluate(() => {
    const txt = (document.body.innerText || '').replace(/\s+/g, ' ');
    return { 有故事板字样: txt.includes('故事板'), 有工作流字样: txt.includes('工作流'), reactFlow节点数: document.querySelectorAll('.react-flow__node').length, 文本片段: txt.slice(0, 260) };
  });
  out.故事板里有新名字 = await page.evaluate((n) => (document.body.innerText || '').includes(n), TMP);
  out.故事板里有原名 = await page.evaluate((n) => (document.body.innerText || '').includes(n), ORIG_NAME);
  console.log('\n切后 =', JSON.stringify(out.切后是故事板));
  console.log(`故事板里出现新名「${TMP}」= ${out.故事板里有新名字}；出现原名「${ORIG_NAME}」= ${out.故事板里有原名}`);
  await shot(page, 'M-319-改名后在故事板里.png', { clip: { x: 0, y: 0, width: 1440, height: 700 } });

  // 切回工作流
  const wf = out.开关探查.find((h) => h.文字 === '工作流');
  if (wf) {
    await page.mouse.click(wf.矩形[0] + Math.round(wf.矩形[2] / 2), wf.矩形[1] + Math.round(wf.矩形[3] / 2));
    await page.waitForTimeout(2800);
  }
  out.切回后节点数 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  console.log('切回工作流 视口内节点数 =', out.切回后节点数);
} else {
  console.log('!! 没找到「故事板」开关');
}

// ④ 复原
await settle();
if (await selectNode(VID)) {
  out.复原 = await rename(VID, ORIG_NAME);
  console.log('\n复原 =', JSON.stringify(out.复原.改完));
}
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

await writeFile(resolve(HERE, '.evidence/ch2-storyboard-name.json'), JSON.stringify(out, null, 2));
console.log('\n=== 复原成功 =', out.复原成功, '===');
await browser.close();

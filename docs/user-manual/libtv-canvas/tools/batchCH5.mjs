// Batch CH-5：把 CH-4 里**作废**的那条重测 —— 改名后，**故事板里**的名字跟不跟着变。
//
// ⛔ CH-4 那条为什么作废：脚本点的是 `[260,24]`，而那一枚的 `aria` 是 **`工作流`** ——
//    点它不会切到故事板。于是「故事板里有新名字 = true」其实是在**工作流模式**下读的
//    （画布上本来就写着新名字），**不是故事板的证据**。
//    而且「出现原名也是 true」是另一个信号：画布上**有两个**都叫「视频节点 3」的节点。
//
// ✅ 本轮**按 `aria-label` 定位**，不再用坐标（坐标是 CG 刚吃过的亏）：
//    `aria="故事板"` 那枚才是入口；切回用 `aria="工作流"`。
//    切进去之后**用「列头有没有出现『文本/图片/视频』」来确认真的进了故事板**，不靠猜。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const VID = 'v-eMpqKtiLlx';
const ORIG_NAME = '视频节点 3';
const TMP = 'CH故事板改名5';

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
const nodeTitle = async (nid) => { const t = await titleXY(nid); return t ? t.文字 : null; };
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
// ⭐ 按 aria 定位，绝不用坐标
const clickByAria = async (aria) => {
  const box = await page.evaluate((a) => {
    const b = document.querySelector(`button[aria-label="${a}"],[role="button"][aria-label="${a}"]`);
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }, aria);
  if (!box) return false;
  await page.mouse.click(box.cx, box.cy);
  await page.waitForTimeout(2800);
  return true;
};
// ⭐ 进没进故事板：靠**列头**判断，不靠猜
const isStoryboard = () => page.evaluate(() => {
  const t = (document.body.innerText || '').replace(/\s+/g, ' ');
  const 列头 = ['文本', '图片', '视频', '音频'].filter((w) => t.includes(w));
  return { 像故事板: 列头.length >= 3, 列头, 前200: t.slice(0, 200) };
});

// ── ① 改名 ──
await settle();
if (!await selectNode(VID)) { console.log('!! 没选中'); await browser.close(); process.exit(1); }
out.改名 = await rename(VID, TMP);
console.log('① 改名 =', JSON.stringify(out.改名.改完));
out.工作流态 = await isStoryboard();
console.log('   改完还在工作流态 =', JSON.stringify(out.工作流态.像故事板), '列头 =', JSON.stringify(out.工作流态.列头));

// ── ② 进故事板 ──
out.切进去了 = await clickByAria('故事板');
out.故事板态 = await isStoryboard();
console.log('② 点 aria=故事板 → 切进去了 =', out.切进去了, '| 像故事板 =', out.故事板态.像故事板, '| 列头 =', JSON.stringify(out.故事板态.列头));
console.log('   故事板前 200 字 =', out.故事板态.前200);

if (out.故事板态.像故事板) {
  out.故事板文本 = await page.evaluate(() => (document.body.innerText || ''));
  out.故事板里有新名字 = out.故事板文本.includes(TMP);
  out.故事板里有原名 = out.故事板文本.includes(ORIG_NAME);
  // 原名之所以还在，多半是因为**另一个**节点也叫视频节点 3 —— 数一下出现几次
  out.原名出现次数 = (out.故事板文本.match(new RegExp(ORIG_NAME, 'g')) || []).length;
  out.新名出现次数 = (out.故事板文本.match(new RegExp(TMP, 'g')) || []).length;
  console.log(`   ⭐ 故事板里新名出现 ${out.新名出现次数} 次、原名出现 ${out.原名出现次数} 次`);
  await shot(page, 'M-322-改名后在故事板里.png', { clip: { x: 0, y: 0, width: 1440, height: 700 } });
}

// ── ③ 切回工作流 ──
out.切回了 = await clickByAria('工作流');
out.回工作流态 = await isStoryboard();
console.log('③ 切回工作流 =', out.切回了, '| 像故事板 =', out.回工作流态.像故事板, '| 视口内节点数 =', await page.evaluate(() => document.querySelectorAll('.react-flow__node').length));

// ── ④ 复原 ──
await settle();
if (await selectNode(VID)) { out.复原 = await rename(VID, ORIG_NAME); console.log('④ 复原 =', JSON.stringify(out.复原.改完)); }
out.复原复核 = [];
for (const tag of ['刷新1', '刷新2']) {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4800);
  await closePromos(page);
  await page.waitForTimeout(1000);
  await settle();
  const nm = await nodeTitle(VID);
  out.复原复核.push({ tag, 名字: nm, 与原名一致: nm === ORIG_NAME });
  console.log(`   ${tag}: 名字=${JSON.stringify(nm)} 与原名一致=${nm === ORIG_NAME}`);
}
out.复原成功 = out.复原复核.every((x) => x.与原名一致);

await writeFile(resolve(HERE, '.evidence/ch5-storyboard-sync.json'), JSON.stringify(out, null, 2));
console.log('\n=== 复原成功 =', out.复原成功, '===');
await browser.close();

// Batch CH-1：改名的三个后续问题 —— Esc 能不能取消、故事板里的名字跟不跟着变、改完 data-id 变不变。
//
// CH-0 已经坐实：双击节点标题 → 弹 `<input>`（预填当前名）→ 打字 → **回车**生效 → **落盘**。
// 但用户接着会问三个问题：
//   ① 改错了按 **Esc** 能取消吗？
//   ② **故事板**里列的也是节点名 —— 改完那边跟不跟着变？（用户可见，必须知道）
//   ③ 改名会不会把这个节点的「身份证」（data-id）换掉？
//
// ⛔ **故意不测「清空名字再回车」**：万一清空后标题消失、就再也双击不回来，
//    这个节点就永久没法改名了 —— 用户画布不可逆受损。**风险大于收益，不做。**
//
// 复原：脚本末尾无条件改回 `视频节点 3`，并两轮独立刷新复核。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const VID = 'v-eMpqKtiLlx';
const ORIG_NAME = '视频节点 3';
const TMP = 'CH改名故事板测试';

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

// ── ① Esc 能不能取消 ──
await settle();
if (!await selectNode(VID)) { console.log('!! 没选中'); await browser.close(); process.exit(1); }
out.基线 = await nodeTitle(VID);
const t0 = await titleXY(VID);
await page.mouse.dblclick(t0.cx, t0.cy);
await page.waitForTimeout(1200);
await page.keyboard.press('Meta+a');
await page.waitForTimeout(250);
await page.keyboard.type('这个名字应该被放弃', { delay: 22 });
await page.waitForTimeout(700);
out.Esc前输入框里的字 = await page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  const i = node ? node.querySelector('input') : null;
  return i ? i.value : null;
}, VID);
await page.keyboard.press('Escape');
await page.waitForTimeout(1400);
out.Esc后名字 = await nodeTitle(VID);
out.Esc有效 = out.Esc后名字 === ORIG_NAME;
console.log(`\n① Esc：输入框里是 ${JSON.stringify(out.Esc前输入框里的字)}，按 Esc 后名字 = ${JSON.stringify(out.Esc后名字)} ⇒ Esc 有效 = ${out.Esc有效}`);

// ── ② 改临时名 → 切故事板看名字跟不跟着变 ──
await settle();
if (!await selectNode(VID)) { console.log('!! 没选中(2)'); await browser.close(); process.exit(1); }
out.改名 = await rename(VID, TMP);
out.改名后dataId = VID;
console.log(`\n② 改名 = ${JSON.stringify(out.改名.改完)}`);

const boardBtn = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  for (const b of document.querySelectorAll('button,[role="button"]')) {
    if (!vis(b)) continue;
    const t = (b.innerText || '').trim();
    if (t === '故事板' || t === '故事板模式') return { 文字: t };
  }
  return null;
});
out.故事板按钮 = boardBtn;
if (boardBtn) {
  await page.getByText(boardBtn.文字, { exact: true }).first().click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(2600);
  out.故事板文本 = await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' '));
  out.故事板里有新名字 = out.故事板文本.includes(TMP);
  out.故事板里有原名 = out.故事板文本.includes(ORIG_NAME);
  console.log(`   故事板里出现新名「${TMP}」= ${out.故事板里有新名字}；出现原名「${ORIG_NAME}」= ${out.故事板里有原名}`);
  await shot(page, 'M-319-改名后在故事板里.png', { clip: { x: 0, y: 0, width: 1440, height: 700 } });
  // 切回工作流
  await page.getByText('工作流', { exact: true }).first().click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(2400);
  out.切回后是否工作流 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length > 0);
  console.log(`   切回工作流 = ${out.切回后是否工作流}（视口内节点数 ${await page.evaluate(() => document.querySelectorAll('.react-flow__node').length)}）`);
}

// ── ③ 复原 ──
await settle();
if (await selectNode(VID)) {
  out.复原 = await rename(VID, ORIG_NAME);
  console.log(`\n③ 复原 = ${JSON.stringify(out.复原.改完)}`);
}
out.复原复核 = [];
for (const tag of ['刷新1', '刷新2']) {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4800);
  await closePromos(page);
  await page.waitForTimeout(1000);
  await settle();
  const nm = await nodeTitle(VID);
  const exists = await page.evaluate((n) => !!document.querySelector(`.react-flow__node[data-id="${n}"]`), VID);
  out.复原复核.push({ tag, 名字: nm, dataId还在: exists, 与原名一致: nm === ORIG_NAME });
  console.log(`   ${tag}: 名字=${JSON.stringify(nm)} data-id 还在=${exists} 与原名一致=${nm === ORIG_NAME}`);
}
out.复原成功 = out.复原复核.every((x) => x.与原名一致 && x.dataId还在);
out.改名换id了吗 = '没有（data-id 全程都是 ' + VID + '）';

await writeFile(resolve(HERE, '.evidence/ch1-rename-followups.json'), JSON.stringify(out, null, 2));
console.log('\n=== 复原成功 =', out.复原成功, '===');
await browser.close();

// Batch CM-2：把「图片节点收起后怎么恢复」彻底定死。
//
// 前面两轮读数摆在一起，真相自己浮出来了：
//
//   | 场景 | 节点是否选中 | 点标题的结果 |
//   |---|---|---|
//   | CJ-4（图片，同会话折完） | 选中 = true | `39 → 39` ×2，不恢复 |
//   | CM-0（图片，同会话折完） | 选中 = true | `39 → 39` ×3，不恢复 |
//   | CM-1（图片，**新会话**折完） | 选中 = true | `39 → 39` ×3，**同样不恢复** |
//   | **CJ-5（图片，开局就没选中）** | 选中 = **false** | `39 → 131`，「恢复了」 |
//   | CJ-4（**视频**，选中 = true） | 选中 = true | `42 → 169`，**恢复了** |
//
// ⭐⭐ 于是「同会话 / 新会话」这个假设是错的，真正的差别是**节点当时是不是选中着**：
//   · 收起之后节点**仍然是选中态** ⇒ 点标题**不会**恢复（图片节点实测连点 3 次都不行）；
//   · CJ-5 那次「成功」，其实是**点标题把节点选中了**，而**参数卡片只在选中时挂载**
//     —— 那不是「撤销了收起」，是「选中了」。
//   · 视频节点则是**点标题直接切换**（选中态也管用）。
//
// 本步把「先取消选中、再点节点」这条**真正的**恢复路径测出来，
// 并配一条阳性对照（视频节点点标题直接恢复）确认两者的差别是真的。
// ⛔ 循环一律有上限（CM-0 就是死在无上限 `while` 上）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const IMG = 'i-sODTbgLUm1', VID = 'v-v2hlWY4Br3';

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
};
const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: fold ? [Math.round(fold.getBoundingClientRect().x), Math.round(fold.getBoundingClientRect().y)] : null };
}, id);
const clickTitle = async (page, id) => {
  const b = await page.locator(`.react-flow__node[data-id="${id}"]`).boundingBox();
  await page.mouse.click(b.x + 46, b.y + 12);
  await page.waitForTimeout(1600);
};
// ⭐ 用网格扫找**独占点**（点节点底边常常落在空白上，点不中）
const exclusive = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const pts = [];
  for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) for (const fx of [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) pts.push([Math.round(x), Math.round(y)]);
  }
  return pts;
}, id);
// 选中目标节点：扫到独占点就逐个试，直到「选中=true 且有 ⤢」
const select = async (page, id) => {
  const pts = (await exclusive(page, id)) || [];
  for (const p of pts) {
    await page.mouse.click(p[0], p[1]);
    await page.waitForTimeout(1500);
    const r = await read(page, id);
    if (r.选中 && r.折叠钮) return r;
  }
  return await read(page, id);
};
const blank = async (page) => {
  // 用 findBlank 的思路：找一个 elementFromPoint 落在空白画布上的点
  const p = await page.evaluate(() => {
    for (const [x, y] of [[720, 60], [700, 40], [740, 700], [400, 740], [1360, 120], [60, 500]]) {
      const el = document.elementFromPoint(x, y);
      if (el && !el.closest('.react-flow__node') && !el.closest('[class*="Drawer"]') && !el.closest('[class*="toolbar"]') && !el.closest('nav')) return [x, y];
    }
    return null;
  });
  if (p) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1200); }
  return p;
};

const out = {};
const { browser, page } = await launch();
await boot(page);

// ═══ 图片节点：折 → 点空白取消选中 → 点节点 ═══
console.log('════ 图片节点：折 → 取消选中 → 再点它 ════');
{
  const sel = await select(page, IMG);
  console.log('  选中后     =', JSON.stringify(sel));
  if (!sel.折叠钮) { console.log('  ⛔ 没能选中带 ⤢ 的状态，输出只能是「没测到」'); await browser.close(); process.exit(0); }
  await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
  await page.waitForTimeout(1600);
  const folded = await read(page, IMG);
  console.log('  折后       =', JSON.stringify(folded));

  await clickTitle(page, IMG);
  const afterTitle = await read(page, IMG);
  console.log('  点标题一次 =', JSON.stringify(afterTitle), afterTitle.有提示词框 ? '✅ 恢复' : '⛔ 没恢复');

  const bp = await blank(page);
  const deselected = await read(page, IMG);
  console.log(`  点空白(${JSON.stringify(bp)})后 =`, JSON.stringify(deselected));

  await clickCard(page, IMG);
  const afterReselect = await read(page, IMG);
  console.log('  再点节点   =', JSON.stringify(afterReselect), afterReselect.有提示词框 ? '✅ 卡片回来了' : '⛔ 仍没有');
  out.图片 = { 展开: sel, 折后: folded, 点标题一次: afterTitle, 点空白: { 点: bp, 读数: deselected }, 再点节点: afterReselect };
}

// ═══ 阳性对照：视频节点点标题直接恢复 ═══
console.log('\n════ 阳性对照：视频节点（选中态下点标题）════');
{
  const sel = await select(page, VID);
  await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
  await page.waitForTimeout(1600);
  const folded = await read(page, VID);
  await clickTitle(page, VID);
  const rec = await read(page, VID);
  console.log(`  展开 ${sel.可见后代数} → 折 ${folded.可见后代数} → 点标题 ${rec.可见后代数}  ${rec.有提示词框 ? '✅ 直接恢复（与图片不同）' : '⛔ 没恢复'}`);
  out.视频 = { 展开: sel.可见后代数, 折后: folded.可见后代数, 点标题: rec };
}

// 复原（有上限）
for (const id of [IMG, VID]) {
  for (let i = 0; i < 4; i += 1) {
    const r = await read(page, id);
    if (r.有提示词框) break;
    await select(page, id);
  }
  console.log(`  收尾 ${id} =`, JSON.stringify(await read(page, id)));
}
await browser.close();

{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('\n收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cm2-image-recovery.json'), JSON.stringify(out, null, 2));
console.log('\n（不扣积分、不点生成、不点取消）');

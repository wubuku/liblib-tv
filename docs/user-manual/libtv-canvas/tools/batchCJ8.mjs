// Batch CJ-8（第四版）：配图不再靠 `elementFromPoint` 断言兜底。
//
// 为什么放弃断言：节点**卡片中心**处的 `elementFromPoint` 拿到的是
// `div.flex.flex-wrap.items-center`，而它 `closest('.react-flow__node')` 是 **null**
// —— 节点的可视内容并不在 `.react-flow__node` 这棵子树里（标题栏 292×23 是独立的
// `.node-floating-ui`，卡片内容又是另一层）。⇒ 用它当「这张图拍的是不是它」的锚点，
// 注定三次三次都判不过。**判据本身与被测对象不同构**，再多试也是白试。
//
// ✅ 改用更朴素、也更靠得住的办法：**拍出来我自己看**。
//    「名不副实的图比没有图更糟」—— 图对不对，看一眼就知道，不必自动化。
//    收尾仍按硬判据走：元素数差 > 30、复原后与起点一致、全新会话复核。
//
// 顺带把两处新发现固定下来：
//   ① 「新功能：支持真人」是**常驻**引导标记（`position:absolute`、opacity 1、
//      静置 4 秒不消失、鼠标移开也不消失）—— 不是悬停气泡；
//   ② 它旁边有一枚 `6×6` 的小圆点，落在**角色库**按钮正上方 ⇒ 角色库挂着 NEW 标。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const TID = 'v-v2hlWY4Br3';
const PARK = [12, 470];

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  const d = page.locator('.mantine-Drawer-inner').first().locator('button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 6000 }).catch(() => {});
  await page.waitForTimeout(1600);
};
const read = (page) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  const fr = fold ? fold.getBoundingClientRect() : null;
  const nr = n.getBoundingClientRect();
  let card = null;
  if (fold) { let a = fold; while (a && !/overflow-hidden/.test(a.className.toString())) a = a.parentElement; const cr = a.getBoundingClientRect(); card = [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)]; }
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: fr ? [Math.round(fr.x), Math.round(fr.y)] : null, 节点rect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)], 参数卡rect: card, 节点文字: (n.innerText || '').replace(/\s+/g, ' ').trim() };
}, TID);

const out = {};
const { browser, page } = await launch();
await boot(page);
{
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
  await page.waitForTimeout(1700);
}
const sel = await read(page);
console.log('选中后 =', JSON.stringify(sel));
if (!sel.选中 || !sel.折叠钮 || !sel.参数卡rect) { console.log('⛔ 硬前置不满足'); await browser.close(); process.exit(0); }

// NEW 小点挂在谁身上
out.NEW标 = await page.evaluate(() => {
  const n = document.querySelector('.react-flow__node[data-id="v-v2hlWY4Br3"]');
  if (!n) return null;
  return [...n.querySelectorAll('*')].map((e) => {
    const r = e.getBoundingClientRect();
    if (r.width > 12 || r.height > 12 || r.width === 0) return null;
    const parentBtn = e.closest('button');
    const br = parentBtn ? parentBtn.getBoundingClientRect() : null;
    return { 小点rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 背景: getComputedStyle(e).backgroundColor, 挂在按钮: parentBtn ? (parentBtn.innerText || '').trim() : null, 按钮rect: br ? [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)] : null };
  }).filter(Boolean);
});
console.log('NEW 小点 =', JSON.stringify(out.NEW标));

const n = sel.节点rect, c = sel.参数卡rect;
const CLIP = { x: Math.max(0, Math.min(n[0], c[0]) - 24), y: Math.max(0, Math.min(n[1], c[1]) - 24), width: 0, height: 0 };
CLIP.width = Math.max(n[0] + n[2], c[0] + c[2]) + 24 - CLIP.x;
CLIP.height = Math.max(n[1] + n[3], c[1] + c[3]) + 24 - CLIP.y;
out.CLIP = CLIP;
console.log('CLIP =', JSON.stringify(CLIP));

await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
await page.waitForTimeout(1700);
const folded = await read(page);
console.log('折后 =', JSON.stringify(folded));
out.元素数差 = sel.可见后代数 - folded.可见后代数;
out.折后文字 = folded.节点文字;
console.log('元素数差 =', out.元素数差, ' 折后节点文字 =', JSON.stringify(folded.节点文字));
if (out.元素数差 < 30) { console.log('⛔ 分辨力不足，不配图'); await browser.close(); process.exit(0); }

await page.mouse.move(PARK[0], PARK[1]);
await page.waitForTimeout(1400);
await shot(page, 'M-330-参数卡片-收起后只剩标题.png', { clip: CLIP });
console.log('已拍 M-330（请人工看一眼再决定留不留）');

{
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.click(b.x + 46, b.y + 12);
  await page.waitForTimeout(1700);
  let rec = await read(page);
  if (!rec.有提示词框) { await page.mouse.click(b.x + 46, b.y + 12); await page.waitForTimeout(1600); rec = await read(page); }
  console.log('复原后 =', JSON.stringify(rec), rec.可见后代数 === sel.可见后代数 ? '✅ 与起点一致' : '⚠️ 不一致');
  out.复原 = rec;
}
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const b = await p2.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await p2.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
  await p2.waitForTimeout(1700);
  const fin = await read(p2);
  console.log('全新会话复核 =', JSON.stringify(fin), fin.有提示词框 ? '✅ 展开着' : '⛔ 折着');
  out.全新会话复核 = fin;
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cj8-shots.json'), JSON.stringify(out, null, 2));
console.log('\n（不扣积分、不点生成、不点取消）');

// Batch CM-3：把「图片节点收起后，恢复动作到底落在哪」钉死 —— 每次点击都报**落点是谁**。
//
// CM-2 的读数很关键但成因不明：
//   折后 `39` → 点「节点标题栏」`39 → 39`（没反应）
//        → 点 (720,60) **`39 → 131`，提示词框和 ⤢ 都回来了**
// 而 (720,60) 那个点，**我的「找空白点」判据判它是空白**
// （判据是 `!el.closest('.react-flow__node')`）——
// ⭐ 但节点标题栏是**独立的 `node-floating-ui`，不在 `.react-flow__node` 子树里**（CJ 记过），
// 所以那个点**很可能就是这张节点自己的标题栏**，只是判据认不出来。
//
// 本步：每个候选落点都先读出「那里到底是什么元素、属于哪个节点」，再点，再读。
// ⛔ 循环一律有上限（CM-0 死在无上限 `while` 上）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const IMG = 'i-sODTbgLUm1';

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
  const r = n.getBoundingClientRect();
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: fold ? [Math.round(fold.getBoundingClientRect().x), Math.round(fold.getBoundingClientRect().y)] : null, 节点rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}, id);
// ⭐ 当前几何：每次**点击之前**重新量，绝不复用旧坐标
const geo = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const nr = n.getBoundingClientRect();
  const box = (r) => [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  let 浮层 = null;
  for (const el of document.querySelectorAll('.node-floating-ui')) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && Math.abs(r.x - nr.x) < 10 && Math.abs(r.y - nr.y) < 10) {
      浮层 = { rect: box(r), 文字: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) };
      break;
    }
  }
  return { 节点: box(nr), 浮层 };
}, id);

// ⭐ 落点身份：这个点上到底是什么、属于哪个节点
const who = (page, x, y) => page.evaluate(([px, py]) => {
  const el = document.elementFromPoint(px, py);
  if (!el) return { 空: true };
  const node = el.closest('.react-flow__node');
  const float = el.closest('.node-floating-ui');
  const box = (r) => [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  return {
    元素: `${el.tagName.toLowerCase()}.${(el.className || '').toString().slice(0, 46)}`,
    文字: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 18),
    在reactflow节点内: !!node, 节点id: node ? node.getAttribute('data-id') : null,
    在node浮层内: !!float, 落在浮层里的rect: float ? box(float.getBoundingClientRect()) : null,
  };
}, [x, y]);

const out = {};
const { browser, page } = await launch();
await boot(page);

// 选中并折
let r = await read(page, IMG);
const pts = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const q = n.getBoundingClientRect();
  const a = [];
  for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) for (const fx of [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]) {
    const x = q.x + q.width * fx, y = q.y + q.height * fy;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) a.push([Math.round(x), Math.round(y)]);
  }
  return a;
}, IMG);
for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1400); r = await read(page, IMG); if (r.选中 && r.折叠钮) break; }
console.log('选中后 =', JSON.stringify(r));
if (!r.折叠钮) { console.log('⛔ 没选中带 ⤢ 的状态'); await browser.close(); process.exit(0); }

// 找「这个节点自己的标题栏」：.node-floating-ui，宽≈节点宽，高≈23
out.标题栏 = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const nr = n.getBoundingClientRect();
  for (const f of document.querySelectorAll('.node-floating-ui')) {
    const r = f.getBoundingClientRect();
    if (r.width > 0 && Math.abs(r.x - nr.x) < 6 && r.height < 40) {
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: (f.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), class: (f.className || '').toString().slice(0, 70) };
    }
  }
  return null;
}, IMG);
console.log('这个节点的标题栏 =', JSON.stringify(out.标题栏));

await page.mouse.click(r.折叠钮[0] + 14, r.折叠钮[1] + 14);
await page.waitForTimeout(1600);
const folded = await read(page, IMG);
console.log('折后 =', JSON.stringify(folded));

// 逐个候选落点：点前重新量几何 → 报身份 → 点 → 读
out.候选 = [];
const 枚举 = [
  { 名: '节点标题栏中心', 取: (g) => (g.浮层 ? [g.浮层.rect[0] + 46, g.浮层.rect[1] + Math.round(g.浮层.rect[3] / 2)] : null) },
  { 名: '节点元素左上(旧手法)', 取: (g) => [g.节点[0] + 46, g.节点[1] + 12] },
  { 名: '节点元素正中', 取: (g) => [g.节点[0] + Math.round(g.节点[2] / 2), g.节点[1] + Math.round(g.节点[3] / 2)] },
  { 名: '字面点(720,60)', 取: () => [720, 60] },
  { 名: '远端空白(1360,700)', 取: () => [1360, 700] },
];
for (const c of 枚举) {
  // 每条都从「折着」开始
  let pre = await read(page, IMG);
  if (pre.有提示词框) {
    const b = await page.locator(`.react-flow__node[data-id="${IMG}"]`).boundingBox();
    await page.mouse.click(b.x + b.width / 2, b.y + b.height / 2);
    await page.waitForTimeout(1400);
    pre = await read(page, IMG);
    if (pre.有提示词框) {
      for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1300); const q = await read(page, IMG); if (q.折叠钮) { await page.mouse.click(q.折叠钮[0] + 14, q.折叠钮[1] + 14); await page.waitForTimeout(1500); break; } }
      pre = await read(page, IMG);
    }
  }
  const g = await geo(page, IMG);
  const xy = g ? c.取(g) : null;
  if (!xy) { console.log(`  ${c.名} —— 几何取不到，跳过`); continue; }
  const id0 = await who(page, xy[0], xy[1]);
  const geoAt = g;
  await page.mouse.click(xy[0], xy[1]);
  await page.waitForTimeout(1600);
  const after = await read(page, IMG);
  console.log(`  ${c.名.padEnd(20)} (${xy[0]},${xy[1]})`);
  console.log(`      落点=${JSON.stringify(id0).slice(0, 150)}`);
  console.log(`      → ${pre.可见后代数} → ${after.可见后代数}  恢复=${after.有提示词框 ? '✅' : '⛔'}`);
  out.候选.push({ 名: c.名, 点: xy, 点前几何: geoAt, 落点: id0, 前: pre.可见后代数, 后: after.可见后代数, 恢复: after.有提示词框 });
}

// 复原
for (let i = 0; i < 5; i += 1) {
  const q = await read(page, IMG);
  if (q.有提示词框) break;
  for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1300); const z = await read(page, IMG); if (z.有提示词框) break; }
}
console.log('\n收尾 =', JSON.stringify(await read(page, IMG)));
await browser.close();

{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cm3-who-is-the-click.json'), JSON.stringify(out, null, 2));

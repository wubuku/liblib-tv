// Batch CM：收拾 CJ 留下的两个「📖 未查清」。
//
//   ① **文本节点上 `⤢` 为什么没反应**（CJ 坐实了「点了没反应」，但没说为什么）
//   ② **图片节点「点标题恢复」为什么不稳定**（CJ-4 两次不行、CJ-5 一次就行）
//
// ① 的假设：文本节点的参数卡是**另一套组件**（它没有模型/规格那一排），
//    所以那枚 `⤢` 挂的容器可能**没有可折叠的那一层**。⇒ 直接比 DOM 结构：
//    视频节点的卡 vs 文本节点的卡，逐层打 class，重点看 `overflow-hidden` 与子层数。
//    另外画布上有**两个**文本节点（`t-2AK3Ukyxj3` / `t-UtVx3lZmrV`）——
//    ⭐ 两个都试，就能分辨「文本这类不行」和「这一张恰好没反应」。
//
// ② 的假设：**同一轮里刚折完就点标题不灵，换一轮（新会话）就灵**。
//    ⇒ 阶梯：折 → 点标题 ×3（同一会话）→ 刷新 → 折 → 点标题 ×1 → 读。
//    阳性对照自带：视频节点在 CJ-4 同一轮里点一次就恢复，说明「点标题」这个手法有效。
//
// ⛔ 全程按 `data-id` 认人；收尾复原并用全新会话复核。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

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
  const fr = fold ? fold.getBoundingClientRect() : null;
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: fr ? [Math.round(fr.x), Math.round(fr.y)] : null };
}, id);
const clickTitle = async (page, id) => {
  const b = await page.locator(`.react-flow__node[data-id="${id}"]`).boundingBox();
  await page.mouse.click(b.x + 46, b.y + 12);
  await page.waitForTimeout(1600);
};
const exclusive = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) for (const fx of [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) return [Math.round(x), Math.round(y)];
  }
  return null;
}, id);

const out = {};
const { browser, page } = await launch();
await boot(page);

// ═══ ① 文本节点的 ⤢ ═══
console.log('════ ① 文本节点 ════');
out.文本 = [];
for (const id of ['t-UtVx3lZmrV', 't-2AK3Ukyxj3']) {
  const pt = await exclusive(page, id);
  if (!pt) { console.log(`  ${id} 扫不出独占点`); continue; }
  await page.mouse.click(pt[0], pt[1]);
  await page.waitForTimeout(1600);
  const sel = await read(page, id);
  if (!sel.选中 || !sel.折叠钮) { console.log(`  ${id} 未选中或无 ⤢：`, JSON.stringify(sel)); out.文本.push({ id, 前置不满足: true, sel }); continue; }

  // 卡的结构：⤢ 往上打 4 层
  const 结构 = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute'); });
    const chain = [];
    for (let a = fold; a && a !== n.parentElement && chain.length < 5; a = a.parentElement) {
      const cs = getComputedStyle(a);
      const r = a.getBoundingClientRect();
      chain.push({ tag: a.tagName.toLowerCase(), cls: (a.className || '').toString().slice(0, 74), overflow: cs.overflow, 高度: Math.round(r.height), 直接子元素数: a.children.length, 子元素class: [...a.children].slice(0, 5).map((c) => (c.className || '').toString().slice(0, 40)) });
    }
    return chain;
  }, id);

  await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
  await page.waitForTimeout(1700);
  const after = await read(page, id);
  const 收起了 = after.可见后代数 < sel.可见后代数;
  console.log(`  ${id}  展开 ${sel.可见后代数} → 点 ⤢ 后 ${after.可见后代数}  ${收起了 ? '✅ 收起了' : '⛔ 没反应'}`);
  console.log('    卡结构（⤢ 往上）:');
  for (const c of 结构) console.log(`      ${c.tag}.${c.cls}  overflow=${c.overflow} 高=${c.高度} 子=${c.直接子元素数} ${JSON.stringify(c.子元素class)}`);
  out.文本.push({ id, 展开: sel, 点后: after, 收起了, 结构 });

  if (收起了) { await clickTitle(page, id); const rec = await read(page, id); console.log(`    点标题复原 = ${rec.可见后代数} ${rec.可见后代数 === sel.可见后代数 ? '✅' : '⚠️'}`); out.文本.at(-1).复原 = rec; }
}

// 阳性对照：视频节点同一手法（证明「点 ⤢」这个手法本身有效）
console.log('\n  ── 阳性对照：视频节点 ──');
{
  const pt = await exclusive(page, 'v-v2hlWY4Br3');
  await page.mouse.click(pt[0], pt[1]);
  await page.waitForTimeout(1600);
  const sel = await read(page, 'v-v2hlWY4Br3');
  await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
  await page.waitForTimeout(1600);
  const after = await read(page, 'v-v2hlWY4Br3');
  console.log(`  v-v2hlWY4Br3  展开 ${sel.可见后代数} → ${after.可见后代数}  ${after.可见后代数 < sel.可见后代数 ? '✅ 收起了（手法有效）' : '⛔ 没反应'}`);
  await clickTitle(page, 'v-v2hlWY4Br3');
  out.阳性对照 = await read(page, 'v-v2hlWY4Br3');
  console.log('  复原 =', JSON.stringify(out.阳性对照));
}

// ═══ ② 图片节点：同会话 vs 重开 ═══
console.log('\n════ ② 图片节点：同一轮里连点 3 次标题 ════');
const IMG = 'i-sODTbgLUm1';
{
  const pt = await exclusive(page, IMG);
  await page.mouse.click(pt[0], pt[1]);
  await page.waitForTimeout(1600);
  const sel = await read(page, IMG);
  console.log('  选中后 =', JSON.stringify(sel));
  await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
  await page.waitForTimeout(1600);
  const folded = await read(page, IMG);
  console.log('  折后 =', JSON.stringify(folded));
  out.图片_同会话 = { 展开: sel, 折后: folded, 尝试: [] };
  for (let i = 0; i < 3; i += 1) {
    await clickTitle(page, IMG);
    const r = await read(page, IMG);
    out.图片_同会话.尝试.push({ 第几次: i + 1, 读数: r });
    console.log(`  同会话点标题第 ${i + 1} 次 = ${r.可见后代数} ${r.有提示词框 ? '✅ 恢复了' : '⛔ 仍折着'}`);
    if (r.有提示词框) break;
  }
  // 复原
  let r = await read(page, IMG);
  while (!r.有提示词框) { await clickTitle(page, IMG); r = await read(page, IMG); }
  out.图片_同会话.收尾 = r;
}
await writeFile(resolve(HERE, '.evidence/cm0-text-image.json'), JSON.stringify(out, null, 2));
await browser.close();

// ═══ ②b 同一个动作，换一个全新会话再做一遍 ═══
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  console.log('\n════ ②b 图片节点：全新会话里折完立刻点标题 ════');
  const pt = await exclusive(p2, IMG);
  await p2.mouse.click(pt[0], pt[1]);
  await p2.waitForTimeout(1600);
  const sel = await read(p2, IMG);
  await p2.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
  await p2.waitForTimeout(1600);
  const folded = await read(p2, IMG);
  console.log('  展开 =', sel.可见后代数, ' 折后 =', folded.可见后代数);
  await clickTitle(p2, IMG);
  const r1 = await read(p2, IMG);
  console.log(`  全新会话点标题第 1 次 = ${r1.可见后代数} ${r1.有提示词框 ? '✅ 恢复了' : '⛔ 仍折着'}`);
  out.图片_新会话 = { 展开: sel, 折后: folded, 第一次点标题: r1 };
  let r = r1;
  while (!r.有提示词框) { await clickTitle(p2, IMG); r = await read(p2, IMG); }
  out.图片_新会话.收尾 = r;
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cm0-text-image.json'), JSON.stringify(out, null, 2));
const ids = await launch().then(async ({ page: p3 }) => { await boot(p3); const v = await p3.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id'))); return v; });
console.log('\n最终节点 =', JSON.stringify(ids), ' 与基线一致 =', ids.length === BASE.length && BASE.every((x) => ids.includes(x)));
out.收尾复核 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
await writeFile(resolve(HERE, '.evidence/cm0-text-image.json'), JSON.stringify(out, null, 2));

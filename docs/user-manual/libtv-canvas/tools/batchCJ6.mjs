// Batch CJ-6：⛔ 把「收起会不会存盘」重测一遍 —— 上一轮的判据**分不开**两种状态。
//
// 问题的根子：`有提示词框=false` / `可见后代数=42` 有**两个**成因：
//   (a) 节点被收起了；
//   (b) 节点**没选中**，参数卡压根没挂载。
// `.react-flow__node` 只在选中时挂参数卡（CI-1 就撞见过「一个只有标题、一个有参数卡」，
// 我当时判成「内容不同」，其实是这个）。
// ⇒ CJ-2 阶段 C 那个「全新会话读出 42 ⇒ 存盘了」**不能成立**，本步作废它。
//
// ⭐ 正确判据：**在全新会话里先把节点选中，再读**。选中后
//   展开 ≈ 大数字 + 有提示词框 + 有 ⤢；折起 ≈ 小数字 + 无提示词框 + 无 ⤢。
//   （这与 CJ-4 用的正是同一套 —— CJ-4 读数都带 `选中=true`，所以那几条是干净的。）
//
// 本步同时是**画布收尾复核**：如果发现某节点真的还折着，本步负责把它展开。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const NODES = [['视频', 'v-v2hlWY4Br3'], ['图片', 'i-sODTbgLUm1'], ['文本', 't-UtVx3lZmrV'], ['音频', 'a-THmbuJXQj4']];

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

const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  const fr = fold ? fold.getBoundingClientRect() : null;
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: fr ? [Math.round(fr.x), Math.round(fr.y)] : null };
}, id);

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

const out = { 复核: [] };

// ── 第 1 遍：全新会话，选中后逐个读 ─────────────────────────────
{
  const { browser, page } = await launch();
  await boot(page);
  console.log('════ 全新会话 · 选中后逐个读 ════');
  for (const [名, id] of NODES) {
    const pt = await exclusive(page, id);
    if (!pt) { console.log(`  ${名} ${id}  扫不出独占点 ⇒ 没测到`); out.复核.push({ 名, id, 说明: '扫不出独占点' }); continue; }
    await page.mouse.click(pt[0], pt[1]);
    await page.waitForTimeout(1700);
    const r = await read(page, id);
    const 展开 = r.有提示词框 && !!r.折叠钮;
    console.log(`  ${名} ${id}  选中=${r.选中} 可见后代=${String(r.可见后代数).padStart(3)} 提示词框=${r.有提示词框} ⤢=${r.折叠钮 ? '有' : '无'}  ⇒ ${展开 ? '✅ 展开着' : '⛔ 折着'}`);
    out.复核.push({ 名, id, ...r, 展开 });
  }

  // ── 画布收尾：真折着的就展开 ──────────────────────────────
  console.log('\n════ 收尾（把还折着的展开）════');
  for (const rec of out.复核) {
    if (rec.展开 || rec.说明) continue;
    const id = rec.id;
    const b = await page.locator(`.react-flow__node[data-id="${id}"]`).boundingBox();
    await page.mouse.click(b.x + 46, b.y + 12);
    await page.waitForTimeout(1700);
    let after = await read(page, id);
    if (!after.有提示词框) { await page.mouse.click(b.x + 46, b.y + 12); await page.waitForTimeout(1600); after = await read(page, id); }
    console.log(`  ${rec.名} ${id}  复原后：${JSON.stringify(after)} ${after.有提示词框 ? '✅' : '⛔ 仍折着'}`);
    rec.复原后 = after;
  }
  await browser.close();
}

// ── 第 2 遍：再开一个全新会话复核第 1 遍的收尾 ─────────────────
{
  const { browser, page } = await launch();
  await boot(page);
  console.log('\n════ 第二个全新会话 · 复核收尾 ════');
  for (const [名, id] of NODES) {
    const pt = await exclusive(page, id);
    if (!pt) { console.log(`  ${名} 扫不出独占点`); continue; }
    await page.mouse.click(pt[0], pt[1]);
    await page.waitForTimeout(1700);
    const r = await read(page, id);
    console.log(`  ${名} ${id}  ${r.可见后代数} 提示词框=${r.有提示词框} ⇒ ${r.有提示词框 ? '✅ 展开着' : '⛔ 折着'}`);
  }
  await browser.close();
}

await writeFile(resolve(HERE, '.evidence/cj6-selected-readonly.json'), JSON.stringify(out, null, 2));
console.log('\n（本步只读 + 必要的复原；不扣积分、不点生成、不点取消）');

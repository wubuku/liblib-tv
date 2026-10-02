// Batch CA-R2 — 修复继续：删掉自己的孤儿节点，再补一个文本节点顶替被误删的那个。
//
// CA-R 的结果：按无损程度排的三步，第一步就失效了 ——
//   ⭐ **`⌘Z` 能撤销断线，但不能撤销删节点**（连线 2→2 回来过，节点删了回不来）。
//     这与 Batch Y 早就记下的老结论一致，本轮再次坐实。
//   于是只能**重建**：语义等价（同样是「文本节点 1」），但 **id 变了**。
//
// 收尾目标（两步，都用 id 认目标，不再按位置挑）：
//   ① 删掉本轮自己建的孤儿 `t-ddP5xh26up`
//   ② 补一个文本节点，顶替被误删的 `t-xVGmDWNLaZ`
//   复核：节点 11 个、文本节点 3 个、连线 2 条未动
//
// ⭐ 而这一轮本身给「没有回收站」那条阴性结论加了一个注脚：
//   **画布里没有回收站，所以删掉的节点是不可恢复的** ——
//   上一轮刚把这条查成阴性结论，这一轮自己就撞上了它的后果。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, beginBatch, logStep } from './scenario.mjs';
import { fitView, addNode, nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchCAR2';
const VICTIM = 't-xVGmDWNLaZ';
const ORPHAN = 't-ddP5xh26up';
const ORIGINALS = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1',
  'n-56F19pXVB4', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-v2hlWY4Br3', 'v-oZNpH99MtM', VICTIM];
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);
const ids = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
const edgeAria = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('aria-label')));
const titleOf = (id) => page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  return n ? (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70) : null; }, id);
const boxOf = (id) => page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);

/** ⭐ 只删**指定 id** 的节点；点完必须读回「选中的正好是它」才按 Delete。 */
const deleteById = async (id) => {
  const box = await boxOf(id);
  if (!box) return { id, ok: false, why: '不在视口里' };
  await page.mouse.click(box[0], box[1]); await settle(1200);
  const sel = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id')));
  if (sel.length !== 1 || sel[0] !== id) return { id, ok: false, why: `选中读数是 ${JSON.stringify(sel)}，不是 ${id}，不按 Delete` };
  await page.keyboard.press('Delete'); await settle(2000);
  const after = await ids();
  return { id, ok: !after.includes(id), sel, afterCount: after.length };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '删孤儿 + 补一个文本节点，全程用 id 认目标' });
  const out = {};
  const start = await ids();
  out.start = { count: start.length, ids: start, orphan: start.includes(ORPHAN), victim: start.includes(VICTIM) };
  console.log(`═══ 现状：节点 ${start.length}｜孤儿 ${ORPHAN} ${out.start.orphan ? '在' : '不在'}｜被误删的 ${VICTIM} ${out.start.victim ? '在' : '不在'}`);

  // ── ① 删掉本轮自己建的孤儿
  console.log(`\n═══ ① 删掉孤儿 ${ORPHAN} ═══`);
  const del = await deleteById(ORPHAN);
  console.log(`  ok=${del.ok}｜${JSON.stringify(del)}`);
  out.delOrphan = del;

  // ── ② 补一个文本节点顶替
  console.log('\n═══ ② 补一个文本节点 ═══');
  const made = await addNode(page, '文本', { settle: 2800 });
  const cur = await ids();
  const fresh = cur.filter((i) => !ORIGINALS.includes(i));
  console.log(`  新建：${JSON.stringify(made)}｜新拿到的 id：${JSON.stringify(fresh)}`);
  for (const f of fresh) console.log(`     ${f} → ${JSON.stringify(await titleOf(f))}`);
  out.added = { made, fresh, titles: Object.fromEntries(await Promise.all(fresh.map(async (f) => [f, await titleOf(f)]))) };

  // ── ③ 复核
  const fin = await ids();
  const texts = [];
  for (const i of fin) { const t = await titleOf(i); if (t && t.includes('文本节点')) texts.push({ id: i, t: t.slice(0, 26) }); }
  out.final = { count: fin.length, ids: fin, textNodes: texts,
    edges: await edgeAria(),
    victimBack: fin.includes(VICTIM), noExtra: fin.every((i) => ORIGINALS.includes(i)) };
  console.log(`\n═══ ③ 复核 ═══`);
  console.log(`  节点 ${fin.length} 个（目标 11）｜文本节点 ${texts.length} 个（目标 3）｜孤儿已清=${!fin.includes(ORPHAN)}`);
  console.log(`  连线：${JSON.stringify(out.final.edges)}`);
  texts.forEach((t) => console.log(`     ${t.id}  ${t.t}`));
  console.log(`  ⚠️ 被误删的 ${VICTIM}：${out.final.victimBack ? '回来了' : '**没回来（不可恢复）**'}；顶替它的新节点 id：${JSON.stringify(fresh)}`);

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 孤儿清干净了吗：${!fin.includes(ORPHAN) ? '✅' : '❌'}`);
  console.log(`  · 节点数回到 11 了吗：${fin.length === 11 ? '✅' : `❌ ${fin.length}`}`);
  console.log(`  · 文本节点回到 3 个了吗：${texts.length === 3 ? '✅' : `❌ ${texts.length}`}`);
  console.log(`  · 原 id ${VICTIM}：${out.final.victimBack ? '✅ 原样回来' : '⛔ 永久丢失，已用同类型新节点顶替'}`);

  await logStep(B, {
    id: 'CA-repair-part2',
    title: '修复收尾：孤儿已清，节点数与文本节点数回到基线（原 id 永久丢失）',
    target: 'CA-R 已坐实：⭐ **`⌘Z` 能撤销断线，但不能撤销删节点**。'
      + '所以被误删的 `t-xVGmDWNLaZ` **无法恢复**，只能补一个同类型的文本节点顶替（id 变）。\n'
      + '本轮两步都用 **id** 认目标（不再按位置/顺序挑），每步点完先读回「选中的正好是它」才按 Delete。\n'
      + '⭐ 顺带给「画布里没有回收站」那条阴性结论加了个注脚：**没有回收站 = 删掉的节点不可恢复** —— '
      + '上一轮刚把它查成阴性结论，这一轮自己撞上了它的后果。',
    evidence: out,
    visible_text: JSON.stringify({ 现状: out.start, 删孤儿: out.delOrphan, 补建: out.added, 复核: out.final }).slice(0, 3000),
  });
  console.log('\nCA-R2 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}

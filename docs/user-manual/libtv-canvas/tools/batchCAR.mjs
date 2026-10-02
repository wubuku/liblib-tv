// Batch CA-R — ⛔ 事故修复：把 CA 误删的原有节点原样恢复。
//
// 出了什么事：
//   CA 建了一个文本节点 `t-ddP5xh26up`（节点 11 → 12），
//   收尾清理时用「DOM 顺序里最后一个文本节点」来挑目标 —— ⛔ **挑错了**：
//   选中并删掉的是 **`t-xVGmDWNLaX`（用户原有的那个）**。
//   节点数回到 11 是**假象**：删的是别人的，留的是自己的。
//
// ⭐ 这条事故本身的教训，比这次修复更值钱：
//   **清理时绝不能用「位置/顺序」认目标，必须用「本轮自己造出来的那个 id」。**
//   位置会变，顺序会变，只有 id 是本轮发出去的那张身份证。
//
// 修复顺序（从最无损到有损）：
//   ① 先按一次 `⌘Z` —— ⌘Z 能撤销删除这轮刚验过，若能恢复，**连 id 都是原来的**；
//   ② 不行就重新建一个文本节点（语义上等价，id 会变，如实记录）；
//   ③ 然后用**新拿到的 id** 删掉本轮自己建的那个。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, beginBatch, logStep } from './scenario.mjs';
import { fitView, addNode, nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchCAR';
const VICTIM = 't-xVGmDWNLaZ';     // 被我误删的原有节点
const MINE = 't-ddP5xh26up';       // 本轮我建的
const ORIGINALS = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1',
  'n-56F19pXVB4', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-v2hlWY4Br3', 'v-oZNpH99MtM', VICTIM];
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);
const ids = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
const titleOf = (id) => page.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  return n ? (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) : null;
}, id);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '修复 CA 误删的原有节点' });
  const out = {};
  const start = await ids();
  out.start = { count: start.length, ids: start, victimPresent: start.includes(VICTIM), minePresent: start.includes(MINE) };
  console.log(`═══ 现状：节点 ${start.length} 个`);
  console.log(`  被误删的 ${VICTIM} 在不在：${out.start.victimPresent ? '✅ 在' : '❌ 不在'}`);
  console.log(`  我建的 ${MINE} 在不在：${out.start.minePresent ? '✅ 在' : '❌ 不在'}`);
  console.log(`  与原有 11 个比对：缺 ${JSON.stringify(ORIGINALS.filter((i) => !start.includes(i)))}｜多 ${JSON.stringify(start.filter((i) => !ORIGINALS.includes(i)))}`);

  // ── ① ⌘Z 撤销一次
  if (!out.start.victimPresent) {
    console.log('\n═══ ① 试 ⌘Z 撤销一次 ═══');
    await page.mouse.click(180, 150); await settle(500);
    await page.keyboard.down('Meta'); await page.keyboard.press('z'); await page.keyboard.up('Meta');
    await settle(2800);
    const after = await ids();
    out.undo = { count: after.length, ids: after, victimBack: after.includes(VICTIM), mineStill: after.includes(MINE) };
    console.log(`  ⌘Z 后：节点 ${after.length}｜${VICTIM} 回来=${out.undo.victimBack ? '✅' : '❌'}｜${MINE} 还在=${out.undo.mineStill ? '✅' : '❌'}`);
    console.log(`  当前：${JSON.stringify(after)}`);
  }

  // ── ② 还缺就重建
  let cur = await ids();
  if (!cur.includes(VICTIM)) {
    console.log('\n═══ ② ⌘Z 没救回来，重建一个文本节点 ═══');
    const made = await addNode(page, '文本', { settle: 2800 });
    console.log(`  新建：${JSON.stringify(made)}`);
    cur = await ids();
    const fresh = cur.filter((i) => !ORIGINALS.includes(i) && !cur.includes(MINE) ? true : i === MINE ? false : true)
      .filter((i) => !ORIGINALS.includes(i));
    console.log(`  现在的节点：${JSON.stringify(cur)}｜不在原有清单里的：${JSON.stringify(fresh)}`);
    out.recreated = { made, fresh };
  }

  // ── ③ ⭐ 用**id** 删掉本轮自己建的那个（不再按位置挑）
  cur = await ids();
  const extra = cur.filter((i) => !ORIGINALS.includes(i));
  console.log(`\n═══ ③ 要清掉的（不在原有 11 个 id 清单里的）：${JSON.stringify(extra)} ═══`);
  out.extraBefore = extra;
  for (const id of extra) {
    const t = await titleOf(id);
    console.log(`  删 ${id}（${t}）`);
    const box = await page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
    if (!box) { console.log('    不在视口，跳过'); continue; }
    await page.mouse.click(box[0], box[1]); await settle(1200);
    const sel = await page.evaluate((i) => [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id')), id);
    console.log(`    选中读数：${JSON.stringify(sel)}（要正好是 ${id} 才按）`);
    if (sel.length === 1 && sel[0] === id) {
      await page.keyboard.press('Delete'); await settle(2000);
      const after = await ids();
      console.log(`    删完：${after.includes(id) ? '❌ 还在' : '✅ 已删'}｜节点 ${after.length}`);
      if (!after.includes(id)) break;
    } else { console.log('    ⛔ 选中读数不符，不按 Delete'); }
  }

  // ── ④ 复核
  const fin = await ids();
  out.final = { count: fin.length, ids: fin,
    allOriginalsBack: ORIGINALS.every((i) => fin.includes(i)),
    noExtra: fin.every((i) => ORIGINALS.includes(i)) };
  console.log(`\n═══ ④ 复核 ═══`);
  console.log(`  节点 ${fin.length} 个（原有 ${ORIGINALS.length}）｜原有全在=${out.final.allOriginalsBack}｜无多余=${out.final.noExtra}`);
  console.log(`  ${JSON.stringify(fin)}`);
  console.log(`  ⭐ 与起始相比：缺 ${JSON.stringify(ORIGINALS.filter((i) => !fin.includes(i)))}｜多 ${JSON.stringify(fin.filter((i) => !ORIGINALS.includes(i)))}`);

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 误删的原有节点恢复了吗：${out.final.allOriginalsBack ? '✅ 是' : '❌ 否'}`);
  console.log(`  · 本轮自己建的清干净了吗：${out.final.noExtra ? '✅ 是' : '❌ 否'}`);
  if (!out.final.allOriginalsBack) console.log(`  ⚠️ 仍缺：${JSON.stringify(ORIGINALS.filter((i) => !fin.includes(i)))} —— 如实报告，不假装复原`);

  await logStep(B, {
    id: 'CA-repair-mistaken-node-deletion',
    title: '⛔ 事故修复：误删的原有节点是否恢复',
    target: 'CA 收尾清理时用「DOM 顺序最后一个文本节点」认目标，⛔ **删错了** —— '
      + '删的是用户原有的 `t-xVGmDWNLaZ`，留的是本轮自己建的。'
      + '节点数回到 11 是假象。\n'
      + '⭐ **事故本身的教训比修复更值钱：清理时绝不能用「位置/顺序」认目标，'
      + '必须用「本轮自己造出来的那个 id」** —— 位置会变、顺序会变，只有 id 是本轮发出去的身份证。\n'
      + '修复顺序按无损程度排：先 `⌘Z` 撤销（能恢复就连 id 都是原来的），不行才重建。',
    evidence: out,
    visible_text: JSON.stringify({ 现状: out.start, 撤销: out.undo, 重建: out.recreated,
      待清: out.extraBefore, 复核: out.final }).slice(0, 3000),
  });
  console.log('\nCA-R 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}

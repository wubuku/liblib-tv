// 批次 108 · c 轮：用**修正后的第四道护栏**选中本轮那两个节点 → 编组 → 核对成员。
//
// 🔴🔴 本轮最重要的一条是**把我自己立的护栏改掉**（批次 105 写进概念页的那条）：
//   原护栏要求落点 **「不在任何他人节点矩形内」**。本轮实测这条件是**假阴性**：
//   甲（`node_d6cn9z91w6`，`544,312 192×192`）的 2209 个采样点里——
//     · 命中甲自身或其后代：**1615** 个
//     · 其中被「矩形重叠」条件杀掉的：**594** 个
//       （`node_d4tjtpnatq` 时间线 2 占 216 个、`node_9y4j9jf0qv` 音频 6 占 378 个）
//     · 按原护栏可用落点：**0** 个 ⇒ 脚本只能中止
//   可是**那两个节点在甲下面**：矩形相交，但 `elementFromPoint` 在那 594 个点上传回的
//   确实是甲自己的后代 ⇒ **那些点本来完全可点**。
//
// ⇒ 📌 **判据修正：只认「`elementFromPoint` 的结果在目标内部」这一条。**
//   它**已经把层叠算进去了**（返回的是最上层元素）；
//   再加一条「不在他人矩形内」只会引入假阴性。
//   批次 105 那次误删靠的本来就是 `elementFromPoint` —— 矩形条件是多余的 belt，
//   而这条 belt 本轮被证明会**勒死自己**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), mine: ['node_d6cn9z91w6', 'node_8vwsfmqc24'] };
const [A, C] = out.mine;
const save = () => writeFileSync(new URL('./_tmp-b108c.json', import.meta.url), JSON.stringify(out, null, 1));

const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1] }; });

/** 🔑 修正后的落点判据：只看 elementFromPoint（已含层叠），不再叠加矩形条件 */
const spot = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const c = [];
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 4)
    for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 4) {
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (el && (el === n || n.contains(el))) c.push({ x, y });
    }
  return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    total: c.length, sample: c.slice(0, 6) };
}, id);

out.start = await status();
log('起点：', JSON.stringify(out.start));
if ((await selIds()).length) { await p.mouse.click(8, 300); await p.waitForTimeout(1300); log('已取消选中 →', JSON.stringify(await selIds())); }

out.spotA = await spot(A); log('\n甲落点（修正判据）：', JSON.stringify(out.spotA));
out.spotC = await spot(C); log('乙落点（修正判据）：', JSON.stringify(out.spotC));
save();
if (!out.spotA.total || !out.spotC.total) { log('🔴 修正判据下仍无落点，中止'); save(); await b.close(); process.exit(1); }

const pa = out.spotA.sample[Math.floor(out.spotA.sample.length / 2)] || out.spotA.sample[0];
const pc = out.spotC.sample[Math.floor(out.spotC.sample.length / 2)] || out.spotC.sample[0];
log('\n用：甲', JSON.stringify(pa), '｜乙', JSON.stringify(pc));

// ① 单击甲
await p.mouse.move(pa.x, pa.y); await p.waitForTimeout(500);
await p.mouse.click(pa.x, pa.y); await p.waitForTimeout(1500);
out.afterA = await selIds();
log('\n点甲之后选中：', JSON.stringify(out.afterA));
if (out.afterA.length !== 1 || out.afterA[0] !== A) { log('🔴 选中不对（期望恰好 [甲]），中止'); save(); await b.close(); process.exit(1); }

// ② Shift+点乙
log('\n>>> Shift+点乙（此刻甲的浮层会盖住乙，判据已不含它）');
await p.keyboard.down('Shift'); await p.waitForTimeout(250);
await p.mouse.move(pc.x, pc.y); await p.waitForTimeout(500);
await p.mouse.click(pc.x, pc.y); await p.waitForTimeout(250);
await p.keyboard.up('Shift'); await p.waitForTimeout(1500);
out.afterC = await selIds();
log('Shift 点乙之后选中：', JSON.stringify(out.afterC));
out.selOk = out.afterC.length === 2 && out.afterC.includes(A) && out.afterC.includes(C);
log('选中核对 =', out.selOk ? '✅ 恰好本轮那两个' : '🔴 不对，**中止编组**');
save();
if (!out.selOk) { await b.close(); process.exit(1); }

out.multiBar = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid]'))
  .filter((e) => /toolbar/i.test(e.getAttribute('data-testid') || ''))
  .map((e) => ({ tid: e.getAttribute('data-testid'), n: e.querySelectorAll('button,[role=button]').length,
    aria: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => x.getAttribute('aria-label') || (x.innerText || '').trim()).filter(Boolean) }))
  .filter((x) => x.n >= 2 && x.n <= 6));
log('\n多选工具条：', JSON.stringify(out.multiBar));
save();

// ③ ⌘G
const g = await keyGuard(p);
out.guardG = g;
log('\nkeyGuard（按 ⌘G 前）：', JSON.stringify(g));
if (!g.safe) { log('🔴 守卫拒绝，中止'); save(); await b.close(); process.exit(1); }
const before = await allIds();
out.idsBeforeGroup = before.length;
await p.keyboard.press('Meta+g');
await p.waitForTimeout(2200);
const after = await allIds();
out.idsAfterGroup = after.length;
out.newIds = after.filter((x) => !before.includes(x));
log('\n⌘G 后：id 数', before.length, '→', after.length, '｜新增：', JSON.stringify(out.newIds));
out.afterGroupStatus = await status();
log('状态行：', JSON.stringify(out.afterGroupStatus));
save();

const GROUP = out.newIds.length === 1 ? out.newIds[0] : null;
out.groupId = GROUP;
log('\nGROUP =', GROUP);
if (GROUP) {
  out.groupInfo = await p.evaluate((g) => {
    const n = document.querySelector(`.react-flow__node[data-id="${g}"]`); if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    const inner = Array.from(n.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'));
    return { aria: n.getAttribute('aria-label'), text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 200),
      rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      inner, innerCount: inner.length,
      testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))) };
  }, GROUP);
  log('组读数：', JSON.stringify(out.groupInfo, null, 1));
  const expect = out.mine.slice().sort();
  const got = (out.groupInfo.inner || []).slice().sort();
  out.membersOk = JSON.stringify(expect) === JSON.stringify(got);
  log('成员核对：期望', JSON.stringify(expect), '｜实际', JSON.stringify(got), '⇒', out.membersOk ? '✅' : '🔴');
}
out.clean = Boolean(GROUP) && out.membersOk;
save();
log('\n已落盘 clean =', out.clean);
await b.close();

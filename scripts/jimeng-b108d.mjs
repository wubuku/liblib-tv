// 批次 108 · d 轮：加上**「落点必须按动作时刻重算」**这一条，再编组。
//
// 🔴 c 轮的新问题（护栏的第 N 次进化，仍是护栏不是产品）：
//   甲选中**成功**了（`elementFromPoint` 修正后落点从 0 变 594 个），但随后
//   **Shift+点乙 之后选中变成了 `[]`** —— 甲被取消了。
//   原因：我给乙选的落点 `(582,363)` 是在**「甲还没被选中」的时候**算的，
//   而那个坐标落在**甲的矩形内**。甲一被选中，它上方的
//   `selection-context-toolbar` 浮层就盖住了那个点 ⇒ Shift+点击被浮层吃掉。
//
// ⇒ 📌 **第四道护栏的最终形态，三条一起才够**：
//   ① `elementFromPoint` 命中目标内部（**已含层叠，不要再叠矩形条件** —— 那是假阴性）；
//   ② **落点必须在「这一步动作即将发生」的那一刻现算**，
//      因为**前一步会改变层叠**（选中会浮出工具条、编辑态会盖住整张卡）；
//   ③ 点完必须读到预期状态（`selected === true` / 选中集合逐字相符）才继续。
//
// 本轮顺序：点甲 → 核对 → **重算乙的落点** → Shift+点乙 → 核对。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), mine: ['node_d6cn9z91w6', 'node_8vwsfmqc24'] };
const [A, C] = out.mine;
const save = () => writeFileSync(new URL('./_tmp-b108d.json', import.meta.url), JSON.stringify(out, null, 1));

const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1] }; });

// 动作时刻现算的落点：只认 elementFromPoint；**顺带报出挡住它的元素**，方便排查
const spotNow = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const c = []; const blockers = {};
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 4)
    for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 4) {
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (el && (el === n || n.contains(el))) { c.push({ x, y }); continue; }
      const k = el ? `${el.tagName}[${el.getAttribute('data-testid') || ''}]` : 'null';
      blockers[k] = (blockers[k] || 0) + 1;
    }
  return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    total: c.length, sample: c.slice(0, 6), blockers };
}, id);

out.start = await status();
log('起点：', JSON.stringify(out.start));
if ((await selIds()).length) { await p.mouse.click(8, 300); await p.waitForTimeout(1300); }

// ① 点甲
const sa = await spotNow(A);
out.spotA = sa;
log('\n甲落点（动作时刻）：', JSON.stringify({ rect: sa.rect, total: sa.total }));
if (!sa.total) { log('🔴 甲无落点'); save(); await b.close(); process.exit(1); }
const pa = sa.sample[Math.floor(sa.sample.length / 2)];
log('用：甲', JSON.stringify(pa));
await p.mouse.move(pa.x, pa.y); await p.waitForTimeout(500);
await p.mouse.click(pa.x, pa.y); await p.waitForTimeout(1500);
out.afterA = await selIds();
log('点甲之后选中：', JSON.stringify(out.afterA));
if (out.afterA.length !== 1 || out.afterA[0] !== A) { log('🔴 选中不对，中止'); save(); await b.close(); process.exit(1); }
save();

// ② 关键：**此刻**重算乙的落点（甲已选中，它的浮层已经浮出）
const sc = await spotNow(C);
out.spotC = sc;
log('\n乙落点（**甲已选中**这一刻重算）：', JSON.stringify({ rect: sc.rect, total: sc.total }));
log('  挡住乙的元素 TOP5：', JSON.stringify(Object.entries(sc.blockers || {}).sort((a, b) => b[1] - a[1]).slice(0, 5)));
if (!sc.total) { log('🔴 此刻乙无落点 —— 说明甲的浮层把乙整个盖住了，**如实记录，不硬来**'); save(); await b.close(); process.exit(2); }
const pc = sc.sample[Math.floor(sc.sample.length / 2)];
log('用：乙', JSON.stringify(pc));

await p.keyboard.down('Shift'); await p.waitForTimeout(250);
await p.mouse.move(pc.x, pc.y); await p.waitForTimeout(500);
await p.mouse.click(pc.x, pc.y); await p.waitForTimeout(250);
await p.keyboard.up('Shift'); await p.waitForTimeout(1500);
out.afterC = await selIds();
log('\nShift 点乙之后选中：', JSON.stringify(out.afterC));
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

// 批次 108 · b 轮：精确选中本轮那两个节点 → 编组 → 核对成员。
//
// 🔴 a 轮撞出的地形问题：两次上传落点几乎重合 ——
//   甲 `544,312 192×192`、乙 `568,360 192×192`（只错开 x+24 / y+48），
//   于是**两个节点互相压住**，标准落点扫描给**各 0 个**。
//   第四道护栏照常生效：拿不到落点就不点，**没有硬来**。
//
// 本轮的解法：**用「属于自己且不属于任何他人」的重叠外点**。
//   甲的非重叠区在**上边**（y 312–360）与**左边**（x 544–568）；
//   乙的非重叠区在**右边**（x 736–760）与**下边**（y 504–552）。
//   扫描时把「他人矩形」= **除自己以外的所有节点**（含另一个自建节点）。
//
// 🔴 按 ⌘G 之前必须先把选中的 `data-id` 全量打出来、**逐字核对**只有那两个；
//   编组后再核对组成员**恰好**是那两个。任何一步对不上就中止。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), mine: ['node_d6cn9z91w6', 'node_8vwsfmqc24'] };
const [A, C] = out.mine;
const save = () => writeFileSync(new URL('./_tmp-b108b.json', import.meta.url), JSON.stringify(out, null, 1));

const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1] }; });

// 只属于自己、且不在任何他人矩形内的落点
const spot = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const others = Array.from(document.querySelectorAll('.react-flow__node'))
    .filter((e) => e.getAttribute('data-id') !== i)
    .map((e) => { const q = e.getBoundingClientRect(); return { id: e.getAttribute('data-id'), x: q.x, y: q.y, w: q.width, h: q.height }; })
    .filter((o) => o.w > 0 && o.h > 0);
  const c = [];
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 4) {
    for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 4) {
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !(el === n || n.contains(el))) continue;
      const blocking = others.filter((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h);
      if (blocking.length) continue;
      c.push({ x, y });
    }
  }
  return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    others: others.length, total: c.length, sample: c.slice(0, 6) };
}, id);

out.start = await status();
log('起点：', JSON.stringify(out.start));
// 🔴 必须先取消选中：上一个节点的 `selection-context-toolbar` 浮层会**盖住**另一个，
//    使它的干净落点直接归零（本轮实测：乙被选中时，甲的 7 个采样点里 5 个不可命中）。
log('>>> 先点画布空白取消选中');
await p.mouse.click(8, 300); await p.waitForTimeout(1400);
out.selCleared = await selIds();
log('取消后选中：', JSON.stringify(out.selCleared));
out.spotA = await spot(A); log('\n甲的落点：', JSON.stringify(out.spotA));
out.spotC = await spot(C); log('乙的落点：', JSON.stringify(out.spotC));
save();
if (!out.spotA.total || !out.spotC.total) { log('🔴 仍无干净落点，中止'); save(); await b.close(); process.exit(1); }

const pa = out.spotA.sample[Math.floor(out.spotA.sample.length / 2)] || out.spotA.sample[0];
const pc = out.spotC.sample[Math.floor(out.spotC.sample.length / 2)] || out.spotC.sample[0];
log('\n用：甲', JSON.stringify(pa), '｜乙', JSON.stringify(pc));

// ① 单击甲 —— 注意：如果乙当前是选中态，先点空白清掉
out.selNow = await selIds();
log('\n当前选中：', JSON.stringify(out.selNow));
if (out.selNow.length && !(out.selNow.length === 1 && out.selNow[0] === A)) {
  log('  先点画布空白清空选中');
  await p.mouse.click(8, 300); await p.waitForTimeout(1100);
  out.selCleared = await selIds();
  log('  清空后：', JSON.stringify(out.selCleared));
}
await p.mouse.move(pa.x, pa.y); await p.waitForTimeout(500);
await p.mouse.click(pa.x, pa.y); await p.waitForTimeout(1400);
out.afterA = await selIds();
log('点甲之后选中：', JSON.stringify(out.afterA));
if (out.afterA.length !== 1 || out.afterA[0] !== A) { log('🔴 选中不对（期望恰好 [甲]），中止'); save(); await b.close(); process.exit(1); }

// ② Shift+点乙
log('\n>>> Shift+点乙');
await p.keyboard.down('Shift'); await p.waitForTimeout(250);
await p.mouse.move(pc.x, pc.y); await p.waitForTimeout(450);
await p.mouse.click(pc.x, pc.y); await p.waitForTimeout(250);
await p.keyboard.up('Shift'); await p.waitForTimeout(1400);
out.afterC = await selIds();
log('Shift 点乙之后选中：', JSON.stringify(out.afterC));
out.selOk = out.afterC.length === 2 && out.afterC.includes(A) && out.afterC.includes(C);
log('选中核对 =', out.selOk ? '✅ 恰好本轮那两个' : '🔴 不对，**中止编组**');
save();
if (!out.selOk) { await b.close(); process.exit(1); }

// 多选工具条读数（顺便记一笔）
out.multiBar = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid]'))
  .filter((e) => /toolbar/i.test(e.getAttribute('data-testid') || ''))
  .map((e) => ({ tid: e.getAttribute('data-testid'), n: e.querySelectorAll('button,[role=button]').length,
    aria: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => x.getAttribute('aria-label') || (x.innerText || '').trim()).filter(Boolean) }))
  .filter((x) => x.n >= 2 && x.n <= 6));
log('\n多选工具条：', JSON.stringify(out.multiBar));
save();

// ③ ⌘G 编组（keyGuard 必过）
const g = await keyGuard(p);
out.guardG = g;
log('\nkeyGuard（按 ⌘G 前）：', JSON.stringify(g));
if (!g.safe) { log('🔴 守卫拒绝，中止'); save(); await b.close(); process.exit(1); }
const before = await allIds();
out.idsBeforeGroup = before.length;
await p.keyboard.press('Meta+g');
await p.waitForTimeout(2000);
const after = await allIds();
out.idsAfterGroup = after.length;
out.newIds = after.filter((x) => !before.includes(x));
log('\n⌘G 后：id 数', before.length, '→', after.length, '｜新增：', JSON.stringify(out.newIds));
out.afterGroupStatus = await status();
log('状态行：', JSON.stringify(out.afterGroupStatus));
save();

// ④ 核对组：aria 逐字 + 成员恰好是那两个
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
      testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
      handles: Array.from(n.querySelectorAll('[data-testid*=handle]')).map((e) => { const q = e.getBoundingClientRect();
        return { tid: e.getAttribute('data-testid'), w: Math.round(q.width), h: Math.round(q.height) }; }) };
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

// 批次 179：钉死批次 176 / 178 之间那个**未解释的差异**。
//
// 差异本体：
//   批次 176 普查（76 个节点逐条）⇒ **68 个**音频节点的描述逐字是
//     `No resources. Current preview: 暂无音频. Not selected.`
//   批次 178 读**同一个** `音频 1`（node_ay7f1jn45r）逐字却是
//     `No resources: 0 ready, 0 processing, 0 failed. Not selected.`
//   ⇒ 两批之间夹着**若干次刷新与选中操作**，而批次 178 **没有控住
//     「刷新会不会改这段文案」这个变量** —— 所以只能记成未解释的差异。
//
// 本批就是把这个变量控住：**只改一个变量**（刷新 / 不刷新），其余全部固定。
//   A 组：不刷新，连读 3 次（判「它自己会不会变」）
//   B 组：刷新 1 次，立刻读
//   C 组：再刷新 1 次，再读（判「刷新后稳不稳」）
//   D 组：选中它，读；取消选中，再读（判「选中会不会改」——批次 178 说是会，
//        这里验证它改的到底是哪一段）
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '179' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 音频1 = 'node_ay7f1jn45r';   // 批次 178 读过的那个
const 读 = () => p.evaluate((i) => {
  const h = document.getElementById(`canvas-node-description-${i}`);
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  return { 描述: h ? (h.innerText || '').trim() : null, 节点aria: n?.getAttribute('aria-label') ?? null,
    选中: n?.classList.contains('selected') ?? null, 节点数: document.querySelectorAll('.react-flow__node').length };
}, 音频1);
const 刷新 = async () => { await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
  const t0 = Date.now();
  while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
  await p.waitForTimeout(2500); };

// ── A 组：不刷新，连读 3 次
rec.A_不刷新 = [];
for (let i = 0; i < 3; i++) { rec.A_不刷新.push(await 读()); await p.waitForTimeout(1500); }
rec.A_三次相同 = JSON.stringify(rec.A_不刷新.map((x) => x.描述)) ===
  JSON.stringify([rec.A_不刷新[0].描述, rec.A_不刷新[0].描述, rec.A_不刷新[0].描述]);

// ── 关键：现在**全量**再普查一次，跟批次 176 的口径完全一样
const 全量 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const id = n.getAttribute('data-id');
  const h = document.getElementById(`canvas-node-description-${id}`);
  return { id, 类型: (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null, 描述: h ? (h.innerText || '').trim() : null };
}));
const 分组 = (们) => Object.entries(们.reduce((a, x) => {
  const k = (x.描述 || '(无)').replace(/node_\w+/g, '<id>'); a[k] = (a[k] || 0) + 1; return a; }, {}))
  .map(([文案, n]) => ({ 文案, n })).sort((a, b2) => b2.n - a.n);
rec.全量_刷新前 = 分组(await 全量());
rec.全量_刷新前_音频1 = (await 全量()).find((x) => x.id === 音频1);

// ── B 组：刷新 1 次
await 刷新();
rec.B_刷新1次 = await 读();
rec.全量_刷新后 = 分组(await 全量());

// ── C 组：再刷新 1 次
await 刷新();
rec.C_刷新2次 = await 读();
rec.全量_刷新2次 = 分组(await 全量());

// ── D 组：选中 / 取消选中，只改这一个变量
const 选中 = async () => {
  await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.scrollIntoView({ block: 'center', inline: 'center' }), 音频1);
  await p.waitForTimeout(900);
  const q = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect();
    if (r.width < 2 || r.x < 0 || r.x > innerWidth || r.y < 0 || r.y > innerHeight) return null;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 音频1);
  if (!q) return false;
  await p.mouse.click(q[0], q[1]); await p.waitForTimeout(900);
  const s = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.getAttribute('data-id')));
  return s.length === 1 && s[0] === 音频1;
};
rec.D_选中成功 = await 选中();
rec.D_选中时 = await 读();
await p.mouse.click(640, 690); await p.waitForTimeout(1200);
rec.D_取消后 = await 读();

// ── 收尾：刷新复位
await p.keyboard.press('Escape'); await p.waitForTimeout(500);
await 刷新();
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(),
  节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length),
  选中: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length) };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

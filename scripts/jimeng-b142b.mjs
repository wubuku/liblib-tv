// 批次 142 b 轮（重写）：组 vs 节点把手**同会话逐档对照**。
//
// 🔴 前两版各栽一个坑，本版从结构上绕开：
//   v1「复用 a 轮留下的组」→ 换缩放后组标题落点失效 → 读数整段跳过；
//      而 `.every()` 对**空数组恒 true** ⇒ **五个公式断言全部假绿**。
//      ⇒ 本版加**非空断言**放在所有 `.every()` 之前（门必须报红，不能假绿）。
//   v2「每档现算标题落点」→ 组卡片未选中时 **`pointer-events: none`**，
//      标题 SPAN **完全不可点**（逐格扫 720 点 0 命中）⇒ 又是空集。
//
// 🔑 **结构上的正解**：**编组完成后组自动处于选中态**（组工具条四项已在），
//   此时**八向把手全部可读可点**，**根本不需要碰标题**。
//   标题只在「组已取消选中」时才是唯一的选中入口 —— 本轮全程不离开选中态。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, 点选一组, 点编组, 可点落点, selCount, idsOf, 组数 } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 档位 = [80, 100, 120, 150, 200];
const rec = { 轮: '142b-v3', 档位 };
let 全过 = true;
const 断言 = (名, ok, 详情) => { (rec.断言 = rec.断言 || []).push({ 名, 通过: !!ok, 详情 }); if (!ok) 全过 = false; };

const { b, p } = await openCanvas();
const R = readers(p);

/** 组是否处于选中态（只看真身，滤影子）。 */
const 组选中 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
  .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
  .filter((g) => g.classList.contains('selected')).length);

/** 读组把手（要求组选中）。**只读**。 */
const 读组 = (p) => p.evaluate(() => {
  const s = (() => { const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
    return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; })();
  const sh = document.querySelector('[data-id^="__group-resize-chrome__"].react-flow__node-group');
  if (!sh) return { __err: 'no-shadow', scale: s };
  const 角 = Array.from(sh.querySelectorAll('[aria-label^="Resize group from"]'))
    .filter((e) => /nwse|nesw/.test(getComputedStyle(e).cursor || ''));
  const 边 = Array.from(sh.querySelectorAll('[aria-label^="Resize group from"]'))
    .filter((e) => /ns-resize|ew-resize/.test(getComputedStyle(e).cursor || ''));
  const r2 = (e) => Math.round(e.getBoundingClientRect().width * 100) / 100;
  const r3 = (e) => Math.round(e.getBoundingClientRect().height * 100) / 100;
  const g = document.querySelector('.react-flow__node-group:not([data-id^="__group-resize-chrome__"])');
  return { scale: s, 角边长: 角[0] ? r2(角[0]) : null, 边长: 边[0] ? r2(边[0]) : null, 边厚: 边[0] ? r3(边[0]) : null,
    卡片canvas: g ? g.offsetWidth : null };
});

/** 读节点把手（要求该节点选中）。**只读**。 */
const 读节点 = (p, id) => p.evaluate((ID) => {
  const s = (() => { const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
    return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; })();
  const n = document.querySelector(`.react-flow__node[data-id="${ID}"]`);
  if (!n) return { __err: 'node-gone', scale: s };
  const all = Array.from(n.querySelectorAll('[data-testid^="text-node-resize-"]'));
  const 角 = all.filter((e) => /nwse|nesw/.test(getComputedStyle(e).cursor || ''));
  const 边 = all.filter((e) => /ns-resize|ew-resize/.test(getComputedStyle(e).cursor || ''));
  const r2 = (e) => Math.round(e.getBoundingClientRect().width * 100) / 100;
  const r3 = (e) => Math.round(e.getBoundingClientRect().height * 100) / 100;
  return { scale: s, 角边长: 角[0] ? r2(角[0]) : null, 边长: 边[0] ? r2(边[0]) : null, 边厚: 边[0] ? r3(边[0]) : null,
    节点canvas: n.offsetWidth };
}, id);

/** 本场景专用的建节点：护栏只看「差集恰好 1 + 新节点恰好 selected」，
 *  **不检查「建前无组」** —— b 轮是「先建组、再建对照节点」，建第二个节点时组已存在。 */
async function 建一个(p, R, 断言) {
  const 记 = async (名, ok, 详情) => 断言(名, !!ok, 详情);
  const 前 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
  const pt = await 可点落点(p, '[aria-label="文本"]', 3, 3);
  if (pt.__err) { await 记('建节点失败', false, pt); return null; }
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(2500);
  await settle(p, R);
  const 后 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
  const 新增 = 后.filter((x) => !前.includes(x));
  await 记('建后差集恰好 1 个', 新增.length === 1, { 新增 });
  if (新增.length !== 1) return null;
  const SELF = 新增[0];
  const 是选中 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    return !!(n && n.classList.contains('selected')); }, SELF);
  await 记('新节点恰好 .selected', 是选中, { SELF });
  return 是选中 ? SELF : null;
}

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), 选中: await selCount(p), zoom: await R.zoom() };
  断言('①起始无组、0 选中', (await 组数(p)) === 0 && (await selCount(p)) === 0, { 组: await 组数(p), 选: await selCount(p) });

  // 建 3 个节点（组还不在，符合「建前无组」）
  const 三 = [];
  for (let i = 0; i < 3; i++) { const id = await 建一个(p, R, 断言); if (id) 三.push(id); else break; }
  if (三.length !== 3) { rec.中止 = '建 3 节点未成'; }
  else {
    const 选3 = await 点选一组(p, 三);
    断言('②点选恰好选中 3 个', 选3.ok, { 选中: 选3.最终选中 });
    const 编组 = 选3.ok ? await 点编组(p) : { ok: false };
    断言('③编组后恰好 1 个真身组', 编组.ok, 编组);
    // 🔑 关键前提：编组后组**自动选中** —— 这才是「不碰标题也能读把手」的根据
    rec.编组后组选中 = await 组选中(p);
    断言('④编组后组自动处于选中态（否则本轮方案不成立）', rec.编组后组选中 === 1, { 组选中: rec.编组后组选中 });

    if (编组.ok && rec.编组后组选中 === 1) {
      // 建一个对照节点 —— 必须在**组外面**，否则会被吸进组里。
      // ⚠️ 此处**组已存在**，所以不能用 `建N个`（它的 ①b 护栏要求「建前无组」）⇒ 用上面那个
      //   本场景专用的 `建一个`。这条护栏设计缺陷本轮也记进 AUDIT。
      if (await selCount(p) > 0) { await p.mouse.click(8, 660); await p.waitForTimeout(900); }
      const 靶 = await 建一个(p, R, 断言);
      rec.靶 = 靶;

      rec.各档 = [];
      for (const pct of 档位) {
        const z = await setZoom(p, pct);
        断言(`⑤${pct}% 实测 scale 已追平`, z.scale已追平, { z });
        // —— 臂 1：组保持选中（编组后一直选中，**不碰标题**）
        const gSel = await 组选中(p);
        let 组读 = { __err: '组未选中' };
        if (gSel === 1) 组读 = await 读组(p);
        // —— 臂 2：点选对照节点，读节点把手（点节点会取消组选中，**每档读完再点回组**）
        let 节点读 = { __err: 'no-target' };
        if (靶) {
          const 落 = await 可点落点(p, `.react-flow__node[data-id="${靶}"]`, 4, 4);
          if (!落.__err) {
            await p.mouse.click(落.x, 落.y);
            await p.waitForTimeout(1000);
            节点读 = await 读节点(p, 靶);
          }
        }
        rec.各档.push({ 标称: pct, 追平: z.scale已追平, 组选中数: gSel, 组读, 节点读 });
      }

      // ---- 非空断言（放在所有 .every 之前）
      const 有读数 = rec.各档.filter((d) => d.组读 && d.组读.角边长 && d.节点读 && d.节点读.角边长);
      rec.有读数档数 = 有读数.length;
      断言('⑥五档都真的读到组与节点把手（防空集通过）', rec.有读数档数 === 5,
        { 有读数档数, 摘要: rec.各档.map((d) => ({ 标称: d.标称, 组: d.组读 && d.组读.角边长, 节点: d.节点读 && d.节点读.角边长 })) });

      if (rec.有读数档数 > 0) {
        rec.对照 = 有读数.map((d) => ({
          标称: d.标称, scale: d.标称 / 100,
          组角: d.组读.角边长, 节点角: d.节点读.角边长,
          组边厚: d.组读.边厚, 节点边厚: d.节点读.边厚,
          组边长反推canvas: Math.round(d.组读.边长 / d.组读.scale * 100) / 100,
          节点边长反推canvas: Math.round(d.节点读.边长 / d.节点读.scale * 100) / 100,
        }));
        const 验 = (key, f) => rec.对照.map((x) => ({ 标称: x.标称, 实测: x[key], 预测: Math.round(f(x.scale) * 100) / 100,
          成立: Math.abs(f(x.scale) - x[key]) < 0.01 }));
        rec.组角验 = 验('组角', (s) => Math.max(24 * s, 24));
        rec.节点角验 = 验('节点角', (s) => Math.min(48 * s, 24));
        rec.组边厚验 = 验('组边厚', (s) => 10 * s);
        rec.节点边厚验 = 验('节点边厚', (s) => Math.min(20 * s, 10));
        断言('⑦组角 = max(24×scale, 24)（保底）', rec.组角验.every((x) => x.成立), rec.组角验);
        断言('⑧节点角 = min(48×scale, 24)（封顶）', rec.节点角验.every((x) => x.成立), rec.节点角验);
        断言('⑨组边厚 = 10×scale（无钳位）', rec.组边厚验.every((x) => x.成立), rec.组边厚验);
        断言('⑩节点边厚 = min(20×scale, 10)（封顶）', rec.节点边厚验.every((x) => x.成立), rec.节点边厚验);
        const 高档 = rec.对照.filter((x) => x.标称 >= 120);
        rec.高档组大于节点 = 高档.every((x) => x.组角 > x.节点角);
        断言('⑪≥120% 时组角 > 节点角（钳位方向相反的直接证据）', 高档.length > 0 && rec.高档组大于节点, 高档);
        rec.组卡片canvas去重 = [...new Set(rec.各档.map((d) => d.组读 && d.组读.卡片canvas))];
        rec.节点canvas去重 = [...new Set(rec.各档.map((d) => d.节点读 && d.节点读.节点canvas))];
        断言('⑫组卡片/节点 canvas 五档各自恒定（证明没换对象）',
          rec.组卡片canvas去重.length === 1 && rec.节点canvas去重.length === 1,
          { 组: rec.组卡片canvas去重, 节点: rec.节点canvas去重 });
      }
    }
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }

try {
  const z = await setZoom(p, 60);
  rec.归位 = { zoom: await R.zoom(), 追平: z.scale已追平 };
  if ((await R.minimap()) && (await R.minimap()).ariaPressed !== 'true') {
    const mm = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
    if (!mm.__err) { await p.mouse.click(mm.x, mm.y); await p.waitForTimeout(1200); }
  }
  rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), 选中: await selCount(p), zoom: await R.zoom() };
} catch (e) { rec.收尾异常 = String(e && e.message).slice(0, 200); }

rec.断言全过 = 全过;
fs.writeFileSync(new URL('./_tmp-b142b.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('断言全过', 全过, '| 通过', (rec.断言 || []).filter((a) => a.通过).length, '/', (rec.断言 || []).length);
(rec.断言 || []).filter((a) => !a.通过).forEach((a) => console.log('  ❌', a.名, JSON.stringify(a.详情).slice(0, 240)));
console.log('| 缩放 | 组角 | 节点角 | 组边厚 | 节点边厚 | 组边长canvas | 节点边长canvas |');
for (const x of rec.对照 || []) console.log(`| ${x.标称}% | **${x.组角}** | **${x.节点角}** | ${x.组边厚} | ${x.节点边厚} | ${x.组边长反推canvas} | ${x.节点边长反推canvas} |`);
await b.close();

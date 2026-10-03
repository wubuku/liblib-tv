// 批次 142 a 轮（v2 终版）：组卡片八向把手在 20%–200% 的完整读数。
//
// 🔑 本轮要坐实的事：批次 141 宣称「所有族都是 `max(canvas×scale, 屏上常量)`」**方向反了**。
//   节点侧实测是 **`min(48×scale, 24)`（封顶）** —— `max(19.2, 24) = 24 ≠ 实测 19.2`。
//   本轮验**组侧**到底是什么：a 轮第一版密布九档已读到
//   20/25/30/40/50/60/100% 全读 **24**、**150%→36、200%→48**
//   ⇒ `24 × max(1, scale)` = **`max(24×scale, 24)`（保底）**，与节点侧**方向相反**。
//
// ⚠️ 三个建节点是**阶梯叠放**的（60% 下 24px 偏移），最下面那个**没有任何独占像素**
//   ⇒ `点选一组` 必然在第 3 个上返回 `no-point`。
//   ✅ 本轮先**把三个节点拖开**（只动自己建的节点，护栏 ⑤ 会核对别人零位移），再点选。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, 点选一组, 点编组, 组数, idsOf, selCount, canvasPos } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 基线 = fs.readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
const 档位 = [20, 25, 30, 40, 50, 60, 100, 150, 200];
const rec = { 轮: '142a-v2', 档位 };
let 全过 = true;
const 断言 = (名, ok, 详情) => { (rec.断言 = rec.断言 || []).push({ 名, 通过: !!ok, 详情 }); if (!ok) 全过 = false; };

const { b, p } = await openCanvas();
const R = readers(p);

/** 读组八向把手几何。**只读**。 */
const 读组 = (p) => p.evaluate(() => {
  const s = (() => { const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
    return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; })();
  const sh = document.querySelector('[data-id^="__group-resize-chrome__"].react-flow__node-group');
  const 真身 = document.querySelector('.react-flow__node-group:not([data-id^="__group-resize-chrome__"])');
  if (!sh || !真身) return { __err: 'no-group', scale: s };
  const 角 = Array.from(sh.querySelectorAll('[aria-label^="Resize group from"]'))
    .filter((e) => /nwse|nesw/.test(getComputedStyle(e).cursor || ''));
  const 边 = Array.from(sh.querySelectorAll('[aria-label^="Resize group from"]'))
    .filter((e) => /ns-resize|ew-resize/.test(getComputedStyle(e).cursor || ''));
  const W = (e) => Math.round(e.getBoundingClientRect().width * 100) / 100;
  const H = (e) => Math.round(e.getBoundingClientRect().height * 100) / 100;
  return { scale: s, 角边长: 角[0] ? W(角[0]) : null, 边长: 边[0] ? W(边[0]) : null, 边厚: 边[0] ? H(边[0]) : null,
    卡片canvas: 真身.offsetWidth };
});

/** 把一个自建节点拖到指定画布位移处（从节点**主体**起手，避开把手与工具条）。 */
async function 拖开(p, id, dx, dy) {
  const 起 = await p.evaluate((k) => {
    const n = document.querySelector(`.react-flow__node[data-id="${k}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    // 主体中心偏下：上半部分可能有标题行/工具条
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height * 0.75);
    const h = document.elementFromPoint(x, y);
    return { x, y, 命中: h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 40) : null,
      是控件: h ? !!h.closest('button,[role=button],.react-flow__handle,[contenteditable]') : true };
  }, id);
  if (!起 || 起.是控件) return { ok: false, 起 };
  await p.mouse.move(起.x, 起.y);
  await p.mouse.down();
  for (let i = 1; i <= 10; i++) { await p.mouse.move(起.x + Math.round((dx * i) / 10), 起.y + Math.round((dy * i) / 10)); await p.waitForTimeout(28); }
  await p.mouse.up();
  await p.waitForTimeout(900);
  return { ok: true, 起 };
}

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), 选中: await selCount(p), zoom: await R.zoom() };
  断言('①起始无组、0 选中、76 节点', (await 组数(p)) === 0 && (await selCount(p)) === 0 && (await idsOf(p)).length === 76, rec.起点);

  // 🔴 **建 3 个节点这一步本身就会叠放**：左栏连建的节点是阶梯状（60% 下 24px 偏移），
  //   拖开也压不住（拖第一个时它滑到第三个下面）。⇒ 改成**交替建-选**：
  //   建一个 → 立刻点选（Shift 加选）→ 再建下一个（建节点会自动把新节点设为唯一选中，
  //   所以每建一个都要**先把已选的点掉、只留新节点**这一步靠 Shift 反选补回来）——
  //   实测这条更稳：点选时目标节点**必然是唯一独占自己那块像素的**。
  const 建 = { ids: [] };
  const 点选序列 = [];
  for (let i = 0; i < 3; i++) {
    const 前 = await idsOf(p);
    // 若已有选中，先清掉
    if (await selCount(p) > 0) { await p.mouse.click(8, 660); await p.waitForTimeout(800); }
    const pt = await p.evaluate(() => {
      const e = document.querySelector('[aria-label="文本"]'); if (!e) return null;
      const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
        for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
        }
      return null;
    });
    if (!pt) { rec.中止 = '左栏文本按钮找不到'; break; }
    await p.mouse.click(pt.x, pt.y);
    await p.waitForTimeout(2500);
    await settle(p, R);
    const 后 = await idsOf(p);
    const 新增 = 后.filter((x) => !前.includes(x));
    await 断言(`②第${i + 1}个建后差集恰好 1 个`, 新增.length === 1, { 新增 });
    if (新增.length !== 1) { rec.中止 = '建节点未成'; break; }
    建.ids.push(新增[0]);
    // 这个新节点此刻是唯一选中 ⇒ 直接 Shift 加选「之前建的那些」
    for (const prev of 建.ids.slice(0, -1)) {
      const 落 = await p.evaluate((k) => {
        const n = document.querySelector(`.react-flow__node[data-id="${k}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 1)
          for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 1) {
            const h = document.elementFromPoint(x, y);
            if (h && h.closest && h.closest('.react-flow__node') === n
              && !h.closest('button,[role=button],[contenteditable],input,textarea')) return { x, y };
          }
        return null;
      }, prev);
      点选序列.push({ 新建: 新增[0], Shift加选: prev, 落点: 落 });
      if (!落) {
        // 🔴 落点扫不到 ⇒ 目标节点此刻**完全被别的节点压住**。
        //   兜底：先取消全部选中（被压住的节点一旦没有选中描边，常能露出像素），
        //   再点它、再 Shift 加选刚才那个。**每一步都回读**，失败就如实记。
        if (await selCount(p) > 0) { await p.mouse.click(8, 660); await p.waitForTimeout(800); }
        const 落2 = await p.evaluate((k) => {
          const n = document.querySelector(`.react-flow__node[data-id="${k}"]`); if (!n) return null;
          const r = n.getBoundingClientRect();
          for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 1)
            for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 1) {
              const h = document.elementFromPoint(x, y);
              if (h && h.closest && h.closest('.react-flow__node') === n
                && !h.closest('button,[role=button],[contenteditable],input,textarea')) return { x, y };
            }
          return null;
        }, prev);
        点选序列[点选序列.length - 1].兜底落点 = 落2;
        if (!落2) continue;
        await p.mouse.click(落2.x, 落2.y);
        await p.waitForTimeout(900);
        // 再把「新建的那个」Shift 加回来
        const 落3 = await p.evaluate((k) => {
          const n = document.querySelector(`.react-flow__node[data-id="${k}"]`); if (!n) return null;
          const r = n.getBoundingClientRect();
          for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 1)
            for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 1) {
              const h = document.elementFromPoint(x, y);
              if (h && h.closest && h.closest('.react-flow__node') === n
                && !h.closest('button,[role=button],[contenteditable],input,textarea')) return { x, y };
            }
          return null;
        }, 新增[0]);
        点选序列[点选序列.length - 1].再加新建落点 = 落3;
        if (落3) {
          await p.keyboard.down('Shift'); await p.mouse.click(落3.x, 落3.y); await p.keyboard.up('Shift');
          await p.waitForTimeout(900);
        }
        continue;
      }
      await p.keyboard.down('Shift');
      await p.mouse.click(落.x, 落.y);
      await p.keyboard.up('Shift');
      await p.waitForTimeout(900);
    }
  }
  rec.点选序列 = 点选序列;
  rec.建 = { ids: 建.ids, ok: 建.ids.length === 3 };
  断言('③三个节点都建成了', 建.ids.length === 3, { ids: 建.ids });
  {
    const 当前选中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected'))
      .map((n) => n.getAttribute('data-id')).sort());
    rec.当前选中 = 当前选中;
    const 点 = { ok: JSON.stringify(当前选中) === JSON.stringify([...建.ids].sort()), 最终选中: 当前选中 };
    rec.点选ok = 点.ok;
    断言('④选中集合恰好等于这 3 个', 点.ok, { 选中: 当前选中 });
    if (点.ok) {
      const 编组 = await 点编组(p);
      rec.编组ok = 编组.ok;
      断言('⑤编组后恰好 1 个真身组', 编组.ok, 编组);
      if (编组.ok) {
        rec.各档 = [];
        for (const pct of 档位) {
          const z = await setZoom(p, pct);
          const h = await 读组(p);
          rec.各档.push({ 标称: pct, 追平: z.scale已追平, ...h });
          断言(`⑥${pct}% 实测 scale 已追平`, z.scale已追平, { z, 实测: h.scale });
        }
        rec.有读数档 = rec.各档.filter((d) => d.角边长 !== null && d.角边长 !== undefined);
        断言('⑦九档都读到组把手（防空集通过）', rec.有读数档.length === 9,
          { 读到: rec.有读数档.length, 摘要: rec.各档.map((d) => ({ 标称: d.标称, 角: d.角边长 })) });
        if (rec.有读数档.length === 9) {
          rec.表 = rec.各档.map((d) => ({ 标称: d.标称, scale: d.scale, 卡片canvas: d.卡片canvas,
            角边长: d.角边长, 边长: d.边长, 边厚: d.边厚,
            角反推canvas: d.scale ? Math.round(d.角边长 / d.scale * 100) / 100 : null,
            边厚反推canvas: d.scale ? Math.round(d.边厚 / d.scale * 100) / 100 : null,
            边长反推canvas: d.scale ? Math.round(d.边长 / d.scale * 100) / 100 : null }));
          断言('⑧组卡片 canvas 九档恒定（自变量只有缩放）',
            new Set(rec.表.map((x) => x.卡片canvas)).size === 1, { 各档: rec.表.map((x) => x.卡片canvas) });
          // 组角 = max(24×scale, 24)（保底）
          rec.角max验 = rec.表.map((x) => ({ 标称: x.标称, 实测: x.角边长,
            预测: Math.max(24 * x.scale, 24), 成立: Math.abs(Math.max(24 * x.scale, 24) - x.角边长) < 0.01 }));
          // 边厚 = 10×scale（无钳位）
          rec.边厚验 = rec.表.map((x) => ({ 标称: x.标称, 实测: x.边厚,
            预测: Math.round(10 * x.scale * 100) / 100, 成立: Math.abs(10 * x.scale - x.边厚) < 0.01 }));
          // 边长 = 卡片canvas × scale（无钳位）
          rec.边长验 = rec.表.map((x) => ({ 标称: x.标称, 实测: x.边长,
            预测: Math.round(x.卡片canvas * x.scale * 100) / 100, 成立: Math.abs(x.卡片canvas * x.scale - x.边长) < 0.01 }));
          断言('⑨组角把手逐字满足 max(24×scale, 24)（保底，与节点侧封顶方向相反）',
            rec.角max验.every((x) => x.成立), rec.角max验);
          断言('⑩组边把手厚度逐字 = 10×scale（无钳位）', rec.边厚验.every((x) => x.成立), rec.边厚验);
          断言('⑪组边把手长度逐字 = 卡片canvas×scale（无钳位）', rec.边长验.every((x) => x.成立), rec.边长验);
        }
      }
    }
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }

try {
  const z = await setZoom(p, 60);
  rec.归位 = { zoom: await R.zoom(), 追平: z.scale已追平 };
  if ((await R.minimap()) && (await R.minimap()).ariaPressed !== 'true') {
    const mm = await 可点落点Safe(p);
    if (mm) { await p.mouse.click(mm.x, mm.y); await p.waitForTimeout(1200); }
  }
  rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), zoom: await R.zoom() };
} catch (e) { rec.收尾异常 = String(e && e.message).slice(0, 200); }

async function 可点落点Safe(p) {
  return p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return null;
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
      for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
      }
    return null;
  });
}

rec.断言全过 = 全过;
fs.writeFileSync(new URL('./_tmp-b142a.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('断言全过', 全过, '| 通过', (rec.断言 || []).filter((a) => a.通过).length, '/', (rec.断言 || []).length);
(rec.断言 || []).filter((a) => !a.通过).forEach((a) => console.log('  ❌', a.名, JSON.stringify(a.详情).slice(0, 200)));
if (rec.表) {
  console.log('| 缩放 | scale | 卡片canvas | 角边长 | 角反推canvas | 边长×厚 | 边长反推canvas |');
  for (const x of rec.表) console.log(`| ${x.标称}% | ${x.scale} | ${x.卡片canvas} | **${x.角边长}** | ${x.角反推canvas} | ${x.边长}×${x.边厚} | ${x.边长反推canvas} |`);
  console.log('角max验', JSON.stringify((rec.角max验 || []).map((x) => `${x.标称}%:${x.实测}/${x.预测}${x.成立 ? '✔' : '✘'}`)));
  console.log('边厚验', JSON.stringify((rec.边厚验 || []).map((x) => `${x.标称}%:${x.实测}/${x.预测}${x.成立 ? '✔' : '✘'}`)));
}
await b.close();

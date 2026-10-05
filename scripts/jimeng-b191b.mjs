// 批次 191 b 轮：a 轮把「⌘V 改缩放」这条**当场证伪了一半** —— ⌘V 确实粘出了节点（76→77），
// 而缩放 7 秒内 6 个时间点**逐字不变**（0.26→0.26，平移也不变）。
// ⇒ 批次 190 那三个数（26%→50%/42%/43%）另有来源。
//
// 🔑 b 轮要检验的假设：**变量是「点搜索结果行」，不是「按 ⌘V」**。
//   依据：批次 188 f 轮早就撞见过「每档重新用搜索面板选中 ⇒ 点结果行触发缩放动画，
//         22/26/40 三档读到的 scale 是 0.5」—— 当时被判成「干扰」丢掉了，没当成一个发现。
//   批次 190 三轮的顺序都是「搜索选中 → ⌘C → ⌘V」，而读数写在 ⌘V 之后
//   ⇒ 变化若来自第一步，就会被记到第三步头上。
//
// 🔑 每条臂都带**阳性守卫**；守卫不过的臂标 `无效臂 = true`，**不计入任何结论**
//   （a 轮的教训：臂 2 因为没选中节点而空跑，却照样被记成「缩放没变」——
//     那是「动作没发生」，不是「动作没有效果」。立规 52 / 58 的又一例。）
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b191b.json';
const 记 = { 轮次: 'b191b', 假设: '缩放变化来自「点搜索结果行」，而非「按 ⌘V」', 臂: [], 收尾: null };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));

const 读缩放 = (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const vp = document.querySelector('.react-flow__viewport');
  const t = (vp && vp.style.transform) || '';
  const ms = /scale\(([-\d.]+)\)/.exec(t);
  const mt = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(t);
  return { aria: e ? e.getAttribute('aria-label') : null,
    实测scale: ms ? Math.round(parseFloat(ms[1]) * 1000) / 1000 : null,
    平移: mt ? [Math.round(parseFloat(mt[1]) * 10) / 10, Math.round(parseFloat(mt[2]) * 10) / 10] : null };
});

async function 序列(p, 标签, 计划表 = [0, 300, 700, 1500, 3000, 5000]) {
  const 点 = []; const t0 = Date.now();
  for (const 计划 of 计划表) {
    const 等 = 计划 - (Date.now() - t0); if (等 > 0) await p.waitForTimeout(等);
    点.push({ ms: Date.now() - t0, ...(await 读缩放(p)) });
  }
  const sc = 点.map((x) => x.实测scale), ar = 点.map((x) => x.aria);
  return { 标签, 点, 末态: 点[点.length - 1], scale是否收敛: new Set(sc).size === 1,
    scale取值集: [...new Set(sc)], 是否单调上升: sc.every((v, i) => i === 0 || v >= sc[i - 1]) };
}

const 归位 = async (p, pct = 26) => { const r = await setZoom(p, pct); await p.waitForTimeout(500); return r; };

/** 打开搜索面板，返回输入框。 */
async function 开搜索(p) {
  const btn = await p.evaluate(() => {
    const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
      .find((b) => (b.getAttribute('aria-label') || '') === '搜索');
    if (!a) return null; const r = a.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), expanded: a.getAttribute('aria-expanded') };
  });
  if (!btn) throw new Error('找不到搜索启动器');
  if (btn.expanded !== 'true') { await p.mouse.click(btn.x, btn.y); await p.waitForTimeout(1100); }
  const 面板 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-panel"]');
    return e ? { aria: e.getAttribute('aria'), r: (({width,height,x,y}) => ({w:Math.round(width),h:Math.round(height),x:Math.round(x),y:Math.round(y)}))(e.getBoundingClientRect()) } : null; });
  const 输入 = await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-feature-panel"] input[aria="搜索"]');
    if (!i) return null; const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  return { 启动器: btn, 面板, 输入 };
}

/** 在搜索面板里输入词，列出结果行（逐字）。 */
async function 搜(p, 点, 词) {
  await p.mouse.click(点[0], 点[1]);
  await p.waitForTimeout(300);
  await p.fill('[data-testid="canvas-feature-panel"] input[aria="搜索"]', 词);
  await p.waitForTimeout(1300);
  return p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]')).map((b) => {
    const r = b.getBoundingClientRect();
    return { id: (b.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), aria: b.getAttribute('aria-label'),
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  }));
}

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };
save();

const S = await 开搜索(p);
记.搜索面板 = S;
console.log('搜索面板 =', JSON.stringify(S.面板));
save();

// ── 臂 A：只点搜索结果行，**不按任何键**（阳性守卫 = 状态行出现 1 selected） ──
async function 臂A(词, 序) {
  await 归位(p, 26);
  const 结果 = await 搜(p, S.输入, 词);
  if (!结果.length) { 记.臂.push({ 序, 词, 无效臂: true, 原因: '没有搜索结果行' }); save(); return null; }
  const 目标 = 结果[0];
  const 前 = await 读缩放(p);
  await p.mouse.click(目标.中心[0], 目标.中心[1]);
  const 状态行 = await R.status();
  const 选中 = await R.selCount();
  const 焦点 = await p.evaluate(() => { const a = document.activeElement; return a ? a.tagName + '[' + (a.getAttribute('data-testid') || '') + ']' : null; });
  const 序读 = await 序列(p, `臂A ${词}`);
  // 顺带量一下这个节点的屏上尺寸（用来测「缩放是不是按节点尺寸算的」）
  const 节点 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return null; const r = n.getBoundingClientRect();
    return { 屏上: [Math.round(r.width), Math.round(r.height)], aria: n.getAttribute('aria-label'),
      canvas: (function () { const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || ''); return m ? [parseFloat(m[1]), parseFloat(m[2])] : null; })() }; }, 目标.id);
  const 臂 = { 序, 词, 目标: { id: 目标.id, aria: 目标.aria }, 前, 状态行, 选中, 焦点, 节点,
    序列: 序读,
    阳性守卫: { 通过: 选中 === 1, 判据: `选中数 = ${选中}（要求 1）` },
    无效臂: 选中 !== 1,
    判定: { scale变化: 前.实测scale !== 序读.末态.实测scale,
      旧scale: 前.实测scale, 新scale: 序读.末态.实测scale,
      平移变化: JSON.stringify(前.平移) !== JSON.stringify(序读.末态.平移),
      旧平移: 前.平移, 新平移: 序读.末态.平移 } };
  记.臂.push(臂); save();
  console.log(`臂A(${词}) 守卫=${选中} scale ${前.实测scale}→${序读.末态.实测scale} 节点屏上=${JSON.stringify(节点 && 节点.屏上)}`);
  return 臂;
}

const A1 = await 臂A('视频', 'A1');
const A2 = await 臂A('音频', 'A2');
const A3 = await 臂A('时间线', 'A3');

// ── 臂 B：搜索选中 → **等缩放稳定** → 按 ⌘V → 再读（看 ⌘V 有没有第二次改动） ──
{
  const 词 = '视频';
  const 结果 = await 搜(p, S.输入, 词);
  const 目标 = 结果[0];
  await p.mouse.click(目标.中心[0], 目标.中心[1]);
  await p.waitForTimeout(4000);              // 等选中带来的缩放动画完全结束
  const 稳定值 = await 读缩放(p);
  const 状态行 = await R.status();
  const ids前 = await R.ids();
  const 焦点 = await p.evaluate(() => { const a = document.activeElement; return a ? a.tagName + '[' + (a.getAttribute('data-testid') || '') + ']' : null; });
  await p.keyboard.press('Meta+v');
  await p.waitForTimeout(250);
  const ids后 = await R.ids();
  const 序读 = await 序列(p, '臂B 稳定后按 ⌘V');
  记.臂.push({ 序: 'B', 动作: '搜索选中 → 等 4 秒稳定 → 按 ⌘V', 目标: { id: 目标.id, aria: 目标.aria },
    稳定值, 状态行, 焦点, 节点数: [ids前.length, ids后.length],
    新增id: ids后.filter((x) => !ids前.includes(x)),
    阳性守卫: { 通过: ids后.length !== ids前.length, 判据: `节点数 ${ids前.length} → ${ids后.length}` },
    无效臂: ids后.length === ids前.length,
    序列: 序读,
    判定: { scale变化: 稳定值.实测scale !== 序读.末态.实测scale, 旧: 稳定值.实测scale, 新: 序读.末态.实测scale } });
  console.log(`臂B 守卫=${ids后.length !== ids前.length} scale ${稳定值.实测scale}→${序读.末态.实测scale}`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  save();
}

// ── 臂 C：对照 · 在画布上直接点节点标题行（不经搜索面板） ──────────────
{
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  await 归位(p, 26);
  const 命中 = await p.evaluate(() => {
    const a = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return null;
      const r = t.getBoundingClientRect();
      if (!(r.width > 3 && r.x > 80 && r.x + r.width < innerWidth - 340 && r.y > 100 && r.y + r.height < innerHeight - 100)) return null;
      return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }).filter(Boolean);
    return a;
  });
  const 前 = await 读缩放(p);
  if (!命中.length) { 记.臂.push({ 序: 'C', 无效臂: true, 原因: '26% 下没有可点的标题行' }); save(); }
  else {
    await p.mouse.click(命中[0].中心[0], 命中[0].中心[1]);
    const 选中 = await R.selCount();
    const 序读 = await 序列(p, '臂C 画布上直接点标题行');
    记.臂.push({ 序: 'C', 动作: '不经搜索面板，直接点画布上的节点标题行', 目标: { id: 命中[0].id, aria: 命中[0].aria }, 前,
      阳性守卫: { 通过: 选中 === 1, 判据: `选中数 = ${选中}` }, 无效臂: 选中 !== 1, 序列: 序读,
      判定: { scale变化: 前.实测scale !== 序读.末态.实测scale, 旧: 前.实测scale, 新: 序读.末态.实测scale } });
    console.log(`臂C 守卫=${选中} scale ${前.实测scale}→${序读.末态.实测scale}`);
    save();
  }
}

// ── 收尾：删掉本轮新增节点（若粘贴留下了文本节点）+ 归位 ────────────────
{
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  const ids = await R.ids();
  const 新 = ids.filter((x) => !基线.ids.includes(x));
  for (const id of 新) {
    const ok = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return { 删: false };
      const t = n.querySelector('[data-testid="flow-node-title"]') || n; const r = t.getBoundingClientRect();
      return { 删: true, aria: n.getAttribute('aria-label'), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }, id);
    if (!ok.删) { 记.收尾 = (记.收尾 || []); continue; }
    await p.mouse.click(ok.点[0], ok.点[1]); await p.waitForTimeout(500);
    await p.mouse.click(ok.点[0], ok.点[1], { button: 'right' }); await p.waitForTimeout(800);
    const bb = await p.evaluateHandle(() => Array.from(document.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim().startsWith('删除')) || null);
    const el = bb.asElement();
    if (!el) { await p.keyboard.press('Escape'); continue; }
    const box = await el.boundingBox();
    if (box) { await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2); await p.waitForTimeout(1200); }
    else await p.keyboard.press('Escape');
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  await 归位(p, 26);
  const ids2 = await R.ids();
  记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(),
    节点数: ids2.length, 基线节点数: 基线.ids.length,
    残留: ids2.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids2.includes(x)) };
  save();
  console.log('收尾 =', JSON.stringify(记.收尾));
}
await b.close();
console.log('写出', OUT);

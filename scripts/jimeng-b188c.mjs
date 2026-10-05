// 批次 188 c 轮：**隔离 ⊕ 屏上尺寸到底是 36×36 还是 19×19**，并**如实判「未定」还是「有结论」**。
//
// 手上已有的读数互相矛盾，必须摆清楚：
//   184c（搜索面板选中，六类各一次）⇒ 全部 `36×36`
//   187 （搜索面板选中，主体节点）  ⇒ `19×19`
//   188 （**点击标题**选中，带内容图片 / 新建空图片）⇒ `19×19`
//   188b（搜索面板选中，带内容图片，**缩放 50%**，5 个交互状态）⇒ 全部 `36×36`
// ⇒ 同一节点、同一类型，见过**两种**尺寸。**自变量还没隔离出来。**
//   两个候选：**① 缩放不同**（19×19 都出现在 26%、36×36 出现在 26% 与 50%，自相矛盾）
//             **② 选中方式不同**（188 用点击、184c/188b 用搜索面板）。
//
// 本轮只做一件事：**在同一个缩放下**，对**同一个节点**，分别用两种选中方式各读一次。
// 每读一次都记录**当次缩放**，凡缩放不相等的读数一律**不参与比较**（不硬凑结论）。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '188c' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 缩放 = () => R.zoom();
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 读 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const 全部 = Array.from(n.querySelectorAll('[aria-label^="Create connected node"]'));
  return { 选中: n.classList.contains('selected'),
    节点class: (n.className || '').toString(),
    节点屏上: (() => { const r = n.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; })(),
    '⊕个数': 全部.length,
    尺寸: 全部.map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { testid: (e.getAttribute('data-testid') || '').replace('flow-node-', '').replace('-connection-menu-button', ''),
        w: Math.round(r.width), h: Math.round(r.height), fontSize: cs.fontSize, padding: cs.padding, transform: cs.transform }; }) };
}, id);
const 标题坐标 = (id) => p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
  if (!t) return null; const r = t.getBoundingClientRect();
  if (!(r.width > 2 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const 适配 = async () => { await p.mouse.move(640, 400); await p.waitForTimeout(250); await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(2600); return R.zoom(); };
const 搜索选中 = async (关键词) => {
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1400);
  const 命中 = await p.evaluate((w) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !w || x.文字.includes(w)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1400);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s };
};
const 目标 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.目标 = 目标;
rec.读数 = [];
try {
  if (!目标) rec.说明 = '没有图片节点';
  else {
    // ── 方式一：**点击标题**选中。适配定住缩放 → 点 → 读 → 再适配归位 → 读
    await 适配(); const z0 = await 缩放();
    const pt = await 标题坐标(目标.id);
    rec.标题坐标 = pt;
    if (pt) {
      await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(2500);
      rec.读数.push({ 方式: '点击标题', 步: '适配后点击_原样', 缩放: await 缩放(), 适配时缩放: z0, 读: await 读(目标.id), 选中集: await 选中集() });
      const z1 = await 适配();
      rec.读数.push({ 方式: '点击标题', 步: '再适配归位后', 缩放: z1, 读: await 读(目标.id), 选中集: await 选中集() });
    }
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
    // ── 方式二：**搜索面板**选中。同样适配定住 → 搜 → 读 → 归位 → 读
    const z2 = await 适配();
    const S = await 搜索选中(目标.标题);
    rec.搜索选中 = S;
    rec.读数.push({ 方式: '搜索面板', 步: '适配后搜索_原样', 缩放: await 缩放(), 适配时缩放: z2, 读: await 读(目标.id), 选中集: await 选中集() });
    const z3 = await 适配();
    rec.读数.push({ 方式: '搜索面板', 步: '再适配归位后', 缩放: z3, 读: await 读(目标.id), 选中集: await 选中集() });
    // ── 判定：只在**缩放相等**的读数之间比较
    const 有读 = rec.读数.filter((x) => x.读 && x.读.尺寸.length);
    rec.出现过几种尺寸 = [...new Set(有读.flatMap((x) => x.读.尺寸.map((s) => `${s.w}×${s.h}`)))];
    const 按缩放分组 = {};
    for (const x of 有读) { (按缩放分组[x.缩放] = 按缩放分组[x.缩放] || []).push({ 方式: x.方式, 步: x.步, 尺寸: x.读.尺寸.map((s) => `${s.w}×${s.h}`) }); }
    rec.按缩放分组 = 按缩放分组;
    const 同缩放两种方式 = Object.entries(按缩放分组).filter(([, v]) => new Set(v.map((x) => x.方式)).size === 2);
    rec.同缩放下的两种方式 = 同缩放两种方式.map(([z, v]) => ({ 缩放: z, 两方式读数: v, 结论: new Set(v.map((x) => x.尺寸.join(','))).size === 1 ? '两种方式一致' : '两种方式不一致' }));
    rec.是否已隔离 = 同缩放两种方式.length > 0;
    rec.自变量是什么 = 同缩放两种方式.length === 0 ? '未定：没有拿到「同缩放下两种选中方式」的读数，不能下结论' :
      (同缩放两种方式.every(([, v]) => new Set(v.map((x) => x.尺寸.join(','))).size === 1) ? '选中方式不影响尺寸' : '🔴 选中方式影响尺寸');
  }
} catch (e) { rec.异常 = String(e).slice(0, 200); }
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(3000);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays(),
  节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

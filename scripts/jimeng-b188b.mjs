// 批次 188 b 轮：**⊕ 按钮的尺寸到底由什么决定** —— 因为我连续两批把它归错了。
//
// 两次过度概括：
//   批次 184：用**带内容**的图片节点读到 ⊕ 只有 1 个 ⇒ 写成「图片节点没有 before ⊕」
//             （**类型**规则）。批次 188 已证伪：空图片节点有 2 个 ⇒ 变量是**内容**。
//   批次 187：读到主体节点的 ⊕ 是 `19×19`、而 184c 抽到的五类是 `36×36`
//             ⇒ 写成「⊕ 屏上恒为 36×36 只覆盖 5 种类型，主体是 19×19」（**类型**规则）。
//             🔴 但 188 同一个节点 `b22-upload`（**184c 当时读到的就是 36×36**）
//             这次读到的是 **`19×19`** ⇒ **同一个节点、同一缩放、尺寸却变了**
//             ⇒ 尺寸**不是按类型定的**，我 187 那句话同样站不住。
//
// 本轮在**同一个节点**上逐状态量，每种状态**读两次**（看它稳不稳定）：
//   ① 空闲（未选中）
//   ② 选中、**鼠标移开**（用搜索面板选中后把鼠标挪到画布空白）
//   ③ 选中、**鼠标悬停在节点标题上**
//   ④ 刚单击选中之后（不等）
//   ⑤ 选中后按 Esc 取消选中
// 另记缩放，**排除「缩放不同」这个解释**。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '188b' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 缩放 = () => R.zoom();
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
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
/** 读某个节点上所有 ⊕ 的屏上尺寸 ＋ 它的 class 状态。 */
const 读加号尺寸 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const 全部 = Array.from(n.querySelectorAll('[aria-label^="Create connected node"]'));
  return { 选中: n.classList.contains('selected'), 节点class: (n.className || '').toString(),
    节点屏上: (() => { const r = n.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; })(),
    '⊕个数': 全部.length,
    尺寸: 全部.map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { testid: (e.getAttribute('data-testid') || '').replace('flow-node-', '').replace('-connection-menu-button', ''),
        w: Math.round(r.width), h: Math.round(r.height), fontSize: cs.fontSize, padding: cs.padding, transform: cs.transform }; }) };
}, id);
const 目标 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.目标 = 目标;
rec.状态 = [];
const 记 = async (名) => { const r = await 读加号尺寸(目标.id); rec.状态.push({ 名, 缩放: await 缩放(), 选中集: await 选中集(), 读数: r }); };
try {
  if (!目标) rec.说明 = '画布上没有图片节点';
  else {
    await 记('①_空闲未选中');
    const S = await 搜索选中(目标.标题);
    rec.搜索选中 = S;
    await p.mouse.move(1250, 10); await p.waitForTimeout(1500);          // 鼠标移开
    await 记('②_选中_鼠标移开_第1次');
    await p.waitForTimeout(2500); await 记('②_选中_鼠标移开_第2次_等2.5秒');
    // 悬停标题
    const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
      if (!t) return null; const r = t.getBoundingClientRect();
      if (!(r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight)) return null;
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 目标.id);
    rec.标题坐标 = pt;
    if (pt) { await p.mouse.move(pt[0], pt[1]); await p.waitForTimeout(1200); await 记('③_选中_鼠标悬停标题');
      await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(120); await 记('④_刚单击后_立刻');
      await p.waitForTimeout(2500); await 记('④_刚单击后_等2.5秒'); }
    await p.keyboard.press('Escape'); await p.waitForTimeout(1200); await 记('⑤_按Esc取消选中');
    // 汇总：同一状态下尺寸是否稳定 / 不同状态是否不同
    const 摘 = rec.状态.filter((s) => s.读数).map((s) => ({ 名: s.名, 缩放: s.缩放, 选中: s.读数.选中,
      个数: s.读数['⊕个数'], 尺寸: s.读数.尺寸.map((x) => `${x.w}×${x.h}`) }));
    rec.摘要 = 摘;
    rec.出现过几种尺寸 = [...new Set(摘.flatMap((x) => x.尺寸))];
  }
} catch (e) { rec.异常 = String(e).slice(0, 200); }
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(3000);
const 末 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
rec.收尾核验 = { 现在节点数: 末.length, 丢失id: 末.filter((i) => !rec.目标 || true).length ? undefined : undefined, 节点数应为: 76 };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays(), 节点数: 末.length };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

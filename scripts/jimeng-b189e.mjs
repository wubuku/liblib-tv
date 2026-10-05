// 批次 189 e 轮：最后一个机制问题 —— **k 会不会跟着缩放走，取决于节点是不是「选中着」**。
//
// 189 d 轮已钉死（**不随时间收敛**：0.85s / 2s / 4s / 7s 四次读数逐字相同）：
//   静息态、26% 档 → 76 个节点的标题与标签 k **全是 2**（与公式 `min(2, 1/0.26)=2` 一致）；
//   静息态、80% 档 → **6 种 k 共存**：`2×41 / 1.771×15 / 1.479×5 / 1.339×1 / 1.285×1 / 1.25×13`。
//   只有 13/76 拿到公式值 1.25，其余 63 个保持旧值或某种中间值。
//
// 🔑 而 188 f 轮里，被选中的那个节点的 ⊕ 在 **10 档缩放下逐档严格命中** `min(72×s, 36)` ——
//    它的 k 是**每档都跟上**的。两个观察合起来给出一个可检验的预测：
//
// **预测**：k 的值是「**渲染时从当前缩放快照下来的**」，而不是跟随全局缩放的活公式；
//          **选中态的节点会跟着重渲染**（所以它的 ⊕ / 标题 / 标签都跟得上），
//          **未选中的节点不重渲染**（k 停在旧值）。
//
// 本轮对照四个对象在 5 档下的 k：
//   ① 选中节点的 ⊕　② 选中节点的标题　③ 选中节点的标签　④ 一个**未选中**节点的标题（按 id 钉住）
// 预测：①②③ 每档都等于 `min(2, 1/缩放)`；④ 只有一档对上，其余停在旧值。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '189e', 预测: '选中节点 4 件都跟公式；未选中节点只在一档对上' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() };

// 选一个带内容的图片节点
const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!开) throw new Error('没有搜索按钮');
await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!输入) { await p.keyboard.press('Escape'); throw new Error('搜索面板没打开'); }
await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
await p.fill('[data-testid="canvas-search-panel"] input', 'b22-upload'); await p.waitForTimeout(1500);
const 命中结果 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
  .map((e) => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
  .filter((x) => x.文字.includes('b22-upload')));
if (!命中结果.length) { await p.keyboard.press('Escape'); throw new Error('搜索无命中'); }
await p.mouse.click(命中结果[0].点[0], 命中结果[0].点[1]); await p.waitForTimeout(1800);
const 选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
rec.选中id = 选中集[0];
// 钉一个**未选中**的对照节点：取一个当前视口内、类型与选中节点不同的
rec.对照id = await p.evaluate((sel) => {
  const n = Array.from(document.querySelectorAll('.react-flow__node')).find((x) => {
    const id = x.getAttribute('data-id'); if (id === sel) return false;
    const r = x.getBoundingClientRect();
    return r.right > 8 && r.x < innerWidth - 340 && r.bottom > 70 && r.y < innerHeight - 70 && !x.classList.contains('selected')
      && !!x.querySelector('[data-testid="flow-node-title"]');
  });
  return n ? n.getAttribute('data-id') : null;
}, rec.选中id);
if (!rec.对照id) throw new Error('找不到可用的未选中对照节点');

const 读 = () => p.evaluate(({ 选中, 对照 }) => {
  const 视口 = document.querySelector('.react-flow__viewport');
  const ms = 视口 ? /scale\(([-\d.]+)\)/.exec(视口.style.transform || '') : null;
  const s = ms ? parseFloat(ms[1]) : null;
  const k = (el) => { if (!el) return null; const v = getComputedStyle(el).scale; const n = parseFloat(v); return Number.isFinite(n) ? Math.round(n * 1000) / 1000 : null; };
  const 节点内 = (id) => document.querySelector(`.react-flow__node[data-id="${id}"]`);
  const 选中节点 = 节点内(选中), 对照节点 = 节点内(对照);
  const 选中中点 = (() => { const a = 选中节点.querySelector('[aria-label^="Create connected node"]');
    if (!a) return null; const r = a.getBoundingClientRect(); return { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 }; })();
  return {
    scale: s, 缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).ariaLabel || null,
    公式期望k: Math.round(Math.min(2, 1 / s) * 1000) / 1000,
    选中仍选中: !!(选中节点 && 选中节点.classList.contains('selected')),
    选中_加号k: k(选中节点 && 选中节点.querySelector('[aria-label^="Create connected node"]')),
    选中_加号屏上: 选中中点,
    选中_标题k: k(选中节点 && 选中节点.querySelector('[data-testid="flow-node-title"]')),
    选中_标签k: k(选中节点 && 选中节点.querySelector('[data-testid="flow-node-selected-tag"]')),
    对照_标题k: k(对照节点 && 对照节点.querySelector('[data-testid="flow-node-title"]')),
    对照_标签k: k(对照节点 && 对照节点.querySelector('[data-testid="flow-node-selected-tag"]')),
    对照_标题屏上: (() => { const e = 对照节点 && 对照节点.querySelector('[data-testid="flow-node-title"]');
      if (!e) return null; const r = e.getBoundingClientRect(); return { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 }; })(),
  };
}, { 选中: rec.选中id, 对照: rec.对照id });

const 档位 = [80, 60, 50, 100, 26, 80, 26];
rec.各档 = [];
for (const pct of 档位) {
  await setZoom(p, pct);
  await p.mouse.move(1250, 706); await p.waitForTimeout(1100);
  rec.各档.push({ 档: pct, ...(await 读()) });
}

const 合 = (a, b) => a !== null && b !== null && Math.abs(a - b) <= 0.01;
rec.判定 = {
  各档: rec.各档.map((x) => ({ 档: x.档, scale: x.scale, 期望k: x.公式期望k,
    选中_加号k: x.选中_加号k, 选中_标题k: x.选中_标题k, 选中_标签k: x.选中_标签k,
    对照_标题k: x.对照_标题k, 对照_标签k: x.对照_标签k,
    加号合: 合(x.选中_加号k, x.公式期望k), 选中标题合: 合(x.选中_标题k, x.公式期望k),
    选中标签合: 合(x.选中_标签k, x.公式期望k), 对照标题合: 合(x.对照_标题k, x.公式期望k) })),
  预测检验: (() => {
    const 首次80 = rec.各档.filter((x) => x.档 === 80);
    const 选中侧都合 = 首次80.every((x) => 合(x.选中_加号k, x.公式期望k) && 合(x.选中_标题k, x.公式期望k) && 合(x.选中_标签k, x.公式期望k));
    const 对照侧有不合 = 首次80.some((x) => !合(x.对照_标题k, x.公式期望k));
    return { 首次80档选中侧三项全合公式: 选中侧都合, 首次80档对照侧存在不合: 对照侧有不合,
      两次80档对照k是否相同: 首次80.length >= 2 ? (首次80[0].对照_标题k === 首次80[1].对照_标题k) : null,
      两次80档对照k: 首次80.map((x) => x.对照_标题k), 两次80档期望k: 首次80.map((x) => x.公式期望k) };
  })(),
  非空守卫: { 档数: rec.各档.length, 每档都读到加号k: rec.各档.every((x) => x.选中_加号k !== null),
    每档都读到对照标题k: rec.各档.every((x) => x.对照_标题k !== null),
    每档选中态都保持: rec.各档.every((x) => x.选中仍选中 === true),
    scale与aria一致: rec.各档.every((x) => Math.abs(x.scale - x.档 / 100) <= 0.005) },
};

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();

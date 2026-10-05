// 批次 174 d 轮：四条「c 轮没钉死」的收尾。
//
// D1 决定性：b 轮 popover 刷新后还在，但 c 轮因为**先关掉了它**所以没区分开
//     「被记住」与「被 hover 重新触发」。这次把鼠标**移开但不关浮层**：
//     若移开后浮层还在 ⇒ 它是点击锁定 ⇒ 刷新后仍在就真是「被记住」；
//     若移开就关 ⇒ 它是 hover 触发 ⇒ b 轮那个读数是**自变量没控住**。
// D2 重复性：刷新后固定回到 26%？连做 3 次，看这个数是**内容决定的确定值**
//     还是碰巧。D2 顺带把「26% ≈ 装下全部节点」量化成**包围盒占比**。
// D3 保存中间态：c 轮没测成（26% 下屏幕上没有可点的文本节点）。
//     改用**画布改名**（手册 2026-10-01 已记流程），因为画布名正是**服务端字段**，
//     保存指示器理应对它最敏感。⚠️ 必须改回「测试项目」并按 id/文字验明。
// D4 `canvas-save-failure-anchor` 到底是不是 UI：基线里它**恒存在**，
//     但手册从没提过。要看它有没有面积、有没有内容 —— 否则「保存失败态存在」
//     只是我看见了一个 testid 就下的结论。
//
// ⛔ 不生成、不分享、不新建节点。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '174d' };

const 浮层 = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[data-testid$=-popover]'))
  .filter((m) => m.getBoundingClientRect().width > 1)
  .map((m) => { const r = m.getBoundingClientRect(); return (m.getAttribute('data-testid') || m.getAttribute('aria-label')) + `@${Math.round(r.x)},${Math.round(r.y)}`; }));
const 点中心 = async (sel) => {
  const pt = await p.evaluate((s) => { const e = document.querySelector(s); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, sel);
  if (!pt) return false; await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(800); return true;
};
const 重载 = async () => {
  await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
  const t0 = Date.now();
  while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
  await p.waitForTimeout(2500);
};
const 量视口 = () => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  const scale = m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null;
  const 盒 = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect()).filter((r) => r.width > 0);
  if (!盒.length) return { scale, 节点数: 0 };
  const x0 = Math.min(...盒.map((r) => r.left)), x1 = Math.max(...盒.map((r) => r.right));
  const y0 = Math.min(...盒.map((r) => r.top)), y1 = Math.max(...盒.map((r) => r.bottom));
  return { scale, 节点数: 盒.length, 视口: [innerWidth, innerHeight],
    包围盒: [Math.round(x0), Math.round(y0), Math.round(x1), Math.round(y1)],
    占视口百分比: [Math.round(((x1 - x0) / innerWidth) * 1000) / 10, Math.round(((y1 - y0) / innerHeight) * 1000) / 10],
    边距: [Math.round(x0), Math.round(innerWidth - x1), Math.round(y0), Math.round(innerHeight - y1)] };
});

await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(400);

// ═══════════════════════ D1 浮层：移开鼠标但不关
rec.D1 = {};
rec.D1.起点浮层 = await 浮层();
rec.D1.点了节点汇总 = await 点中心('[data-testid="canvas-node-summary-trigger"]');
rec.D1.点开后_鼠标在按钮上 = await 浮层();
await p.mouse.move(1250, 10); await p.waitForTimeout(1500);
rec.D1.鼠标移开后 = await 浮层();               // 关键读数：还在 = 点击锁定
await 重载();
await p.mouse.move(1250, 10); await p.waitForTimeout(1500);
rec.D1.重载后_鼠标已移开 = await 浮层();
// 再做一次「刷新时鼠标停在按钮上」的对照，闭合 b 轮那个读数的解释
await 点中心('[data-testid="canvas-node-summary-trigger"]');
rec.D1.再点开_鼠标留在按钮 = await 浮层();
await 重载();
rec.D1.重载后_鼠标仍在按钮上 = await 浮层();
await p.mouse.move(1250, 10); await p.waitForTimeout(1200);
await p.keyboard.press('Escape'); await p.waitForTimeout(500);

// ═══════════════════════ D2 刷新后视口是否确定（连做 3 次）
rec.D2 = { 三次: [] };
for (let i = 0; i < 3; i++) {
  // 每轮都先把视口**改乱**（缩放 + 平移），再刷新，看回不回到同一个值
  await p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport'); if (vp) vp.style.transform = 'translate(400px, 300px) scale(1.2)'; });
  await p.waitForTimeout(500);
  const 乱 = await p.evaluate(() => document.querySelector('.react-flow__viewport')?.style.transform);
  await 重载();
  rec.D2.三次.push({ 轮: i + 1, 改乱成: 乱, 刷新后: await 量视口() });
}

// ═══════════════════════ D3 画布改名，抓「保存中」中间态
rec.D3 = {};
const 原名 = await p.evaluate(() => (document.querySelector('[data-testid="canvas-project-title-trigger"]')?.innerText || '').trim());
rec.D3.原名 = 原名;
rec.D3.采样 = []; rec.D3.不同态 = new Set(); rec.D3.时间轴 = [];
const 改名 = async (新名) => {
  const ok = await 点中心('[data-testid="canvas-project-title-trigger"]');
  if (!ok) return { 失败: '找不到标题按钮' };
  const 输入 = 'input,textarea';
  const 有 = await p.evaluate((s) => { const e = document.querySelector(`[data-testid="workspace-canvas-title"] ${s}`)
    || Array.from(document.querySelectorAll(s)).find((x) => x.getBoundingClientRect().width > 20 && x.getBoundingClientRect().y < 60);
    if (!e) return null; const r = e.getBoundingClientRect();
    return { tag: e.tagName.toLowerCase(), 值: e.value, 宽: Math.round(r.width) }; }, 输入);
  if (!有) return { 失败: '标题没变成输入框' };
  await p.fill(输入, 新名);
  await p.waitForTimeout(120);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(2500);
  return { 有, 回读: await p.evaluate(() => (document.querySelector('[data-testid="canvas-project-title-trigger"]')?.innerText || '').trim()) };
};
if (原名) {
  // ⚠️ t0 先建，再建采样器（c 轮踩过：顺序反了时间轴全是 NaN，而 NaN 全相等）
  rec.D3.t0 = Date.now();
  const 采样 = setInterval(async () => {
    try { const s = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-title-save-status"]');
      return e ? { 文本: (e.textContent || '').trim(), 父链: e.parentElement?.getAttribute('data-testid') } : null; });
      if (s && s.文本) { rec.D3.采样.push([Date.now() - rec.D3.t0, s.文本]); rec.D3.不同态.add(s.文本); }
    } catch {}
  }, 30);
  rec.D3.改名 = await 改名(原名 + 't');
  await p.waitForTimeout(2500);
  clearInterval(采样);
  rec.D3.采样ms = Date.now() - rec.D3.t0;
  rec.D3.不同态 = [...rec.D3.不同态];
  rec.D3.采样条数 = rec.D3.采样.length;
  rec.D3.态切换点 = rec.D3.采样.reduce((acc, cur, i, arr) => {
    if (i === 0 || cur[1] !== arr[i - 1][1]) acc.push(cur); return acc; }, []);
  // ---- 复原
  rec.D3.复原 = await 改名(原名);
  await p.waitForTimeout(2500);
  rec.D3.复原后核对 = await p.evaluate(() => ({
    标题: (document.querySelector('[data-testid="canvas-project-title-trigger"]')?.innerText || '').trim(),
    aria: document.querySelector('[data-testid="canvas-project-title-trigger"]')?.getAttribute('aria-label'),
    积分: (document.querySelector('[data-testid="canvas-commerce-entry"]')?.getAttribute('aria-label') || null),
    节点数: document.querySelectorAll('.react-flow__node').length,
  }));
  rec.D3.复原成功 = rec.D3.复原后核对.标题 === 原名;
  delete rec.D3.t0;
} else rec.D3.失败 = '读不到当前画布名';

// ═══════════════════════ D4 canvas-save-failure-anchor 是 UI 还是定位锚
rec.D4 = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-save-failure-anchor"]');
  if (!e) return { 存在: false };
  const r = e.getBoundingClientRect();
  const cs = getComputedStyle(e);
  const 链 = []; for (let n = e; n && n !== document.body; n = n.parentElement) 链.push(n.tagName.toLowerCase() + (n.dataset?.testid ? `[${n.dataset.testid}]` : ''));
  return { 存在: true, 标签: e.tagName.toLowerCase(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    有面积: r.width > 0 && r.height > 0, 内文: JSON.stringify((e.textContent || '').slice(0, 60)), 子元素数: e.children.length,
    display: cs.display, visibility: cs.visibility, position: cs.position, pointerEvents: cs.pointerEvents, 祖先链: 链.slice(0, 5) };
});
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

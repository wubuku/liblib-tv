// 批次 190 d 轮：**专工清理**。上一轮 ⌘V 粘出的 `node_x2j4zn9thf` 没删掉，
// 而上一轮的删除尝试失败在「右键菜单根本没弹出来」（`菜单项: []`）。
//
// 失败原因（先假设再验）：那个节点是**文本节点**，而文本节点的**卡片主体是可编辑区**
// —— 点它会进入 `text-editor-node-overlay`（批次 30 立规那条），于是右键落到了编辑器里，菜单自然没有。
// ⇒ 清理策略改成**按 id → 读出它的标题行矩形 → 只点/右键标题行**，逐级回退：
//   ① 搜索面板选中 → 右键**标题行**
//   ② 直接点**标题行**选中（把焦点交回画布）→ 右键标题行
//   ③ 选中后按 ⌫（点过标题行后焦点在画布，按手册给的正解）
//   ④ 适配画布（⇧1）后再试 ①
// 每级都验证「节点数减一」，失败就把那一级的诊断如实记下来（不留残局、不假装成功）。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '190d', 目标: '删掉 190c 留下的文本节点并把缩放复位' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 缩放: await R.zoom(), 状态行: await R.status(), 积分: await R.credits() };
const 节点数 = async () => (await R.ids()).length;

const 目标id = 'node_x2j4zn9thf';
rec.目标还在 = (await R.ids()).includes(目标id);
if (!rec.目标还在) { rec.结果 = '目标已不在画布，无需清理'; }

/** 读一个节点的几块矩形：标题行 / 卡片主体 / 整体。 */
const 矩形 = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const b = (el) => { if (!el) return null; const r = el.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; };
  return { 整体: b(n), 标题: b(n.querySelector('[data-testid="flow-node-title"]')),
    主体: b(n.querySelector('[data-testid="text-flow-node-full"]') || n),
    是否有编辑器: !!n.querySelector('[data-testid="text-editor-node-overlay"], .ProseMirror') }; }, id);

const 菜单扫描 = () => p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"]'))
  .filter((m) => m.getBoundingClientRect().width > 1);
  return { 菜单数: ms.length,
    逐项: ms.length ? Array.from(ms[0].querySelectorAll('[role="menuitem"]')).map((e) => (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 40)) : [],
    画布上有没有编辑器: !!document.querySelector('[data-testid="text-editor-node-overlay"]') }; });

/**
 * 🔴 上一版把记录写在动作**之后**才 push，动作里却去读 `rec.尝试[0]` ⇒
 *   `Cannot set properties of undefined`，三轮尝试全废。
 *   ⇒ 这一版**先把空记录 push 进去、再让动作往这条记录上填**（动作与记录一一对应，不再靠下标猜）。
 */
const 试 = async (名, 动作) => { const 前 = await 节点数();
  const 诊断 = { 名, 前节点数: 前, 成功: false };
  rec.尝试.push(诊断);
  try { await 动作(诊断); } catch (e) { 诊断.异常 = e.message; }
  let 后 = 前;
  for (let i = 0; i < 14 && 后 === 前; i++) { await p.waitForTimeout(250); 后 = await 节点数(); }
  诊断.后节点数 = 后; 诊断.成功 = 后 === 前 - 1 && !(await R.ids()).includes(目标id);
  return 诊断.成功; };

rec.尝试 = [];
if (rec.目标还在) {
  const R0 = await 矩形(目标id);
  rec.目标矩形 = R0;
  // ① 搜索面板选中 → 右键标题行
  const 成了 = await 试('① 搜索选中后右键标题行', async (D) => {
    const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
      if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
    if (!开) throw new Error('没有搜索按钮');
    await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
    const inp = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
    if (!inp) { await p.keyboard.press('Escape'); throw new Error('搜索面板没打开'); }
    await p.mouse.click(inp[0], inp[1]); await p.waitForTimeout(400);
    await p.fill('[data-testid="canvas-search-panel"] input', 'JIMENG-B190-SENTINEL'); await p.waitForTimeout(1600);
    const hit = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
      .map((e) => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
      .filter((x) => x.文字.includes('JIMENG-B190-SENTINEL')));
    if (!hit.length) { await p.keyboard.press('Escape'); throw new Error('搜索无命中'); }
    await p.mouse.click(hit[0].点[0], hit[0].点[1]); await p.waitForTimeout(1400);
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);
    const r1 = await 矩形(目标id);
    if (!r1 || !r1.标题) throw new Error('标题行矩形读不到');
    const c = [r1.标题.x + Math.min(30, r1.标题.w / 2), r1.标题.y + r1.标题.h / 2];
    await p.mouse.click(c[0], c[1], { button: 'right' }); await p.waitForTimeout(1300);
    D.菜单扫描 = await 菜单扫描();
    const 项 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"]')).find((e) => (e.innerText || '').trim().startsWith('删除'));
      if (!it) return null; const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (项) { await p.mouse.click(项[0], 项[1]); } else { throw new Error('菜单里没有「删除」'); }
  });
  if (!成了) {
    // ② 点标题行选中 → ⌫（手册给的正解之一）
    await 试('② 点标题行后按 ⌫', async (D) => {
      const r1 = await 矩形(目标id); if (!r1 || !r1.标题) throw new Error('标题行矩形读不到');
      const c = [r1.标题.x + Math.min(30, r1.标题.w / 2), r1.标题.y + r1.标题.h / 2];
      await p.mouse.click(c[0], c[1]); await p.waitForTimeout(1100);
      D.点后焦点 = await p.evaluate(() => { const a = document.activeElement;
        return { tag: a.tagName, testid: a.getAttribute('data-testid'), cls: String(a.className || '').split(' ')[0] }; });
      D.菜单扫描前 = await 菜单扫描();
      await p.keyboard.press('Backspace');
    });
  }
  if (!(await R.ids()).includes(目标id) === false) {
    // ③ 适配画布后重试 ①
    await 试('③ 适配画布后重试', async (D) => {
      await p.keyboard.press('Shift+1'); await p.waitForTimeout(2500);
      D.适配后缩放 = await R.zoom();
      const r1 = await 矩形(目标id); if (!r1) throw new Error('适配后仍读不到矩形');
      D.矩形 = r1;
      const c = [r1.整体.x + r1.整体.w / 2, r1.整体.y + Math.min(16, r1.整体.h / 2)];
      await p.mouse.click(c[0], c[1]); await p.waitForTimeout(900);
      await p.mouse.click(c[0], c[1], { button: 'right' }); await p.waitForTimeout(1300);
      D.菜单扫描 = await 菜单扫描();
      const 项 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"]')).find((e) => (e.innerText || '').trim().startsWith('删除'));
        if (!it) return null; const r = it.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
      if (!项) throw new Error('菜单里没有「删除」');
      await p.mouse.click(项[0], 项[1]);
    });
  }
}

// 缩放复位
rec.缩放复位 = await setZoom(p, 26);
await p.keyboard.press('Escape'); await p.waitForTimeout(800);
const ids = await R.ids();
rec.清理后 = { 节点数: ids.length, 缩放: await R.zoom(), 状态行: await R.status(),
  目标还在: ids.includes(目标id),
  相对基线多: ids.filter((x) => !基线.ids.includes(x)), 相对基线少: 基线.ids.filter((x) => !ids.includes(x)) };
rec.判定 = { 清理成功: !ids.includes(目标id), 与基线一致: rec.清理后.相对基线多.length === 0 && rec.清理后.相对基线少.length === 0,
  缩放已复位: rec.清理后.缩放 === 'Zoom options, 26%',
  用了几级才成功: rec.尝试.filter((x) => x.成功).map((x) => x.名),
  非空守卫: { 尝试次数: rec.尝试.length, 目标已不在画布时跳过: !rec.目标还在 } };
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();

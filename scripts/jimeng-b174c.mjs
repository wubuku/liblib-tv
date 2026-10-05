// 批次 174 c 轮：把 b 轮那**三处「等于没有这道门」的检查**逐条修掉，外加两个新问题。
//
// 🔴 b 轮自曝的三个假通过（同一类毛病：前置态没造出来 / 比较恒真 / 自变量没控住）
//   ① `选中态 ✅活`   —— 改后 `选中: []`。点了「视频 1」的标题**根本没选中**，
//                        前后都是空数组，比的是 [] == []。
//   ② `侧栏开 ✅活`   —— 原始/改后/重载后**侧栏一直开着**，比较恒真。
//   ③ `浮层 ✅活`     —— `canvas-node-summary-popover` 刷新后还在 @73,47。
//                        ⚠️ 但 reload **不会移动鼠标**，而鼠标此刻正停在顶栏
//                        「节点 N」按钮上（就是点它开浮层的那一下）⇒
//                        很可能 popover 是 **hover 触发**，刷新后是「重新触发」不是「被记住」。
//                        必须做**鼠标移开**的对照，否则会把「没控住自变量」写成产品行为。
//
// 本轮四个问题：
//   Q1 浮层：鼠标移开 + 关掉浮层 → reload → 它自己会弹回来吗？
//   Q2 选中：怎么才能真选中一个节点（带**非空守卫**）？移开鼠标 → reload → 选中还在吗？
//   Q3 `canvas-panels.openPanelId` 到底记什么？（b 轮读出节点汇总浮层开着时它**仍是 null**）
//   Q4 刷新后的 26% 缩放，是不是「装下全部节点」的 fit？（可算：量节点包围盒）
//   Q5 顶栏「已保存」有没有中间态「保存中」？（手册只见过「已保存」三个字）
//
// ⛔ 不生成、不分享、不新建节点。重命名会**改回原样**。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '174c' };

const 读 = () => p.evaluate(() => ({
  浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[data-testid$=-popover]'))
    .filter((m) => m.getBoundingClientRect().width > 1)
    .map((m) => { const r = m.getBoundingClientRect(); return (m.getAttribute('data-testid') || m.getAttribute('aria-label')) + `@${Math.round(r.x)},${Math.round(r.y)}`; }),
  选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')),
  选中标题: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => (n.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0]),
  保存态: (() => { const e = document.querySelector('[data-testid="canvas-title-save-status"]'); return e ? (e.textContent || '').trim() : null; })(),
  偏好: Object.fromEntries(Object.keys(localStorage).filter((k) => /octo\.user-preferences/.test(k)).map((k) => [k.split('.').pop(), localStorage.getItem(k)])),
  缩放: document.querySelector('[data-testid="canvas-zoom-percent"]')?.getAttribute('aria-label'),
  transform: document.querySelector('.react-flow__viewport')?.style.transform,
  节点数: document.querySelectorAll('.react-flow__node').length,
}));
/** 鼠标挪到一个**确定为空白**的位置，并把当前浮层关掉。 */
const 清场 = async () => {
  await p.mouse.move(640, 700); await p.waitForTimeout(500);
  for (let i = 0; i < 3; i++) {
    const r = await 读();
    if (!r.浮层.length) break;
    await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  }
  return 读();
};
const 点中心 = async (选择器) => {
  const pt = await p.evaluate((sel) => { const e = document.querySelector(sel); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 选择器);
  if (!pt) return false;
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(800); return true;
};
const 重载 = async () => {
  await p.reload({ waitUntil: 'domcontentloaded' });
  await pinViewport(p);
  const t0 = Date.now();
  while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
  await p.waitForTimeout(2500);
};

await settle(p, R);

// ═══════════════════════ Q1 浮层：鼠标移开 + 显式关掉，再刷新
rec.Q1 = {};
await 点中心('[data-testid="canvas-node-summary-trigger"]');
rec.Q1.点开后 = await 读();
rec.Q1.清场后 = await 清场();
await 重载();
rec.Q1.重载后_鼠标仍在原位 = await 读();
await p.mouse.move(1250, 10); await p.waitForTimeout(1200);   // 鼠标彻底离开顶栏
rec.Q1.重载后_鼠标已移开 = await 读();

// ═══════════════════════ Q2 选中：非空守卫 —— 必须真的选中一个才继续
rec.Q2 = { 尝试: [] };
const 候选 = await p.evaluate(() => {
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    if (r.width < 30 || r.x < 200 || r.x > 1000 || r.y < 100 || r.y > 620) continue;
    const t = n.querySelector('[data-testid="flow-node-title"]');
    if (!t) continue;
    const tr = t.getBoundingClientRect();
    out.push({ id: n.getAttribute('data-id'), 标题: (t.innerText || '').trim().split('\n')[0],
      标题点: [Math.round(tr.x + tr.width / 2), Math.round(tr.y + tr.height / 2)],
      节点中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
  }
  return out.slice(0, 6);
});
for (const c of 候选) {
  for (const [方式, pt] of [['标题', c.标题点], ['中心', c.节点中心]]) {
    await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(700);
    const 读回 = await 读();
    rec.Q2.尝试.push({ id: c.id, 标题: c.标题, 方式, 选中数: 读回.选中.length, 选中: 读回.选中 });
    if (读回.选中.length) { rec.Q2.选中成功 = { id: c.id, 方式, 标题: c.标题 }; break; }
  }
  if (rec.Q2.选中成功) break;
}
if (rec.Q2.选中成功) {
  await p.mouse.move(640, 700); await p.waitForTimeout(800);      // 鼠标移开，防 hover 干扰
  rec.Q2.移开鼠标后 = await 读();
  await 重载();
  await p.mouse.move(1250, 10); await p.waitForTimeout(1000);
  rec.Q2.重载后 = await 读();
} else {
  rec.Q2.重载后 = '没选中成功，**这一项没测到**（不写成「刷新后选中态清空」）';
}

// ═══════════════════════ Q3 openPanelId 到底记什么
rec.Q3 = { 起点: (await 读()).偏好 };
await 点中心('[data-testid="canvas-panel-launcher"]');           // 「搜索」
rec.Q3.点搜索后 = await 读();
await 清场();
await 点中心('[data-testid="canvas-node-summary-trigger"]');
rec.Q3.点节点汇总后 = await 读();
await 清场();

// ═══════════════════════ Q4 刷新后的缩放是不是 fit（算包围盒）
rec.Q4 = await p.evaluate(() => {
  const ns = Array.from(document.querySelectorAll('.react-flow__node'));
  const 盒 = ns.map((n) => n.getBoundingClientRect()).filter((r) => r.width > 0);
  if (!盒.length) return { 失败: '没有可见节点' };
  const x0 = Math.min(...盒.map((r) => r.left)), x1 = Math.max(...盒.map((r) => r.right));
  const y0 = Math.min(...盒.map((r) => r.top)), y1 = Math.max(...盒.map((r) => r.bottom));
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  const scale = m ? parseFloat(m[1]) : null;
  // 把包围盒换算回 **canvas 坐标**（去掉视口平移与缩放）
  const mm = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  const tx = mm ? parseFloat(mm[1]) : 0, ty = mm ? parseFloat(mm[2]) : 0;
  const w = (x1 - x0) / scale, h = (y1 - y0) / scale;
  return {
    节点数: ns.length, 当前缩放: scale, 视口: [innerWidth, innerHeight],
    屏幕包围盒: [Math.round(x0), Math.round(y0), Math.round(x1), Math.round(y1)],
    屏幕包围盒尺寸: [Math.round(x1 - x0), Math.round(y1 - y0)],
    换算成canvas的尺寸: [Math.round(w), Math.round(h)],
    fit所需缩放_按宽: Math.round((innerWidth / w) * 1000) / 1000,
    fit所需缩放_按高: Math.round((innerHeight / h) * 1000) / 1000,
    视口平移: [Math.round(tx * 10) / 10, Math.round(ty * 10) / 10],
  };
});

// ═══════════════════════ Q5 「已保存」有没有中间态
// 方法：重命名一个**文本节点**，然后**高频轮询**保存指示器，看能不能撞到别的态。
// 🔴 守卫：轮询必须带**非空**读数（batch 57 教训：恒真的检查等于没检查）。
rec.Q5 = { 采样: [], 撞到的不同态: new Set() };
const 目标 = await p.evaluate(() => {
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const t = n.querySelector('[data-testid="flow-node-title"]');
    if (!t) continue;
    const r = n.getBoundingClientRect();
    if (r.x < 200 || r.x > 1000 || r.y < 100 || r.y > 620) continue;
    const 标题 = (t.innerText || '').trim().split('\n')[0];
    if (/^文本\s*\d+$/.test(标题)) { const tr = t.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), 原名: 标题, 点: [Math.round(tr.x + tr.width / 2), Math.round(tr.y + tr.height / 2)] }; }
  }
  return null;
});
if (!目标) {
  rec.Q5.失败 = '屏幕上找不到可点的文本节点';
} else {
  rec.Q5.目标 = 目标;
  await p.mouse.click(目标.点[0], 目标.点[1]); await p.waitForTimeout(700);
  // 双击标题进编辑，追加一个字符后回车
  await p.mouse.dblclick(目标.点[0], 目标.点[1]); await p.waitForTimeout(700);
  const 编辑中 = await p.evaluate(() => { const a = document.activeElement;
    return { tag: a?.tagName?.toLowerCase(), testid: a?.getAttribute?.('data-testid'), contenteditable: a?.getAttribute?.('contenteditable') }; });
  rec.Q5.双击后焦点 = 编辑中;
  if (编辑中.tag === 'input' || 编辑中.tag === 'textarea' || 编辑中.contenteditable != null) {
    await p.keyboard.press('End');
    await p.keyboard.type('t', { delay: 40 });
    // ⏱ 从落下这第一笔就开始采样：保存指示器是 aria-live=polite 的 <output>，
    //    改完到点保存之间只隔一个防抖窗口，采样必须比它快。
    // ⚠️ t0 必须**先**建好再建 interval，否则回调里 `Date.now() - undefined` 全是 NaN
    //    （而 NaN 全相等 ⇒ 时间轴读数会看起来"正常"却全是垃圾）。
    rec.Q5.t0 = Date.now();
    const 采样 = setInterval(async () => {
      try { const s = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-title-save-status"]');
        return e ? (e.textContent || '').trim() : null; });
        if (s) { rec.Q5.采样.push([Date.now() - rec.Q5.t0, s]); rec.Q5.撞到的不同态.add(s); }
      } catch {}
    }, 40);
    await p.keyboard.press('Enter');
    await p.waitForTimeout(4000);
    clearInterval(采样);
    rec.Q5.采样ms = Date.now() - rec.Q5.t0;
    // ---- 复原：把名字改回去
    await p.mouse.dblclick(目标.点[0], 目标.点[1]); await p.waitForTimeout(600);
    await p.keyboard.press('End'); await p.keyboard.press('Backspace');
    await p.keyboard.press('Enter'); await p.waitForTimeout(2500);
    rec.Q5.复原后标题 = await p.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      return n ? (n.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0] : null; }, 目标.id);
    rec.Q5.复原成功 = rec.Q5.复原后标题 === 目标.原名;
  } else {
    rec.Q5.失败 = '双击标题没有进编辑态，不能测保存中间态';
    await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  }
}
rec.Q5.撞到的不同态 = [...rec.Q5.撞到的不同态];
delete rec.Q5.t0;

console.log(JSON.stringify(rec, null, 1));
process.exit(0);

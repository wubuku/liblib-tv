// 批次 177 b 轮：① 钉死搜索面板那个**没插值的 ICU aria**；② **撤销/重做状态机**。
//
// ⚠️ v1 崩了：`document.querySelector('.react-flow__node.selected [data-testid=…]')`
//    在「当前没有选中」时返回 null，紧接着 `.getBoundingClientRect()` ⇒ TypeError。
//    ⇒ 本版**每个查询都带守卫**，返回不了就显式记 null，**不中断整轮**。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { keyGuard } from './jimeng-safe-keys.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '177b' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 选中并确认 = async (id) => {
  const 准 = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    if (!t) return null; t.scrollIntoView({ block: 'center', inline: 'center' }); return true; }, id);
  if (!准) return { 成功: false, 原因: '节点没有标题元素' };
  await p.waitForTimeout(800);
  const q = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect();
    return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; }, id);
  if (!q) return { 成功: false, 原因: '标题没有面积（可能被压扁或在视口外）' };
  await p.mouse.click(q[0], q[1]); await p.waitForTimeout(800);
  const s = await 选中集();
  return { 成功: s.length === 1 && s[0] === id, 选中集: s };
};
const 读撤销重做 = async () => {
  const s = await 选中集();
  if (s.length !== 1) return { 读不到: `选中集=${JSON.stringify(s)}` };
  const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, s[0]);
  if (!pt) return { 读不到: '取不到标题坐标' };
  await p.mouse.move(pt[0], pt[1]); await p.waitForTimeout(250);
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1300);
  const m = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]'); if (!e) return null;
    return { 项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => ({ aria: i.getAttribute('aria-label'),
      快捷键: i.getAttribute('aria-keyshortcuts'), 禁用: i.getAttribute('aria-disabled') === 'true',
      span: Array.from(i.children).map((c) => (c.innerText || '').trim()) })) };
  });
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  if (!m) return { 读不到: '菜单没开' };
  const 挑 = (k) => { const x = m.项.find((i) => i.aria === k); return x ? { 禁用: x.禁用, 快捷键: x.快捷键, 原文: x.span.join(' ｜ ') } : '(菜单里没有这一项)'; };
  return { 选中: s[0], 重做: 挑('重做'), 撤销: 挑('撤销') };
};

// ═════════ ① 搜索面板分页
rec.分页 = {};
const 搜开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (搜开) {
  await p.mouse.click(搜开[0], 搜开[1]); await p.waitForTimeout(2200);
  rec.分页.NAV = await p.evaluate(() => {
    const n = Array.from(document.querySelectorAll('[aria-label]')).find((x) => /Search result pages/.test(x.getAttribute('aria-label') || ''));
    if (!n) return { 失败: '没有分页 NAV' };
    const r = n.getBoundingClientRect();
    return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      aria: n.getAttribute('aria-label'), 文字: (n.innerText || '').trim().replace(/\n/g, ' | '),
      逐个: Array.from(n.querySelectorAll('button,[role=button],a')).map((b) => {
        const q = b.getBoundingClientRect(); const cs = getComputedStyle(b);
        return { aria: b.getAttribute('aria-label'), 文字: (b.innerText || '').trim(), 禁用: b.getAttribute('aria-disabled') || (b.disabled ? 'true' : null),
          颜色: cs.color, 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; }) };
  });
  rec.分页.模板出现处 = await p.evaluate(() => {
    const 出 = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let x; while ((x = w.nextNode())) if (x.nodeValue && x.nodeValue.includes('{num, plural,')) {
      const e = x.parentElement; const r = e.getBoundingClientRect();
      出.push({ 标签: e.tagName.toLowerCase(), 元素aria: e.getAttribute('aria-label'), 文字: (e.textContent || '').trim().slice(0, 70),
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }); }
    return 出; });
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
} else rec.分页.失败 = '顶栏没有「搜索」按钮';

// ═════════ ② 撤销/重做状态机
const 前id = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));
rec.状态机 = { 起始节点数: 前id.length, 步: [], 守卫: await keyGuard(p) };
const 靶 = await p.evaluate(() => {
  for (const n of document.querySelectorAll('.react-flow__node')) {
    if (!/node-text/.test(n.className)) continue;
    const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) continue;
    t.scrollIntoView({ block: 'center', inline: 'center' });
    return { id: n.getAttribute('data-id'), 标题: (t.innerText || '').trim().split('\n')[0] }; }
  return null; });
rec.状态机.靶子 = 靶;
if (!靶) rec.状态机.中止 = '画布上找不到文本节点';
else {
  const S = await 选中并确认(靶.id);
  rec.状态机.选中靶子 = S;
  rec.状态机.步.push({ 步: 'S0 刚刷新完、未做任何操作', 节点数: 前id.length, 撤销重做: S.成功 ? await 读撤销重做() : S });

  let 新增 = [];
  if (S.成功) {
    const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
      const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 靶.id);
    await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1400);
    const 定位 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
        .find((x) => (x.innerText || '').trim().startsWith('复制副本'));
      if (!e) return null; const r = e.getBoundingClientRect();
      return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
    rec.状态机.复制副本项 = 定位;
    if (定位 && !定位.禁用) {
      await p.mouse.click(定位.点[0], 定位.点[1]); await p.waitForTimeout(3200);
      const 现 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));
      新增 = 现.filter((i) => !前id.includes(i));
    }
    rec.状态机.步.push({ 步: 'S1 走菜单「复制副本」之后', 节点数: (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)), 新增id: 新增 });
  }
  if (新增.length) {
    const 副本 = 新增[0];
    const 选副本 = await 选中并确认(副本);
    rec.状态机.步.push({ 步: 'S1b 选中刚造出来的副本', 选中: 选副本, 撤销重做: 选副本.成功 ? await 读撤销重做() : null });
    const G = await keyGuard(p);
    if (G.safe) {
      const 撤前 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
      await p.keyboard.press('Meta+z'); await p.waitForTimeout(2600);
      const 撤后 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
      rec.状态机.步.push({ 步: 'S2 按 ⌘Z 之后', 守卫: G, 前节点数: 撤前, 后节点数: 撤后,
        副本还在: (await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), 副本)),
        撤销重做: await 读撤销重做() });
    } else rec.状态机.步.push({ 步: 'S2 跳过', 原因: '焦点守卫不通过', 守卫: G });
  }
  // 收尾：按 id 清掉本轮新增
  for (const id of 新增) {
    const ok = await 选中并确认(id);
    if (ok.成功) { await p.keyboard.press('Backspace'); await p.waitForTimeout(1800); }
  }
  rec.状态机.收尾 = { 现在节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length),
    新增: 新增, 残留: await p.evaluate((ids) => ids.filter((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`)), 新增),
    原有总数: 前id.length, 原有仍在: await p.evaluate((old) => old.filter((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`)).length, 前id) };
}
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
await p.mouse.move(1250, 10);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

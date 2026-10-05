// 批次 175 d 轮：修 c 轮两处**脚本 bug**，并把 S1×S3 对账做完。
//
// c 轮两处自身失误（都不是页面的问题，是我没对齐）：
//   ① C2 拿**中文类型名**去比 `react-flow__node-<type>` 的 **英文** class
//      （`'图片' === 'image'` 永远不成立）⇒ 候选全空、整段空转。
//   ② C1 用 `element.click()`（JS 合成事件）去开「用户菜单」——
//      React 组件未必响应 ⇒ 菜单项读到空数组，还误判成「没有帮助入口」。
//      ⇒ 触发控件一律用**真实鼠标点击**。
//
// d 轮要产出的三件东西：
//   D1 帮助面板的 28 项（现场重读，S1）× 菜单声明的 7 项（S3）→ **对账表**
//   D2 「下载」的禁用规则：**类型规则**（音频/导演台不在允许列表）还是**空壳规则**（没资源）
//   D3 收尾：刷新一次让视口回到 app 自己的 fit 读数（c 轮结束时是 21%）
//
// ⛔ 不生成、不下载、不分享。⛔ 本轮**不按任何快捷键**（实测已在 c 轮做完）。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '175d' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(500);

/** 真实鼠标点一个元素（不用 element.click()）。 */
const 真点 = async (sel, 说明) => {
  const pt = await p.evaluate((s) => { const e = document.querySelector(s); if (!e) return null;
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return null;
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, sel);
  if (!pt) { (rec.失败 ||= []).push(说明 || sel); return false; }
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1800); return true;
};
const 可见项 = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem],[role=dialog] button,[role=dialog] [role=button]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { 文字: (e.innerText || '').trim().replace(/\n/g, ' | '), 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
const 按id选中 = async (id) => {
  const ok = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return false;
    n.querySelector('[data-testid="flow-node-title"]')?.scrollIntoView({ block: 'center', inline: 'center' }); return true; }, id);
  if (!ok) return false; await p.waitForTimeout(700);
  const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    if (!t) return null; const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
  if (!pt) return false;
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(800);
  const s = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  return s.length === 1 && s[0] === id;
};

// ═══════════ D1 帮助面板（真实点击进入）
rec.D1 = {};
rec.D1.用户菜单 = { 点开: await 真点('[data-testid="canvas-user-menu-trigger"]', '用户菜单按钮') };
rec.D1.用户菜单.项 = await 可见项();
const 帮 = rec.D1.用户菜单.项.find((m) => /帮助|手册|快捷键/.test(m.文字));
rec.D1.帮助入口 = 帮 ? 帮.文字 : null;
if (帮) {
  await p.mouse.click(帮.盒[0] + 24, 帮.盒[1] + 帮.盒[3] / 2); await p.waitForTimeout(2400);
  rec.D1.面板 = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="shortcut-help-scroll-region"]');
    if (!e) return null;
    const q = e.getBoundingClientRect();
    return { 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      scrollHeight: e.scrollHeight, clientHeight: e.clientHeight,
      行: e.innerText.split('\n').map((s) => s.trim()).filter(Boolean) };
  });
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
}

// ═══════════ D1b 菜单侧（节点右键，7 项）
rec.D1.菜单 = {};
const 候选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return null;
  return { id: n.getAttribute('data-id'), 标题: (t.innerText || '').trim().split('\n')[0],
    类型: (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null }; })
  .filter(Boolean));
rec.D1.类型分布 = 候选.reduce((a, c) => { a[c.类型] = (a[c.类型] || 0) + 1; return a; }, {});

// ═══════════ D2 「下载」的禁用规则（受控对照，用**英文**类型名）
rec.D2 = [];
const 顺序 = ['audio', 'video', 'image', 'text', 'director', 'timeline', 'subject'].filter((t) => 候选.some((c) => c.类型 === t));
for (const 类型 of 顺序.slice(0, 6)) {
  const 节点 = 候选.find((c) => c.类型 === 类型);
  if (!await 按id选中(节点.id)) { rec.D2.push({ 类型, 节点: 节点.id, 说明: '选不中' }); await p.mouse.click(640, 690); continue; }
  const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    const r = t.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 节点.id);
  await p.mouse.move(pt[0], pt[1]); await p.waitForTimeout(250);
  await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1400);
  const 读 = await p.evaluate(() => {
    const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return null;
    return { 盒: (() => { const q = m.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; })(),
      innerText: m.innerText,
      项: Array.from(m.querySelectorAll('[role=menuitem]')).map((i) => ({ aria: i.getAttribute('aria-label'),
        快捷键: i.getAttribute('aria-keyshortcuts'), 禁用: i.getAttribute('aria-disabled') === 'true',
        span: Array.from(i.children).map((c) => (c.innerText || '').trim()) })) };
  });
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  await p.mouse.click(640, 690); await p.waitForTimeout(600);
  const 下 = 读?.项.find((i) => i.aria === '下载');
  rec.D2.push({ 类型, 节点id: 节点.id, 标题: 节点.标题, 菜单盒: 读?.盒, 菜单全文: 读?.innerText?.replace(/\n/g, ' / '),
    下载存在: !!下, 下载禁用: 下 ? 下.禁用 : null, 原因: 下 ? 下.span[1] : null,
    菜单项数: 读?.项.length, 全部快捷键: 读?.项.map((i) => `${i.aria}=${i.快捷键 || '—'}${i.禁用 ? '(禁用)' : ''}`) });
}
await p.keyboard.press('Escape'); await p.waitForTimeout(600);

// ═══════════ D3 收尾：刷新一次，让视口回到 app 自己的 fit
rec.D3 = { 刷新前缩放: await R.zoom() };
await p.reload({ waitUntil: 'domcontentloaded' });
await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
rec.D3.刷新后 = { 状态行: await R.status(), 缩放: await R.zoom(), 积分: await R.credits(),
  节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length),
  选中: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length) };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

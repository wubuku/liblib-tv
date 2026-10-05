// 批次 175 c 轮：对账 + **实测「菜单印着、帮助面板没列」的那几个键到底能不能用**。
//
// a 轮的结论（`aria-keyshortcuts` 全页只有 2 个、都是 F）在本轮**被推翻**：
// 那是因为 a 轮扫的是**空闲页面**，而这些属性**只在浮层打开时才存在**。
// 打开节点右键菜单一读：`aria-keyshortcuts` **每个菜单项都有**。
// ⇒ 🔴 立规候选：**静态普查前先问「这个属性是不是只在某个状态下才存在」**；
//    在空闲态扫出来的「没有」和「这个功能没有」是两件事。
//
// 菜单实测（选中「音频 1」时，200×292，7 项）：
//   复制 ⌘ C        → aria-keyshortcuts `Meta+C`
//   复制副本 ⌘ D    → `Meta+D`
//   粘贴 ⌘ V        → `Meta+V`
//   下载 +「请选择至少一个组、文本、图片或视频项」→ **无快捷键**、**禁用**
//   重做 ⌘ ⇧ Z +「无需重做操作」→ **`Meta+Shift+Z` + `Meta+Y`（两个！）**、禁用
//   撤销 ⌘ Z +「无需撤销操作」→ `Meta+Z`、禁用
//   删除 ⌫          → **`Backspace`**
//
// 三个待答：
//   C1 对账：菜单声明的键里，哪些**帮助面板的 28 项里没有**？
//   C2「下载」的禁用是**类型规则**（音频/导演台不在允许列表）还是**空壳规则**（没资源）？
//   C3 面板没列的那几个键，**到底能不能用**？
//
// ⚠️ C3 有副作用，用**一条自造链**兜住：⌘D 造副本 → 选中副本 → ⌫ 删副本。
//    全程**不碰任何原有节点**，画布节点数应回到 76 并按 id 验明。
// ⛔ 不生成、不下载、不分享。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '175c' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(500);

const 菜单 = async (x, y) => {
  await p.mouse.move(x, y); await p.waitForTimeout(300);
  await p.mouse.click(x, y, { button: 'right' }); await p.waitForTimeout(1400);
  const m = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    if (!e) return null;
    const q = e.getBoundingClientRect();
    return { 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      innerText: e.innerText,
      项: Array.from(e.querySelectorAll('[role=menuitem]')).map((i) => ({
        aria: i.getAttribute('aria-label'), 快捷键: i.getAttribute('aria-keyshortcuts'),
        禁用: i.getAttribute('aria-disabled') === 'true',
        文字: (i.innerText || '').trim().replace(/\n/g, ' | '),
        两个span: Array.from(i.children).map((c) => (c.innerText || '').trim()),
        点: (() => { const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; })() })) };
  });
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  return m;
};
/** 按 id 找节点标题行的中心（立规：别点几何中心，批次 171/173 两次教训）。 */
const 标题点 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return null;
  t.scrollIntoView({ block: 'center', inline: 'center' }); return true;
}, id).then(async (ok) => {
  if (!ok) return null; await p.waitForTimeout(700);
  return p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const t = n.querySelector('[data-testid="flow-node-title"]'); const r = t.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
});
const 选中 = async (id) => { const pt = await 标题点(id); if (!pt) return false;
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(800);
  const s = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  return s.length === 1 && s[0] === id; };
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const 存在 = (id) => p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), id);

// ═════════════ C1 对账：帮助面板 28 项（现场重读）
rec.C1 = {};
await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]');
  if (e) e.click(); }); await p.waitForTimeout(1200);
const 用户菜单 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem],[role=dialog] button'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { 文字: (e.innerText || '').trim(), 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
rec.C1.用户菜单 = 用户菜单;
const 帮助 = 用户菜单.find((m) => /帮助|手册|快捷键/.test(m.文字));
if (帮助) {
  await p.mouse.click(帮助.盒[0] + 20, 帮助.盒[1] + 10); await p.waitForTimeout(2200);
  rec.C1.面板全文 = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="shortcut-help-scroll-region"]');
    return e ? e.innerText.split('\n').map((s) => s.trim()).filter(Boolean) : null; });
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
} else { await p.keyboard.press('Escape'); await p.waitForTimeout(600); rec.C1.说明 = '用户菜单里没找到帮助入口'; }

// ═════════════ C2 「下载」的禁用是类型规则还是空壳规则（受控对照）
rec.C2 = [];
const 候选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return null;
  return { id: n.getAttribute('data-id'), 标题: (t.innerText || '').trim().split('\n')[0], 类型类: (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null }; })
  .filter(Boolean).slice(0, 40));
const 挑 = ['音频', '文本', '视频', '图片', '导演台', '时间线', '主体'].map((k) => ({ 类型: k, 节点: 候选.find((c) => c.类型类 === k) })).filter((x) => x.节点);
for (const { 类型, 节点 } of 挑.slice(0, 5)) {
  if (!await 选中(节点.id)) { rec.C2.push({ 类型, 节点: 节点.id, 说明: '选不中（已跳过）' }); continue; }
  const pt = await 标题点(节点.id);
  const m = await 菜单(pt[0], pt[1]);
  const 下载 = m?.项.find((i) => i.aria === '下载') || null;
  rec.C2.push({ 类型, 节点id: 节点.id, 标题: 节点.标题,
    下载禁用: 下载 ? 下载.禁用 : '菜单里没有下载项', 原因: 下载 ? 下载.两个span[1] : null });
  await p.mouse.click(640, 690); await p.waitForTimeout(700);
}
await p.keyboard.press('Escape'); await p.waitForTimeout(500);

// ═════════════ C3 实测「菜单印着、面板没列」的键
rec.C3 = { 守卫: await keyGuard(p), 起始节点数: await 节点数() };
if (!rec.C3.守卫.safe) rec.C3.中止 = '焦点守卫不通过，按键会打进输入框';

// 链条：⌘D 造副本 → 选中副本 → ⌫ 删副本。全程不碰原有节点。
// ⚠️ 键名里带 `⌘` 就**不能**用点号属性（批次 173 踩过），统一用 `rec.C3['…']`。
if (rec.C3.守卫.safe) {
  const 原有 = await p.evaluate(() =>
    Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());

  // 选一个**有内容的**节点做复制副本（图片节点 b22-upload，带 IMG）
  const 宿主候选 = 候选.find((c) => c.类型类 === '图片') || 候选[0];
  rec.C3.宿主 = { id: 宿主候选.id, 标题: 宿主候选.标题, 类型: 宿主候选.类型类 };
  await 选中(宿主候选.id);
  await p.keyboard.press('Meta+d'); await p.waitForTimeout(2500);
  const D后数 = await 节点数();
  const D后新 = await p.evaluate((旧) =>
    Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).filter((i) => !旧.includes(i)), 原有);
  rec.C3['按Meta+D后'] = { 节点数: D后数, 新id: D后新 };
  rec.C3['Meta+D结论'] = D后新.length ? '✅ 生成了副本'
    : (D后数 === rec.C3.起始节点数 ? '❌ 什么都没发生' : '⚠️ 数量变了但没有新 id');

  if (D后新.length) {
    const 副本 = D后新[0];
    rec.C3.选中副本 = await 选中(副本);
    const 前 = await 节点数();
    await p.keyboard.press('Backspace'); await p.waitForTimeout(2000);
    const 后数 = await 节点数(), 还在 = await 存在(副本);
    rec.C3['按Backspace后'] = { 前节点数: 前, 后节点数: 后数, 副本还在: 还在 };
    rec.C3['Backspace结论'] = (!还在 && 后数 === 前 - 1) ? '✅ Backspace 删掉了副本' : '❌ Backspace 没生效';
  }
  // ⌘C / ⌘V：只测「有没有生效 / 有没有炸」，不深挖剪贴板（剪贴板读法批次 157 已验）
  await 选中(宿主候选.id);
  await p.keyboard.press('Meta+c'); await p.waitForTimeout(1200);
  rec.C3['按Meta+C后'] = { 节点数: await 节点数(),
    出现错误字样: await p.evaluate(() => /失败|错误|不支持/.test(document.body.innerText)) };
  const 前2 = await 节点数();
  await p.keyboard.press('Meta+v'); await p.waitForTimeout(2800);
  const V后数 = await 节点数();
  rec.C3['按Meta+V后'] = { 前节点数: 前2, 后节点数: V后数,
    浮层: await p.evaluate(() => Array.from(document.querySelectorAll('[role=alert],[role=menu],[data-testid=canvas-context-menu-terminal-feedback]'))
      .filter((e) => e.getBoundingClientRect().width > 20).map((e) => (e.innerText || '').trim().slice(0, 40))) };
  rec.C3['Meta+V结论'] = V后数 > 前2 ? '✅ 粘贴出了新节点' : '⚠️ 节点数没变';

  // 清理：本轮新增的 id 全部按 id 删掉并验明
  const 现存 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));
  rec.C3.本轮新增 = 现存.filter((i) => !原有.includes(i));
  for (const id of rec.C3.本轮新增) { if (await 选中(id)) { await p.keyboard.press('Backspace'); await p.waitForTimeout(1600); } }
  const 仍存 = [];
  for (const id of rec.C3.本轮新增) if (await 存在(id)) 仍存.push(id);
  const 原有仍在 = await p.evaluate((旧) => 旧.filter((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`)).length, 原有);
  rec.C3.收尾 = { 起始节点数: rec.C3.起始节点数, 现在节点数: await 节点数(),
    本轮新增: rec.C3.本轮新增, 新增是否全清: 仍存.length === 0, 仍残留: 仍存,
    原有总数: 原有.length, 原有仍在, 原有是否全在: 原有仍在 === 原有.length };
}
await p.mouse.click(640, 690); await p.waitForTimeout(700);
await p.keyboard.press('Escape'); await p.waitForTimeout(500);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

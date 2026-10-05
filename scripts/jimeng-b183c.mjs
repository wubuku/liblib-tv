// 批次 183 收尾补刀：**把批次 183 残留的那个副本节点删掉。**
//
// 发生了什么（原文不改写，记在这里）：
//   183 主探针里，菜单点「复制副本」造出了 `node_xjvjdw1de0`（标题 `b22-upload (2)`），
//   收尾按三道守卫走：搜索面板选中 → 读 `.selected` 确认就是它 → 按 `⌫` → 2.2 秒后复查。
//   **结果 `删后还在吗: true`** —— 删除没生效，canvas 停在 **77 节点**，缩放被搜索定位改成 25%。
//   好消息是**原有 76 个 id 逐个仍在**（没有删错），坏的只是**多留了一个副本**。
//
// 🔴 这次失败**不是**「点不中就不删」那类保守留白，而是**守卫通过后动作没生效**：
//   选中集确认是对的（`['node_xjvjdw1de0']`），但 `⌫` 按下去 2.2 秒内节点还在。
//   两个可疑原因，逐一排：
//   甲 **等待不够** —— 新建节点可能还在落位/动画中，删除有延迟；
//   乙 **`⌫` 被吞** —— 搜索面板的 helper 结尾按了 `Escape`，焦点/选区状态可能已变。
//   ⇒ 本探针逐级加码：重试 `⌫`（等待加长）→ 不行就**走菜单的「删除」项** → 再不行就换节点类型对照。
//   每一步都按同一把尺子验：**该 id 消失，且原有 76 个 id 逐个仍在**。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '183-收尾补刀' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 标题文案 = (id) => p.evaluate((i) => (document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)?.innerText || '').trim().split('\n')[0], id);
const 存在 = (id) => p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), id);

/** 搜索面板选中（与 183 同一份实现，**这次不按 Escape**，把 Escape 变量先排掉）。 */
const 搜索选中 = async (关键词, 按Escape) => {
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有「搜索」按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1400);
  const 命中 = await p.evaluate((词) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 50),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !词 || x.文字.includes(词)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没有命中「${关键词}」`, 命中数: 0 }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1500);
  const s = await 选中集();
  if (按Escape) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); }
  return { 成功: s.length >= 1, 选中集: s, 命中: 命中.slice(0, 3) };
};

const 目标 = 'node_xjvjdw1de0';
rec.目标 = { id: 目标, 标题: await 标题文案(目标), 现在存在吗: await 存在(目标) };
// 原有 76 个 = 现在的全部减去目标（183 收尾核验已证明原有 76 个逐个仍在）
const 全部 = await id集();
rec.节点数起点 = 全部.length;
const 应保留 = 全部.filter((i) => i !== 目标);
rec.应保留数 = 应保留.length;
rec.步骤 = [];

// ── 步骤 1：重试 ⌫，**不按 Escape**（排乙）+ **等 4 秒**（排甲）
let S = await 搜索选中(rec.目标.标题, false);
rec.步骤.push({ 步: '1_不按Esc按退格_等4秒', 选中: S.选中集, 守卫: (await keyGuard(p)).safe });
if (S.成功 && S.选中集.includes(目标)) {
  await p.keyboard.press('Backspace'); await p.waitForTimeout(4000);
  rec.步骤[rec.步骤.length - 1].删后还在吗 = await 存在(目标);
  rec.步骤[rec.步骤.length - 1].节点数 = await 节点数();
}
if (await 存在(目标)) {
  // ── 步骤 2：走菜单的「删除」项（绕开快捷键）
  S = await 搜索选中(rec.目标.标题, true);
  rec.步骤.push({ 步: '2_走菜单删除项', 选中: S.选中集 });
  if (S.成功 && S.选中集.includes(目标)) {
    const pt = await p.evaluate((i) => { const t = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
      if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; }, 目标);
    rec.步骤[rec.步骤.length - 1].标题坐标 = pt;
    if (pt) {
      await p.mouse.click(pt[0], pt[1], { button: 'right' }); await p.waitForTimeout(1500);
      const 项 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"] [role=menuitem]'))
        .find((x) => (x.innerText || '').trim().startsWith('删除'));
        if (!e) return null; const r = e.getBoundingClientRect();
        return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
      rec.步骤[rec.步骤.length - 1].菜单项 = 项;
      if (项 && !项.禁用) { await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(3000);
        rec.步骤[rec.步骤.length - 1].删后还在吗 = await 存在(目标); rec.步骤[rec.步骤.length - 1].节点数 = await 节点数(); }
    }
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
}

await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 目标还在吗: 末.includes(目标), 节点数是否回到应保留数: 末.length === 应保留.length,
  应保留的逐个还在: 应保留.filter((i) => 末.includes(i)).length, 应保留数: 应保留.length,
  意外丢失: 应保留.filter((i) => !末.includes(i)), 意外多出: 末.filter((i) => !应保留.includes(i)) };
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

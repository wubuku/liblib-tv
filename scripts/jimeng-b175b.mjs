// 批次 175 b 轮：**三路快捷键对账** —— 帮助面板 S1 / 菜单印字 S3 / aria-keyshortcuts S2。
//
// a 轮已经否掉了一个很诱人的假设：全页 `aria-keyshortcuts` **只有 2 个、都是 `F`**，
// `<kbd>` 标签 **0 个** ⇒ **`aria-keyshortcuts` 不是快捷键登记表**，是零散用的。
//
// 而手册那份「28 项三态总账」的来源是**帮助中心面板**，
// 它自己也写明「与下面四张表**逐字一致，无漏项、无多项**」——
// 但那是**同一个源的两 views**（面板 ↔ 抄进手册的表），**不是三方对账**。
// ⇒ 缺的那一路是：**界面自己在菜单里印出来的快捷键**。
//
// 本轮只**打开并读取**三类菜单 + 帮助面板，⛔ 不点任何菜单条目（复制/删除/下载一律不点）。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '175b' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(500);

const 形 = /[⌘⌥⇧⌃⌫⏎↩]|\bEsc\b/;
const 关浮层 = async () => {
  for (let i = 0; i < 5; i++) {
    const n = await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[data-testid$=-popover],[data-testid$=panel]'))
      .filter((m) => m.getBoundingClientRect().width > 1).length);
    if (!n) break;
    await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  }
};
/** 把当前所有可见浮层里的**每一行文字**捞出来（带快捷键的单独标出来）。 */
const 读浮层 = async () => p.evaluate((re) => {
  const re2 = new RegExp(re);
  const 浮 = Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[data-testid$=-popover],[data-testid$=panel]'))
    .filter((m) => m.getBoundingClientRect().width > 1);
  return 浮.map((m) => {
    const r = m.getBoundingClientRect();
    const 行 = Array.from(m.querySelectorAll('[role=menuitem],[role=tab],[role=button],button,li,[data-testid*=item],div'))
      .filter((e) => { const q = e.getBoundingClientRect();
        return q.width > 4 && q.height > 4 && !Array.from(e.children).some((c) => { const cr = c.getBoundingClientRect(); return cr.width > 0 && cr.height > 0; }); })
      .map((e) => { const q = e.getBoundingClientRect();
        return { 文字: (e.textContent || '').trim().replace(/\s+/g, ' '), 角色: e.getAttribute('role'),
          testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
          带快捷键: re2.test([(e.textContent || ''), e.getAttribute('aria-label') || ''].join(' ')),
          rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; })
      .filter((x) => x.文字);
    return { testid: m.getAttribute('data-testid'), role: m.getAttribute('role'), aria: m.getAttribute('aria-label'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      行数: 行.length, 行 };
  });
}, 形.source);

/** 在画布上右键一个坐标。 */
const 右键 = async (x, y) => { await p.mouse.move(x, y); await p.waitForTimeout(300);
  await p.mouse.click(x, y, { button: 'right' }); await p.waitForTimeout(1200); };

// ═══════════ S3-a 空白处右键菜单
rec.空白右键 = { 前节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length) };
await 右键(430, 640);
rec.空白右键.浮层 = await 读浮层();
await p.keyboard.press('Escape'); await p.waitForTimeout(600);

// ═══════════ S3-b 节点右键菜单（点标题选中，批次 171 教训：别点几何中心）
const 目标 = await p.evaluate(() => {
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) continue;
    const r = t.getBoundingClientRect();
    if (r.width > 20 && r.x > 200 && r.x < 1000 && r.y > 100 && r.y < 600)
      return { id: n.getAttribute('data-id'), 标题: (t.innerText || '').trim().split('\n')[0], 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  } return null; });
rec.节点右键 = { 目标 };
if (目标) {
  await p.mouse.click(目标.点[0], 目标.点[1]); await p.waitForTimeout(900);
  rec.节点右键.选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  await 右键(目标.点[0], 目标.点[1]);
  rec.节点右键.浮层 = await 读浮层();
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
}

// ═══════════ S3-c 选中后的节点工具条（可能也印快捷键）
rec.工具条 = {};
if (目标) {
  await p.mouse.click(目标.点[0], 目标.点[1]); await p.waitForTimeout(1000);
  rec.工具条.浮层 = await 读浮层();
  // 工具条通常不是 role=dialog，直接扫一遍带快捷键字形的可见元素
  rec.工具条.带快捷键的可见元素 = await p.evaluate((re) => {
    const r2 = new RegExp(re), 出 = [];
    for (const e of document.querySelectorAll('[aria-label],[title],button,[role=button]')) {
      if (e.closest('[role=dialog],[role=menu],[role=listbox],[data-testid$=-popover]')) continue;
      const s = [e.getAttribute('aria-label') || '', e.getAttribute('title') || '', (e.textContent || '').trim()].join(' ');
      if (!r2.test(s)) continue;
      const q = e.getBoundingClientRect(); if (q.width < 2 || q.height < 2) continue;
      出.push({ 值: s.trim().slice(0, 60), testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
        所属节点: e.closest('.react-flow__node')?.getAttribute('data-id') || null });
    }
    return 出;
  }, 形.source);
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  await p.mouse.click(640, 690); await p.waitForTimeout(700);   // 点空白取消选中
}

// ═══════════ S1 帮助中心面板（手册那份 28 项的源头）
rec.帮助面板 = {};
const 帮助钮 = await p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('button,[role=button],[aria-label]'))
    .find((x) => ['帮助中心', '使用手册', '快捷键'].includes((x.getAttribute('aria-label') || '').trim()));
  if (!e) return null; const r = e.getBoundingClientRect();
  return { aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'), pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
});
rec.帮助面板.按钮 = 帮助钮;
if (帮助钮) {
  await p.mouse.click(帮助钮.pt[0], 帮助钮.pt[1]); await p.waitForTimeout(2000);
  rec.帮助面板.浮层 = await 读浮层();
  rec.帮助面板.滚动区 = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="shortcut-help-scroll-region"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { scrollHeight: e.scrollHeight, clientHeight: e.clientHeight, 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      全文: (e.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean) };
  });
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
}
await 关浮层();

// ═══════════ 汇总：S1 ∪ S3 的并集与差集
const 抽 = (浮) => {
  const 集 = new Map();
  for (const f of 浮 || []) for (const 行 of f.行) {
    if (!行.带快捷键) continue;
    const m = 行.文字.match(/(?:[⌘⌥⇧⌃]\s*)*[A-Z0-9⌫⏎↩]+$/);
    const 键 = (m ? m[0] : 行.文字).trim();
    if (!集.has(键)) 集.set(键, []);
    集.get(键).push(`${f.testid || f.aria}｜${行.文字}`);
  }
  return [...集.entries()].map(([键, 处]) => ({ 键, 处 }));
};
rec.并集 = {
  S3_空白: 抽(rec.空白右键?.浮层),
  S3_节点: 抽(rec.节点右键?.浮层),
  S1_帮助面板: 抽(rec.帮助面板?.浮层),
};
rec.基线 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

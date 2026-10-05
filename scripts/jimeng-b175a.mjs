// 批次 175 a 轮：快捷键的**第二真相源**静态普查。
//
// 手册现状（自我降级，立规 34）：`help-and-shortcuts.md` 已经有一份
// 「28 项快捷键三态总账」＋ 帮助中心面板的逐字列表 ＋ 逐项实测，
// **覆盖是够的**。但注意两件事：
//   ① 手册里 **`aria-keyshortcuts` 与 `<kbd>` 一次都没出现过**（grep 零命中）
//      ⇒ 页面很可能带着一份**机器可读的**快捷键声明，而手册只用了「肉眼读面板」这一路。
//   ② 页面上的**右键菜单项会印快捷键**（如「复制 ⌘C」「删除 ⌫」），
//      这是**第三路**来源。
//
// 本轮只做**静态枚举**，不开任何面板、不按任何键：
//   S2 = 所有带 `aria-keyshortcuts` 的元素
//   S3 = 所有 `aria-label` / `title` / 可见文字里**含快捷键字形**的元素
// 下一轮再把这两路和手册的 S1（帮助中心面板）做三路对账。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '175a' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(500);

rec.页面 = await p.evaluate(() => ({
  url: location.href,
  testid总数: document.querySelectorAll('[data-testid]').length,
  元素总数: document.querySelectorAll('body *').length,
  kbd标签数: document.querySelectorAll('kbd').length,
  ariaKeyshortcuts数: document.querySelectorAll('[aria-keyshortcuts]').length,
  status区域数: document.querySelectorAll('[role=status]').length,
}));

// ── S2：aria-keyshortcuts 全量
rec.S2 = await p.evaluate(() => Array.from(document.querySelectorAll('[aria-keyshortcuts]')).map((e) => {
  const r = e.getBoundingClientRect();
  const t = e.querySelector('[data-testid="flow-node-title"]');
  return {
    声明: e.getAttribute('aria-keyshortcuts'),
    标签: e.tagName.toLowerCase(),
    testid: e.getAttribute('data-testid'),
    role: e.getAttribute('role'),
    aria: e.getAttribute('aria-label'),
    可见: r.width > 1 && r.height > 1,
    所属节点: e.closest('.react-flow__node')?.getAttribute('data-id') || null,
    所属节点标题: t ? (t.innerText || '').trim().split('\n')[0] : null,
    祖先链: (() => { const o = []; for (let n = e; n && n !== document.body; n = n.parentElement)
      o.push(n.tagName.toLowerCase() + (n.dataset?.testid ? `[${n.dataset.testid}]` : '') + (n.getAttribute('role') ? `[role=${n.getAttribute('role')}]` : '')); return o.slice(0, 4); })(),
  };
}));

// ── S3：含快捷键字形的 aria-label / title / 可见文字
// 字形集：⌘ ⌥ ⇧ ⌃ ⌫ ⏎ ↩ Esc ⌘⇧ 等。只做**单遍**遍历（教训来自批次 174 a 轮的 O(n²)）。
rec.S3 = await p.evaluate(() => {
  const 形 = /[⌘⌥⇧⌃⌫⏎↩]|\\bEsc\\b/;
  const 出 = [];
  for (const e of document.querySelectorAll('[aria-label],[title],button,a,[role=button],[role=menuitem],[role=tab]')) {
    const aria = e.getAttribute('aria-label') || '';
    const title = e.getAttribute('title') || '';
    const txt = (e.textContent || '').trim();
    const 命中 = [aria, title, txt].filter((s) => 形.test(s));
    if (!命中.length) continue;
    const r = e.getBoundingClientRect();
    const t = e.querySelector('[data-testid="flow-node-title"]') || e.closest('.react-flow__node')?.querySelector('[data-testid="flow-node-title"]');
    出.push({
      来源: [aria && 形.test(aria) ? 'aria-label' : null, title && 形.test(title) ? 'title' : null, 形.test(txt) ? '文字' : null].filter(Boolean).join('+'),
      值: 命中.join(' ｜ '),
      标签: e.tagName.toLowerCase(),
      testid: e.getAttribute('data-testid'),
      role: e.getAttribute('role'),
      可见: r.width > 1 && r.height > 1,
      所属节点: e.closest('.react-flow__node')?.getAttribute('data-id') || null,
      所属节点标题: t ? (t.innerText || '').trim().split('\n')[0] : null,
    });
  }
  return 出;
});

// ── 归一化出「快捷键集合」，供下一轮与手册对账
rec.归一 = await p.evaluate(() => {
  const 拆 = (s) => (s || '').trim();
  const 集 = new Map();
  const 加 = (k, v) => { if (k) 集.set(k, (集.get(k) || 0) + 1); };
  for (const e of document.querySelectorAll('[aria-keyshortcuts]')) 加(拆(e.getAttribute('aria-keyshortcuts')), 'S2');
  const 形 = /[⌘⌥⇧⌃⌫⏎↩]|\bEsc\b/;
  for (const e of document.querySelectorAll('[aria-label],[title]')) {
    for (const s of [e.getAttribute('aria-label'), e.getAttribute('title')]) {
      if (!s || !形.test(s)) continue;
      // 抽出形如「复制 ⌘C」「删除 ⌫」里的快捷键尾巴
      const m = s.match(/[^\s]*\s*((?:[⌘⌥⇧⌃]\s*)*[A-Z0-9⌫⏎↩][^\s]*)$/);
      if (m) 加(拆(m[1]), 'S3');
    }
  }
  return [...集.entries()].map(([键, 来源]) => ({ 键, 来源 }));
});

rec.基线 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

// 批次 177 a 轮：**浮层内**的禁用态普查 —— 把批次 176 欠下的那一半补上。
//
// 176 a 轮实测：空闲页上 aria-disabled / :disabled / [data-state=disabled] **全为 0**，
// 并写下「所有禁用态都活在浮层/工具条/菜单里」（立规 48）。
// 本轮就是去**逐个打开**这些浮层，把「灰的东西 + 逐字原因」收齐。
//
// ⛔ 只读：打开面板、读 DOM、关掉。不点任何会改画布或扣积分的条目。
// ⚠️ 不点「分享」（会带出权限设置）、不点「保存到主体库」。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '177a' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

/** 读当前页面上所有「灰的」：aria-disabled / :disabled / data-state=disabled。 */
const 读灰 = (场景) => p.evaluate((名) => {
  const 出 = [];
  const seen = new Set();
  for (const e of document.querySelectorAll('[aria-disabled="true"],button:disabled,input:disabled,[disabled],[data-state="disabled"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const 宿主 = e.closest('[role=dialog],[role=menu],[role=listbox],[data-testid$=-popover],[data-testid$=panel],[data-testid=node-toolbar],[data-testid=canvas-bottom-dock]');
    const 键 = `${名}|${e.getAttribute('data-testid')}|${e.getAttribute('aria-label')}`;
    if (seen.has(键)) continue; seen.add(键);
    const t = e.closest('.react-flow__node');
    出.push({
      场景: 名,
      宿主: 宿主 ? (宿主.getAttribute('data-testid') || 宿主.getAttribute('aria-label') || 宿主.tagName.toLowerCase()) : '(页面本体)',
      节点: t ? (t.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0] : null,
      标签: e.tagName.toLowerCase(), testid: e.getAttribute('data-testid'),
      aria: e.getAttribute('aria-label'), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
      描述: e.getAttribute('aria-describedby'),
      原因: (() => { const d = e.getAttribute('aria-describedby');
        if (!d) return null; const n = document.getElementById(d.split(/\s+/)[0]);
        return n ? (n.innerText || '').trim().slice(0, 60) : `(id=${d} 找不到宿主)`; })(),
      第二SPAN: (() => { const s = Array.from(e.querySelectorAll(':scope > span')); return s.length > 1 ? (s[1].innerText || '').trim() : null; })(),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      颜色: cs.color, 光标: cs.cursor,
    });
  }
  return 出;
}, 场景);

const 累 = [];
const 记 = async (场景) => { const r = await 读灰(场景); 累.push(...r); return r; };

// ── 场景 1：左栏 + 底部 dock（选中一个节点前）
rec.场景 = {};
rec.场景['左栏与底部dock'] = (await 记('左栏与底部dock')).length;

// ── 场景 2~5：各类顶栏浮层
const 浮层 = async (开, 名) => {
  await 开(); await p.waitForTimeout(1600);
  const n = (await 记(名)).length;
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  return n;
};
const 点testid = (t) => p.evaluate((s) => { const e = document.querySelector(`[data-testid="${s}"]`); if (!e) return false;
  const r = e.getBoundingClientRect(); if (r.width < 2) return false;
  e.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
  e.dispatchEvent(new MouseEvent('mouseup', { bubbles: true })); e.click(); return true; }, t);
const 点aria = (a) => p.evaluate((s) => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === s);
  if (!e) return false; const r = e.getBoundingClientRect(); if (r.width < 2) return false; e.click(); return true; }, a);

rec.场景['项目面板'] = await 浮层(() => 点testid('canvas-project-trigger'), '项目面板');
rec.场景['节点汇总'] = await 浮层(() => 点testid('canvas-node-summary-trigger'), '节点汇总');
rec.场景['缩放菜单'] = await 浮层(() => 点testid('canvas-zoom-percent'), '缩放菜单');
rec.场景['更多菜单'] = await 浮层(() => 点aria('更多'), '更多菜单');
rec.场景['搜索面板'] = await 浮层(() => 点aria('搜索'), '搜索面板');
rec.场景['生成历史'] = await 浮层(() => 点aria('生成历史'), '生成历史');
rec.场景['用户菜单'] = await 浮层(() => 点testid('canvas-user-menu-trigger'), '用户菜单');
// ⛔ 分享不打开（会带出权限设置）；资产库先跳过（另开一轮）
rec.未开 = ['分享面板（⛔ 会带出权限设置）', '资产库（另批）'];

// ── 场景 8：节点工具条（每种类型各选一次）
rec.节点类型 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
  id: n.getAttribute('data-id'), 类型: (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null,
  标题: (n.querySelector('[data-testid="flow-node-title"]')?.innerText || '').trim().split('\n')[0] })));
const 类型顺序 = [...new Set(rec.节点类型.map((x) => x.类型))];
rec.场景.节点工具条 = {};
for (const t of 类型顺序) {
  const 节点 = rec.节点类型.find((x) => x.类型 === t);
  await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`)
    ?.scrollIntoView({ block: 'center', inline: 'center' }), 节点.id);
  await p.waitForTimeout(800);
  const pt = await p.evaluate((i) => { const q = document.querySelector(`.react-flow__node[data-id="${i}"] [data-testid="flow-node-title"]`);
    const r = q.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 节点.id);
  await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(900);
  const 选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  rec.场景.节点工具条[t] = 选中集.includes(节点.id) ? (await 记(`工具条:${t}`)).length : '❌ 选不中';
  await p.mouse.click(640, 690); await p.waitForTimeout(700);
}
await p.keyboard.press('Escape'); await p.waitForTimeout(600);

rec.全部灰项 = 累;
rec.按场景 = 累.reduce((a, x) => { a[x.场景] = (a[x.场景] || 0) + 1; return a; }, {});
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);

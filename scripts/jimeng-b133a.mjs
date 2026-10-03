// 批次 133 · a 轮：打开 Agent 面板里的两个**打开型**子面板，推进「全灭 testid」里剩下的可验项。
//
// 🔑 靶子（批次 129 的 21 个「全灭 testid」现剩 19 个，本批攻其中能安全验的）：
//   ① `agent-skill-chip` + `canvas-agent-skill-menu` / `canvas-agent-skill-picker`
//      —— 入口是 Agent 面板里的 `canvas-agent-skill-trigger`「使用技能」按钮（**纯打开型**）。
//   ② `canvas-agent-session-menu-trigger`「会话列表」按钮打开的会话列表（**纯打开型**）。
//
// ⚠️ 纪律：本轮**不输入任何字符**（手册说技能也可用 `/` 触发，但那会改变输入区状态）、
//   **不点「发送消息」**、**不点「新建会话」**、**不点任何技能项**
//   —— 只开面板、只读 DOM、只关面板。收尾必须把侧栏归位成**关态**（批次 132 的基线）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b133a.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[role=tooltip]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const collect = () => p.evaluate(() => { const s = new Set(); for (const e of document.querySelectorAll('[data-testid]')) s.add(e.getAttribute('data-testid')); return Array.from(s); });
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const sidecar = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  return e ? { op: getComputedStyle(e).opacity, state: e.getAttribute('data-state'), 子元素: e.children.length } : null; });
const escAll = async () => { for (let i = 0; i < 4; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), credits: await credits(), 浮层: await overlays(), 侧栏: await sidecar() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await escAll();
out.起始id = await idsNow();
const 基线 = await collect();
log('静态基线 testid', 基线.length, '种｜节点', out.起始id.length, '个｜侧栏', JSON.stringify(await sidecar()));
save();

// 点击某个 testid 的按钮（校验落点命中自身后才点）
const 点 = async (tid, label) => {
  const pt = await p.evaluate((t) => { const e = document.querySelector('[data-testid="' + t + '"]'); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect(); if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 命中: h.tagName }; }
    return { __err: 'no-point' }; }, tid);
  if (pt.__err) { log(`  【${label}】⛔ ${pt.__err}`); return pt; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1700);
  return pt;
};

const 快照 = (label) => p.evaluate((lb) => {
  const 新 = Array.from(document.querySelectorAll('[data-testid]')).map((e) => {
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    const 宿主链 = []; for (let n = e; n && n.nodeType === 1 && 宿主链.length < 4; n = n.parentElement) 宿主链.push(n.getAttribute('data-testid') || n.tagName.toLowerCase());
    return { tid: e.getAttribute('data-testid'), tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 有面积: r.width >= 1 && r.height >= 1,
      op: cs.opacity, pe: cs.pointerEvents, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50), 祖先链: 宿主链 }; });
  const 基 = new Set(['canvas-feature-sidecar', 'canvas-agent-panel', 'canvas-agent-session-menu-trigger', 'canvas-agent-session-title',
    'canvas-agent-session-create', 'canvas-agent-session-collapse', 'canvas-agent-session-heading', 'canvas-agent-session-modes',
    'canvas-agent-mode-action', 'canvas-agent-session-composer', 'prompt-composer', 'canvas-agent-composer-placeholder-mention',
    'canvas-agent-composer-action-row', 'canvas-agent-composer-add', 'canvas-agent-skill-trigger', 'canvas-agent-composer-mention',
    'canvas-agent-send', 'canvas-sidecar-resize-handle']);
  return { 状态: lb, 新增testid元素: 新.filter((x) => !基.has(x.tid) && x.有面积),
    浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[role=tooltip]')).filter((m) => m.getBoundingClientRect().width > 1).length };
}, label);

// ---------------------------------------------------------------- ① 打开侧栏
log('\n=== ① ⌘/ 打开 Agent 侧栏 ===');
{
  const g = await keyGuard(p);
  log('  keyGuard safe =', g.safe, '｜', g.where);
  await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1600);
  const t = await collect();
  out.侧栏态 = { testid: t.length, 增量: t.filter((x) => !基线.includes(x)) };
  log('  侧栏', JSON.stringify(await sidecar()), '｜testid', t.length, '种');
  save();
}
out.侧栏基线testid = await collect();

// ---------------------------------------------------------------- ② 「使用技能」
log('\n=== ② 点「使用技能」canvas-agent-skill-trigger ===');
{
  const before = await collect();
  const pt = await 点('canvas-agent-skill-trigger', '使用技能');
  out.技能落点 = pt;
  if (!pt.__err) {
    log('  落点', JSON.stringify(pt));
    const s = await 快照('点「使用技能」后');
    out.技能面板 = s;
    log('  浮层数', s.浮层, '｜相对侧栏态**新增的有面积 testid 元素**：', s.新增testid元素.length, '个');
    s.新增testid元素.forEach((e) => log('      ·', e.tid, `<${e.tag}>${e.role ? ' role=' + e.role : ''} ${e.矩形.join(',')} «${e.逐字}»  ⊂ ${e.祖先链.slice(0, 3).join(' < ')}`));
    const t = await collect();
    out.技能面板testid = { 种类: t.length, 增量: t.filter((x) => !before.includes(x)), 减量: before.filter((x) => !t.includes(x)) };
    log('  🔑 testid 增量', JSON.stringify(out.技能面板testid.增量), '｜减量', JSON.stringify(out.技能面板testid.减量));
    const 关注 = ['agent-skill-chip', 'canvas-agent-skill-menu', 'canvas-agent-skill-picker', 'ai-agent-chip-opens-guide', 'agent-skill-menu', 'ai-agent-drawer'];
    log('  本批关注项：', 关注.map((k) => `${k}=${t.includes(k) ? '✅在' : '·不在'}`).join(' '));
    save();
  }
  await escAll();
  const t2 = await collect();
  log('  关闭后 testid', t2.length, '种｜相对侧栏态 增量', JSON.stringify(t2.filter((x) => !out.侧栏基线testid.includes(x))), '减量', JSON.stringify(out.侧栏基线testid.filter((x) => !t2.includes(x))));
  save();
}

// ---------------------------------------------------------------- ③ 「会话列表」
log('\n=== ③ 点「会话列表」canvas-agent-session-menu-trigger ===');
{
  const before = await collect();
  const pt = await 点('canvas-agent-session-menu-trigger', '会话列表');
  out.会话列表落点 = pt;
  if (!pt.__err) {
    log('  落点', JSON.stringify(pt));
    const s = await 快照('点「会话列表」后');
    out.会话列表面板 = s;
    log('  浮层数', s.浮层, '｜新增的有面积 testid 元素：', s.新增testid元素.length, '个');
    s.新增testid元素.forEach((e) => log('      ·', e.tid, `<${e.tag}>${e.role ? ' role=' + e.role : ''} ${e.矩形.join(',')} «${e.逐字}»  ⊂ ${e.祖先链.slice(0, 3).join(' < ')}`));
    const t = await collect();
    out.会话列表testid = { 种类: t.length, 增量: t.filter((x) => !before.includes(x)), 减量: before.filter((x) => !t.includes(x)) };
    log('  testid 增量', JSON.stringify(out.会话列表testid.增量), '｜减量', JSON.stringify(out.会话列表testid.减量));
    save();
  }
  await escAll();
  const t2 = await collect();
  log('  关闭后 testid', t2.length, '种｜相对侧栏态 增量', JSON.stringify(t2.filter((x) => !out.侧栏基线testid.includes(x))), '减量', JSON.stringify(out.侧栏基线testid.filter((x) => !t2.includes(x))));
  save();
}

// ---------------------------------------------------------------- 收尾：关侧栏
log('\n=== ④ 收尾归位：关掉侧栏（批次 132 的基线是关态）===');
{
  await escAll();
  let s = await sidecar();
  let n = 0;
  while (s && s.op === '1' && n < 3) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1500); s = await sidecar(); n++;
    log('  补按一次 →', JSON.stringify(s)); }
  out.侧栏归位 = s;
  log('  侧栏', JSON.stringify(s), s && s.op === '0' && s.子元素 === 0 ? '✅ 已归位关态' : '⚠️');
  await p.mouse.move(1276, 716); await p.waitForTimeout(700);
  const t = await collect();
  out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), credits: await credits(),
    节点数: (await idsNow()).length, 起始节点数: out.起始id.length, testid种类: t.length };
  out.新增id = (await idsNow()).filter((x) => !out.起始id.includes(x));
  out.相对基线增量 = t.filter((x) => !基线.includes(x));
  out.相对基线减量 = 基线.filter((x) => !t.includes(x));
  log('收尾：', JSON.stringify(out.收尾));
  log('  新增 id（必须空）：', JSON.stringify(out.新增id));
  log('  testid 相对静态基线：增量', JSON.stringify(out.相对基线增量), '减量', JSON.stringify(out.相对基线减量));
  save();
}
log('\nDONE a');
process.exit(0);

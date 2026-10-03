// 批次 132 · a 轮：用 **⌘/** 打开 Agent 侧栏，收口批次 129/130 的伏笔。
//
// 🔑 伏笔链：
//   批次 129 发现 `canvas-feature-sidecar` `<ASIDE aria="Agent">` `200×348@1068,360`
//     **有非零矩形但 `子元素 0`、`opacity:0`、`pointer-events:none`、`scale(0.5)`**，
//     所有 `canvas-agent-*` testid 缺席的原因就在这儿；
//   批次 130 回溯「有面积」判据时又量到它一次；
//   手册 `help-and-shortcuts.md:168` 记「**⌘ /（打开/关闭 Agent）** 2026-10-01 逐项实测可用」。
//   ⇒ **三批的伏笔该收了**：侧栏打开后到底长什么样。
//
// 📌 纪律：本轮**只开合侧栏、只读 DOM**，**不输入、不发送、不点技能**（Agent 面板里常有「生成」类动作）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b132a.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const collect = () => p.evaluate(() => { const s = new Set(); for (const e of document.querySelectorAll('[data-testid]')) s.add(e.getAttribute('data-testid')); return Array.from(s); });
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), credits: await credits(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); } }
out.起始id = await idsNow();
const 基线 = await collect();
log('静态基线 testid', 基线.length, '种｜节点', out.起始id.length, '个');
save();

const 快照 = (label) => p.evaluate((lb) => {
  const s = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  const rd = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { testid: e.getAttribute('data-testid'), tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      有面积: r.width >= 1 && r.height >= 1, opacity: cs.opacity, pe: cs.pointerEvents,
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60), 子元素数: e.children.length }; };
  if (!s) return { 状态: lb, 侧栏: null };
  const r = s.getBoundingClientRect(); const cs = getComputedStyle(s);
  const 子 = Array.from(s.querySelectorAll('*')).map(rd).filter((x) => x);
  const 按钮 = Array.from(s.querySelectorAll('button,[role=button],[role=tab],[role=menuitem],input,textarea,[contenteditable]')).map((e) => {
    const q = e.getBoundingClientRect();
    return { tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
      type: e.getAttribute('type'), placeholder: e.getAttribute('placeholder'), contenteditable: e.getAttribute('contenteditable'),
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      矩形: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], 有面积: q.width >= 1 }; });
  return { 状态: lb, 侧栏: { 矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      opacity: cs.opacity, pe: cs.pointerEvents, dataState: s.getAttribute('data-state'), sidecarId: s.getAttribute('data-sidecar-id'),
      逐字: (s.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200), 子元素数: s.children.length },
    有testid的子元素: 子.filter((x) => x.testid), 子元素总数: 子.length, 可交互元素: 按钮 };
}, label);

// ---------------------------------------------------------------- ① ⌘/ 打开
log('\n=== ① 按 ⌘/ 打开 Agent 侧栏 ===');
out.前 = await 快照('按 ⌘/ 前');
log('  前：侧栏', JSON.stringify(out.前.侧栏 ? { 矩形: out.前.侧栏.矩形, opacity: out.前.侧栏.opacity, dataState: out.前.侧栏.dataState, 子元素数: out.前.侧栏.子元素数 } : null));
{
  const g = await keyGuard(p);
  log('  keyGuard：', JSON.stringify(g));
  await p.keyboard.press('Meta+Slash');
  await p.waitForTimeout(1600);
  out.后 = await 快照('按 ⌘/ 后');
  const s = out.后.侧栏;
  log('  后：侧栏', JSON.stringify(s ? { 矩形: s.矩形, opacity: s.opacity, pe: s.pe, dataState: s.dataState, 子元素数: s.子元素数, 逐字: s.逐字 } : null));
  log('  有 testid 的子元素', out.后.有testid的子元素.length, '个｜子元素总数', out.后.子元素总数, '｜可交互元素', out.后.可交互元素.length, '个');
  out.后.有testid的子元素.forEach((e) => log('      ·', e.testid, `<${e.tag}>${e.role ? ' role=' + e.role : ''} ${e.矩形.join(',')} 有面积=${e.有面积} «${e.逐字}»`));
  out.后.可交互元素.forEach((e) => log('      · 交互 <' + e.tag + '>' + (e.role ? ' role=' + e.role : '') + ' aria=' + e.aria + ' testid=' + e.testid + (e.placeholder ? ' placeholder=' + e.placeholder : '') + (e.contenteditable ? ' contenteditable=' + e.contenteditable : '') + ' ' + e.矩形.join(',') + ' «' + e.逐字 + '»'));
  const t = await collect();
  out.打开后testid = { 种类: t.length, 增量: t.filter((x) => !基线.includes(x)), 减量: 基线.filter((x) => !t.includes(x)) };
  log('  testid', t.length, '种｜**增量**', JSON.stringify(out.打开后testid.增量), '**减量**', JSON.stringify(out.打开后testid.减量));
  log('  状态行', JSON.stringify(await status()), '｜选中', await sel(), '｜浮层', await overlays(), '｜积分', await credits());
  save();
}

// ---------------------------------------------------------------- ② 再按一次关闭（验幂等/可逆）
log('\n=== ② 再按一次 ⌘/（验可逆）===');
{
  await p.keyboard.press('Meta+Slash');
  await p.waitForTimeout(1500);
  out.再按 = await 快照('再按一次后');
  const t = await collect();
  log('  侧栏', JSON.stringify(out.再按.侧栏 ? { opacity: out.再按.侧栏.opacity, dataState: out.再按.侧栏.dataState, 子元素数: out.再按.侧栏.子元素数 } : null));
  log('  testid', t.length, '种｜相对基线 增量', JSON.stringify(t.filter((x) => !基线.includes(x))), '减量', JSON.stringify(基线.filter((x) => !t.includes(x))));
  save();
}

// ---------------------------------------------------------------- ③ 第三次（确认完全回到基线）
log('\n=== ③ 第三次 ⌘/ ===');
{
  await p.keyboard.press('Meta+Slash');
  await p.waitForTimeout(1500);
  out.第三按 = await 快照('第三按');
  const t = await collect();
  log('  侧栏', JSON.stringify(out.第三按.侧栏 ? { opacity: out.第三按.侧栏.opacity, dataState: out.第三按.侧栏.dataState, 子元素数: out.第三按.侧栏.子元素数 } : null));
  log('  testid', t.length, '种｜相对基线 增量', JSON.stringify(t.filter((x) => !基线.includes(x))), '减量', JSON.stringify(基线.filter((x) => !t.includes(x))));
  out.最终态 = { testid种类: t.length, 与基线一致: t.length === 基线.length && t.every((x) => 基线.includes(x)) };
  log('  与基线一致：', out.最终态.与基线一致);
  save();
}

await p.mouse.move(1276, 716); await p.waitForTimeout(600);
const endIds = await idsNow();
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), credits: await credits(), 节点数: endIds.length, 起始节点数: out.起始id.length };
out.新增id = endIds.filter((x) => !out.起始id.includes(x));
log('\n收尾：', JSON.stringify(out.收尾));
log('  新增 id（必须空）：', JSON.stringify(out.新增id));
save();
log('\nDONE a');
process.exit(0);

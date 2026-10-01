// 批次 60：关掉 F 键对照表里最后那个「阻塞理由本身就是错的」未测行
//
// `20-reference.md` 的「F 键按节点类型的对照」表有两行 ⛔ 未测：
//   | 导演台 | ⛔ 未测 | 其唯一按钮「进入导演台」属跨页面动作，未获授权，不冒险 |
//   | 音频   | ⛔ 未测 | 画布上无音频节点，建节点需素材 |
//
// 🔴 两行的**理由本身都要审**：
//   · 音频：「画布上无音频节点」——**批次 57 与 59 都已经建成过空音频节点**
//     （批次 59 还完整量了它的 7×7 连线矩阵），**阻塞早已不存在**。直接可关。
//   · 导演台：「唯一按钮『进入导演台』属跨页面动作」——🔴 **张冠李戴**：
//     那说的是**点那个按钮**，而本行要测的是**按 F 键**。按 F 会不会导航，
//     恰恰是**未知**的；真按下去若触发了跨页面跳转，做的就是那件没授权的事。
//     ⇒ 本批**不按**，但把「理由写错了」这件事本身订正掉，
//       并写清「为什么仍然不按」——理由必须落在**真正的**风险上。
//
// 音频这一轮的设计：
//   批次 40 测过 文本/时间线/视频/图片/主体，得出的规律是
//   「有全屏编辑器概念的（文本、时间线）能开；**媒体类（视频、图片）明确报不可用**」。
//   音频是第 7 种类型，正好是这条规律的**第 7 个样本**。
//   → 若 F 在音频上弹出**逐字相同**的「此快捷键当前不可用」，
//     就是规律的**阳性对照**：分类规则从 6 类扩到 7 类，样本 +1；
//   → 若结果不同，规律就只覆盖了 6 类中的 6 个，必须改写。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { keyGuard, canvasBaseline, diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b60-f-audio.json', import.meta.url);
const MINE = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const href = () => p.url();
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty();
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  for (let i = 0; i < 3 && (await selIds()).length; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  return (await selIds()).length === 0; };
const selectByScan = async (id) => {
  const pts = await p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return [];
    const r = n.getBoundingClientRect(); const out = [];
    for (let fy = 0.10; fy <= 0.92; fy += 0.06) for (let fx = 0.10; fx <= 0.92; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"],[contenteditable="true"]')) continue;
      out.push({ x, y }); } return out; }, id);
  for (const pt of pts) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(550);
    const s = await selIds(); if (s.length === 1 && s[0] === id) return true; }
  return false;
};
const makeNode = async (kind) => {
  await deselect();
  const rb = await p.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith(nm)); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, kind);
  if (!rb) return { err: `左栏找不到「${kind}」` };
  const pre = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(3000);
  const made = (await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')))).filter((x) => !pre.includes(x));
  if (made.length !== 1) return { err: `新建「${kind}」新增 ${made.length} 个` };
  MINE.push(made[0]); return { id: made[0] };
};
const deleteById = async (id) => {
  if (!(await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"]`), id))) return 'absent';
  await deselect(); if (!(await selectByScan(id))) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return;
    const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, id);
  await p.waitForTimeout(800);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1300); await reset(); return ok ? 'deleted' : 'noclick';
};

// 全页可见 DOM 指纹：用来判断 F 到底有没有留下可见痕迹
const fingerprint = () => p.evaluate(() => Array.from(document.querySelectorAll('body *'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
  .map((e) => { const r = e.getBoundingClientRect();
    return `${e.tagName}#${e.id || ''}.${String(e.className || '').split(' ').filter(Boolean).slice(0, 2).join('.')}@${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`; }));
const snapshot = async (label) => {
  const fp = await fingerprint();
  const dialogs = await p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"]')).filter((e) => e.getBoundingClientRect().width > 1)
    .map((e) => { const r = e.getBoundingClientRect(); return { tid: e.getAttribute('data-testid'), cls: String(e.className || '').slice(0, 60), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').slice(0, 40) }; }));
  const toasts = await p.evaluate(() => Array.from(document.querySelectorAll('div,span')).filter((e) => {
    const r = e.getBoundingClientRect(); const t = (e.innerText || '').trim();
    return r.width > 1 && r.height > 1 && r.y < 120 && /快捷键|不可用|打开|编辑器/.test(t) && t.length < 40;
  }).map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, text: (e.innerText || '').trim(), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      role: e.getAttribute('role'), aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid') }; }));
  const sr = await p.evaluate(() => Array.from(document.querySelectorAll('[class*="sr-only"]')).filter((e) => e.getBoundingClientRect().width > 0 || (e.textContent || '').trim())
    .map((e) => { const r = e.getBoundingClientRect(); return { text: (e.textContent || '').trim().slice(0, 60), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; })
    .filter((x) => x.text));
  return { label, n: fp.length, fp, dialogs, toasts, sr, url: await href() };
};

const result = { startedAt: new Date().toISOString(), zoom: await zoomOf(), cases: [] };
console.log('=== 批次 60：关掉 F 键对照表的「音频」未测行 ===\n');
const base0 = await canvasBaseline(p);
console.log('起点:', base0.status, '| 缩放', base0.zoom, '| 节点', base0.nodes.length);
if (base0.nodes.length !== 6) { console.error('ABORT: 起点节点数异常'); process.exit(2); }

// ── 音频 ──
const r = await makeNode('音频');
if (r.err) { console.error('ABORT:', r.err); await b.close(); process.exit(3); }
console.log('音频节点', r.id, '| 选中:', await selectByScan(r.id));
const nodeInfo = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`);
  return e ? { aria: e.getAttribute('aria-label'), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) } : null; }, r.id);
console.log('节点 aria:', JSON.stringify(nodeInfo));

const g = await keyGuard(p);
console.log(`\n焦点守卫: ${g.safe ? '✅' : '⛔'} ${g.where} —— ${g.reason}`);
if (!g.safe) { console.error('ABORT: 焦点不安全，不按 F'); await b.close(); process.exit(4); }

const before = await snapshot('按 F 前');
console.log(`按 F 前：可见元素 ${before.n} | dialogs ${before.dialogs.length} | url 片段 ${before.url.slice(-24)}`);
await p.keyboard.press('f');
await p.waitForTimeout(1500);
const after = await snapshot('按 F 后');
console.log(`按 F 后：可见元素 ${after.n} | dialogs ${after.dialogs.length} | url 片段 ${after.url.slice(-24)}`);

const beforeSet = new Set(before.fp);
const added = after.fp.filter((x) => !beforeSet.has(x));
const afterSet = new Set(after.fp);
const removed = before.fp.filter((x) => !afterSet.has(x));
console.log(`\n可见 DOM 差分：+${added.length} / −${removed.length}`);
for (const x of added.slice(0, 12)) console.log(`   + ${x}`);
for (const x of removed.slice(0, 12)) console.log(`   − ${x}`);
console.log(`\n按 F 后可见 dialog：${after.dialogs.length ? JSON.stringify(after.dialogs) : '（无）'}`);
console.log(`按 F 后疑似 toast：${after.toasts.length ? JSON.stringify(after.toasts, null, 1) : '（无）'}`);
console.log(`按 F 后 sr-only 文本：${after.sr.length ? JSON.stringify(after.sr.slice(0, 6)) : '（无）'}`);
const navigated = before.url !== after.url;
console.log(`\n🔴 是否发生页面跳转：${navigated ? '⛔ 是！' : '✅ 否'}  (${before.url === after.url ? 'url 未变' : before.url + ' → ' + after.url})`);

result.cases.push({ node: r.id, nodeInfo, guard: g, before: { ...before, fp: undefined }, after: { ...after, fp: undefined },
  added, removed, navigated, beforeUrl: before.url, afterUrl: after.url });

// 与批次 40 记录的签名逐字比对
const SIGN = '此快捷键当前不可用';
const hit = after.toasts.some((t) => (t.text || '').includes(SIGN)) || after.sr.some((s) => (s.text || '').includes(SIGN));
console.log(`\n与批次 40 记录的签名「${SIGN}」逐字比对：${hit ? '✅ 命中 —— 音频与视频/图片同型' : '⛔ 没命中 —— 规律不覆盖音频，须改写'}`);

await reset();
console.log('\n删除音频节点:', await deleteById(r.id));

// ── 收尾 ──
await reset();
for (let t = 0; t < 3; t++) { const z = await zoomOf();
  if (z && z.includes('60%')) { console.log('缩放归位 ok:', z); break; }
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const s = 'input[data-testid="canvas-zoom-percent-input"]';
  if (await p.$(s)) { await p.fill(s, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
  else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  if (t === 2) console.log('缩放归位 FAILED:', await zoomOf()); }
await reset();
const after2 = await canvasBaseline(p);
const drifted = await diffNodePositions(p, Object.fromEntries(Object.entries(BASELINE.nodes).map(([k, v]) => [k, v.canvas])), 1.5);
console.log('终态:', after2.status, '| 缩放', await zoomOf(), '| 节点', after2.nodes.length, '| 偏离', JSON.stringify(drifted), '| 积分', after2.credit);
result.end = { status: after2.status, zoom: await zoomOf(), nodes: after2.nodes.length, drifted, credit: after2.credit };
writeFileSync(OUT, JSON.stringify(result, null, 1));
console.log('写入', OUT.pathname);
await b.close();

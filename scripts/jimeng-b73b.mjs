// 批次 73：带**内容**的图片节点，before ⊕ 与 after ⊕ 各读一遍。
//
// 靶子：批次 71 在 connect-nodes.md 明确留的第二个洞 ——
//   「带内容节点 + before ⊕ 本批未取证，别把上表当成两个方向都成立」。
// 空源那一侧本批已测完（before：仅文本/图片可连，图片/视频报「没有可用的就绪资源」）。
// 关键问题：**喂了素材之后，before ⊕ 的图片/视频会不会从「无就绪资源」变成可连？**
//   若会 ⇒ 「没有可用的就绪资源」确实是**临时**状态，且**跨方向**成立。
//
// 三条已踩过的坑，直接写进设计：
//   ① filechooser 必须用**全局** `p.on('filechooser')`（connectOverCDP 下
//      `p.waitForEvent('filechooser')` 会超时 —— 批次 64）；
//   ② 素材是**已授权**的那张 PNG（批次 22 授权通道），不改素材、不点生成；
//   ③ 关菜单只按**一次** Escape（第二下会解掉选中 —— 批次 71 第四轮作废过一次），
//      并且**每次读数前硬断言 selected===1**，前置不成立的读数记 VOID 不记 0。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const OUT = new URL('./_tmp-b73b.json', import.meta.url);
const ASSET = '/tmp/b22-upload.png';   // 批次 22 授权的 PNG（1005431 字节）

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
// 批次 64：filechooser 必须全局挂
let chooserSeen = false;
p.on('filechooser', async (fc) => { chooserSeen = true; await fc.setFiles(ASSET); });

const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selCount = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } };

const scanPlus = (id) => p.evaluate((vid) => Array.from(document.querySelectorAll('[aria-label^="Create connected node"]')).map((e) => {
  const q = e.getBoundingClientRect(); if (q.width <= 1) return null;
  return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
    cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2),
    inTarget: !!e.closest(`.react-flow__node[data-id="${vid}"]`) }; }).filter(Boolean), id);

async function selectNode(id) {
  for (const [fx, fy] of [[0.5, 0.2], [0.5, 0.12], [0.15, 0.2], [0.85, 0.2], [0.3, 0.3], [0.5, 0.5], [0.7, 0.18], [0.25, 0.45]]) {
    const pt = await p.evaluate(([vid, ax, ay]) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
      const r = n.getBoundingClientRect(); const x = Math.round(r.x + r.width * ax), y = Math.round(r.y + r.height * ay);
      if (x < 4 || y < 4 || x > innerWidth - 4 || y > innerHeight - 4) return null;
      return { x, y, inNode: !!(document.elementFromPoint(x, y) || {}).closest?.(`.react-flow__node[data-id="${vid}"]`) }; }, [id, fx, fy]);
    if (!pt || !pt.inNode) continue;
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900);
    if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) return true;
  } return false;
}
const readMenu = () => p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
  const el = ms[ms.length - 1]; if (!el) return { none: true }; const r = el.getBoundingClientRect();
  return { aria: el.getAttribute('aria-label'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => ({ name: (x.innerText || '').trim().split('\n')[0],
      reason: (x.textContent || '').replace((x.innerText || '').split('\n')[0], '').replace(/\s+/g, ' ').trim() || null,
      dis: x.getAttribute('aria-disabled'), cursor: getComputedStyle(x).cursor, color: getComputedStyle(x).color })) }; });
/** 节点里「有没有内容」的机器可读判据：卡片内是否还有生成面板 / 空态文案 */
const nodeContentProbe = (id) => p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
  const txt = (n.innerText || '').trim();
  return { hasPanel: !!n.querySelector('[data-testid*="panel"],[data-testid*="generation"],[data-testid*="gen"],form'),
    emptyHints: ['暂无', '创建', '生成', '上传', '添加描述'].filter((k) => txt.includes(k)),
    imgs: n.querySelectorAll('img').length, text: txt.replace(/\s+/g, ' ').slice(0, 120) }; }, id);
async function ctxDelete(id) {
  const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, id);
  if (!box) return true;
  await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(900);
  await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1500);
  return !(await ids()).includes(id);
}

const out = { startedAt: new Date().toISOString(), created: [] };
const log = (...a) => console.log(a.join(' '));
let mine = null;
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^图片$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2500);
  const created = (await ids()).filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建数异常 ' + JSON.stringify(created));
  mine = created[0]; out.created.push(mine);
  log('新建图片节点', mine, '| 空态探针:', JSON.stringify(await nodeContentProbe(mine)));

  // —— 找「本地上传」入口；用 aria/text 两条路找，**不用猜坐标**
  const upBtn = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), text: (e.innerText || '').trim().slice(0, 16),
        box: `${Math.round(r.width)}x${Math.round(r.height)}`, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
    .filter((x) => /上传|Upload|upload/.test((x.aria || '') + (x.text || ''))));
  log('上传入口候选:', JSON.stringify(upBtn, null, 1));
  const up = upBtn.find((x) => /本地上传|上传图片|Upload image/i.test((x.aria || '') + (x.text || ''))) || upBtn[0];
  if (!up) throw new Error('找不到上传入口');
  chooserSeen = false;
  await p.mouse.click(up.cx, up.cy);
  await p.waitForTimeout(2500);
  log('filechooser 触发 =', chooserSeen, chooserSeen ? '✅' : '🔴（批次 64 的坑）');
  if (!chooserSeen) throw new Error('filechooser 未触发，不继续（避免把空读数当证据）');
  // —— 等素材就绪：批次 64 记录过缩略图要 **两阶段换源**，这里最多等 12s
  let ready = null;
  for (let t = 0; t < 12; t++) {
    await p.waitForTimeout(1000);
    ready = await nodeContentProbe(mine);
    if (ready.imgs > 0 && !ready.emptyHints.includes('暂无')) { log(`素材就绪 t=+${t + 1}s`, JSON.stringify(ready)); break; }
  }
  out.contentProbe = ready;
  log('内容探针终值:', JSON.stringify(ready));

  // —— 读两套菜单；每次读数前硬断言 selected===1
  await esc(1);
  if ((await selCount()) !== 1) { await selectNode(mine); }
  if ((await selCount()) !== 1) throw new Error('前置不成立：带内容图片节点没选中 ⇒ 本轮读数一律作废');
  // 🔴 DOM 级判据：before ⊕ 的 testid 元素**到底在不在 DOM 里**（不限于可见/可点）——
  // 只看「可见的 ⊕」会把「元素不存在」与「元素存在但 0 尺寸」混为一谈。
  const domProbe = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const cnt = (sel) => document.querySelectorAll(sel).length;
    const inNode = (sel) => n.querySelectorAll(sel).length;
    const detail = ['flow-node-target-connection-menu-button', 'flow-node-source-connection-menu-button']
      .map((s2) => { const e = n.querySelector(`[data-testid="${s2}"]`); const r = e && e.getBoundingClientRect();
        return { testid: s2, exists: !!e, box: r ? `${Math.round(r.width)}x${Math.round(r.height)}` : null,
          aria: e ? e.getAttribute('aria-label') : null, pe: e ? getComputedStyle(e).pointerEvents : null }; });
    return { 全文档_target: cnt('[data-testid="flow-node-target-connection-menu-button"]'),
      全文档_source: cnt('[data-testid="flow-node-source-connection-menu-button"]'),
      本节点内: { target: inNode('[data-testid="flow-node-target-connection-menu-button"]'), source: inNode('[data-testid="flow-node-source-connection-menu-button"]') },
      逐个: detail };
  }, mine);
  out.domProbe = domProbe;
  log('\nDOM 级探针:', JSON.stringify(domProbe, null, 1));
  const plus = await scanPlus(mine);
  log('⊕ 可见', plus.length, JSON.stringify(plus.map((x) => x.testid)));
  out.plus = plus.map((x) => ({ testid: x.testid, aria: x.aria }));
  out.reads = [];
  for (const x of plus) {
    if ((await selCount()) !== 1) { log(`⛔ 读 ${x.testid} 前 selected=${await selCount()} → 作废`); out.reads.push({ testid: x.testid, VOID: true }); continue; }
    await p.mouse.click(x.cx, x.cy); await p.waitForTimeout(1800);
    const m = await readMenu();
    const avail = (m.items || []).filter((i) => i.dis !== 'true' && i.cursor !== 'not-allowed').map((i) => i.name);
    const dis = (m.items || []).filter((i) => i.dis === 'true').map((i) => `${i.name}:${i.reason}`);
    log(`\n  ⊕ ${x.testid.replace(/flow-node-|-connection-menu-button/g, '')} → 标题「${m.aria}」 ${m.box}`);
    log(`     可用: ${avail.join(' / ') || '（无）'}`);
    log(`     禁用: ${dis.join(' | ')}`);
    out.reads.push({ testid: x.testid, aria: x.aria, menuAria: m.aria, avail, dis });
    await esc(1);
    if ((await selCount()) !== 1) await selectNode(mine);
  }
  await esc(2);
  log('\n积分（全程）:', await credit());
} catch (e) { console.error('ABORT:', e.message); out.abort = e.message; }
finally {
  await esc(3);
  if (mine && (await ids()).includes(mine)) log('清理', mine, (await ctxDelete(mine)) ? '✅ deleted' : '🔴 仍在');
  await esc(3);
  for (let t = 0; t < 3; t++) { const z = await zoomOf(); if (z && z.includes('60%')) break;
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const sl = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(sl)) { await p.fill(sl, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); } else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  const extra = Object.keys(cp).filter((x) => !BASE.nodes[x]);
  out.end = { status: await status(), zoom: await zoomOf(), credit: await credit(), nodes: Object.keys(cp).length, dev, extra };
  log('终态', JSON.stringify(out.end));
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  // 把本批创建过的 id 记进 ledger（门 8 靠它判「我没删干净」）
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); led.ids = [...new Set([...(led.ids || []), ...out.created])].sort();
    led.per_batch = { ...(led.per_batch || {}), 73: out.created }; led.updated_at = new Date().toISOString().slice(0, 10);
    writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('ledger 追加', JSON.stringify(out.created)); } catch (e) { log('ledger 更新失败', e.message); }
  await b.close();
}

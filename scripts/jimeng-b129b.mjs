// 批次 129 · b 轮：**当前构建的 testid 全景 + 与手册的差集**（重做 a 轮的错误方向）。
//
// 🔴 a 轮自身失误（本轮要正面记下来）：a 轮用「从手册反引号里捞形似 testid 的 token」当分母，
//   捞出 551 个 —— 其中混着 **SVG 表现属性**（`accent-height`/`dominant-baseline`/`flood-color`…）、
//   **npm 包名**（`unist-util-*`/`hast-util-*`/`vfile-*`…）、**我自己历年的探针夹具名**
//   （`b22-upload`/`gate-a`/`cy-18`…）、**手册自己的文件名**（`navigate-canvas`/`connect-nodes`…）。
//   于是「485 未命中 → 434 疑似过时」是**垃圾进垃圾出**：分母本来就不是 testid 集合。
//   ⇒ 立规：**「全册普查」必须先证明分母是干净的那一类**；靠正则猜 token 语义不可靠。
//
// 📌 本轮改成**页面侧事实集 → 再与手册求差**，方向反过来，分母由页面保证：
//   ① **阳性对照**（两条分支都验）：注入 3 个已知 testid + 1 个「只有 class」+ 1 个「只有属性名」，
//      证明分类器的**两个分支**都抓得到（批次 128 只验过「抓得到」这一支）。
//   ② **12 个状态**逐个收集全文档 testid 集合（静态 / 搜索 / 生成历史 / 更多 / 用户菜单 /
//      快捷键抽屉 / 分享 / 项目 / 节点N / 缩放菜单 / 选中一个音频节点 / 右键菜单）。
//   ③ 手册的 **64 个逐字 `data-testid="X"` 字面量**逐状态命中表（这才是「我们真在文档里写过 testid」）。
//   ④ 页面并集里**手册从没提过**的 testid（= 知识缺口）。
//
// ⚠️ 共享画布纪律：**绝不点左栏「主体 / 时间线 / 导演台」**（它们会建节点）——本轮只用顶栏与右键。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const DOC_DIR = new URL('../docs/user-manual/jimeng-canvas/', import.meta.url).pathname;

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b129b.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), credits: await credits(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1000); } }

// ---------------------------------------------------------------- ① 阳性对照
log('\n=== ① 阳性对照：先证明分类器两个分支都抓得到 ===');
await p.evaluate(() => {
  const mk = (attrs, parent) => { const e = document.createElement('div');
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    (parent || document.body).appendChild(e); return e; };
  window.__b129 = [
    mk({ 'data-testid': 'b129-probe-alpha' }),
    mk({ 'data-testid': 'b129-probe-bravo' }),
    mk({ 'data-testid': 'b129-probe-charlie' }),
    mk({ class: 'b129-probe-delta' }),
    mk({ 'aria-b129probe': 'echo' }),
  ];
});
const probe = await p.evaluate(() => {
  const attrNames = new Set(), classNames = new Set();
  for (const e of Array.from(document.querySelectorAll('*'))) {
    for (const a of Array.from(e.attributes)) attrNames.add(a.name);
    if (e.classList) for (const c of e.classList) classNames.add(c);
  }
  const testids = new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')));
  return {
    三个testid都抓到: ['b129-probe-alpha', 'b129-probe-bravo', 'b129-probe-charlie'].every((t) => testids.has(t)),
    class被归到class: classNames.has('b129-probe-delta'),
    属性被归到属性: attrNames.has('aria-b129probe'),
    误判成testid: testids.has('b129-probe-delta') || testids.has('aria-b129probe'),
  };
});
out.阳性对照 = probe;
log('  三个已知 testid 全部抓到：', probe.三个testid都抓到, '｜纯 class 归到 class：', probe.class被归到class,
  '｜纯属性归到属性：', probe.属性被归到属性, '｜**误判成 testid**：', probe.误判成testid);
await p.evaluate(() => { (window.__b129 || []).forEach((e) => e.remove()); window.__b129 = null; });
const probeGone = await p.evaluate(() => document.querySelectorAll('[data-testid^="b129-probe"]').length);
out.阳性对照.移除后残留 = probeGone;
log('  移除后残留：', probeGone, '（应为 0）');
if (!probe.三个testid都抓到 || probe.误判成testid || probeGone !== 0) { log('  ⛔ 阳性对照不通过，后续结论不成立'); save(); process.exit(1); }
save();

// ---------------------------------------------------------------- 状态遍历
const collect = () => p.evaluate(() => {
  const s = new Set();
  for (const e of Array.from(document.querySelectorAll('[data-testid]'))) s.add(e.getAttribute('data-testid'));
  return Array.from(s);
});

async function openBySel(s, label) {
  const pt = await p.evaluate((sel) => {
    const e = document.querySelector(sel);
    if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect(); if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
    }
    return { __err: 'no-point' };
  }, s);
  if (pt.__err) { log(`  【${label}】⛔ ${pt.__err}`); return pt; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1700);
  return pt;
}
const escAll = async () => { for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };

out.状态 = {}; out.顺序 = [];
const record = async (name) => {
  const set = await collect();
  out.状态[name] = { 种类: set.length, testids: set };
  out.顺序.push(name);
  log(`  【${name}】testid ${set.length} 种`);
  save();
};

log('\n=== ② 逐状态收集 testid ===');
await record('静态');

const topSeq = [
  ['搜索', '[data-testid="canvas-panel-launcher"][aria-label="搜索"]'],
  ['生成历史', '[data-testid="canvas-panel-launcher"][aria-label="生成历史"]'],
  ['更多', 'button[aria-label="更多"]'],
  ['用户菜单', '[data-testid="canvas-user-menu-trigger"]'],
  ['分享', '[data-testid="canvas-share-trigger"]'],
  ['项目', '[data-testid="canvas-project-trigger"]'],
  ['节点N', '[data-testid="canvas-node-summary-trigger"]'],
  ['缩放菜单', '[data-testid="canvas-zoom-percent"]'],
];
for (const [name, s] of topSeq) {
  const pt = await openBySel(s, name);
  if (pt.__err) { out.状态[name] = { 打开失败: pt.__err }; out.顺序.push(name); await escAll(); continue; }
  await record(name);
  await escAll();
}

// 快捷键抽屉：用户菜单 → 「快捷键」项（两级打开）
{
  const um = await openBySel('[data-testid="canvas-user-menu-trigger"]', '用户菜单(2)');
  if (!um.__err) {
    const it = await p.evaluate(() => {
      const items = Array.from(document.querySelectorAll('[role=menuitem],button'));
      const e = items.find((x) => /^快捷键/.test((x.innerText || '').replace(/\s+/g, '').trim()));
      if (!e) return { __err: 'not-found' };
      const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
      }
      return { __err: 'no-point' };
    });
    out.快捷键项 = it;
    if (!it.__err) { await p.mouse.click(it.x, it.y); await p.waitForTimeout(1900); await record('快捷键抽屉'); }
    else log('  【快捷键抽屉】⛔', it.__err);
  }
  await escAll();
}

// 选中一个可见的音频节点（点选是安全的；不做任何别的）
let picked = null;
{
  picked = await p.evaluate(() => {
    for (const n of document.querySelectorAll('.react-flow__node-audio')) {
      const r = n.getBoundingClientRect();
      if (r.x + r.width < 90 || r.x > innerWidth - 90 || r.y + r.height < 110 || r.y > innerHeight - 110) continue;
      for (let y = Math.ceil(r.y) + 3; y <= r.y + r.height - 3; y += 4) for (let x = Math.ceil(r.x) + 3; x <= r.x + r.width - 3; x += 4) {
        const h = document.elementFromPoint(x, y); if (h && (h === n || n.contains(h))) return { x, y, id: n.getAttribute('data-id') };
      }
    }
    return { __err: 'no-visible-audio-node' };
  });
  out.选中落点 = picked;
  if (picked.__err) { log('  【选中音频节点】⛔', picked.__err); }
  else {
    await p.mouse.click(picked.x, picked.y); await p.waitForTimeout(1500);
    out.选中后 = { 选中数: await sel(), 状态行: await status() };
    log('  点中音频节点', picked.id, '→ 选中数', out.选中后.选中数);
    if (out.选中后.选中数 === 1) await record('选中一个音频节点');
    // 右键菜单（只开，不点任何菜单项）
    await p.mouse.click(picked.x, picked.y, { button: 'right' }); await p.waitForTimeout(1500);
    out.右键后浮层 = await overlays();
    if (await overlays()) { await record('节点右键菜单'); } else log('  【节点右键菜单】⛔ 没有浮层');
    await escAll();
    // 点空白取消选中（必须命中 .react-flow__pane）
    const panePt = await p.evaluate(() => {
      for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) {
        const h = document.elementFromPoint(x, y);
        if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y };
      }
      return null;
    });
    out.收尾落点 = panePt;
    if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1200); }
  }
}
await escAll();

// ---------------------------------------------------------------- ③ 手册 64 个逐字字面量
log('\n=== ③ 手册逐字字面量 data-testid="X"（64 个）逐状态命中 ===');
const lits = readFileSync('/tmp/b129-doc-testids.txt', 'utf8').split('\n').filter(Boolean);
const perState = {};
for (const s of out.顺序) { const set = new Set(out.状态[s]?.testids || []); perState[s] = set; }
out.字面量 = {};
out.静态未活 = []; out.全状态未活 = [];
for (const t of lits) {
  const hits = out.顺序.filter((s) => perState[s].has(t));
  out.字面量[t] = { 命中状态: hits, 命中数: hits.length };
  if (!perState['静态']?.has(t)) out.静态未活.push(t);
  if (hits.length === 0) out.全状态未活.push(t);
}
log('  静态态就存活：', lits.length - out.静态未活.length, '｜静态未活：', out.静态未活.length);
log('  **12 个状态全都没活**（真·疑似过时或记错）：', out.全状态未活.length, '个');
log('  ', JSON.stringify(out.全状态未活));
save();

// ---------------------------------------------------------------- ④ 页面并集 vs 手册全文
const 并集 = Array.from(new Set(out.顺序.flatMap((s) => out.状态[s]?.testids || []))).sort();
out.并集种类 = 并集.length;
out.并集 = 并集;
log('\n=== ④ 页面并集 vs 手册全文 ===\n  12 个状态的 testid 并集：', 并集.length, '种');

function walk(dir) { const acc = []; for (const e of readdirSync(dir)) { const q = join(dir, e);
  if (statSync(q).isDirectory()) acc.push(...walk(q)); else if (q.endsWith('.md')) acc.push(q); } return acc; }
const mdFiles = walk(DOC_DIR);
let corpus = ''; for (const f of mdFiles) corpus += readFileSync(f, 'utf8');
out.手册文件数 = mdFiles.length; out.手册字符数 = corpus.length;
const 漏记 = 并集.filter((t) => !corpus.includes(t));
out.漏记 = 漏记;
log('  手册 md 文件：', mdFiles.length, '份 /', corpus.length, '字符');
log('  **页面并集里、手册全文一次都没提过**的 testid：', 漏记.length, '种');
log('  ', JSON.stringify(漏记));
const 记了但页面没有 = out.全状态未活;
out.记了但页面没有 = 记了但页面没有;
log('  反向：手册写了、页面 12 态都没有的：', 记了但页面没有.length, '个（见上）');
save();

// ---------------------------------------------------------------- 收尾
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), credits: await credits() };
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE b');
process.exit(0);

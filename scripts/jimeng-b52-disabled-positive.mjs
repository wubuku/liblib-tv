// 批次 52：「禁用 + 原因副文案」形态的**阳性对照** + 资产库页签的空态全覆盖。
//
// 为什么做这一批：批次 51 得出的是**阴性**结论（「下载」没有 aria-disabled、
// 也没有「就绪资源」副文案）。但「我没找到」本身很弱 —— 除非我先知道
// 「有的话长什么样」。资产库的「确认」按钮就是一个真实的禁用实例：
// 未选素材时它禁用、并挂着一句「请先选择素材」。
//
// 本批量三件事：
//  ① 阳性对照：把「确认」（禁用）和同一弹窗里的可用按钮用**同一个函数**测一遍，
//     看禁用到底会体现在哪些属性/计算样式上 —— 以后判断任何按钮都拿这张表当基准。
//  ② 副文案「请先选择素材」住在哪：按钮内文本？还是兄弟节点？（决定该往哪找）
//  ③ 资产库两级页签的**空态逐字**与几何（现在只记了图片页与视频页）
//
// 全程只读：开弹窗、切页签、读 DOM。不点「确认」、不选素材、不产生任何画布变更。
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { keyGuard, canvasBaseline, diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('canvas page not found'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const nodes = async () => await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));

await reset();
const bad0 = await diffNodePositions(p, BASELINE.nodes, 1.5);
if (bad0.length || (await nodes()).length !== 6) { console.error('ABORT: 起点与基线不一致', JSON.stringify(bad0)); await b.close(); process.exit(2); }
console.log('起点与基线一致 ✅  6 节点、canvas 位置逐项对齐');
const before = await canvasBaseline(p);
console.log('起点状态行:', before.status, '| 积分', before.credit);

// 🔑 统一的「按钮状态」测量函数 —— 阳性/阴性对照必须用同一把尺子
const buttonState = (label) => p.evaluate((lb) => {
  const root = document.querySelector('[data-testid="canvas-asset-library-dialog"]') || document.body;
  const all = Array.from(root.querySelectorAll('button,[role="button"],[role="tab"]'));
  const pick = (e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return {
      label: lb,
      name: e.getAttribute('aria-label') || (e.innerText || '').trim().split('\n')[0] || (e.getAttribute('data-testid') || ''),
      tag: e.tagName, role: e.getAttribute('role'),
      ariaDisabled: e.getAttribute('aria-disabled'),
      ariaSelected: e.getAttribute('aria-selected'),
      disabledAttr: e.hasAttribute('disabled') ? 'true' : null,
      dataDisabled: e.getAttribute('data-disabled'),
      dataState: e.getAttribute('data-state'),
      title: e.getAttribute('title'),
      innerText: (e.innerText || '').replace(/\n/g, ' ⏎ ').trim().slice(0, 40),
      rect: [r.x, r.y, r.width, r.height].map(Math.round),
      opacity: cs.opacity, pointerEvents: cs.pointerEvents, cursor: cs.cursor,
      color: cs.color, bg: cs.backgroundColor,
      clsHead: String(e.className).slice(0, 150),
    };
  };
  return all.map(pick);
}, label);

// 「请先选择素材」住在哪：往上找它最近的祖先元素
const locateReason = (needle) => p.evaluate((n) => {
  const hits = [];
  for (const e of document.querySelectorAll('*')) {
    if (e.children.length) continue;
    const t = (e.textContent || '').trim();
    if (t === n || (t.includes(n) && t.length < 40)) {
      const chain = [];
      let cur = e;
      for (let i = 0; i < 5 && cur; i++) {
        const r = cur.getBoundingClientRect();
        chain.push({ tag: cur.tagName, tid: cur.getAttribute('data-testid'), cls: String(cur.className).slice(0, 60), rect: [r.x, r.y, r.width, r.height].map(Math.round) });
        cur = cur.parentElement;
      }
      hits.push({ text: t, own: { tag: e.tagName, tid: e.getAttribute('data-testid'), cls: String(e.className).slice(0, 80) }, chain });
    }
  }
  return hits;
}, needle);

try {
  // ---- 打开资产库 ----
  console.log('\n########## ① 资产库弹窗的 DOM 契约 ##########');
  await p.click('button[aria-label="资产库"]');
  await p.waitForTimeout(2200);
  const dlg = await p.evaluate(() => {
    const g = (s) => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return { tid: e.getAttribute('data-testid'), role: e.getAttribute('role'), rect: [r.x, r.y, r.width, r.height].map(Math.round) }; };
    const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
    return { dialog: g('[data-testid="canvas-asset-library-dialog"]'), surface: g('[data-testid="canvas-asset-library-surface"]'),
      operationArea: g('[data-testid="canvas-asset-library-operation-area"]'), viewport: g('[data-testid="canvas-asset-library-viewport"]'),
      footer: g('[data-testid="canvas-asset-library-footer"]'),
      fullText: d ? (d.innerText || '').replace(/\n+/g, ' | ') : null };
  });
  console.log(JSON.stringify(dlg, null, 1));

  // ---- ② 页签几何逐项 ----
  console.log('\n########## ② 两级页签逐项（几何 + 逐字） ##########');
  const tabs = await p.evaluate(() => {
    const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
    const row1 = d.querySelector('[data-testid="canvas-asset-library-operation-area"]');
    return Array.from(row1.querySelectorAll('button,[role="tab"],[role="button"]')).map((e) => { const r = e.getBoundingClientRect();
      return { txt: (e.innerText || '').trim().split('\n')[0], aria: e.getAttribute('aria-label'), role: e.getAttribute('role'),
        sel: e.getAttribute('aria-selected'), rect: [r.x, r.y, r.width, r.height].map(Math.round) }; });
  });
  console.log('第一行（操作区）:', JSON.stringify(tabs, null, 1));

  // ---- ③ 阳性对照：禁用 vs 可用 ----
  console.log('\n########## ③ 阳性对照：未选素材时的「确认」 ##########');
  const states = await buttonState('未选素材');
  const byName = (n) => states.filter((s) => (s.name || '').includes(n));
  console.log('「确认」按钮:', JSON.stringify(byName('确认'), null, 1));
  console.log('同窗可用按钮对照（取前 3 个非禁用）:', JSON.stringify(states.filter((s) => !s.ariaDisabled && s.disabledAttr === null && s.name).slice(0, 3), null, 1));
  console.log('\n该弹窗内 aria-disabled / disabled 的按钮逐字:',
    JSON.stringify(states.filter((s) => s.ariaDisabled !== null || s.disabledAttr !== null || s.dataDisabled !== null).map((s) => ({ name: s.name, ariaDisabled: s.ariaDisabled, disabledAttr: s.disabledAttr, dataDisabled: s.dataDisabled, cursor: s.cursor, opacity: s.opacity }))));

  console.log('\n「请先选择素材」住在哪:', JSON.stringify(await locateReason('请先选择素材'), null, 1));

  // ---- ④ 页签空态全覆盖 ----
  console.log('\n########## ④ 资产 / 主体 下的空态逐字 ##########');
  const clickTab = async (txt) => {
    const ok = await p.evaluate((t) => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
      const all = Array.from(d.querySelectorAll('button,[role="tab"],[role="button"]'));
      const hit = all.find((e) => (e.innerText || '').trim().split('\n')[0] === t);
      if (!hit) return false; hit.click(); return true; }, txt);
    await p.waitForTimeout(1100);
    return ok;
  };
  const readViewport = () => p.evaluate(() => { const v = document.querySelector('[data-testid="canvas-asset-library-viewport"]');
    const r = v.getBoundingClientRect();
    return { rect: [r.x, r.y, r.width, r.height].map(Math.round), text: (v.innerText || '').replace(/\n+/g, ' | ').trim().slice(0, 120), imgs: v.querySelectorAll('img').length, items: v.querySelectorAll('[class*="card" i],[class*="item" i]').length }; });
  for (const t of ['图片', '视频', '音频', '文档']) {
    const ok = await clickTab(t);
    console.log(`  [资产/${t}] 点击${ok ? '成功' : '失败'} →`, JSON.stringify(await readViewport()));
  }
  const okSubject = await clickTab('主体');
  if (okSubject) {
    const sub = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
      const row = d.querySelector('[data-testid="canvas-asset-library-operation-area"]');
      return Array.from(row.querySelectorAll('button,[role="tab"],[role="button"]')).map((e) => (e.innerText || '').trim().split('\n')[0]).filter(Boolean); });
    console.log('  [主体] 第二级页签:', JSON.stringify(sub));
    for (const t of sub.slice(0, 6)) {
      const ok2 = await clickTab(t);
      console.log(`    [主体/${t}] ${ok2 ? '' : '点击失败 '}→`, JSON.stringify(await readViewport()));
    }
  }
} catch (e) {
  console.error('ABORT:', e.message);
}

// ---- 收尾 ----
await reset();
await p.mouse.click(700, 150); await p.waitForTimeout(600);
const fin = await canvasBaseline(p);
const bad = await diffNodePositions(p, BASELINE.nodes, 1.5);
const g = await keyGuard(p);
console.log('\n=== 收尾核对 ===');
console.log(' 焦点守卫:', g.safe ? '✅' : g.where);
console.log(' 节点数', (await nodes()).length, '| 状态行:', fin.status);
console.log(' 积分', fin.credit, '(起点', before.credit + ') | 位置偏离', bad.length, bad.length ? bad.join(',') : '✅ 0');
await b.close();

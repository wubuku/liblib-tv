// 批次 129 · c 轮：**补扫 b 轮漏掉的状态**，把「26 个全灭」里属于「我还没扫到」的挑出来。
//
// 🔑 b 轮把 12 个状态扫完了，得出 64 个手册字面量里 26 个「一个状态都没活」。
//   但**「12 态没活」≠「过时」**——b 轮的状态集本就不全，缺三个明显的：
//   ① **资产库面板**（左栏 `aria-label="资产库"`，b128 已开过且**不建节点**——同批被证建节点的
//      主体/时间线/导演台三个都建了节点，资产库没建，这是旁证不是猜测）；
//   ② **多选态**（`selection-context-toolbar*` 按名字就该在多选时出现，b 轮只做了单选）；
//   ③ **Agent 侧栏**（b 轮探测发现 `canvas-feature-sidecar` **常驻屏上** `200×348@1068,360`，
//      但 b 轮没对侧栏内部做任何交互，技能芯片/会话折叠这类只在交互后才出现的层没被扫到）。
//
// ⚠️ 共享画布纪律：左栏「文本/图片/视频/音频」**也建节点**（本轮探测确认 4 个 40×40 按钮），
//   一律不碰。只用资产库（已验证不建节点）、Shift 多选、Agent 侧栏。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b129c.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1000); } }

// 收尾护栏：本轮只允许「新增节点恰好 0 个」——全程不碰建节点按钮
const collect = () => p.evaluate(() => {
  const s = new Set(); for (const e of Array.from(document.querySelectorAll('[data-testid]'))) s.add(e.getAttribute('data-testid')); return Array.from(s);
});
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
out.起始id = await idsNow();
log('起始节点数：', out.起始id.length);
save();

const record = async (name) => { const t = await collect(); out.状态[name] = { 种类: t.length, testids: t }; log(`  【${name}】testid ${t.length} 种`); save(); return t; };
const escAll = async () => { for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };

out.状态 = {}; out.顺序 = [];
log('\n=== ① 资产库面板（左栏，已验证不建节点）===');
{
  const pt = await p.evaluate(() => {
    const e = document.querySelector('[aria-label="资产库"]'); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 命中: h.tagName };
    }
    return { __err: 'no-point' };
  });
  out.资产库落点 = pt;
  if (pt.__err) log('  ⛔ 资产库', pt.__err);
  else {
    log('  落点：', JSON.stringify(pt));
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800);
    out.资产库后 = { 浮层: await overlays(), 节点数: (await idsNow()).length, testid: (await collect()).length };
    log('  打开后：浮层', out.资产库后.浮层, '｜节点数', out.资产库后.节点数, '（必须仍为', out.起始id.length, '）');
    await record('资产库面板'); out.顺序.push('资产库面板');
    // 资产库内的分页/空态控件也扫一遍
    out.资产库内元素 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid]')).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.x < 400; }).map((e) => { const r = e.getBoundingClientRect(); return { tid: e.getAttribute('data-testid'), tag: e.tagName, rect: [r.x, r.y, r.width, r.height].map(Math.round), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) }; }));
    log('  左半屏有面积的 testid 元素：', out.资产库内元素.length);
    out.资产库内元素.forEach((e) => log('      ·', e.tid, `<${e.tag}>`, e.rect.join(','), '«' + e.文字 + '»'));
    save();
  }
  await escAll();
}

log('\n=== ② 多选两个节点（Shift + 点第二个）===');
{
  const pts = await p.evaluate(() => {
    const acc = [];
    for (const n of document.querySelectorAll('.react-flow__node-audio')) {
      const r = n.getBoundingClientRect();
      if (r.x + r.width < 90 || r.x > innerWidth - 90 || r.y + r.height < 110 || r.y > innerHeight - 110) continue;
      for (let y = Math.ceil(r.y) + 3; y <= r.y + r.height - 3; y += 4) for (let x = Math.ceil(r.x) + 3; x <= r.x + r.width - 3; x += 4) {
        const h = document.elementFromPoint(x, y); if (h && (h === n || n.contains(h))) { acc.push({ x, y, id: n.getAttribute('data-id') }); break; }
      }
      if (acc.length >= 2) break;
    }
    return acc;
  });
  out.多选落点 = pts;
  log('  落点：', JSON.stringify(pts));
  if (pts.length < 2) log('  ⛔ 可见节点不足 2 个');
  else {
    await p.mouse.click(pts[0].x, pts[0].y); await p.waitForTimeout(1200);
    await p.keyboard.down('Shift');
    await p.mouse.click(pts[1].x, pts[1].y);
    await p.keyboard.up('Shift');
    await p.waitForTimeout(1500);
    out.多选后 = { 选中数: await sel(), 状态行: await status() };
    log('  多选后：选中数', out.多选后.选中数, '｜状态行', JSON.stringify(out.多选后.状态行));
    if (out.多选后.选中数 === 2) { await record('多选两个音频节点'); out.顺序.push('多选两个音频节点'); }
    else log('  ⛔ 选中数不是 2，跳过');
    save();
  }
  // 点空白取消（必须命中 .react-flow__pane）
  const panePt = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1100); }
  log('  取消后选中数：', await sel());
}

log('\n=== ③ Agent 侧栏（常驻 ASIDE）内部 ===');
{
  // 3a 侧栏本体到底有哪些 testid / 有没有可点的子控件
  out.Agent侧栏 = await p.evaluate(() => {
    const s = document.querySelector('[data-testid="canvas-feature-sidecar"]');
    if (!s) return { __err: 'not-found' };
    const r = s.getBoundingClientRect();
    const inner = [];
    for (const e of Array.from(s.querySelectorAll('*'))) {
      const q = e.getBoundingClientRect();
      if (q.width < 1 || q.height < 1) continue;
      inner.push({ tid: e.getAttribute('data-testid'), tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
        rect: [q.x, q.y, q.width, q.height].map(Math.round), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) });
    }
    return { 矩形: [r.x, r.y, r.width, r.height].map(Math.round), aria: s.getAttribute('aria-label'), 屏上文字: (s.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200), 子元素: inner };
  });
  if (out.Agent侧栏.__err) log('  ⛔', out.Agent侧栏.__err);
  else {
    log('  侧栏', JSON.stringify(out.Agent侧栏.矩形), 'aria=' + out.Agent侧栏.aria);
    log('  屏上文字：«' + out.Agent侧栏.屏上文字 + '»');
    log('  有面积的子元素：', out.Agent侧栏.子元素.length);
    out.Agent侧栏.子元素.slice(0, 30).forEach((e) => log('      ·', e.tid || '(无 tid)', `<${e.tag}>`, e.role || '', e.rect.join(','), '«' + e.文字 + '»'));
  }
  save();
  // 3b 点侧栏历史入口（不发送任何消息）
  {
    const pt = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-agent-history-surface"]'); if (!e) return { __err: 'not-found' };
      const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
      }
      return { __err: 'no-point' };
    });
    out.Agent历史落点 = pt;
    if (pt.__err) log('  【Agent 历史】⛔', pt.__err);
    else {
      await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1700);
      log('  【Agent 历史】浮层', await overlays(), '｜节点数', (await idsNow()).length);
      await record('Agent 历史'); out.顺序.push('Agent 历史');
      save();
    }
    await escAll();
  }
}
await escAll();

// ---------------------------------------------------------------- 差集重算
const lits = readFileSync('/tmp/b129-doc-testids.txt', 'utf8').split('\n').filter(Boolean);
const B = JSON.parse(readFileSync(new URL('./_tmp-b129b.json', import.meta.url), 'utf8'));
const 全态 = new Set([...B.顺序, ...out.顺序].flatMap((s) => (B.状态[s]?.testids || []).concat(out.状态[s]?.testids || [])));
out.补扫后仍全灭 = lits.filter((t) => !全态.has(t));
out.补扫捞回 = B.全状态未活.filter((t) => 全态.has(t));
out.全态并集 = 全态.size;
log('\n=== ④ 差集重算 ===');
log('  b 轮 12 态并集：', B.并集种类, '｜补扫后并集：', out.全态并集, '种');
log('  **补扫捞回**（b 轮以为没了、其实只是没扫到）：', out.补扫捞回.length, '个：', JSON.stringify(out.补扫捞回));
log('  补扫后**仍全灭**：', out.补扫后仍全灭.length, '个：', JSON.stringify(out.补扫后仍全灭));
save();

// 差集里每个在全态下到底存不存在
out.仍全灭明细 = {};
for (const t of out.补扫后仍全灭) out.仍全灭明细[t] = { 在全态: 全态.has(t) };
save();

out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(),
  节点数: (await idsNow()).length, 起始节点数: out.起始id.length };
log('\n收尾：', JSON.stringify(out.收尾));
const 多了 = (await idsNow()).filter((x) => !out.起始id.includes(x));
out.新增id = 多了;
log('  本轮新增的 id（必须为空）：', JSON.stringify(多了));
save();
log('\nDONE c');
process.exit(0);

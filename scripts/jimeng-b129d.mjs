// 批次 129 · d 轮：把剩下**能安全验的**两条缺口验掉，并对全灭项做最终分诊。
//
// 📌 b/c 两轮之后 21 个「全状态没活」，c 轮脚本自身有两处失误，本轮正面修：
//   ① **多选落点收集写错**：内层 `break` 只跳出 y 循环，`acc` 里 33 个点**全是同一个节点**
//      ⇒ `pts[0]`、`pts[1]` 点的同一个节点 ⇒ Shift+点已选中的节点＝**取消选中** ⇒ 选中数 0。
//      本轮改成「**每个节点只收一个点**」，并断言两个落点的 `data-id` 必须不同。
//      ⇒ 立规：**收集落点列表时，`break` 要跳出两层循环**；拿「点过的节点数」当「落点数」会自欺。
//   ② **资产库内元素用 `x < 400` 过滤**：屏外节点坐标是负数，全被捞进来，输出 541 条噪声。
//      本轮改成**按 testid 前缀**过滤。
//
// 🔑 本轮要回答的三件事：
//   ① 多选两个节点时，基座 `selection-context-toolbar` 到底在不在
//      （`...-surface` / `...-popup-host` 在**单选**态就已经存在了，基座反而缺——这本身是个反直觉点）；
//   ② 资产库「主体」页的 `canvas-asset-library-subjects-panel` 在不在（切页是只读的）；
//   ③ Agent 侧栏 `canvas-feature-sidecar` 有面积却**零个子元素**是怎么回事；
//      以及 c 轮点「Agent 历史」后 testid 174→171 少了哪三个。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd' };
const save = () => writeFileSync(new URL('./_tmp-b129d.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const collect = () => p.evaluate(() => { const s = new Set(); for (const e of document.querySelectorAll('[data-testid]')) s.add(e.getAttribute('data-testid')); return Array.from(s); });
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const escAll = async () => { for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), credits: await credits(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await escAll();
out.起始id = await idsNow();
const 基线 = await collect();
out.静态基线 = { 种类: 基线.length };
log('静态基线 testid：', 基线.length, '种｜节点', out.起始id.length, '个');
save();

// ---------------------------------------------------------------- ① 多选（修好落点收集）
log('\n=== ① 多选两个节点（每个节点只收一个落点，且断言两个 id 不同）===');
{
  const pts = await p.evaluate(() => {
    const acc = [];
    for (const n of document.querySelectorAll('.react-flow__node-audio')) {
      const r = n.getBoundingClientRect();
      if (r.x + r.width < 90 || r.x > innerWidth - 90 || r.y + r.height < 110 || r.y > innerHeight - 110) continue;
      let hit = null;
      for (let y = Math.ceil(r.y) + 3; y <= r.y + r.height - 3 && !hit; y += 4)
        for (let x = Math.ceil(r.x) + 3; x <= r.x + r.width - 3; x += 4) {
          const h = document.elementFromPoint(x, y);
          if (h && (h === n || n.contains(h))) { hit = { x, y, id: n.getAttribute('data-id') }; break; }
        }
      if (hit) acc.push(hit);
      if (acc.length >= 2) break;
    }
    return acc;
  });
  out.多选落点 = pts;
  log('  落点（' + pts.length + ' 个）：', JSON.stringify(pts));
  if (pts.length < 2 || pts[0].id === pts[1].id) log('  ⛔ 落点不足或两个 id 相同，放弃');
  else {
    await p.mouse.click(pts[0].x, pts[0].y); await p.waitForTimeout(1200);
    const 单选数 = await sel();
    await p.keyboard.down('Shift');
    await p.mouse.click(pts[1].x, pts[1].y);
    await p.keyboard.up('Shift');
    await p.waitForTimeout(1500);
    out.多选后 = { 单选数, 选中数: await sel(), 状态行: await status() };
    log('  第一个点后选中数 =', 单选数, '｜Shift 点第二个后选中数 =', out.多选后.选中数);
    log('  状态行：', JSON.stringify(out.多选后.状态行));
    if (out.多选后.选中数 === 2) {
      const 多选 = await collect();
      out.多选testid = { 种类: 多选.length, 相对单选的增量: 多选.filter((t) => !基线.includes(t)), 相对单选的减量: 基线.filter((t) => !多选.includes(t)) };
      log('  多选态 testid', 多选.length, '种');
      log('  **相对静态基线的增量**：', JSON.stringify(out.多选testid.相对单选的增量));
      log('  相对静态基线的减量：', JSON.stringify(out.多选testid.相对单选的减量));
      for (const t of ['selection-context-toolbar', 'selection-context-toolbar-surface', 'selection-context-toolbar-popup-host', 'selection-context-toolbar-count', 'node-toolbar'])
        log(`    ${t} → ${多选.includes(t) ? '在' : '不在'}（静态基线：${基线.includes(t) ? '在' : '不在'}）`);
    } else log('  ⛔ 选中数不是 2');
    save();
  }
  const panePt = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1100); }
  log('  点空白取消后选中数：', await sel());
}

// ---------------------------------------------------------------- ② 资产库切页
log('\n=== ② 资产库切页找「主体」页 ===');
{
  const pt = await p.evaluate(() => { const e = document.querySelector('[aria-label="资产库"]'); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'no-point' }; });
  if (pt.__err) log('  ⛔', pt.__err);
  else {
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800);
    out.资产库后节点数 = (await idsNow()).length;
    log('  打开后节点数', out.资产库后节点数, '（必须仍为', out.起始id.length, '）');
    // 只看资产库自己的 testid（按前缀，不是按坐标）
    out.资产库元素 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-asset-library"]')).map((e) => {
      const r = e.getBoundingClientRect();
      return { tid: e.getAttribute('data-testid'), tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
        矩形: [r.x, r.y, r.width, r.height].map(Math.round), 有面积: r.width >= 1 && r.height >= 1, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) };
    }));
    log('  `canvas-asset-library*` 元素', out.资产库元素.length, '个：');
    out.资产库元素.forEach((e) => log('      ·', e.tid, `<${e.tag}>`, e.role || '', '有面积=' + e.有面积, e.矩形.join(','), '«' + e.文字 + '»'));
    // 找页签（资产库对话框里的 tab / 导航按钮）
    out.页签 = await p.evaluate(() => {
      const dlg = document.querySelector('[data-testid="canvas-asset-library-dialog"]') || document.body;
      const cands = Array.from(dlg.querySelectorAll('[role=tab],[data-testid$="tab"],[data-testid*="tab"],nav button,button'))
        .map((e) => { const r = e.getBoundingClientRect(); return { tid: e.getAttribute('data-testid'), role: e.getAttribute('role'), aria: e.getAttribute('aria-label'), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), 矩形: [r.x, r.y, r.width, r.height].map(Math.round), 有面积: r.width >= 1 && r.height >= 1 }; })
        .filter((x) => x.有面积);
      return cands;
    });
    log('  对话框内可点控件：', out.页签.length, '个：');
    out.页签.slice(0, 20).forEach((t) => log('      ·', t.role || '', t.tid || '(无 tid)', t.矩形.join(','), '«' + t.文字 + '»'));
    save();
    // 逐个点「看起来像页签」的（只切页，不点任何生成/上传按钮）
    out.切页 = [];
    for (const t of out.页签) {
      const isTab = t.role === 'tab' || /tab|页/i.test(t.tid || '');
      if (!isTab) continue;
      const before = await collect();
      const hit = await p.evaluate((sel) => { const e = document.querySelector(sel); if (!e) return { __err: 'nf' };
        const r = e.getBoundingClientRect();
        for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
        return { __err: 'np' }; }, `[data-testid="${t.tid}"]` || `[role=tab]`);
      if (hit.__err) continue;
      await p.mouse.click(hit.x, hit.y); await p.waitForTimeout(1500);
      const after = await collect();
      out.切页.push({ 页签: t, 命中: await overlays(), 增量: after.filter((x) => !before.includes(x)), 减量: before.filter((x) => !after.includes(x)), 节点数: (await idsNow()).length });
      log(`      点页签「${t.文字}」(${t.tid}) → 增量 ${JSON.stringify(after.filter((x) => !before.includes(x)))} 减量 ${JSON.stringify(before.filter((x) => !after.includes(x)))}`);
      save();
    }
  }
  await escAll();
  log('  关闭后浮层：', await overlays(), '｜节点数', (await idsNow()).length);
}

// ---------------------------------------------------------------- ③ Agent 侧栏
log('\n=== ③ Agent 侧栏：有面积却零子元素？===');
{
  out.侧栏前 = await collect();
  out.侧栏DOM = await p.evaluate(() => { const s = document.querySelector('[data-testid="canvas-feature-sidecar"]');
    if (!s) return { __err: 'nf' };
    const r = s.getBoundingClientRect();
    const cs = getComputedStyle(s);
    return { 矩形: [r.x, r.y, r.width, r.height].map(Math.round), outer: s.outerHTML.slice(0, 700),
      display: cs.display, visibility: cs.visibility, opacity: cs.opacity, overflow: cs.overflow, pointerEvents: cs.pointerEvents,
      子元素总数: s.children.length, 屏上文字: (s.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) }; });
  if (out.侧栏DOM.__err) log('  ⛔ 侧栏不存在');
  else {
    log('  矩形', JSON.stringify(out.侧栏DOM.矩形), '｜子元素总数', out.侧栏DOM.子元素总数, '｜屏上文字«' + out.侧栏DOM.屏上文字 + '»');
    log('  计算样式：display=' + out.侧栏DOM.display, 'visibility=' + out.侧栏DOM.visibility, 'opacity=' + out.侧栏DOM.opacity, 'pointer-events=' + out.侧栏DOM.pointerEvents);
    log('  outerHTML 前 700：', out.侧栏DOM.outer);
  }
  save();
  // 点历史入口，看 174→171 少了哪三个
  const hp = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-agent-history-surface"]'); if (!e) return { __err: 'nf' };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'np' }; });
  out.历史落点 = hp;
  if (hp.__err) log('  【Agent 历史】⛔', hp.__err);
  else {
    await p.mouse.click(hp.x, hp.y); await p.waitForTimeout(1800);
    const after = await collect();
    out.历史后 = { testid种类: after.length, 浮层: await overlays(), 增量: after.filter((t) => !out.侧栏前.includes(t)), 减量: out.侧栏前.filter((t) => !after.includes(t)) };
    log('  点「Agent 历史」后：testid', out.历史后.testid种类, '种｜浮层', out.历史后.浮层);
    log('  **减量**：', JSON.stringify(out.历史后.减量));
    log('  增量：', JSON.stringify(out.历史后.增量));
    log('  节点数', (await idsNow()).length);
    save();
  }
  await escAll();
  const back = await collect();
  out.关闭后 = { testid种类: back.length, 增量: back.filter((t) => !out.侧栏前.includes(t)), 减量: out.侧栏前.filter((t) => !back.includes(t)) };
  log('  Esc 关闭后：testid', back.length, '种｜增量', JSON.stringify(out.关闭后.增量), '减量', JSON.stringify(out.关闭后.减量));
  // 再点一次回去，确认幂等
  if (hp.__err !== 'nf') { await p.mouse.click(hp.x, hp.y); await p.waitForTimeout(1600);
    const again = await collect();
    out.再点后 = { testid种类: again.length, 增量: again.filter((t) => !out.侧栏前.includes(t)), 减量: out.侧栏前.filter((t) => !again.includes(t)) };
    log('  **再点一次**（应回静态基线）：testid', again.length, '种｜增量', JSON.stringify(out.再点后.增量), '减量', JSON.stringify(out.再点后.减量));
    save(); }
  await escAll();
}

// ---------------------------------------------------------------- 收尾
const endIds = await idsNow();
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), credits: await credits(), 节点数: endIds.length, 起始节点数: out.起始id.length };
out.新增id = endIds.filter((x) => !out.起始id.includes(x));
out.丢失id = out.起始id.filter((x) => !endIds.includes(x));
log('\n收尾：', JSON.stringify(out.收尾));
log('  新增 id（必须空）：', JSON.stringify(out.新增id), '｜丢失 id（必须空）：', JSON.stringify(out.丢失id));
save();
log('\nDONE d');
process.exit(0);

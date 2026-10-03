// 批次 128 · 善后 · 清事故：删掉**本批 b 轮自己建出来的 3 个节点**。
//
// 🔴 事故复盘（先写清楚，再动鼠标）：
//   b 轮为了「扩面扫描」点了左栏的 **主体 / 时间线 / 导演台** 三个按钮，
//   而 `90-troubleshooting.md:358` 早就写着「**点左栏的「主体 / 时间线 / 导演台」，
//   画布上凭空多出节点**」—— 我读了那行标题还是踩了进去。
//   证据链：批次 127 收尾是 `76 nodes / 0 selected`；b 轮点了那三个按钮之后，
//   c 轮起点变成 `79 nodes / 1 selected`；差集恰好 3 个：
//     node_4erz156z9n  主体 1（「添加描述... Empty」＝ 全新空节点）
//     node_5w5462j2vz  时间线 3（00:00 / 00:00 ＝ 全新空时间线）
//     node_21nf5zy2wk  导演台（**处于选中态** —— 点导演台按钮会把它选中）
//   ⇒ **三个都是本批的遗留**，必须清掉。
//
// 📌 由此得出一条要写进手册的规：**左栏那三个按钮不是「打开面板」，它们会往画布上插节点**
//   ⇒ 任何「只读普查」都**不许**用左栏这三个入口当面板来开。
//
// 🛡 护栏（沿用批次 97 三道 ＋ 105 第四道 ＋ 120 规二）：
//   ① 每个节点：点它选中 → 右键 → 上下文菜单 →「删除」（**不走键盘**，子控件会抢焦点）
//   ② 落点在**动作即将发生的那一刻**现算 ＋ `elementFromPoint` 自检（同一个 evaluate 里做完）
//   ③ 事后核对「本轮消失的 id 集合」**恰好只有 SELF**
//   ④ 只删这 3 个白名单里的 id；任何超出 ⇒ 立刻停手
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'cleanup' };
const save = () => writeFileSync(new URL('./_tmp-b128clean.json', import.meta.url), JSON.stringify(out, null, 1));

const SELF = ['node_4erz156z9n', 'node_5w5462j2vz', 'node_21nf5zy2wk'];
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')).filter(Boolean));
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.白名单 = SELF;
out.起点 = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), credits: await credits(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.起点));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1000); } }

out.清理前 = { 节点数: (await ids()).length, 选中: await sel() };
const base = '/tmp/b120-baseline-ids.txt';
if (existsSync(base)) {
  const bset = new Set(readFileSync(base, 'utf8').split('\n').map((s) => s.trim()).filter(Boolean));
  const now0 = await ids();
  out.基线 = { 基线数: bset.size, 多出: now0.filter((x) => !bset.has(x)), 少掉: [...bset].filter((x) => !now0.includes(x)) };
  log('  与批次 120 基线比对：多出', JSON.stringify(out.基线.多出), '｜少掉', JSON.stringify(out.基线.少掉));
}
log('  清理前节点数：', out.清理前.节点数);
save();

// ---- 逐个删除 ----
out.删除记录 = [];
for (const id of SELF) {
  const rec = { id };
  // ① 目标还在吗
  rec.存在 = await p.evaluate((i) => !!document.querySelector('.react-flow__node[data-id="' + i + '"]'), id);
  if (!rec.存在) { rec.结果 = '已不存在（可能已被别人删掉）'; out.删除记录.push(rec); log(`  ${id} ⛔ ${rec.结果}`); save(); continue; }

  // ② 选中它（若未选中）：落点现算 + 自检，命中必须落在该节点内部
  rec.选中前 = await p.evaluate((i) => !!document.querySelector('.react-flow__node[data-id="' + i + '"].selected'), id);
  if (!rec.选中前) {
    const pt = await p.evaluate((i) => {
      const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
      if (!n) return { __err: 'gone' };
      const r = n.getBoundingClientRect();
      if (r.width < 1 || r.x < 0 || r.y < 0 || r.x + r.width > window.innerWidth || r.y + r.height > window.innerHeight)
        return { __err: 'offscreen', rect: [r.x, r.y, r.width, r.height].map(Math.round) };
      for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4; y += 3)
        for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 3) {
          const h = document.elementFromPoint(x, y);
          if (h && (h === n || n.contains(h))) return { x, y };
        }
      return { __err: 'no-point-in-node', rect: [r.x, r.y, r.width, r.height].map(Math.round) };
    }, id);
    rec.选中落点 = pt;
    if (pt.__err) { rec.结果 = '选中失败:' + pt.__err; out.删除记录.push(rec); log(`  ${id} ⛔ ${rec.结果}`); save(); continue; }
    await p.mouse.click(pt.x, pt.y);
    await p.waitForTimeout(1100);
  }
  rec.选中后 = await p.evaluate((i) => !!document.querySelector('.react-flow__node[data-id="' + i + '"].selected'), id);
  log(`  ${id}｜选中前=${rec.选中前} 选中后=${rec.选中后}`);
  if (!rec.选中后) { rec.结果 = '没能选中，停手（不硬删）'; out.删除记录.push(rec); save(); continue; }

  // ③ 右键 → 上下文菜单 →「删除」：**落点现算 + 自检放在同一个 evaluate 里**
  const before = new Set(await ids());
  const del = await p.evaluate((i) => {
    const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
    if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    let pt = null;
    for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4 && !pt; y += 3)
      for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 3) {
        const h = document.elementFromPoint(x, y);
        if (h && (h === n || n.contains(h))) { pt = { x, y }; break; }
      }
    if (!pt) return { __err: 'no-point' };
    return pt;
  }, id);
  rec.右键落点 = del;
  if (del.__err) { rec.结果 = '右键落点失败:' + del.__err; out.删除记录.push(rec); log(`  ${id} ⛔ ${rec.结果}`); save(); continue; }
  await p.mouse.click(del.x, del.y, { button: 'right' });
  await p.waitForTimeout(1200);
  rec.菜单 = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role=menu]')).filter((m) => m.getBoundingClientRect().width > 1);
    return ms.map((m) => { const r = m.getBoundingClientRect(); return { rect: [r.x, r.y, r.width, r.height].map(Math.round),
      项: Array.from(m.querySelectorAll('[role=menuitem]')).map((k) => { const q = k.getBoundingClientRect();
        return { 文字: (k.innerText || '').replace(/\s+/g, ' ').trim(), rect: [q.x, q.y, q.width, q.height].map(Math.round) }; }) }; }); });
  log(`  ${id}｜菜单：`, JSON.stringify(rec.菜单).slice(0, 220));

  const item = await p.evaluate(() => { for (const m of Array.from(document.querySelectorAll('[role=menu]')).filter((x) => x.getBoundingClientRect().width > 1)) {
      for (const k of m.querySelectorAll('[role=menuitem]')) {
        // ⚠️ 用**前缀**匹配：菜单项逐字是「删除 ⌫」，`^删除$` 精确相等匹配不到
        //    （批次 120 的教训同一类：别拿逐字相等去认 UI 元素）
        if (!/^删除/.test((k.innerText || '').replace(/\s+/g, '').trim())) continue;
        const r = k.getBoundingClientRect(); if (r.width < 1) continue;
        for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
          const h = document.elementFromPoint(x, y);
          const c = h && h.closest('[role=menuitem]');
          if (c === k) return { x, y, 文字: (k.innerText || '').replace(/\s+/g, ' ').trim(), rect: [r.x, r.y, r.width, r.height].map(Math.round) };
        } } }
    return { __err: 'no-delete-item' }; });
  rec.删除项落点 = item;
  if (item.__err) { rec.结果 = '找不到删除项:' + item.__err; out.删除记录.push(rec); log(`  ${id} ⛔ ${rec.结果}`); save(); continue; }
  await p.mouse.click(item.x, item.y);
  await p.waitForTimeout(1500);

  // ④ 事后核对：消失的 id 集合必须**恰好只有 SELF**
  const after = new Set(await ids());
  const gone = [...before].filter((x) => !after.has(x));
  rec.消失的id = gone;
  rec.消失恰好只有SELF = gone.length === 1 && gone[0] === id;
  rec.结果 = rec.消失恰好只有SELF ? '已删除（消失 id 恰好只有自己）' : '⛔ 异常：消失集合 = ' + JSON.stringify(gone);
  out.删除记录.push(rec);
  log(`  ${id}｜消失的 id：${JSON.stringify(gone)} ⇒ ${rec.结果}`);
  save();
}

// ---- 收尾 ----
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1000); } }
out.收尾 = { 状态行: await status(), 选中: await sel(), zoom1: await zoom(), credits: await credits(), 浮层: await overlays() };
await p.waitForTimeout(1500);
out.收尾.zoom2 = await zoom();
if (existsSync(base)) {
  const bset = new Set(readFileSync(base, 'utf8').split('\n').map((s) => s.trim()).filter(Boolean));
  const now = await ids();
  out.收尾.节点 = { 现在数: now.length, 基线数: bset.size, 多出: now.filter((x) => !bset.has(x)), 少掉: [...bset].filter((x) => !now.includes(x)) };
}
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE cleanup');
process.exit(0);

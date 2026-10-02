// 批次 114 · b 轮：读 `@` **二级子菜单**的排除规则。
//
// 悬案（`20-reference.md`「二级子菜单」/ `prepare-generation.md:216`）：
//   「四类内容实测**逐字都是 `暂无相关节点`**」
//   「🔴 空列表成因**未能确认**（空节点被排除 / 当前节点自身被排除 / 两者叠加）
//    —— 观测条件下画布只有一个空的『视频 1』」
//
// 🔑 批次 113 的 b114pre 轮把画布读全了，于是**四个类别的约束各不相同**：
//   | 类别 | 画布上该类型节点 | 其中有资源 |
//   |---|---|---|
//   | 主体 | **0** | 0 |
//   | 图片 | 1（`b22-upload`） | **1**（`image-node-result` 在） |
//   | 视频 | 1（他人，空）+ **1（本批自建，空）** = 2 | **0** |
//   | 音频 | 68（他人，全空）+ **1（本批自建，空）** = 69 | **0** |
//
// ⇒ 四条约束叠起来只剩**一个解**：
//   · 若「排除空节点」成立 ⇒ 主体/视频/音频 三类都空，只有图片能列出 1 条
//   · 若「不排除空节点」成立 ⇒ 视频列 2、音频列 69
//   ⇒ **`音频` 类是决定性的那一条**（69 个节点，足以把「0 条」和「漏采样」区分开）。
//
// ⚠️ 判据不只看「有没有条目」，**逐字读** `role="option"` 文本 + `role="status"` 文本，
//    并与画布上该类型的节点清单**逐个对账**（含「宿主自身在不在列表里」）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const HOST_AUDIO = 'node_fnarb6091q';
const HOST_VIDEO = 'node_57qe0pz31m';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b114b.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// 画布上每类的节点清单（判据要能逐个对账，不是只数个数）
const inventory = () => p.evaluate(() => {
  const m = {};
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const type = ((n.getAttribute('class') || '').toString().match(/react-flow__node-(\w+)/) || [])[1] || '?';
    const t = (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '';
    const hasRes = !!n.querySelector('[data-testid$="-node-result"],[data-testid$="-node-uploading"]');
    (m[type] = m[type] || []).push({ id, title: (t || '').replace(/\s+/g, ' ').trim().slice(0, 24), hasRes });
  }
  return m;
});

// 读 `@` 一级面板 + （若已展开）二级子菜单
const readMention = (lbl) => p.evaluate((l) => {
  const r = { at: Date.now(), lbl: l, level1: null, level2: null };
  const l1 = document.querySelector('[data-testid="generation-mention-panel"]');
  if (l1) { const b = l1.getBoundingClientRect();
    r.level1 = { rect: [b.x, b.y, b.width, b.height].map(Math.round), role: l1.getAttribute('role'),
      aria: l1.getAttribute('aria-label'),
      options: Array.from(l1.querySelectorAll('[role="option"]')).map((o) => { const ob = o.getBoundingClientRect();
        return { t: (o.innerText || '').replace(/\s+/g, ' ').trim(), sel: o.getAttribute('aria-selected'),
          rect: [ob.x, ob.y, ob.width, ob.height].map(Math.round) }; }),
      groups: Array.from(l1.querySelectorAll('[role="group"]')).map((g) => g.getAttribute('aria-label') || (g.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30)) };
  }
  const l2 = document.querySelector('[data-testid="generation-mention-submenu"]');
  if (l2) { const b = l2.getBoundingClientRect();
    r.level2 = { rect: [b.x, b.y, b.width, b.height].map(Math.round), role: l2.getAttribute('role'),
      aria: l2.getAttribute('aria-label'),
      text: (l2.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      options: Array.from(l2.querySelectorAll('[role="option"]')).map((o) => { const ob = o.getBoundingClientRect();
        return { t: (o.innerText || '').replace(/\s+/g, ' ').trim(), rect: [ob.x, ob.y, ob.width, ob.height].map(Math.round) }; }),
      statuses: Array.from(l2.querySelectorAll('[role="status"]')).map((s) => { const sb = s.getBoundingClientRect();
        return { t: (s.innerText || '').replace(/\s+/g, ' ').trim(), rect: [sb.x, sb.y, sb.width, sb.height].map(Math.round) }; }),
      groups: Array.from(l2.querySelectorAll('[role="group"]')).map((g) => g.getAttribute('aria-label')) };
  }
  return r;
}, lbl);

// 选宿主：现算落点，命中元素必须落在目标内部
const selectHost = async (id) => {
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
    if (n.classList.contains('selected')) return { already: true };
    const r = n.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 5)
      for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 5) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
    return { __err: 'unreachable' }; }, id);
  if (pt.x) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800); }
  return pt;
};

// 点进提示词框（判据落在 `generation-prompt-editor` 容器上 —— 批次 113 立规）
const focusEditor = () => p.evaluate(() => {
  const host = document.querySelector('[data-testid="generation-prompt-editor"]'); if (!host) return { __err: 'no-host' };
  const r = host.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 2) {
      if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !(el === host || host.contains(el))) continue;
      if (el.closest('button,[role=button],a,input,textarea')) continue;
      return { x, y }; }
  return { __err: 'no-clickable' };
});

out.start = { nodes: await nodeN(), credits: await credits() };
out.inventory = await inventory();
log('起点：', JSON.stringify(out.start));
log('画布节点清单（按类型）：');
for (const [k, v] of Object.entries(out.inventory)) log(`  ${k.padEnd(9)} ${v.length} 个：有资源 ${v.filter((x) => x.hasRes).length} ｜ 例 ${JSON.stringify(v.slice(0, 2))}`);
save();

out.hosts = [];
out.results = [];
for (const [host, hostType] of [[HOST_AUDIO, 'audio'], [HOST_VIDEO, 'video']]) {
  log(`\n########## 宿主：${host}（${hostType}） ##########`);
  const sel = await selectHost(host);
  log('  选中：', JSON.stringify(sel));
  const st = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    return { selected: n.classList.contains('selected'), title: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '' }; }, host);
  log('  状态：', JSON.stringify(st));
  const fe = await focusEditor();
  log('  提示词框落点：', JSON.stringify(fe));
  if (fe.__err) { log('  🔴 点不到提示词框 ⇒ 中止本宿主'); out.hosts.push({ host, hostType, fe }); save(); continue; }
  await p.mouse.click(fe.x, fe.y); await p.waitForTimeout(900);
  const g = await keyGuard(p);
  log('  keyGuard：', g.safe ? '✅' : 'ⓘ unsafe（焦点在编辑器，正是本轮要的）—— 显式放行', g.where || '');
  out.keyGuardWaiver = { granted: true, why: '本轮测试前提就是焦点在编辑器内；只往本批自建节点的提示词里打字；不触发任何生成。' };

  // 清空可能残留的内容（本批自建节点，不影响他人）
  await p.keyboard.press('Meta+a'); await p.waitForTimeout(250);
  await p.keyboard.press('Backspace'); await p.waitForTimeout(700);
  const edTxt = await p.evaluate(() => { const e = document.querySelector('[data-testid="generation-prompt-editor"] .ProseMirror');
    return e ? (e.innerText || '').replace(/\s+/g, ' ').trim() : null; });
  log('  清空后提示词：', JSON.stringify(edTxt));

  await p.keyboard.type('@', { delay: 60 });
  log('  已打 @，等面板…');
  // 密集采样直到一级面板出现（批次 113 记：+1.84s 插入）
  let seen = null;
  for (let k = 0; k < 20; k++) { await p.waitForTimeout(180);
    const r = await readMention(`${hostType}#${k}`);
    if (r.level1) { seen = r; log(`  一级面板在第 ${k} 次采样出现（+${((k + 1) * 0.18).toFixed(2)}s）`); break; } }
  if (!seen) { log('  🔴 一级面板没出现'); out.hosts.push({ host, hostType, noPanel: true }); save(); continue; }
  log('  一级：', JSON.stringify({ rect: seen.level1.rect, role: seen.level1.role, aria: seen.level1.aria, groups: seen.level1.groups }));
  log('  一级选项：', JSON.stringify(seen.level1.options.map((o) => o.t)));
  out.hosts.push({ host, hostType, level1: seen.level1 });

  // 逐个类别：点一级选项 → 读二级
  for (const o of seen.level1.options) {
    // 落点现算：命中元素必须在该 option 内部
    const ok = await p.evaluate((t) => { const el = Array.from(document.querySelectorAll('[data-testid="generation-mention-panel"] [role="option"]'))
      .find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === t);
      if (!el) return { __err: 'gone' };
      const r = el.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy); if (!h || !(h === el || el.contains(h))) return { __err: 'hit', tag: h ? h.tagName : null };
      return { x: cx, y: cy }; }, o.t);
    if (ok.__err) { log(`  ▸ ${o.t}：拿不到可点落点 ${JSON.stringify(ok)}`); out.results.push({ hostType, cat: o.t, fail: ok }); continue; }
    await p.mouse.click(ok.x, ok.y);
    await p.waitForTimeout(1100);
    const r2 = await readMention(`${hostType}-${o.t}`);
    if (!r2.level2) { log(`  ▸ ${o.t}：二级子菜单**没出现**`); out.results.push({ hostType, cat: o.t, noSub: true }); save(); continue; }
    const inv = (out.inventory[o.t] || []);
    log(`  ▸ ${o.t}：二级 ${JSON.stringify(r2.level2.rect)} role=${r2.level2.role} aria=${JSON.stringify(r2.level2.aria)}`);
    log(`      画布上该类型共 ${inv.length} 个（有资源 ${inv.filter((x) => x.hasRes).length}）`);
    log(`      二级 options ${r2.level2.options.length} 条：${JSON.stringify(r2.level2.options.map((x) => x.t).slice(0, 12))}`);
    log(`      二级 status ${r2.level2.statuses.length} 条：${JSON.stringify(r2.level2.statuses.map((x) => x.t))}`);
    log(`      二级 text 逐字：${JSON.stringify(r2.level2.text)}`);
    out.results.push({ hostType, host, cat: o.t, invN: inv.length, invReady: inv.filter((x) => x.hasRes).length,
      level2: r2.level2 });
    save();
  }
  // 收尾：清空提示词，Esc 收起面板
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  await p.keyboard.press('Meta+a'); await p.waitForTimeout(200);
  await p.keyboard.press('Backspace'); await p.waitForTimeout(600);
}

log('\n=== 汇总 ===');
out.summary = out.results.map((r) => ({ host: r.hostType, cat: r.cat, invN: r.invN ?? null, invReady: r.invReady ?? null,
  opts: r.level2 ? r.level2.options.length : null, status: r.level2 ? r.level2.statuses.map((s) => s.t) : null,
  text: r.level2 ? r.level2.text.slice(0, 120) : null }));
log(JSON.stringify(out.summary, null, 1));
out.end = { nodes: await nodeN(), credits: await credits() };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE b');
process.exit(0);

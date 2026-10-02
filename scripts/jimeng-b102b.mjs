// 批次 102 · b 轮：把 a 轮挖到的两样东西读透 —— `accept` 白名单 与 空白右键的「新建节点」子菜单。
//
// a 轮的两个发现：
//   ① 左栏「上传」点开后，那个 `<input type=file>` **带完整 `accept` 白名单**
//      ⇒ 「支持哪些格式」终于有了**机器可读的权威答案**（批次 64 是逐个格式试出来的 20 种视频）
//      且 `multiple` 属性 = `true`、`display:none`、`0×0`、父级是左栏那个
//      `SPAN.inline-flex absolute inset-y-0 z-workspace-chrome-`
//   ② 空白右键**同时**弹出了**两个** `[role=menu]`：
//      `240×172` aria=`Canvas context menu`（4 个可见项 + 9 个空 `192×36` 内嵌项）
//      以及 `200×404` 的**另一个** menu（12 个 `192×36` 项，`innerText` 全空）
//      ⇒ a 轮那次右击**没有悬停到「新建节点」**，子菜单却已经在 DOM 里了
//
// 🔴 本轮**只读不点**：子菜单里若有「文本」「图片」等项，**点一下就会建节点**。
//    只做「读」+「悬停」，绝不点子菜单项。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// ================= ① accept 白名单分类 =================
out.accept = await p.evaluate(() => {
  const inp = document.querySelector('input[type=file]');
  if (!inp) return { none: true };
  const raw = inp.getAttribute('accept') || '';
  const toks = raw.split(',').map((s) => s.trim()).filter(Boolean);
  const byPrefix = {};
  for (const t of toks) {
    const isExt = t.startsWith('.');
    const mime = isExt ? '(ext)' : t.split('/')[0];
    byPrefix[mime] = byPrefix[mime] || { count: 0, exts: [], mimes: [] };
    byPrefix[mime].count++;
    if (isExt) byPrefix[mime].exts.push(t.slice(1)); else byPrefix[mime].mimes.push(t);
  }
  const extSet = new Set(toks.filter((t) => t.startsWith('.')).map((t) => t.slice(1).toLowerCase()));
  return {
    total: toks.length, uniqExt: extSet.size,
    byPrefix,
    extSorted: Array.from(extSet).sort(),
    // 找重复：同一个扩展名在白名单里出现两次的（wma 就有一个坑）
    dupExt: (() => { const seen = new Map();
      for (const t of toks.filter((x) => x.startsWith('.'))) seen.set(t, (seen.get(t) || 0) + 1);
      return Array.from(seen.entries()).filter(([, n]) => n > 1); })(),
    // 反过来：哪些 mime 没有配套扩展名
    mimesWithoutExt: toks.filter((t) => !t.startsWith('.')).filter((t) => {
      const sub = t.split('/')[1] || ''; return ![...extSet].some((e) => e.includes(sub) || sub.includes(e)); }),
  };
});
log('=== accept 白名单 ===');
log('  条目总数', out.accept.total, '｜去重后扩展名', out.accept.uniqExt, '｜重复扩展名', JSON.stringify(out.accept.dupExt));
for (const [k, v] of Object.entries(out.accept.byPrefix))
  log(`  ${k.padEnd(18)} ${String(v.count).padStart(3)} 条｜扩展名(${v.exts.length}): ${v.exts.join(' ')}`);

// ================= ② 空白右键 → 新建节点 子菜单（只读 + 悬停） =================
log('\n=== 空白右键 → 新建节点 ===');
{
  const blank = await p.evaluate(() => {
    const bad = (x, y) => { const el = document.elementFromPoint(x, y);
      if (!el || el.closest('.react-flow__node')) return true;
      if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
      if (el.closest('button,[role=button],input,a')) return true; return false; };
    for (let y = 280; y < 620; y += 16) for (let x = 260; x < 1100; x += 16) if (!bad(x, y)) return [x, y];
    return null; });
  await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(400);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1000);

  // 先记「悬停前」两个 menu 的状态
  out.beforeHover = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menu]')).map((m) => {
    const r = m.getBoundingClientRect();
    return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      aria: m.getAttribute('aria-label'), items: m.querySelectorAll('[role=menuitem]').length,
      visible: r.width > 0 && r.height > 0 }; }));
  log('悬停前：', JSON.stringify(out.beforeHover));

  // 找到「新建节点」这一项并**悬停**（不点）
  const nj = await p.evaluate(() => {
    for (const m of document.querySelectorAll('[role=menu]')) for (const it of m.querySelectorAll('[role=menuitem]')) {
      if ((it.innerText || '').trim().startsWith('新建节点')) { const r = it.getBoundingClientRect();
        return { point: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
          attrs: Array.from(it.attributes).map((a) => `${a.name}=${a.value}`).slice(0, 8) }; } }
    return null; });
  log('「新建节点」项：', JSON.stringify(nj));
  if (nj) {
    await p.mouse.move(nj.point[0], nj.point[1]); await p.waitForTimeout(400);
    await p.mouse.move(nj.point[0] + 3, nj.point[1]); await p.waitForTimeout(1200);
  }

  out.afterHover = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menu]')).map((m) => {
    const r = m.getBoundingClientRect();
    // 逐项读全：innerText / textContent / aria-label / testid / 尺寸 / 是否禁用
    const items = Array.from(m.querySelectorAll('[role=menuitem]')).map((e) => { const q = e.getBoundingClientRect();
      return { innerText: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        textContent: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
        disabled: e.getAttribute('aria-disabled') === 'true',
        rect: `${Math.round(q.x)},${Math.round(q.y)} ${Math.round(q.width)}×${Math.round(q.height)}`,
        hasImg: !!e.querySelector('img,svg') }; });
    return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      aria: m.getAttribute('aria-label'), testid: m.getAttribute('data-testid'),
      n: items.length, items };
  }));
  log('悬停后：');
  for (const m of out.afterHover) {
    log(`  menu rect=${m.rect} aria=${m.aria} testid=${m.testid} n=${m.n}`);
    for (const it of m.items) log(`     innerText=${JSON.stringify(it.innerText)} text=${JSON.stringify(it.textContent)} aria=${it.aria} tid=${it.tid} dis=${it.disabled} ${it.rect}`);
  }

  // 关掉菜单，别留着污染下一轮
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
}

out.end = { nodes: await nodeN() };
log('\n终态 nodes：', out.end.nodes);
writeFileSync(new URL('./_tmp-b102b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();

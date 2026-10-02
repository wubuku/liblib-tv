// 批次 114 · a 轮：造**两个**宿主节点（空音频 + 空视频）。
//
// 靶子：`@` 二级子菜单的「暂无相关节点」成因。三处都记着同一条悬案：
//   `20-reference.md`「二级子菜单」/ `prepare-generation.md:216`
//   「🔴 空列表成因**未能确认**（空节点被排除 / 当前节点自身被排除 / 两者叠加）
//    —— 观测条件下画布只有一个空的『视频 1』」
//
// b114pre 轮（只读）读到的画布现状，恰好构成一组**干净对照**：
//   · 音频 68 个，**全部 `audio-node-empty`（全空）**、有资源 0 个
//   · 视频 1 个（`video-node-empty`，空）
//   · 图片 1 个（`b22-upload`，**有资源**，`image-node-result` + `image-primary-preview-viewport`）
//   · 主体 **0 个**
//   · 文本 3、时间线 2、导演台 1
// ⇒ 判据就是一句：**二级子菜单列出的条目数，能不能用「该类型节点数 − 空节点数」
//   解释。** 四个类别的 (总数, 空, 有资源) 各不相同，四条约束叠起来只有一个解。
//
// 🔴 护栏：两个节点**分两次造**，每次各自存 idsBefore、各自校验「差集恰好一个
//    且同时 .selected」—— 一次造两个会让差集变成 2，护栏就废了。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b114a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// 找一个**当下**可用的空白落点（按动作时刻现算）
const findBlank = () => p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a')) return true;
    return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return [x, y];
  return null; });

out.start = { nodes: await nodeN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
save();

const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// 造一个节点：空白右键 → 新建节点 → <类型>
async function makeNode(typeName) {
  const blank = await findBlank();
  log(`\n=== 造「${typeName}」｜空白落点 ${JSON.stringify(blank)} ===`);
  if (!blank) { log('  🔴 找不到可用空白'); return null; }
  await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(400);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1300);
  const nj = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]'))
    for (const it of m.querySelectorAll('[role=menuitem]')) {
      if ((it.innerText || '').trim().startsWith('新建节点')) { const r = it.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } return null; });
  if (!nj) { log('  🔴 找不到「新建节点」'); await p.keyboard.press('Escape'); return null; }
  await p.mouse.move(nj.x, nj.y); await p.waitForTimeout(500);
  await p.mouse.move(nj.x + 3, nj.y); await p.waitForTimeout(1500);
  // 「找 + 校验」放同一次 evaluate（批次 113 立规）
  const target = await p.evaluate((tn) => { for (const m of document.querySelectorAll('[role=menu]')) {
      if (getComputedStyle(m).visibility === 'hidden') continue;
      for (const it of m.querySelectorAll('[role=menuitem]')) { if ((it.innerText || '').trim() !== tn) continue;
        const r = it.getBoundingClientRect(); if (r.width < 1) continue;
        const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
        const h = document.elementFromPoint(cx, cy); if (!h || !(h === it || it.contains(h))) continue;
        return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], hit: h.tagName }; } }
    return { __err: 'no-clickable' }; }, typeName);
  if (target.__err) { log('  🔴 拿不到可点的「' + typeName + '」', JSON.stringify(target)); await p.keyboard.press('Escape'); return null; }
  log('  落点：', JSON.stringify(target));
  await p.mouse.click(target.rect[0] + target.rect[2] / 2, target.rect[1] + target.rect[3] / 2);
  log(`  已点「${typeName}」`);
  return true;
}

out.made = [];
for (const tn of ['音频', '视频']) {
  const idsBefore = await allIds();
  const ok = await makeNode(tn);
  if (!ok) { out.made.push({ type: tn, failed: true }); save(); continue; }
  let SELF = null, guard = null;
  for (let k = 1; k <= 16; k++) {
    await p.waitForTimeout(1200);
    const ids = await allIds();
    const diff = ids.filter((id) => !idsBefore.includes(id));
    if (diff.length === 1) {
      const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
      guard = { diff, sel, ok: sel.includes(diff[0]) };
      if (guard.ok) { SELF = diff[0]; break; }
    } else if (diff.length > 1) { log('  ⛔ 差集超过一个，中止：', JSON.stringify(diff)); break; }
  }
  log(`  护栏②：${JSON.stringify(guard)} ⇒ ${SELF ? '✅ ' + SELF : '🔴'}`);
  out.made.push({ type: tn, self: SELF, guard, idsBeforeN: idsBefore.length });
  save();
  if (!SELF) { log('  🔴 没建出来，中止后续'); break; }
  // 读一下这个节点，确认类型对
  const st = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
    return { cls: (n.getAttribute('class') || '').toString().match(/react-flow__node-(\w+)/)?.[1] || null,
      inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90),
      tids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
      rect: (() => { const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() }; }, SELF);
  log('  节点状态：', JSON.stringify(st));
  out.made[out.made.length - 1].state = st;
  save();
}

out.end = { nodes: await nodeN(), credits: await credits() };
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE a');
process.exit(0);

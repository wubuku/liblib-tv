// 批次 62 第三轮：补上第二轮被我自己挡掉的两项（`/` 与 `@`），并取配图。
//
// 第二轮的中止点是**我自己的错**，值得留档：
//   第 2 轮点「使用技能」弹出 `canvas-agent-skill-picker`（**role=dialog，360×372@896,274**），
//   它**盖住了输入框**（输入框 890,554 落在 dialog 的 274~646 之内）。
//   第 3 轮开头我 `clearComposer()` 清掉了输入框内容，**但没关 dialog**，
//   于是 `elementFromPoint(910,574)` 命中的是 dialog 而不是 composer ——
//   `landed:false` ⇒ 脚本正确地拒绝继续。**这正是「阴性结果先问前置条件」在起作用。**
//
// 🔑 第二轮还纠正了第一轮的两个假阳性：
//   ① `canvas-agent-composer-mention` **不是 mention 弹层**，它是输入卡底部
//      **aria 逐字「引用参考」的 @ 按钮**（32×32@1020,654），**恒存在**。
//      拿它当判据 ⇒ 任何时刻都判「弹层已出现」。
//   ② 点 skill chip 走的是**同步**路径（第二轮 t=0 即生效，AddingSkill 全程 0），
//      第一轮读到的「滞后」是**连点 5 个 chip 把状态堆脏**造成的，不是产品行为。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b62-round3.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const skillPicker = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-agent-skill-picker"]');
  if (!e) return null; const r = e.getBoundingClientRect();
  if (r.width < 1) return null;
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, role: e.getAttribute('role'),
    parentTag: e.parentElement.tagName, inPanel: !!e.closest('[data-testid="canvas-agent-panel"]'),
    rows: Array.from(e.querySelectorAll('[data-testid^="canvas-agent-skill-row-"]')).map((x) => { const b = x.getBoundingClientRect();
      return { tid: x.getAttribute('data-testid'), title: (x.querySelector('[data-testid^="canvas-agent-skill-title-"]') || {}).innerText,
        official: !!x.querySelector('[data-testid^="canvas-agent-skill-official-"]'),
        hasMore: !!x.querySelector('[class*="option-more"]'),
        y: Math.round(b.y), h: Math.round(b.height), visible: b.height > 1 && b.top < innerHeight && b.bottom > 0,
        desc: (x.querySelector('[data-testid^="canvas-agent-skill-description-"]') || {}).innerText }; }),
    search: (() => { const s = e.querySelector('[data-testid="canvas-agent-skill-search"] input, [data-testid="canvas-agent-skill-search"]');
      if (!s) return null; const b = s.getBoundingClientRect();
      return { box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`, value: s.value !== undefined ? s.value : s.innerText }; })(),
    footer: (e.querySelector('[data-testid="canvas-agent-skill-picker-footer"]') || {}).innerText,
    overflow: (() => { const l = e.querySelector('[data-testid="canvas-agent-skill-picker-list"]');
      if (!l) return null; return { scrollH: l.scrollHeight, clientH: l.clientHeight, scrollable: l.scrollHeight > l.clientHeight + 1 }; })() };
});
const composer = () => p.evaluate(() => {
  const c = document.querySelector('[data-testid="prompt-composer"] [contenteditable="true"], [data-testid="prompt-composer"], [contenteditable="true"]');
  if (!c) return null; const r = c.getBoundingClientRect();
  const chips = Array.from(c.querySelectorAll('[data-testid="agent-skill-chip"]')).map((x) => { const b = x.getBoundingClientRect();
    return { text: (x.innerText || '').trim(), box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}` }; });
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    text: (c.innerText || '').replace(/\n+$/, ''), chips, tid: c.getAttribute('data-testid') };
});
// 主体/参考弹层：找**非技能**的候选 dialog/listbox
const otherPop = () => p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[data-testid*="mention"],[data-testid*="subject"],[data-testid*="reference"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { tid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 260) }; }));

const openDrawer = async () => { const s = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
    .find((x) => /与\s*AI\s*对话/.test(x.getAttribute('aria-label') || '')); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (!s) return 'nobtn'; await p.mouse.click(s.cx, s.cy); await p.waitForTimeout(1500); return 'ok'; };
const clickRe = async (re) => { const h = await p.evaluate((src) => { const rx = new RegExp(src);
    const e = Array.from(document.querySelectorAll('button,[role="button"]')).filter((x) => { const r = x.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
      .find((x) => rx.test(x.getAttribute('aria-label') || '') || rx.test((x.innerText || '').trim()));
    if (!e) return null; const r = e.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const o = (document.elementFromPoint(cx, cy) || {}).closest?.('button,[role="button"]');
    return { cx, cy, aria: e.getAttribute('aria-label'), ok: !!o && (o === e || e.contains(o)) }; }, re.source);
  if (!h) return { ok: false, why: 'notfound' }; if (!h.ok) return { ok: false, why: 'occluded', h };
  await p.mouse.click(h.cx, h.cy); await p.waitForTimeout(900); return h; };
// 🔑 故意往 composer 里打 `/` 或 `@`：**这正是本轮要观察的东西**。
// keyGuard 会拒绝（焦点在输入面）—— 这里的拒绝恰恰是正确的默认，
// 我要的是「明确知道自己在往哪里打字」，所以先断言落点属于 composer，再按键。
const focusComposer = async () => {
  const c = await p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] [contenteditable="true"], [contenteditable="true"]');
    if (!e) return null; e.scrollIntoView({ block: 'center' }); const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + 24), cy: Math.round(r.y + 24), tid: e.getAttribute('data-testid') }; });
  if (!c) return { ok: false, why: 'nocomp' };
  const landed = await p.evaluate(([x, y]) => { const t = document.elementFromPoint(x, y);
    const ce = document.querySelector('[data-testid="prompt-composer"] [contenteditable="true"], [contenteditable="true"]');
    return { tag: t && t.tagName, isInside: !!(t && ce && ce.contains(t)) }; }, [c.cx, c.cy]);
  if (!landed.isInside) return { ok: false, why: 'occluded', c, landed };
  await p.mouse.click(c.cx, c.cy); await p.waitForTimeout(450);
  const g = await keyGuard(p);
  const real = await p.evaluate(() => { const a = document.activeElement;
    return { ce: !!a && (a.closest('[contenteditable]') !== null), tid: a && a.getAttribute('data-testid') }; });
  return { ok: real.ce, c, landed, keyGuardSays: g, focus: real };
};
const clearComposer = async () => { await p.evaluate(() => { const c = document.querySelector('[contenteditable="true"]');
  if (c) { c.focus(); c.innerHTML = ''; c.dispatchEvent(new InputEvent('input', { bubbles: true, data: '', inputType: 'deleteContentBackward' })); } });
  await p.waitForTimeout(350); return (await composer()).text; };
const shot = async (name) => { const f = new URL(name, SHOTS); await p.screenshot({ path: f.pathname, clip: { x: 860, y: 8, width: 412, height: 700 } }); console.log('  📷', name); return name; };
const drawerOpen = async () => !!(await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-agent-panel"]');
  return e && e.getBoundingClientRect().width > 1; }));
// 🔑 上一版就是死在这里：我假设「开场抽屉是关着的」，于是先 Esc 再 openDrawer 再 Esc ——
// 第二轮崩在中途没跑收尾，抽屉**当时是开着的**；第一个 Esc 关上抽屉，openDrawer 重新打开，
// 第二个 Esc 又把它关掉 ⇒ 全程对着空气点「使用技能」。
// 教训：**Esc 是盲操作，状态要读不要猜。** 改成「读到什么才关什么」，并且每一步都断言。
const closeAll = async (max = 6) => { const log = [];
  for (let i = 0; i < max; i++) { const pk = (await skillPicker()) !== null; const dr = await drawerOpen();
    if (!pk && !dr) { log.push('(已全关)'); return log; }
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
    log.push(`Esc#${i + 1} 关掉 ${[pk && 'skill-picker', dr && 'drawer'].filter(Boolean).join('+')}`); }
  return log; };

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 62 第三轮：技能选择器 / `/` / `@` ===\n起点:', await statusLine(), '| 积分', c0);
out.creditStart = c0;

// ── 0. 先把残留的浮层/抽屉**按实际状态**关掉，再显式开抽屉并断言
console.log('开场状态: drawer =', await drawerOpen(), '| skill-picker =', (await skillPicker()) !== null);
console.log('清场:', JSON.stringify(await closeAll()));
console.log('清场后 drawer =', await drawerOpen());
if (await drawerOpen()) { console.error('ABORT: 清场没成功'); await b.close(); process.exit(8); }
await openDrawer();
const opened = await drawerOpen();
console.log('开抽屉后 drawer =', opened);
if (!opened) { console.error('ABORT: 抽屉没打开'); await b.close(); process.exit(9); }
const comp0 = await composer();
console.log('\n--- 空态 composer ---'); console.log(' ', JSON.stringify(comp0));
if (!comp0) { console.error('ABORT: composer 读不到'); await b.close(); process.exit(10); }
await shot('62-agent-empty.png');

// ── 1. 「使用技能」→ 技能选择器（完整读数 + 搜索过滤）
console.log('\n【A】「使用技能」按钮 → 技能选择器');
const hA = await clickRe(/^使用技能$/);
await p.waitForTimeout(1200);
let sp = await skillPicker();
console.log('  点击:', JSON.stringify(hA));
if (!sp) { console.error('ABORT: 技能选择器没开'); await b.close(); process.exit(11); }
console.log('  dialog:', sp.box, '| role=', sp.role, '| 在 canvas-agent-panel 内?', sp.inPanel, '| 父元素 <', sp.parentTag, '>');
console.log('  搜索框:', JSON.stringify(sp.search));
console.log('  footer:', JSON.stringify(sp.footer));
console.log('  列表滚动:', JSON.stringify(sp.overflow));
console.log('  技能行', sp.rows.length, '条:');
for (const r of sp.rows) console.log(`    y=${String(r.y).padStart(3)} h=${r.h} 可见=${r.visible} 官方=${r.official} more=${r.hasMore}  «${r.title}»  ${r.desc ? r.desc.slice(0, 40) : ''}`);
out.skillPicker = sp;
await shot('62-agent-skill-picker.png');

// 搜索过滤（纯 UI，不发送）
const spBox = await p.evaluate(() => { const s = document.querySelector('[data-testid="canvas-agent-skill-search"] input, [data-testid="canvas-agent-skill-search"]');
  if (!s) return null; s.scrollIntoView({ block: 'center' }); const r = s.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
if (spBox) {
  const land = await p.evaluate(([x, y]) => { const t = document.elementFromPoint(x, y); const s = document.querySelector('[data-testid="canvas-agent-skill-search"] input, [data-testid="canvas-agent-skill-search"]');
    return { tag: t && t.tagName, inside: !!(t && s && (s === t || s.contains(t) || (t.closest('input') && t.closest('input') === s))) }; }, [spBox.cx, spBox.cy]);
  console.log('\n  搜索框落点:', JSON.stringify(land));
  if (land.inside) {
    await p.mouse.click(spBox.cx, spBox.cy); await p.waitForTimeout(300);
    await p.keyboard.type('海报', { delay: 70 }); await p.waitForTimeout(1100);
    sp = await skillPicker();
    console.log('  输入「海报」后 → 行数', sp.rows.length, ':', sp.rows.map((r) => r.title).join(' / '));
    await shot('62-agent-skill-search.png');
    out.skillSearch = { query: '海报', rows: sp.rows.map((r) => r.title) };
    // 还原搜索词
    await p.keyboard.press('Backspace'); await p.keyboard.press('Backspace'); await p.waitForTimeout(900);
    sp = await skillPicker();
    console.log('  退格还原后 → 行数', sp.rows.length);
  }
}
// 关闭 dialog
await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
const spAfter = await skillPicker();
console.log('  Esc 后 skill-picker =', spAfter === null ? 'null ✓ 关闭成功' : '还在 ✗');
console.log('  Esc 后 drawer 仍在 =', await drawerOpen(), '（要断言：Esc 只关弹层、不关抽屉）');
out.pickerClosedByEsc = spAfter === null;
out.drawerSurvivedEsc = await drawerOpen();

// ── 2. 空输入框按 `/`
console.log('\n【B】空输入框按「/」');
console.log('  清空 composer ->', JSON.stringify(await clearComposer()));
const fB = await focusComposer();
console.log('  聚焦:', JSON.stringify(fB));
if (!fB.ok) { console.error('ABORT: 聚焦失败', JSON.stringify(fB)); await b.close(); process.exit(6); }
console.log('  (keyGuard 的判定:', JSON.stringify(fB.keyGuardSays.reason), '—— 本轮**故意**要往输入框打字,落点已断言属于 composer)');
await p.keyboard.press('/');
const serB = [];
for (const t of [0, 300, 700, 1200, 2000, 3000]) { const w = t - (serB.length ? [0, 300, 700, 1200, 2000, 3000][serB.length - 1] : 0); if (w > 0) await p.waitForTimeout(w);
  const s = { t, picker: (await skillPicker()) ? 'YES' : 'no', other: (await otherPop()).map((x) => x.tid || x.role), comp: (await composer()).text };
  serB.push(s); console.log(`    t=${String(t).padStart(4)}ms picker=${s.picker} other=${JSON.stringify(s.other)} composer=${JSON.stringify(s.comp)}`); }
out.slash = serB;
const pickerAfterSlash = (await skillPicker()) !== null;
console.log('  => 按「/」后技能选择器出现?', pickerAfterSlash ? 'YES' : 'no', pickerAfterSlash ? '<< 与「使用技能」按钮同一个' : '');

if (pickerAfterSlash) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
await p.evaluate(() => { const c = document.querySelector('[contenteditable="true"]'); if (c) { c.focus(); c.innerHTML = ''; c.dispatchEvent(new InputEvent('input', { bubbles: true, data: '', inputType: 'deleteContentBackward' })); } });
await p.waitForTimeout(400);

// ── 3. 空输入框按 `@`
console.log('\n【C】空输入框按「@」（主体引用）');
console.log('  清空 composer ->', JSON.stringify(await clearComposer()));
const fC = await focusComposer();
console.log('  聚焦 ok =', fC.ok, '| 落点 =', JSON.stringify(fC.landed));
if (!fC.ok) { console.error('ABORT: 聚焦失败', JSON.stringify(fC)); await b.close(); process.exit(7); }
const beforeAt = await otherPop();
console.log('  按「@」前可见 pop:', JSON.stringify(beforeAt));
await p.keyboard.press('@');
const serC = [];
const TT = [0, 300, 700, 1200, 2000, 3000, 4500];
for (const t of TT) { const w = t - (serC.length ? TT[serC.length - 1] : 0); if (w > 0) await p.waitForTimeout(w);
  const s = { t, picker: (await skillPicker()) ? 'YES' : 'no', other: await otherPop(), comp: (await composer()).text };
  serC.push(s); console.log(`    t=${String(t).padStart(4)}ms picker=${s.picker} composer=${JSON.stringify(s.comp)}`); for (const o of s.other) console.log(`        pop: ${JSON.stringify(o)}`); }
out.at = serC;
await shot('62-agent-at.png');

// ── 4. 点一个 skill chip → 带 chip 的 composer 配图
console.log('\n【D】点 skill chip 后的输入卡');
console.log('  清空 ->', JSON.stringify(await clearComposer()));
console.log('  确保弹层已关:', JSON.stringify(await closeAll(3)), '| drawer =', await drawerOpen());
const hD = await clickRe(/^视频反解$|^\/\s*视频反解$/);
await p.waitForTimeout(1300);
const cd = await composer();
console.log('  点击:', JSON.stringify(hD));
console.log('  composer:', cd.box, '| text =', JSON.stringify(cd.text), '| chips =', JSON.stringify(cd.chips));
out.chip = { click: hD, composer: cd };
await shot('62-agent-skill-chip.png');

const c1 = await credit();
console.log('\n=== 积分全程 ===', c0, '->', c1, 'Δ=', c1 - c0);
out.creditEnd = c1;

// ── 收尾
const finText = await clearComposer();
console.log('收尾 composer 文本 =', JSON.stringify(finText), finText.trim() ? '<< 仍有残留 ✗' : '<< 已清空 ✓');
await p.evaluate(() => { const c = document.querySelector('[contenteditable="true"]'); if (c) c.blur(); });
await p.waitForTimeout(300);
const hZ = await clickRe(/^收起$/);
console.log('点收起:', JSON.stringify(hZ));
await p.waitForTimeout(1100);
for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(280); }
console.log('终态:', await statusLine(), '| 积分', await credit(), '| skill-picker =', (await skillPicker()) === null ? 'null' : '还在',
  '| otherPop =', JSON.stringify(await otherPop()));
out.end = { status: await statusLine(), credit: await credit(), composerLeft: finText, picker: (await skillPicker()) === null };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();

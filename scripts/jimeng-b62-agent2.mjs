// 批次 62 第二轮：修正第一轮的三处变量混淆。
//
// 第一轮读出来的东西里，有三处是我自己制造的坑：
//
//   ① **异步滞后被读成了「没反应」**。点 chip 后输入框走异步（chips 区冒 `Adding skill`），
//      我只等 1.2s。chip4「剧本开发」、chip5「剧情短片」的 value 读数**卡在前一个值**上，
//      直到我点「使用技能」时「剧本开发」才落地 —— 于是我以为「使用技能」= 填入技能名。
//      **那是前一个动作的尾巴，不是这个动作的效果。**
//   ② **连点 5 个 chip 把状态堆脏了**，chip5 的真实结果根本没测到。
//   ③ **`canvas-agent-composer-mention` 是恒存在且 text 恒为空的常驻元素**。
//      拿「有没有这个弹层」当判据，就会得到 **`@` 唤起了 mention 弹层** 的假阳性 ——
//      批次 58 在质量门上栽过一次，这里差点在取证上重演。
//
// 所以第二轮：**一个变量一轮，密集采样异步态，并给「真的弹出了列表」配阳性对照**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const OUT = new URL('./_tmp-b62-round2.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);

// 抽屉状态快照：一次拿全所有需要的读数
const snap = () => p.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
  const cands = Array.from(document.querySelectorAll('div,aside,section')).filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width >= 340 && r.width <= 460 && r.right >= innerWidth - 12 && r.height >= innerHeight * 0.6 && vis(e); });
  let root = cands[0];
  for (const c of cands) if (root && !c.contains(root)) root = c;
  if (!root) return { open: false };
  const comp = root.querySelector('[contenteditable="true"],textarea,input');
  // **全文档**找 agent/composer/skill/mention 相关浮层（不能只搜抽屉内 —— 浮层可能挂在 body 上）
  const floats = Array.from(document.querySelectorAll('[data-testid],[role="listbox"],[role="menu"],[role="dialog"]'))
    .filter((e) => { const t = ((e.getAttribute('data-testid') || '') + ' ' + (e.getAttribute('role') || '')).toLowerCase();
      return vis(e) && /agent|composer|skill|mention|suggest|popover|dropdown|popup|command|slash/.test(t); })
    .map((e) => { const r = e.getBoundingClientRect();
      return { tid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
        box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        kids: e.children.length, inDrawer: root.contains(e),
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) }; });
  const chips = Array.from(root.querySelectorAll('button')).filter(vis)
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
        box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
  return {
    open: true, drawer: (() => { const r = root.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; })(),
    composer: comp ? { aria: comp.getAttribute('aria-label'), ce: comp.getAttribute('contenteditable'),
      value: comp.value !== undefined ? comp.value : (comp.innerText || '').replace(/\n$/, '') } : null,
    adding: (root.innerText || '').split('Adding skill').length - 1,
    chips, floats,
    text: (root.innerText || '').replace(/\n{2,}/g, '\n').trim(),
  };
});
// 密集采样：t = 0,250,500,900,1400,2000,2800,3800,5000
const dense = async (label, ms = 5000) => {
  const ts = [0, 250, 500, 900, 1400, 2000, 2800, 3800, 5000].filter((t) => t <= ms);
  const series = [];
  const t0 = Date.now();
  for (const t of ts) { const w = t0 + t - Date.now(); if (w > 0) await new Promise((r) => setTimeout(r, w));
    const s = await snap();
    series.push({ t, composer: s.composer ? s.composer.value : null, adding: s.adding,
      floatKinds: s.floats.filter((f) => f.kids > 0).map((f) => f.tid || f.role), nFloat: s.floats.length }); }
  console.log(`  [${label}] 密集采样:`);
  for (const s of series) console.log(`    t=${String(s.t).padStart(4)}ms  composer=${JSON.stringify(s.composer)}  AddingSkill×${s.adding}  浮层(有子元素)=${JSON.stringify(s.floatKinds)}`);
  return series;
};
const clearComposer = async () => {
  const ok = await p.evaluate(() => { const c = document.querySelector('[contenteditable="true"],textarea,input');
    if (!c) return 'nocomp';
    c.focus();
    if (c.value !== undefined) { c.value = ''; c.dispatchEvent(new Event('input', { bubbles: true })); return 'value'; }
    c.innerHTML = ''; c.dispatchEvent(new InputEvent('input', { bubbles: true, data: '', inputType: 'deleteContentBackward' })); return 'html'; });
  await p.waitForTimeout(400);
  const s = await snap();
  return { method: ok, value: s.composer ? s.composer.value : null, cleared: s.composer && !s.composer.value.trim() };
};
const openDrawer = async () => { const s = await snap(); if (s.open) return 'already';
  const rb = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role="button"]'))
      .find((x) => /与\s*AI\s*对话/.test(x.getAttribute('aria-label') || ''));
    if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (!rb) return 'nobtn'; await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(1500); return 'clicked'; };
const clickRe = async (re) => { const h = await p.evaluate((src) => { const rx = new RegExp(src);
    const e = Array.from(document.querySelectorAll('button,[role="button"]')).filter((x) => { const r = x.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
      .find((x) => rx.test(x.getAttribute('aria-label') || '') || rx.test((x.innerText || '').trim()));
    if (!e) return null; const r = e.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2); const top = document.elementFromPoint(cx, cy);
    const owner = top && top.closest('button,[role="button"]');
    return { cx, cy, aria: e.getAttribute('aria-label'), ok: !!owner && (owner === e || e.contains(owner)) }; }, re.source);
  if (!h) return { ok: false, why: 'notfound' }; if (!h.ok) return { ok: false, why: 'occluded', h };
  await p.mouse.click(h.cx, h.cy); return h; };

const out = { startedAt: new Date().toISOString(), rounds: [] };
const c0 = await credit();
console.log('=== 批次 62 第二轮：一个变量一轮 ===\n起点:', await statusLine(), '| 积分', c0, '\n');
out.creditStart = c0;
console.log('打开抽屉:', await openDrawer());

// ── 基准：什么都没点时的浮层清单（这就是「恒存在」元素的基线）
let s0 = await snap();
console.log('\n【基准 · 未点任何东西】composer =', JSON.stringify(s0.composer && s0.composer.value));
console.log('  浮层清单:'); for (const f of s0.floats) console.log('    ', JSON.stringify(f));
out.floatsBaseline = s0.floats;
out.composerInitial = s0.composer;

// ── 第 1 轮：清空 → 单点一个 chip → 密集采样
console.log('\n【第 1 轮】清空输入框，单点 chip「/ 视频反解」，密集采样');
console.log('  清空:', JSON.stringify(await clearComposer()));
const h1 = await clickRe(/^视频反解$|^\/\s*视频反解$/);
console.log('  点击:', JSON.stringify(h1));
const r1 = await dense('单点视频反解', 5000);
const s1 = await snap();
console.log('  终态 chips 区:'); for (const c of s1.chips) console.log('    ', JSON.stringify(c));
console.log('  终态浮层:'); for (const f of s1.floats) console.log('    ', JSON.stringify(f));
console.log('  终态全文:\n' + s1.text.split('\n').map((x) => '    | ' + x).join('\n'));
out.rounds.push({ name: 'chip-视频反解', click: h1, series: r1, end: s1 });

// ── 第 2 轮：清空 → 单独点「使用技能」（输入框为空时）
console.log('\n【第 2 轮】清空输入框（保持空），单独点「使用技能」');
console.log('  清空:', JSON.stringify(await clearComposer()));
const h2 = await clickRe(/^使用技能$/);
console.log('  点击:', JSON.stringify(h2));
const r2 = await dense('使用技能', 5000);
const s2 = await snap();
console.log('  终态全文:\n' + s2.text.split('\n').map((x) => '    | ' + x).join('\n'));
console.log('  终态浮层:'); for (const f of s2.floats) console.log('    ', JSON.stringify(f));
out.rounds.push({ name: 'use-skill-button', click: h2, series: r2, end: s2 });

// ── 第 3 轮：清空 → 在空输入框按 `/`
console.log('\n【第 3 轮】清空后按「/」（空输入框 + 光标在开头）');
console.log('  清空:', JSON.stringify(await clearComposer()));
const cc = await p.evaluate(() => { const c = document.querySelector('[contenteditable="true"],textarea,input'); c.focus();
  const s = window.getSelection(); const r = document.createRange(); r.selectNodeContents(c); r.collapse(true); s.removeAllRanges(); s.addRange(r);
  const b = c.getBoundingClientRect(); return { cx: Math.round(b.x + 20), cy: Math.round(b.y + 20) }; });
await p.mouse.click(cc.cx, cc.cy); await p.waitForTimeout(400);
const h3 = await p.evaluate(() => { const c = document.querySelector('[contenteditable="true"],textarea,input'); c.focus();
  const b = c.getBoundingClientRect(); const t = document.elementFromPoint(Math.round(b.x + 20), Math.round(b.y + 20));
  return { landed: !!(t && c.contains(t)), tag: t && t.tagName }; });
console.log('  光标落点确认（必须属于输入框，否则读数不算）:', JSON.stringify(h3));
if (!h3.landed) { console.error('ABORT: 落点不属于输入框'); await b.close(); process.exit(4); }
await p.keyboard.press('/');
const r3 = await dense('空框按斜杠', 5000);
const s3 = await snap();
console.log('  终态浮层:'); for (const f of s3.floats) console.log('    ', JSON.stringify(f));
console.log('  终态全文:\n' + s3.text.split('\n').map((x) => '    | ' + x).join('\n'));
out.rounds.push({ name: 'slash-in-empty', landing: h3, series: r3, end: s3 });

// ── 第 4 轮：清空 → 在空输入框按 `@`
console.log('\n【第 4 轮】清空后按「@」（主体引用）');
console.log('  清空:', JSON.stringify(await clearComposer()));
await p.mouse.click(cc.cx, cc.cy); await p.waitForTimeout(400);
const h4 = await p.evaluate(() => { const c = document.querySelector('[contenteditable="true"],textarea,input'); c.focus();
  const b = c.getBoundingClientRect(); const t = document.elementFromPoint(Math.round(b.x + 20), Math.round(b.y + 20));
  return { landed: !!(t && c.contains(t)) }; });
if (!h4.landed) { console.error('ABORT: 落点不属于输入框'); await b.close(); process.exit(5); }
await p.keyboard.press('@');
const r4 = await dense('空框@', 6000);
const s4 = await snap();
console.log('  终态浮层:'); for (const f of s4.floats) console.log('    ', JSON.stringify(f));
console.log('  终态全文:\n' + s4.text.split('\n').map((x) => '    | ' + x).join('\n'));
out.rounds.push({ name: 'at-in-empty', series: r4, end: s4 });

const c1 = await credit();
console.log('\n=== 积分全程 ===', c0, '->', c1, 'Δ=', c1 - c0);
out.creditEnd = c1;

// ── 收尾：清空草稿 + 关抽屉
const clean = await clearComposer();
console.log('\n收尾清空 composer:', JSON.stringify(clean));
await p.evaluate(() => { const c = document.querySelector('[contenteditable="true"],textarea,input');
  if (c) c.blur(); });
await p.waitForTimeout(300);
const h5 = await clickRe(/^收起$/);
console.log('点收起:', JSON.stringify(h5));
await p.waitForTimeout(1200);
for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
console.log('终态:', await statusLine(), '| 积分', await credit(), '| 抽屉 open =', (await snap()).open);
out.end = { status: await statusLine(), credit: await credit(), drawerOpen: (await snap()).open, cleanup: clean };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();

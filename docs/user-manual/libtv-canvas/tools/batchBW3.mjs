// Batch BW3 — 补上「画布 2 ▾」这个下拉（BW2 点的是外层 div，正文 0 变化 = 根本没开）。
//
// BW2 的教训写在这里：**「没报错」不等于「点开了」**。
// 判定必须用**页面文本长度变化 / 新浮层**这种能被读出来的东西。
// 本轮直接拿 BUTTON 本身的坐标（`BUTTON.group/canvas-chip` @`[200,24]`），
// 并在点开前后各读一次「顶栏附近所有可见浮层的文本」，逐条点名。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBW3';
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

/** 顶栏一带所有「看得见的文字块」——菜单项、浮层、提示条都在里面。 */
const topTexts = () => page.evaluate(() => {
  const seen = new Map();
  for (const e of document.querySelectorAll('div,span,li,a,button,p')) {
    const r = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    if (r.width < 6 || r.height < 6 || r.y < -10 || r.y > 500) continue;
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity < 0.05) continue;
    if (e.children.length > 2) continue;               // 只取叶子块，避免整页父子重复
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 30) continue;
    const k = `${t}@${Math.round(r.x)},${Math.round(r.y)}`;
    if (!seen.has(k)) seen.set(k, { text: t, at: [Math.round(r.x), Math.round(r.y)], size: [Math.round(r.width), Math.round(r.height)], tag: e.tagName });
  }
  return [...seen.values()];
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1800);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '打开顶栏「画布 2 ▾」并逐条点名' });
  const out = {};

  // 拿 BUTTON 本身的矩形（BW2 点的是包着它的 div）
  const btn = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '画布 2');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { cls: (b.getAttribute('class') || '').slice(0, 60), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  });
  out.button = btn;
  console.log(`═══ 「画布 2」按钮：${JSON.stringify(btn)} ═══`);
  if (!btn) { console.log('⛔ 按钮没找到'); }

  const before = await topTexts();
  const beforeKeys = new Set(before.map((t) => t.text));
  await page.mouse.move(btn.at[0], btn.at[1]); await settle(600);
  await page.mouse.click(btn.at[0], btn.at[1]); await settle(2000);
  const after = await topTexts();
  const appeared = after.filter((t) => !beforeKeys.has(t.text));
  out.opened = { before: before.length, after: after.length, appeared: appeared.length };
  console.log(`\n═══ 点开读数：可见文字块 ${before.length} → ${after.length}｜新出现 ${appeared.length} 条 ═══`);
  appeared.forEach((t) => console.log(`  + ${t.text}  @${JSON.stringify(t.at)} ${JSON.stringify(t.size)} <${t.tag}>`));
  if (appeared.length) {
    await shot(page, 'M-286-顶栏画布菜单.png');
    console.log('  📸 M-286 已拍');
  }
  const all = appeared.map((t) => t.text).join(' ');
  out.trashHit = /回收|垃圾桶|废纸|trash|recycle/i.test(all);
  console.log(`  ⭐ 菜单里有没有回收站字样：${out.trashHit ? '有' : '没有'}`);

  // 悬停每一项，看有没有子菜单（有些入口是两级）
  for (const t of appeared.slice(0, 8)) {
    await page.mouse.move(t.at[0] + 4, t.at[1] + 4); await settle(1100);
    const now = await topTexts();
    const extra = now.filter((x) => !beforeKeys.has(x.text) && !appeared.some((a) => a.text === x.text));
    if (extra.length) console.log(`  悬停「${t.text}」→ 又冒出 ${extra.length} 条：${JSON.stringify(extra.map((e) => e.text).slice(0, 8))}`);
  }
  await page.keyboard.press('Escape'); await settle(1000);
  await clearToasts(page);

  out.finalTexts = (await topTexts()).length;
  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 「画布 2 ▾」点开了吗：${appeared.length > 0 ? '✅ 是' : '❌ 没有'}`);
  console.log(`  · 菜单项：${JSON.stringify(appeared.map((t) => t.text))}`);
  console.log(`  · 回收站字样：${out.trashHit ? '有' : '没有'}`);

  await logStep(B, {
    id: 'BW3-canvas-chip-menu',
    title: '顶栏「画布 2 ▾」菜单逐条点名',
    target: 'BW2 点的是包着按钮的 `div`（正文 0 变化 = 根本没开），本轮直接拿 '
      + '`BUTTON.group/canvas-chip` 自己的坐标，并**在点开前后各读一次顶栏一带所有可见文字块**，'
      + '只报「新出现」的那些 —— ⭐ **「没报错」不等于「点开了」**，判定必须用能被读出来的东西。',
    evidence: out,
    visible_text: JSON.stringify({ 按钮: out.button, 点开读数: out.opened,
      菜单项: (out.opened || {}).appeared, 有回收站: out.trashHit }).slice(0, 3000),
    shot: out.opened && out.opened.appeared ? 'M-286-顶栏画布菜单.png' : undefined,
  });
  console.log('\nBW3 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}

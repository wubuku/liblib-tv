// 批次 74 · B：菜单里**有没有任何元素**是 144×22？
// 逐个 menuitem 的后代与祖先都量，连菜单本体一起列出来。
import { chromium } from 'playwright';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const pre = await ids();
const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
  .find((x) => /^图片$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
  const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2500);
const mine = (await ids()).filter((x) => !pre.includes(x))[0];
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
for (const [fx, fy] of [[0.5, 0.2], [0.5, 0.12], [0.3, 0.3], [0.5, 0.5]]) {
  const pt = await p.evaluate(([id, ax, ay]) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width * ax), y: Math.round(r.y + r.height * ay) }; }, [mine, fx, fy]);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
  if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), mine)) break;
}
const btn = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label^="Create connected node"]')).find((x) => /source/.test(x.getAttribute('data-testid') || ''));
  const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
await p.mouse.click(btn.x, btn.y); await p.waitForTimeout(1600);
const dump = await p.evaluate(() => {
  const el = Array.from(document.querySelectorAll('[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
  const box = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; };
  const label = (e) => e.tagName + (e.getAttribute('role') ? `[${e.getAttribute('role')}]` : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ').slice(0, 2).join('.') : '');
  const out = { 菜单本体: box(el), 菜单逐代: [] };
  let cur = el;
  while (cur && cur !== document.body) { out.菜单逐代.push({ el: label(cur), box: box(cur) }); cur = cur.parentElement; }
  out.项 = Array.from(el.querySelectorAll('[role="menuitem"]')).map((it) => ({
    name: (it.innerText || '').trim().split('\n')[0], box: box(it),
    子: Array.from(it.querySelectorAll('*')).map((c) => ({ el: label(c), box: box(c), text: (c.innerText || '').trim().slice(0, 8) })).slice(0, 6),
  }));
  // 全文扫一遍：当前页面上有没有任何 144 宽 / 22 高的元素
  out.命中144x22 = Array.from(document.querySelectorAll('*')).filter((e) => { const r = e.getBoundingClientRect(); return Math.round(r.width) === 144 && Math.round(r.height) === 22; })
    .map((e) => label(e) + '|' + (e.innerText || '').trim().slice(0, 10));
  out.命中144宽 = Array.from(document.querySelectorAll('*')).filter((e) => { const r = e.getBoundingClientRect(); return Math.round(r.width) === 144; }).length;
  out.命中22高 = Array.from(document.querySelectorAll('*')).filter((e) => { const r = e.getBoundingClientRect(); return Math.round(r.height) === 22; }).length;
  return out;
});
console.log(JSON.stringify(dump, null, 1));
await p.keyboard.press('Escape'); await p.waitForTimeout(400);
const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, mine);
await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(900);
await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
  const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
await p.waitForTimeout(1500);
console.log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
await b.close();

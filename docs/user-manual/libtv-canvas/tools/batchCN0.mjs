// Batch CN-0：盘大编辑器底部的两个下拉 —— `默认模式` 和 `16:9 · 720P · 30s`。
//
// CM 查清了 `⤢` 开的是大编辑器，但**框里那两个下拉里到底有什么，手册一个字都没写**。
// 下拉是纯前端菜单：点开只读不选，安全；关掉用 ESC 或再点一次按钮，不碰 `发送`。
//
// ⛔ 安全边界：不点任何选项、不点 `发送`、不按 ⌘Enter。每次开合前后都读一次
//    「模态全文 + 节点读数」，确认**没有发生写入**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const VID = 'v-oZNpH99MtM';

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
};
const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: !!fold };
}, id);
const modal = (page) => page.evaluate(() => {
  const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!dlg) return { 开: false };
  const r = dlg.getBoundingClientRect();
  return { 开: true, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 全文: (dlg.innerText || '').replace(/\s+/g, ' ').trim() };
});

// ⭐ 通用探针：打开之后「多出来的东西」是什么
const probe = (page) => page.evaluate(() => {
  const box = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  const txt = (e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
  // 语义化的选项
  const 语义 = [...document.querySelectorAll('[role="option"],[role="menuitem"],[role="menuitemradio"],[role="radio"],[role="listbox"],[role="menu"],[data-combobox-option],[data-option]')]
    .map((e) => ({ 角色: e.getAttribute('role') || (e.dataset.comboboxOption !== undefined ? 'combobox-option' : '?'), 文字: txt(e).slice(0, 30), 选中: e.getAttribute('aria-selected'), 禁用: e.getAttribute('aria-disabled') === 'true' || e.className.toString().includes('disabled'), rect: box(e) }));
  // body 直属层里，矩形在视口内、且不是模态本身的
  const 层 = [...document.body.children]
    .map((e) => { const s = getComputedStyle(e); const r = e.getBoundingClientRect(); return { cls: (e.className || '').toString().slice(0, 64), z: s.zIndex, rect: box(e), 子元素数: e.children.length, 文字: txt(e).slice(0, 60) }; })
    .filter((x) => x.rect[2] > 0 && x.rect[3] > 0 && x.rect[0] >= 0 && x.rect[1] >= 0);
  // 模态之外、但落在视口里的所有可见文字叶子（用来兜住「既不是 option 也不是 body 直属」的菜单）
  const 浮层文字 = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('.react-flow')) continue;
    const s = getComputedStyle(e);
    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || r.width > 700) continue;
    if (e.children.length) continue;
    const t = txt(e);
    if (!t) continue;
    if (e.closest('[z-index="601"], .mantine-Modal-inner')) continue;   // 模态自己的文字不算
    浮层文字.push({ 文字: t.slice(0, 24), rect: box(e) });
  }
  return { 语义, 层, 浮层文字 };
});

const out = {};
const { browser, page } = await launch();
await boot(page);

// 选中 + 打开大编辑器
let sel = await read(page, VID);
const pts = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const q = n.getBoundingClientRect(); const a = [];
  for (const fy of [0.25, 0.4, 0.55, 0.7, 0.85]) for (const fx of [0.1, 0.25, 0.5, 0.75, 0.9]) {
    const x = q.x + q.width * fx, y = q.y + q.height * fy;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n && !el.closest('button,a')) a.push([Math.round(x), Math.round(y)]);
  }
  return a;
}, VID);
for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1400); sel = await read(page, VID); if (sel.选中 && sel.折叠钮) break; }
console.log('选中后 =', JSON.stringify(sel));
await page.mouse.click(sel.折叠钮 ? 1346 + 14 : 0, 217 + 14);
await page.waitForTimeout(1800);
out.模态 = await modal(page);
console.log('模态 =', out.模态.开, JSON.stringify(out.模态.全文 || '').slice(0, 100));

out.下拉 = [];
for (const 名 of ['默认模式', '16:9 · 720P · 30s']) {
  const R = { 名 };
  // 每次都从「没打开」开始
  const st0 = await modal(page);
  const btn = await page.evaluate((t) => {
    const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
    if (!dlg) return null;
    const b = [...dlg.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(t));
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 全名: (b.innerText || '').replace(/\s+/g, ' ').trim() };
  }, 名);
  R.按钮 = btn;
  if (!btn) { console.log(`  ${名}: 找不到按钮`); out.下拉.push(R); continue; }
  const [bx, by, bw, bh] = btn.rect;
  const 落点 = await page.evaluate(([x, y]) => {
    const el = document.elementFromPoint(x, y);
    return el ? { tag: el.tagName.toLowerCase(), cls: (el.className || '').toString().slice(0, 40), 文字: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18), 在模态内: !!(el.closest('body > *') && getComputedStyle(el.closest('body > *')).zIndex === '601') } : null;
  }, [bx + bw / 2, by + bh / 2]);
  R.落点 = 落点;
  await page.mouse.click(bx + bw / 2, by + bh / 2);
  await page.waitForTimeout(1400);
  R.开 = await probe(page);
  R.开时模态 = await modal(page);
  console.log(`\n  === ${名} (${JSON.stringify(btn.rect)}) 落点=${JSON.stringify(落点).slice(0, 130)}`);
  console.log(`  语义选项 ${R.开.语义.length} 条:`, JSON.stringify(R.开.语义).slice(0, 700));
  console.log(`  模态外浮层文字 ${R.开.浮层文字.length} 条:`, JSON.stringify(R.开.浮层文字).slice(0, 500));
  const 新层 = R.开.层.filter((x) => x.z !== '600' && x.z !== '601' && x.rect[0] > 100);
  console.log(`  视口内非模态层:`, JSON.stringify(新层).slice(0, 500));

  // 拍一张开着的样子（这一张是名副其实的：菜单真的开着）
  R.截图 = `cn0-${名.replace(/[^\w]/g, '')}.png`;
  await page.screenshot({ path: resolve(HERE, '.evidence', R.截图) });

  // ⛔ 不点任何选项。ESC 收起；若 ESC 无效就再点一次按钮
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);
  let after = await probe(page);
  if (after.语义.length || after.浮层文字.length > 8) {
    await page.mouse.click(bx + bw / 2, by + bh / 2);
    await page.waitForTimeout(1200);
    after = await probe(page);
  }
  R.关后语义数 = after.语义.length;
  R.关后模态 = await modal(page);
  R.关后节点 = await read(page, VID);
  R.关后全文 = R.关后模态.全文 || '';
  R.有写入吗 = (st0.全文 || '') !== (R.关后全文 || '');
  console.log(`  ESC 之后: 语义选项 ${R.关后语义数} 条 | 模态仍在 ${R.关后模态.开} | 模态全文变化=${R.有写入吗} | 节点=${JSON.stringify(R.关后节点)}`);
  out.下拉.push(R);
}

await page.screenshot({ path: resolve(HERE, '.evidence/cn0-收尾.png') });
console.log('\n收尾 模态 =', JSON.stringify(await modal(page)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cn0-dropdowns.json'), JSON.stringify(out, null, 2));

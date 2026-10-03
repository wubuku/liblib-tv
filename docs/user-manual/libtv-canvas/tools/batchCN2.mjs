// Batch CN-2：用**前后差分**重做菜单枚举，并盘模态里的 `参考` 按钮。
//
// CN-1 的判据缺陷（§124）：`menuItems` 只按「在按钮上方」过滤，
// 于是把模态自身的 `参考` / `1` / `描述想剪成什么效果` 也当成菜单项读了出来
// ⇒ 「16:9 那个下拉里有 3 个选项」这条读数**作废**。
// CN-0 的 `默认模式` 读数（5 条）内容是对的（有截图作阳性对照），
// 但它靠的过滤条件同样不干净 —— 这里用差分法把它**独立复核一遍**。
//
// ⭐ 差分法：开之前快照模态内全部「文字叶子」，开之后再快照一次，**只把新出现的算成菜单项**。
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
const killPromo = async (page) => {
  const b = await page.evaluate(() => {
    const t = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (!b) return false;
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1200); return true;
};
const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: !!fold };
}, id);
const modal = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  return d ? { 开: true, rect: [Math.round(d.getBoundingClientRect().x), Math.round(d.getBoundingClientRect().y), Math.round(d.getBoundingClientRect().width), Math.round(d.getBoundingClientRect().height)], 全文: (d.innerText || '').replace(/\s+/g, ' ').trim() } : { 开: false };
});
// ⭐ 模态内（或全页）「文字叶子」快照 —— 键 = 文字 + 取整后的位置
const snap = (page, 限浮层) => page.evaluate((limit) => {
  const out = new Map();
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e);
    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 26) continue;
    const p = e.querySelector('svg path') || (e.parentElement && e.parentElement.querySelector('svg path'));
    const key = `${t}@${Math.round(r.x)},${Math.round(r.y)}`;
    out.set(key, { 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 图标: p ? (p.getAttribute('d') || '').slice(0, 20) : null, 在模态: !!e.closest('div[class*="z-overlay"], div[class*="z-\\(--z-overlay\\)"]') });
  }
  return [...out.entries()].map(([k, v]) => ({ k, ...v }));
}, 限浮层);
const diff = (before, after) => after.filter((a) => !before.some((b) => b.k === a.k));

const btnRect = (page, 起始) => page.evaluate((t) => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return null;
  const b = [...d.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(t));
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 全名: (b.innerText || '').replace(/\s+/g, ' ').trim() };
}, 起始);
const openModal = async (page) => {
  for (let i = 0; i < 3; i += 1) {
    if ((await modal(page)).开) return true;
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
    let ok = false;
    for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1300); const s = await read(page, VID); if (s.选中 && s.折叠钮) { ok = true; break; } }
    if (!ok) return false;
    const fx = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const f = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
      if (!f) return null; const r = f.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)];
    }, VID);
    if (!fx || fx[0] + 14 > 1440 || fx[1] + 14 > 810) return false;
    await page.mouse.click(fx[0] + 14, fx[1] + 14);
    await page.waitForTimeout(1700);
  }
  return (await modal(page)).开;
};
const closeModal = async (page) => { if ((await modal(page)).开) { await page.mouse.click(1360, 780); await page.waitForTimeout(1500); } };

const out = { 控件: [] };
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);
console.log('点掉促销弹窗 =', out.促销);

for (const 名 of ['默认模式', '16:9', '参考']) {
  if (!(await openModal(page))) { console.log(`${名}: 开不出模态`); break; }
  const R = { 名 };
  const b = await btnRect(page, 名);
  R.按钮 = b;
  if (!b) { console.log(`${名}: 找不到按钮`); await closeModal(page); continue; }
  const [bx, by, bw, bh] = b.rect;
  const before = await snap(page, true);
  R.开之前页面文字数 = before.length;
  await page.mouse.click(bx + bw / 2, by + bh / 2);
  await page.waitForTimeout(1500);
  const after = await snap(page, true);
  R.新出现的 = diff(before, after);
  R.模态 = await modal(page);
  console.log(`\n=== ${名} (${JSON.stringify(b.rect)}) 点之前 ${before.length} 条文字叶子，点之后 ${after.length} 条，**新出现 ${R.新出现的.length} 条**`);
  for (const it of R.新出现的) console.log(`     ${JSON.stringify(it.rect)} 「${it.文字}」 图标=${it.图标}`);
  R.截图 = `cn2-${名.replace(/[^\w]/g, '')}.png`;
  await page.screenshot({ path: resolve(HERE, '.evidence', R.截图) });
  // ⛔ 不选。点回同一个按钮收掉
  await page.mouse.click(bx + bw / 2, by + bh / 2);
  await page.waitForTimeout(1300);
  const closed = await snap(page, true);
  R.收掉后仍多出 = diff(before, closed).length;
  console.log(`  再点一次收掉，仍多出 ${R.收掉后仍多出} 条`);
  if (R.收掉后仍多出 > 0) { await page.keyboard.press('Escape'); await page.waitForTimeout(1200); }
  R.收后模态 = await modal(page);
  out.控件.push(R);
  await closeModal(page);
}

console.log('\n收尾 =', JSON.stringify(await read(page, VID)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cn2-diff.json'), JSON.stringify(out, null, 2));

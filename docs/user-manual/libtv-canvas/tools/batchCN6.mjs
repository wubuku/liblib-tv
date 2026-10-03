// Batch CN-6：验证「下拉菜单是 portal 到 body 的，不在模态子树里」这个假设。
//
// CN-2 用**全页**差分读到了 13 条（规格面板）/ 5 条（模式），有截图；
// CN-3 / CN-4 / CN-5 把差分范围锁死在 `z-index: 601` 那个元素里，差分恒为 0 ——
// ⭐ 我据此判了「面板没打开」，**那是我的仪器坏了，不是产品没反应**。
// 本步：同一个按钮，同一次点击，**全页差分** vs **模态内差分**，并列输出。
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
  return d ? { 开: true, 全文: (d.innerText || '').replace(/\s+/g, ' ').trim() } : { 开: false };
});
// ⭐ 两种范围：全页 / 只模态子树。并列取，用来证明差异出在范围上
const snap = (page, 范围) => page.evaluate((scope) => {
  const root = scope === 'modal'
    ? [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601')
    : document.body;
  if (!root) return [];
  const out = new Map();
  for (const e of root.querySelectorAll('*')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(); if (!t || t.length > 26) continue;
    if (scope === 'page') {
      const host = e.closest('body > *');
      const z = host ? getComputedStyle(host).zIndex : 'auto';
      if (z === '600' || z === '305' || z === '180') continue;      // 遮罩 / 跟随横幅 / 空层
      if (host && /ysf-chat-layer|z-\(\-\-z-overlay\)/.test((host.className || '').toString())) continue;
    }
    out.set(`${t}@${Math.round(r.x)},${Math.round(r.y)}`, { 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return [...out.values()];
}, 范围);
const diff = (a, b) => b.filter((x) => !a.some((y) => y.文字 === x.文字 && y.rect[0] === x.rect[0] && y.rect[1] === x.rect[1]));
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
    await page.waitForTimeout(1900);
  }
  return (await modal(page)).开;
};

const out = {};
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);

for (const [名, 起始] of [['模式', '默认模式'], ['规格', '16:9']]) {
  if (!(await openModal(page))) { console.log(`${名}: 开不出模态`); break; }
  const b = await btnRect(page, 起始);
  if (!b) { console.log(`${名}: 找不到按钮`); continue; }
  const 页0 = await snap(page, 'page'); const 模0 = await snap(page, 'modal');
  await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
  await page.waitForTimeout(1600);
  const 页1 = await snap(page, 'page'); const 模1 = await snap(page, 'modal');
  const dPage = diff(页0, 页1); const dModal = diff(模0, 模1);
  const R = { 名, 按钮: b, 全页差分: dPage, 模态内差分: dModal };
  console.log(`\n=== ${名} ${JSON.stringify(b.rect)}`);
  console.log(`  ⭐ 全页差分 ${dPage.length} 条 | 模态内差分 ${dModal.length} 条  ⇒ 假设${dPage.length > 0 && dModal.length === 0 ? '成立：菜单不在模态子树里' : '不成立'}`);
  for (const it of dPage) console.log(`      ${JSON.stringify(it.rect)} 「${it.文字}」`);
  if (名 === '规格' && dPage.length) {
    R.控件全页 = await page.evaluate(() => {
      const box = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
      const 滑 = [...document.querySelectorAll('input[type="range"],[role="slider"],[role="spinbutton"]')].map((r) => ({ tag: r.tagName.toLowerCase(), type: r.type || r.getAttribute('role'), min: r.min ?? r.getAttribute('aria-valuemin'), max: r.max ?? r.getAttribute('aria-valuemax'), step: r.step ?? r.getAttribute('aria-valuetext'), now: r.value ?? r.getAttribute('aria-valuenow'), rect: box(r) }));
      const 比例钮 = [...document.querySelectorAll('button')].filter((b) => /^\d+:\d+$/.test((b.innerText || '').trim())).map((b) => ({ 文字: b.innerText.trim(), 选中: b.getAttribute('aria-pressed') || b.getAttribute('aria-checked'), 类: (b.className || '').toString().slice(0, 30) }));
      return { 滑杆: 滑, 比例按钮: 比例钮 };
    });
    console.log('      滑杆 =', JSON.stringify(R.控件全页.滑杆));
    console.log('      比例按钮 =', JSON.stringify(R.控件全页.比例按钮));
    R.图 = 'cn6-规格面板-干净.png';
    await page.screenshot({ path: resolve(HERE, '.evidence', R.图) });
  }
  if (名 === '模式' && dPage.length) { R.图 = 'cn6-模式菜单-干净.png'; await page.screenshot({ path: resolve(HERE, '.evidence', R.图) }); }
  out[名] = R;
  await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
  await page.waitForTimeout(1000);
  if ((await modal(page)).开) { await page.mouse.click(1360, 780); await page.waitForTimeout(1500); }
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
await writeFile(resolve(HERE, '.evidence/cn6-scope.json'), JSON.stringify(out, null, 2));

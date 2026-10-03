// Batch CN-4：收 CN-3 的两个窟窿。
//
// ① ⛔ CN-3 的「规格面板」三项全空（滑杆/数字框/分组）—— 面板那次**根本没打开**，
//    那条读数作废。CN-2 的 13 条差分（58 → 71 条文字叶子）仍然成立，且有截图。
//    本步**先用差分确认面板真的开了**，开了才去读滑杆。
// ② CN-0 那张「模式」截图里促销弹窗还在画面上，本步促销先收掉，重拍一张干净的。
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
const snap = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return [];
  const out = new Map();
  for (const e of d.querySelectorAll('*')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(); if (!t) continue;
    out.set(`${t}@${Math.round(r.x)},${Math.round(r.y)}`, { 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return [...out.values()];
});
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

const out = {};
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);
console.log('促销收掉 =', out.促销);

// ① 干净的「模式」下拉
if (await openModal(page)) {
  const b = await btnRect(page, '默认模式');
  const before = await snap(page);
  await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
  await page.waitForTimeout(1500);
  const after = await snap(page);
  out.模式 = { 按钮: b, 新出现: after.filter((a) => !before.some((x) => x.文字 === a.文字 && x.rect[0] === a.rect[0] && x.rect[1] === a.rect[1])) };
  console.log('模式选项 =', JSON.stringify(out.模式.新出现));
  out.模式图 = 'cn4-模式菜单-干净.png';
  await page.screenshot({ path: resolve(HERE, '.evidence', out.模式图) });
  await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
  await page.waitForTimeout(1300);

  // ② 规格面板：先差分确认开了，再读滑杆
  const c = await btnRect(page, '16:9');
  const s0 = await snap(page);
  await page.mouse.click(c.rect[0] + c.rect[2] / 2, c.rect[1] + c.rect[3] / 2);
  await page.waitForTimeout(1600);
  const s1 = await snap(page);
  out.规格新文字 = s1.filter((a) => !s0.some((x) => x.文字 === a.文字 && x.rect[0] === a.rect[0] && x.rect[1] === a.rect[1]));
  out.面板开着了 = out.规格新文字.length >= 10;
  console.log(`规格面板：差分 ${out.规格新文字.length} 条 ⇒ 判定面板${out.面板开着了 ? '已打开 ✅' : '没开 ⛔（读数作废）'}`);
  if (out.面板开着了) {
    out.规格控件 = await page.evaluate(() => {
      const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
      const box = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
      return {
        input: [...d.querySelectorAll('input')].map((r) => ({ type: r.type, min: r.min, max: r.max, step: r.step, value: r.value, rect: box(r) })),
        滑杆: [...d.querySelectorAll('[role="slider"],[role="spinbutton"]')].map((r) => ({ 角色: r.getAttribute('role'), aria: { min: r.getAttribute('aria-valuemin'), max: r.getAttribute('aria-valuemax'), now: r.getAttribute('aria-valuenow'), text: r.getAttribute('aria-valuetext') }, rect: box(r) })),
      };
    });
    console.log('  控件 =', JSON.stringify(out.规格控件));
    out.规格图 = 'cn4-规格面板-干净.png';
    await page.screenshot({ path: resolve(HERE, '.evidence', out.规格图) });
  }
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
await writeFile(resolve(HERE, '.evidence/cn4-spec.json'), JSON.stringify(out, null, 2));

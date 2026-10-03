// Batch CN-5：CN-2 能点开下拉、CN-3/CN-4 点不开（差分恒 0）—— 本步查清并重拍。
//
// 两处可疑：① Playwright 的 click 是 down+up 极快连发，若组件在 onMouseDown 开、onClick 关，
// 就会「开了又关」；② 模态刚挂载时第一下点击可能被入场动画吃掉。
// 处理：显式 move → 等 → down → 等 → up，并**按差分判定重试**（最多 3 次），差分非 0 才算数。
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
  const out = new Map();
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(); if (!t || t.length > 26) continue;
    const inModal = !!(e.closest('body > *') && getComputedStyle(e.closest('body > *')).zIndex === '601');
    if (!inModal) continue;
    const p = e.querySelector('svg path') || (e.parentElement && e.parentElement.querySelector('svg path'));
    out.set(`${t}@${Math.round(r.x)},${Math.round(r.y)}`, { 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 图标: p ? (p.getAttribute('d') || '').slice(0, 20) : null });
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
    await page.waitForTimeout(1900);
  }
  return (await modal(page)).开;
};
// ⭐ 慢速点击：move → 等 → down → 等 → up
const slowClick = async (page, x, y) => {
  await page.mouse.move(x - 40, y - 40);
  await page.waitForTimeout(250);
  await page.mouse.move(x, y, { steps: 8 });
  await page.waitForTimeout(450);
  await page.mouse.down();
  await page.waitForTimeout(140);
  await page.mouse.up();
  await page.waitForTimeout(1500);
};

const out = { 试: [] };
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);

for (const [名, 起始] of [['模式', '默认模式'], ['规格', '16:9']]) {
  if (!(await openModal(page))) { console.log(`${名}: 开不出模态`); break; }
  const b = await btnRect(page, 起始);
  if (!b) { console.log(`${名}: 找不到按钮`); continue; }
  const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
  const R = { 名, 按钮: b, 尝试: [] };
  for (let k = 1; k <= 3; k += 1) {
    const s0 = await snap(page);
    await slowClick(page, cx, cy);
    const s1 = await snap(page);
    const 新 = s1.filter((a) => !s0.some((x) => x.文字 === a.文字 && x.rect[0] === a.rect[0] && x.rect[1] === a.rect[1]));
    R.尝试.push({ 次: k, 新出现数: 新.length });
    console.log(`  ${名} 第 ${k} 次慢点 → 新出现 ${新.length} 条`);
    if (新.length >= 5) {
      R.成功 = true; R.新出现 = 新;
      for (const it of 新) console.log(`      ${JSON.stringify(it.rect)} 「${it.文字}」 图标=${it.图标}`);
      R.图 = `cn5-${名}菜单.png`;
      await page.screenshot({ path: resolve(HERE, '.evidence', R.图) });
      // 顺带读滑杆（只在规格面板真的开了时）
      if (名 === '规格') {
        R.控件 = await page.evaluate(() => {
          const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
          const box = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
          return {
            input: [...d.querySelectorAll('input')].map((r) => ({ type: r.type, min: r.min, max: r.max, step: r.step, value: r.value, rect: box(r) })),
            滑杆: [...d.querySelectorAll('[role="slider"],[role="spinbutton"]')].map((r) => ({ 角色: r.getAttribute('role'), min: r.getAttribute('aria-valuemin'), max: r.getAttribute('aria-valuemax'), now: r.getAttribute('aria-valuenow'), text: r.getAttribute('aria-valuetext'), rect: box(r) })),
          };
        });
        console.log('      控件 =', JSON.stringify(R.控件));
      }
      break;
    }
    // 没开就再试（顺便把可能吞掉的第一次点击消耗掉）
  }
  out.试.push(R);
  if (R.成功) { await slowClick(page, cx, cy); await page.waitForTimeout(600); }
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
await writeFile(resolve(HERE, '.evidence/cn5-slowclick.json'), JSON.stringify(out, null, 2));

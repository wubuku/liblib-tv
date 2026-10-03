// Batch CR：认领剩下的匿名控件。
//
// 目标一：图片节点大编辑器底部那枚**无文字、无 aria、无悬停气泡**的按钮（CO 记为 `[959,664]`）。
//   CO-1 只截了 class 的前 40 个字符，认不出来 —— 这次读**完整 class + 完整祖先链**。
// 目标二：素材详情浮层右上角那枚 `⤡`（CL 留下的 📖）。
//
// ⛔ 全程只读：不选任何模型/规格、不点 `⤡` 之外会产生写入的控件。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const IMG = 'i-sODTbgLUm1';

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2800);
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
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  return { 在: true, 选中: n.classList.contains('selected'), 折叠钮: !!fold };
}, id);
const modal = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  return d ? { 开: true } : { 开: false };
});
const snap = (page) => page.evaluate(() => {
  const out = new Map();
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(); if (!t || t.length > 30) continue;
    const host = e.closest('body > *');
    if (host && (getComputedStyle(host).zIndex === '600' || /ysf-chat-layer/.test((host.className || '').toString()))) continue;
    out.set(`${t}@${Math.round(r.x)},${Math.round(r.y)}`, { 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return [...out.values()];
});
const diff = (a, b) => b.filter((x) => !a.some((y) => y.文字 === x.文字 && y.rect[0] === x.rect[0] && y.rect[1] === x.rect[1]));
// ⭐ 完整身份的读法：完整 class、完整祖先链、全部属性、全部 svg
const identity = (page, x, y) => page.evaluate(([px, py]) => {
  const el = document.elementFromPoint(px, py);
  if (!el) return { 无: true };
  const b = el.closest('button, [role="button"], a') || el;
  const attrs = {};
  for (const a of b.attributes) attrs[a.name] = (a.value || '').slice(0, 80);
  const 链 = [];
  let n = b;
  for (let i = 0; i < 6 && n; i += 1, n = n.parentElement) {
    const s = getComputedStyle(n); const r = n.getBoundingClientRect();
    链.push({ tag: n.tagName.toLowerCase(), cls完整: (n.className || '').toString(), cursor: s.cursor, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  const svgs = [...b.querySelectorAll('svg')].map((s) => ({ viewBox: s.getAttribute('viewBox'), class: (s.className.baseVal || s.className || '').toString().slice(0, 40), 路径数: s.querySelectorAll('path').length, 全部路径: [...s.querySelectorAll('path')].map((p) => (p.getAttribute('d') || '').slice(0, 40)) }));
  return {
    tag: b.tagName.toLowerCase(), 文字: (b.innerText || '').replace(/\s+/g, ' ').trim(),
    全部属性: attrs, 完整class: (b.className || '').toString(), 禁用: b.disabled === true, 链, svgs,
    兄弟文字: [...(b.parentElement ? b.parentElement.children : [])].map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10)),
  };
}, [x, y]);
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
    }, IMG);
    let ok = false;
    for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1300); const s = await read(page, IMG); if (s.选中 && s.折叠钮) { ok = true; break; } }
    if (!ok) return false;
    const fp = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const f = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
      if (!f) return null; const r = f.getBoundingClientRect();
      for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) for (const fx of [0.3, 0.5, 0.7]) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const el = document.elementFromPoint(x, y);
        if (el && el.closest('button') && el.closest('button').className.toString().includes('size-7') && x < 1440 && y < 810) return [x, y];
      }
      return null;
    }, IMG);
    if (!fp) return false;
    await page.mouse.click(fp[0], fp[1]);
    await page.waitForTimeout(1900);
  }
  return (await modal(page)).开;
};

const out = {};
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);

// —— 目标一：图片大编辑器底部四枚按钮的完整身份 ——
if (await openModal(page)) {
  out.身份 = await page.evaluate(() => {
    const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
    if (!d) return null;
    return [...d.querySelectorAll('button')].map((b) => {
      const r = b.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: (b.innerText || '').replace(/\s+/g, ' ').trim(), aria: b.getAttribute('aria-label'), 禁用: b.disabled, 完整class: (b.className || '').toString() };
    }).filter((b) => b.rect[2] > 0 && b.rect[1] > 600);
  });
  console.log('=== 图片大编辑器底排按钮（完整 class）===');
  for (const b of (out.身份 || [])) console.log(`  ${JSON.stringify(b.rect)} 「${b.文字}」aria=${b.aria} 禁用=${b.禁用}\n     class=${b.完整class}`);

  // 逐个匿名按钮做「完整身份 + 点开前后差分」
  out.逐个 = [];
  for (const b of (out.身份 || []).filter((x) => !x.文字 && !x.禁用)) {
    const [x, y, w, h] = b.rect;
    const 身份 = await identity(page, x + w / 2, y + h / 2);
    const s0 = await snap(page);
    await page.mouse.click(x + w / 2, y + h / 2);
    await page.waitForTimeout(1500);
    const 新 = diff(s0, await snap(page));
    console.log(`\n--- 匿名按钮 ${JSON.stringify(b.rect)}`);
    console.log(`    完整class = ${身份.完整class}`);
    console.log(`    全部属性 = ${JSON.stringify(身份.全部属性)}`);
    console.log(`    svg = ${JSON.stringify(身份.svgs).slice(0, 260)}`);
    console.log(`    兄弟文字 = ${JSON.stringify(身份.兄弟文字)}`);
    console.log(`    点开 → 新出现 ${新.length} 条: ${新.map((x) => x.文字).join(' / ')}`);
    out.逐个.push({ rect: b.rect, 身份, 新出现: 新 });
    if (新.length) {
      await page.mouse.click(x + w / 2, y + h / 2);
      await page.waitForTimeout(1100);
      if (diff(s0, await snap(page)).length) { await page.keyboard.press('Escape'); await page.waitForTimeout(1100); }
    }
    if (!(await modal(page)).开) { console.log('    ⛔ 模态没了，重开'); if (!(await openModal(page))) break; }
  }
  if ((await modal(page)).开) { await page.mouse.click(1360, 780); await page.waitForTimeout(1400); }
}

console.log('\n收尾 =', JSON.stringify(await read(page, IMG)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cr0-anonymous.json'), JSON.stringify(out, null, 2));

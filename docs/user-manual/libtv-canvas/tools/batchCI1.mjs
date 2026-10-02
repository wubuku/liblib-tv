// Batch CI-1：把「正在跟随」这个从未写进手册的东西查清楚 —— **仍然只读**。
//
// CI-0 的三条读数：
//   ① 顶栏正中有个 174x34 的容器（`fixed left-1/2 top-0 z-[305]`），里面是
//      `正在跟随` + 一枚 64x16 的白胶囊按钮，文字 `取消ESC`、aria `退出跟随`。
//   ② 悬停气泡读不到（空）—— 但这次带了阳性对照。
//   ③ 画布上 11 个节点，其中 4 对同名（`i-9nlG6HdjK2`/`i-sODTbgLUm1` 都是「图片节点 2」……）。
//
// ⭐ 本步要解决的疑点，按重要性排：
//   A. **它跟的是谁？** 174x34 装不下头像+名字，猜不得，去读 DOM。
//   B. **它是 toast 还是状态？** toast 会自己消失；如果是状态，就说明「这画布一直开着跟随」。
//   C. **§12.2 的因果可能是错的。** 旧记录写「点故事板 → TV Director 拉出来跟着」，
//      而 CI-0 **一次故事板都没点**就看见了横幅 ⇒ 因果要重新核。
//   D. **那 4 对同名节点是不是「跟着来的」？** 不能靠「感觉像我复制的」，去比对参数卡内容。
//   E. **顺手修 M-323 的病根**：`page.screenshot({clip})` 的 clip 基准和
//      `getBoundingClientRect()` 不一致，先量出到底差多少。
//
// ⛔ 依然**不点「取消」**：那是对用户画布的一次持久状态写入，且我还没确认「跟随」跟谁有关。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
const out = {};

await open(page, URL_);
await closePromos(page);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(5000);
await closePromos(page);
await page.waitForTimeout(1500);

// ── E. 先量坐标基准 ────────────────────────────────────────────────
out.坐标基准 = await page.evaluate(() => {
  const el = document.querySelector('[aria-label="退出跟随"]');
  const r = el?.getBoundingClientRect();
  return {
    scrollX: window.scrollX, scrollY: window.scrollY,
    docScrollTop: document.documentElement.scrollTop,
    bodyScrollTop: document.body.scrollTop,
    视口: [window.innerWidth, window.innerHeight],
    文档尺寸: [document.documentElement.scrollWidth, document.documentElement.scrollHeight],
    按钮rect: r ? { x: r.x, y: r.y, w: r.width, h: r.height } : null,
    body的overflow: getComputedStyle(document.body).overflow,
    html的overflow: getComputedStyle(document.documentElement).overflow,
  };
});
console.log('坐标基准 =', JSON.stringify(out.坐标基准, null, 2));

// ── A. 横幅全文 + 每一个后代元素 ───────────────────────────────────
out.横幅 = await page.evaluate(() => {
  const btn = document.querySelector('[aria-label="退出跟随"]');
  if (!btn) return { found: false };
  // 往上找到那个有边框的 174x34 容器
  let box = btn;
  while (box.parentElement && !/border/.test(box.parentElement.className || '')) box = box.parentElement;
  const rb = box.getBoundingClientRect();
  const cs = getComputedStyle(box);
  const kids = [...box.querySelectorAll('*')].map((e) => {
    const r = e.getBoundingClientRect();
    return {
      tag: e.tagName.toLowerCase(),
      cls: (e.className || '').toString().slice(0, 54),
      文字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      src: e.getAttribute('src')?.slice(0, 90) || null,
      alt: e.getAttribute('alt') || null,
      aria: e.getAttribute('aria-label') || null,
      svg路径: e.tagName === 'path' ? (e.getAttribute('d') || '').slice(0, 46) : null,
    };
  });
  return {
    found: true,
    容器cls: (box.className || '').toString().slice(0, 120),
    容器全文: (box.innerText || '').replace(/\s+/g, ' ').trim(),
    容器rect: [Math.round(rb.x), Math.round(rb.y), Math.round(rb.width), Math.round(rb.height)],
    背景: cs.backgroundColor, 边框: cs.border, 圆角: cs.borderRadius,
    子元素数: kids.length,
    子元素: kids,
  };
});
console.log('\n横幅 =', JSON.stringify(out.横幅, null, 2));

// ── C2. 页面上**所有**「跟随」元素，一次列全（避免只认到一枚）──────
out.所有跟随元素 = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const rows = [];
  for (const el of document.querySelectorAll('*')) {
    if (!vis(el)) continue;
    const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
    const a = el.getAttribute('aria-label') || '';
    const ti = el.getAttribute('title') || '';
    if (t && t.length <= 14 && /跟随/.test(t)) {
      const r = el.getBoundingClientRect();
      rows.push({ 怎么找到: '文字', tag: el.tagName.toLowerCase(), 文字: t, cls: (el.className || '').toString().slice(0, 44), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    } else if (/跟随|follow/i.test(a + '|' + ti)) {
      const r = el.getBoundingClientRect();
      rows.push({ 怎么找到: 'aria/title', tag: el.tagName.toLowerCase(), aria: a, title: ti, 文字: t.slice(0, 20), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
  }
  return rows;
});
console.log('\n所有跟随元素 =', JSON.stringify(out.所有跟随元素, null, 2));

// ── 截图诊断：同一时刻拍「全屏」和「按 rect 裁」两张，对照看 ────────
const btnBox = await page.locator('[aria-label="退出跟随"]').boundingBox();
console.log('\nPlaywright boundingBox =', JSON.stringify(btnBox));
await shot(page, 'M-324a-诊断-全屏.png');
const bx = await page.locator('[aria-label="退出跟随"]').boundingBox();
await shot(page, 'M-324b-诊断-按boundingBox裁.png', { clip: { x: Math.max(0, bx.x - 190), y: 0, width: 420, height: 130 } });
// 元素自带截图：让 Playwright 自己算裁剪区，绕开坐标系疑问
await page.locator('div[class*="rounded-b-xl"]').first().screenshot({ path: resolve(HERE, '../screenshots/M-324c-诊断-元素截图.png') })
  .then(() => console.log('元素截图 ok')).catch((e) => console.log('元素截图失败 =', e.message));

// ── 悬停读名（只悬停，不点）+ **阳性对照** ─────────────────────────
const readTips = () => page.evaluate(() => {
  const grab = (sel) => [...document.querySelectorAll(sel)].map((e) => (e.innerText || e.textContent || '').trim()).filter((t) => t && t.length < 60);
  return { role: grab('[role="tooltip"]'), mantine: grab('[class*="Tooltip"]') };
});
await page.mouse.move(5, 500);
await page.waitForTimeout(500);
const t0 = await readTips();
await page.mouse.move(bx.x + 12, bx.y + 8);
await page.waitForTimeout(1200);
await page.mouse.move(bx.x + 13, bx.y + 8);
await page.waitForTimeout(900);
const t1 = await readTips();
out.悬停 = { 阴性: t1.role.filter((x) => !t0.role.includes(x)).concat(t1.mantine.filter((x) => !t0.mantine.includes(x))) };
// 阳性对照：CH 已经坐实顶栏「工作流」图标悬停会出名字
const wf = page.locator('[aria-label="工作流"]').first();
if (await wf.count()) {
  const wb = await wf.boundingBox();
  await page.mouse.move(5, 500); await page.waitForTimeout(400);
  const c0 = await readTips();
  await page.mouse.move(wb.x + 12, wb.y + 12);
  await page.waitForTimeout(1100);
  await page.mouse.move(wb.x + 13, wb.y + 12);
  await page.waitForTimeout(800);
  const c1 = await readTips();
  out.阳性对照 = c1.role.filter((x) => !c0.role.includes(x)).concat(c1.mantine.filter((x) => !c0.mantine.includes(x)));
}
await page.mouse.move(5, 500);
console.log('\n悬停气泡(阴性) =', JSON.stringify(out.悬停), ' 阳性对照 =', JSON.stringify(out.阳性对照));

// ── B. 是 toast 还是状态：完全不动，静置 55 秒看它会不会自己消失 ────
const snap = () => page.evaluate(() => {
  const el = document.querySelector('[aria-label="退出跟随"]');
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { 时刻: new Date().toISOString().slice(11, 19), 文字: (el.innerText || '').trim(), rect: [Math.round(r.x), Math.round(r.y)] };
});
out.静置观察 = [await snap()];
for (const wait of [15000, 20000, 20000]) {
  await page.waitForTimeout(wait);
  out.静置观察.push(await snap());
}
console.log('\n静置观察 =', JSON.stringify(out.静置观察, null, 2));

// ── D. 那 4 对同名节点：比对内容，判断是不是我自己复制的 ────────────
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);
out.节点内容 = await page.evaluate(() => {
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const r = n.getBoundingClientRect();
    // 节点上所有可见文字（标题 + 参数卡文字），用于两两比对
    const txt = (n.innerText || '').replace(/\s+/g, ' ').trim();
    rows.push({
      id,
      类型前缀: (id || '').split('-')[0],
      标题: n.querySelector('input')?.value || null,
      transform: (n.style.transform || '').replace(/translate\(([^)]*)\)/, '$1'),
      视口内位置: [Math.round(r.x), Math.round(r.y)],
      文本: txt.slice(0, 150),
      文本长度: txt.length,
    });
  }
  return rows;
});
console.log('\n节点内容（视口内）=');
for (const r of out.节点内容) console.log(`  ${r.id.padEnd(18)} ${r.文本}`);
console.log('\n两两同名配对：');
const byName = {};
for (const r of out.节点内容) {
  const k = (r.文本.split(' ')[0] || '?');
  (byName[k] ||= []).push(r);
}
out.同名配对 = Object.entries(byName).filter(([, v]) => v.length > 1).map(([k, v]) => ({
  共同开头: k,
  节点: v.map((n) => ({ id: n.id, 位置: n.transform, 文本长度: n.文本长度, 文本: n.文本 })),
  内容是否相同: v.every((n) => n.文本 === v[0].文本),
}));
console.log(JSON.stringify(out.同名配对, null, 2));

await writeFile(resolve(HERE, '.evidence/ci1-follow-deep.json'), JSON.stringify(out, null, 2));
console.log('\n（本步仍只读：未点「取消」、未切故事板、未碰任何节点）');
await browser.close();

// Batch CT-4：`[999,664]`（lucide `sliders-horizontal`）点下去到底发生了什么。
//
// CT-3 的读数：点它之后 8 次采样里新增了 5 个文字叶子
//   `Lib Image 2.5 Pro` / `16:9 · 标准画质 · 2K · 1张` / `15` / `高级设置` / `智能引用 AutoLink`
//   —— 这 5 个**全是节点内联卡片上的内容**（generate-media.md 的「图片节点」表），
//   而且同时 `z-index:601` 的大编辑器不见了。
// ⇒ 假设：点它 = **关掉大编辑器、节点内联卡片回来**。
//
// ⭐ 但这个假设只由「前后两个采样点」支撑，缺时间线 ——
//   有可能是「它开了个设置面板，顺带把大编辑器顶掉了」，
//   也可能是「过了一会儿才关」（延迟渲染）。CM 批次只记了两种关闭方式
//   （点遮罩 / 点右上角收拢箭头），这里要的是**第三种关闭方式**的硬证据。
//
// 本步：点之前记基线 → 点 → **每 100ms 采 10 次**，每��记
//   ① `z-index:601` 的大编辑器在不在
//   ② 内联卡片的那 5 个字出现了几个
//   ③ 新出现的文字叶子
// 顺带拍两张图（大编辑器里的这枚按钮，从没拍过）：
//   M-341 翻译提示词的悬停气泡（大编辑器底栏里）
//   M-342 大编辑器底栏 7 枚按钮的全景
import { launch, open, closePromos, ORIGIN, shot, SHOTS } from './lib.mjs';
import { resolve } from 'node:path';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const IMG = 'i-9nlG6HdjK2';
const LOG = console.log;

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
  const p = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!b) return null; const r = b.getBoundingClientRect();
    return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (p) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1200); }
};
const modalOn = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return { 开: false };
  const r = d.getBoundingClientRect();
  return { 开: r.width > 0 && r.height > 0, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
const cardWords = (page) => page.evaluate(() => {
  const want = ['Lib Image 2.5 Pro', '16:9 · 标准画质 · 2K · 1张', '高级设置', '智能引用 AutoLink'];
  const all = [...document.querySelectorAll('body *')].filter((e) => e.children.length === 0).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
  return want.filter((w) => all.includes(w));
});
const leaves = (page) => page.evaluate(() => {
  const res = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 60) continue;
    res.push(`${t}@${Math.round(r.x)},${Math.round(r.y)}`);
  }
  return res;
});

const { browser, page } = await launch();
await boot(page);
await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 }));
}, IMG);
await page.waitForTimeout(800);
const fp = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const f = [...n.querySelectorAll('button')].find((b) => {
    const c = (b.className || '').toString();
    return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
  });
  const r = f.getBoundingClientRect();
  for (let dx = 4; dx < r.width; dx += 3) for (let dy = 4; dy < r.height; dy += 3) {
    const el = document.elementFromPoint(r.x + dx, r.y + dy);
    if (el && (el === f || f.contains(el) || el.contains(f))) return [Math.round(r.x + dx), Math.round(r.y + dy)];
  }
  return null;
}, IMG);
await page.mouse.click(fp[0], fp[1]);
await page.waitForTimeout(1400);
LOG(`大编辑器: ${JSON.stringify(await modalOn(page))}`);

// ---- 📸 M-342 大编辑器底栏全景 ------------------------------------------------
const barRect = await page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  const b = d.querySelector('[data-generator-control-bar]');
  const r = b.getBoundingClientRect();
  return [Math.round(r.x) - 8, Math.round(r.y) - 26, Math.round(r.width) + 16, Math.round(r.height) + 44];
});
await shot(page, 'M-342-大编辑器-底栏七枚按钮.png', { clip: { x: barRect[0], y: barRect[1], width: barRect[2], height: barRect[3] } });
LOG(`📸 M-342 clip=${JSON.stringify(barRect)}`);

// ---- 📸 M-341 翻译提示词悬停气泡 ---------------------------------------------
await page.mouse.move(10, 10); await page.waitForTimeout(300);
await page.mouse.move(959 + 16, 664 + 16);
await page.waitForTimeout(1100);
const tip = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const t = [...document.querySelectorAll('[role="tooltip"]')].filter(vis).map((e) => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
  return t;
});
LOG(`悬停气泡: ${JSON.stringify(tip)}`);
if (tip.length) {
  const r = tip[0].rect;
  const clip = { x: Math.max(0, r[0] - 150), y: Math.max(0, r[1] - 300), width: 560, height: 380 };
  await shot(page, 'M-341-大编辑器-翻译提示词悬停.png', { clip });
  LOG(`📸 M-341 clip=${JSON.stringify(clip)}`);
}
await page.mouse.move(10, 10); await page.waitForTimeout(400);

// ---- ⭐ 时间序列：点 `[999,664]` ----------------------------------------------
const out = { tip, timeline: [] };
LOG('\n===== 点 [999,664] 的 100ms 时间序列 =====');
LOG(`  t=-0  基线: 大编辑器=${JSON.stringify(await modalOn(page))} 卡片词=${JSON.stringify(await cardWords(page))}`);
const base = await leaves(page);
await page.mouse.click(999 + 16, 664 + 16);
for (let i = 0; i < 10; i += 1) {
  await page.waitForTimeout(100);
  const m = await modalOn(page);
  const c = await cardWords(page);
  const l = await leaves(page);
  const bset = new Set(base);
  const nu = [...new Set(l.filter((x) => !bset.has(x)).map((x) => x.split('@')[0]))];
  out.timeline.push({ t: (i + 1) * 100, 大编辑器: m, 卡片词数: c.length, 卡片词: c, 新增文字: nu });
  LOG(`  t=+${(i + 1) * 100}ms  大编辑器开=${m.开}  卡片词数=${c.length}  新增=${JSON.stringify(nu)}`);
}
out.结论 = {
  大编辑器在点击后多久消失: out.timeline.find((x) => !x.大编辑器.开)?.t ?? null,
  卡片词在点击后多久出现: out.timeline.find((x) => x.卡片词数 > 0)?.t ?? null,
};
LOG(`\n结论: ${JSON.stringify(out.结论)}`);

await writeFile(new URL('./batchCT4.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCT4.json');
await browser.close();

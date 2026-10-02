// Batch CH-6：重拍模式切换器 —— 这次要**框住悬停气泡**。
//
// CH-4 那张 M-321 拍的时候鼠标已经移到 (5,400)，气泡没了，
// 于是图只能证明「顶栏有两个没文字的图标」，**说不出它们是工作流和故事板** ——
// 而「更正手册的形态写法」这条恰恰需要读者一眼看到名字。
//
// ⭐ 本轮**按 `aria-label` 定位**（不用坐标），鼠标停在「故事板」那枚上**不动**再拍。
// ⛔ 本轮**不改任何数据** —— 只读 + 拍图。
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
await page.waitForTimeout(1200);

const boxOf = (aria) => page.evaluate((a) => {
  const b = document.querySelector(`button[aria-label="${a}"],[role="button"][aria-label="${a}"]`);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), w: Math.round(r.width), h: Math.round(r.height) };
}, aria);

const wf = await boxOf('工作流');
const sb = await boxOf('故事板');
out.工作流图标 = wf;
out.故事板图标 = sb;
console.log('工作流图标 =', JSON.stringify(wf), ' 故事板图标 =', JSON.stringify(sb));
if (!wf || !sb) { console.log('!! 定位失败'); await browser.close(); process.exit(1); }

// 鼠标停在「故事板」上，等气泡冒出来，**不动**再拍
await page.mouse.move(sb.cx, sb.cy);
await page.waitForTimeout(1500);
await page.mouse.move(sb.cx + 1, sb.cy);
await page.waitForTimeout(1400);
out.气泡 = await page.evaluate(() => {
  const grab = (sel) => [...document.querySelectorAll(sel)].map((e) => (e.innerText || e.textContent || '').trim()).filter((t) => t && t.length < 40);
  return { role: grab('[role="tooltip"]'), mantine: grab('[class*="Tooltip"]') };
});
out.命中确认 = await page.evaluate(({ x, y }) => {
  const el = document.elementFromPoint(x, y);
  const b = el ? el.closest('button,[role="button"]') : null;
  return b ? b.getAttribute('aria-label') : null;
}, { x: sb.cx, y: sb.cy });
console.log('气泡 =', JSON.stringify(out.气泡), ' 命中 aria =', out.命中确认);

// clip 要把图标**和它下方/上方的气泡**都框进去
const clip = { x: Math.max(0, wf.cx - 130), y: 0, width: 300, height: 170 };
await shot(page, 'M-321-顶栏两个模式图标-悬停显示名字.png', { clip });

out.收尾未改动 = true;
await writeFile(resolve(HERE, '.evidence/ch6-mode-switch-shot.json'), JSON.stringify(out, null, 2));
console.log('\n拍完。clip =', JSON.stringify(clip));
await browser.close();

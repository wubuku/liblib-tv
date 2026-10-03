// Batch CT-1：给底栏三枚匿名按钮定名。
//
// CT-0 拿到了决定性的新证据：
//   `[959,664]` 的 svg class 是 **`iconify--libtv`**（产品自己的图标集），
//   `[999,664]`（已知 = 高级设置）是 **`iconify--lucide`**；
//   `[744,664]`（彩色球）**一个 svg 都没有**，`data-*` 也是空。
//   ⇒ 三枚按钮走的是三条不同的「身份来源」，靠同一招是认不出来的。
//
// 本步全部针对这 3 枚：
//   ① 完整 outerHTML（含 svg 全部属性，看有没有图标名线索 / 注释）
//   ② **逐枚 hover 读气泡**（`title` / `aria-describedby` / `role="tooltip"` /
//      Mantine Tooltip）—— 这是唯一还没用过的手段
//   ③ class 尾部完整读完（CT-0 截断在 120 字符，`[744,664]` 的 `cu…` 没读完）
//
// ⛔ 第 ④ 步（点 `[959,664]`）只在**描述为空**时点一次，CO 已记它会弹
//    `提示词为空，请输入内容后点击` ⇒ 不扣积分。要验的是**归属**：
//    这个 toast 到底是这枚按钮弹的，还是「描述为空时点任何提交类按钮都弹它」。
//    所以要带**阴性对照**：描述为空时点彩色球 `[744,664]`（同样没有文字），
//    看它弹不弹同样的 toast。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const IMG = 'i-9nlG6HdjK2';
const TARGETS = [
  { key: 'ball-744', rect: [744, 664], 已知: '彩色球（无 svg / 无 data-*）' },
  { key: 'libtv-959', rect: [959, 664], 已知: 'iconify--libtv 斜杆图标 / data-practice-generator-lock' },
  { key: 'lucide-999', rect: [999, 664], 已知: 'iconify--lucide 滑块图标 / 高级设置（阳性对照）' },
];

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

const { browser, page } = await launch();
await boot(page);
await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 }));
}, IMG);
await page.waitForTimeout(900);
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

// ---- ① 完整 outerHTML + 完整 class -----------------------------------------
const full = await page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  const at = (x) => {
    const e = document.elementFromPoint(x, 664 + 16);
    let b = e; while (b && b.tagName !== 'BUTTON') b = b.parentElement;
    return b;
  };
  return [744, 959, 999].map((x) => {
    const b = at(x);
    if (!b) return { x, 找到: false };
    return {
      x, 找到: true,
      outerHTML: b.outerHTML,
      完整class: (b.className || '').toString(),
      完整title: b.getAttribute('title'),
      ariaDescribedby: b.getAttribute('aria-describedby'),
      svgClass: b.querySelector('svg')?.getAttribute('class') || null,
      svgAttrs: b.querySelector('svg') ? Object.fromEntries([...b.querySelector('svg').attributes].map((a) => [a.name, a.value])) : null,
      全部path: b.querySelector('svg') ? [...b.querySelectorAll('path,rect,circle,line,polyline,polygon')].map((q) => `${q.tagName}:${q.getAttribute('d') || q.getAttribute('points') || ''}`) : [],
      伪元素背景: (() => { const cs = getComputedStyle(b, '::before'); return cs.content !== 'none' ? cs.background.slice(0, 120) : null; })(),
      子元素数: b.children.length,
      子元素tag: [...b.children].map((c) => `${c.tagName.toLowerCase()}.${(c.className || '').toString().slice(0, 60)}`),
    };
  });
});
console.log('===== ① 三枚匿名按钮完整身份 =====');
for (const f of full) {
  console.log(`\n--- @x=${f.x} ---`);
  if (!f.找到) { console.log('  没找到'); continue; }
  console.log(`  title        = ${JSON.stringify(f.完整title)}`);
  console.log(`  describedby  = ${JSON.stringify(f.ariaDescribedby)}`);
  console.log(`  svg class    = ${f.svgClass}`);
  console.log(`  svg attrs    = ${JSON.stringify(f.svgAttrs)}`);
  console.log(`  全部 path    = ${JSON.stringify(f.全部path)}`);
  console.log(`  伪元素背景   = ${JSON.stringify(f.伪元素背景)}`);
  console.log(`  子元素       = ${JSON.stringify(f.子元素tag)}`);
  console.log(`  完整 class   = ${f.完整class}`);
  console.log(`  outerHTML    = ${f.outerHTML.slice(0, 700)}`);
}

// ---- ② 逐枚 hover 读气泡 -----------------------------------------------------
console.log('\n===== ② hover 读气泡（4 种来源全查） =====');
const hoverReport = [];
for (const t of TARGETS) {
  await page.mouse.move(10, 10);
  await page.waitForTimeout(250);
  const before = await page.evaluate(() => document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip,[title]').length);
  await page.mouse.move(t.rect[0] + 16, t.rect[1] + 16);
  await page.waitForTimeout(1100);
  const r = await page.evaluate((prev) => {
    const vis = (e) => { const b = e.getBoundingClientRect(); const s = getComputedStyle(e); return b.width > 0 && b.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    const tips = [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip')]
      .filter(vis).map((e) => ({ 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), id: e.id || null, rect: (() => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; })() }));
    const titled = [...document.querySelectorAll('[title]')].filter(vis).map((e) => ({ title: e.getAttribute('title'), tag: e.tagName.toLowerCase() }));
    return { tips, titled };
  }, before);
  const state = await page.evaluate(([x]) => {
    const el = document.elementFromPoint(x, 680);
    let b = el; while (b && b.tagName !== 'BUTTON') b = b.parentElement;
    return b ? { cursor: getComputedStyle(b).cursor, 背景: getComputedStyle(b).backgroundColor, class含hover: (b.className || '').toString().includes('hover:bg-btn-ghost-hover') } : null;
  }, t.rect);
  console.log(`\n  ${t.key} (${t.已知})`);
  console.log(`     role=tooltip 气泡: ${JSON.stringify(r.tips)}`);
  console.log(`     [title] 元素   : ${JSON.stringify(r.titled)}`);
  console.log(`     hover 态样式    : ${JSON.stringify(state)}`);
  hoverReport.push({ ...t, ...r, state });
}

await writeFile(new URL('./batchCT1.json', import.meta.url), JSON.stringify({ full, hoverReport }, null, 2));
console.log('\n已写 tools/batchCT1.json');
await browser.close();

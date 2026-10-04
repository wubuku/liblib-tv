// Batch EG-0b：EG-0 的三重自证通过了，但 ⋯ 菜单点不开 —— 查这个节点到底有没有菜单入口。
//
// ⭐ 先诊断再动作（EF 批的教训）：把这个节点 DOM 里所有可交互元素列出来，
//    看「⋯」到底是不是 button、藏在哪一层。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEG0b.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {} };
const 记 = (s) => console.log("· " + s);
const 目标 = 'm-LYXQggoOBr';

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  // 选中它
  const 框 = await page.evaluate((id) => {
    const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [r.left, r.top, r.width, r.height];
  }, 目标);
  if (!框) { console.log('节点不在'); }
  await page.mouse.click(框[0] + 框[2] / 2, 框[1] + 框[3] / 2);
  await page.waitForTimeout(1200);

  const 选中 = await page.evaluate((id) => {
    const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    return { selected: el.className.toString().includes('selected'), cls: el.className.toString().slice(0, 120) };
  }, 目标);
  console.log('选中态:', JSON.stringify(选中));

  // ⭐ 列出节点内所有可交互元素
  const 元素 = await page.evaluate((id) => {
    const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!el) return [];
    const out = [];
    for (const e of el.querySelectorAll('button,[role="button"],[class*="cursor-pointer"]')) {
      const r = e.getBoundingClientRect();
      if (r.width === 0) continue;
      const cs = getComputedStyle(e);
      out.push({
        tag: e.tagName,
        text: (e.innerText || '').trim().slice(0, 20),
        aria: e.getAttribute('aria-label') || '',
        cls: e.className.toString().slice(0, 80),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        opacity: cs.opacity, cursor: cs.cursor, visible: cs.visibility,
      });
    }
    return out;
  }, 目标);
  结果.读数.节点内可交互 = 元素;
  console.log(`\n节点内可交互元素 ${元素.length} 个:`);
  for (const e of 元素) console.log(`  <${e.tag}> "${e.text}" aria="${e.aria}" box=${JSON.stringify(e.box)} op=${e.opacity} cur=${e.cursor}`);

  // 悬停看看有没有浮出的操作条
  await page.mouse.move(框[0] + 框[2] / 2, 框[1] + 框[3] / 2);
  await page.waitForTimeout(1200);
  const 悬停后 = await page.evaluate((id) => {
    const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const out = [];
    for (const e of document.querySelectorAll('button,[role="button"]')) {
      const r = e.getBoundingClientRect();
      if (r.width === 0) continue;
      if (!el.contains(e) && !el.parentElement?.contains(e)) continue;
      out.push({ text: (e.innerText || '').trim().slice(0, 16), aria: e.getAttribute('aria-label') || '', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
    return out;
  }, 目标);
  结果.读数.悬停后 = 悬停后;
  console.log(`\n悬停后（含祖先）可交互 ${悬停后.length} 个:`);
  for (const e of 悬停后) console.log(`  "${e.text}" aria="${e.aria}" box=${JSON.stringify(e.box)}`);

  await page.screenshot({ path: '.evidence/batchEG0b-素材节点结构.png' });
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEG0b.json ===');
}

// Batch CT-5：`[999,664]` 到底点没点上？
//
// CT-4 时间序列（100ms × 10）：大编辑器 **10/10 一直开着**，卡片词不变，
//   新增 0 ⇒ **[999,664] 什么都没发生**。
// 而 CT-3 曾读到「点它之后大编辑器不见了 + 新增 5 个卡片词」—— CT-4 证明
//   那是**基线快照采得太早**（大编辑器还在渲染，`Lib Image 2.5 Pro` 等文字
//   后来才出现，被误读成「点击新增」），且 `modalOn=false` 是 probe 内部
//   的 ESC 造成的，不是点击造成的。⇒ CT-3 的 ② 作废。
//
// 剩下唯一的问题：**这枚按钮到底点没点上？**
// ⭐ 既定教训：「拍局部图前逐项验『那个点上最上面的是不是它』」——
//   本次一路都用固定坐标 `page.mouse.click(999+16, 664+16)`，**从没验过**。
//
// 本步：
//   ① 在按钮矩形内扫点，用 `elementFromPoint` 找出**真落在它身上**的点
//   ② 报告「固定坐标那个点上最上面的是谁」
//   ③ 用验过的落点再点一次，读全页新增 + **大编辑器内部所有按钮的 class
//      变化**（纯图标面板没有文字，只有 class 变化能测到）
//   ④ 顺便把描述填上内容再点一次 —— ⭐ 假设：它需要描述有内容才响应
//      （和「翻译提示词」同属一排，都读提示词）
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
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
  if (!d) return false;
  const r = d.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
});
const modalBtnSig = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return [];
  return [...d.querySelectorAll('button')].map((b) => {
    const r = b.getBoundingClientRect();
    return `${Math.round(r.x)},${Math.round(r.y)}|${(b.className || '').toString().slice(0, 50)}|${b.getAttribute('aria-disabled')}|${b.getAttribute('aria-pressed')}`;
  }).sort();
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
await page.waitForTimeout(1800);      // ⭐ 多等一会，让渲染彻底完成（CT-3 的坑）
LOG(`大编辑器: ${await modalOn(page)}`);

// ---- ① 扫点验落点 -------------------------------------------------------------
const scan = await page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  const b = d.querySelector('[data-practice-generator-lock][aria-disabled]');   // [999,664] 那枚
  const r = b.getBoundingClientRect();
  const own = [];
  for (let dx = 2; dx < r.width; dx += 2) for (let dy = 2; dy < r.height; dy += 2) {
    const el = document.elementFromPoint(r.x + dx, r.y + dy);
    if (el && (el === b || b.contains(el))) own.push([Math.round(r.x + dx), Math.round(r.y + dy)]);
  }
  const fixed = document.elementFromPoint(1015, 680);
  let f = fixed; while (f && f !== document.body && f.tagName !== 'BUTTON') f = f.parentElement;
  return {
    按钮rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    自身命中点数: own.length,
    落点样例: own.slice(0, 6),
    固定坐标点上的最上层: f ? { tag: f.tagName.toLowerCase(), class: (f.className || '').toString().slice(0, 80), text: (f.innerText || '').slice(0, 20) } : null,
    固定坐标点是否命中它: own.some((p) => p[0] === 1015 && p[1] === 680),
  };
});
LOG(`\n===== ① 落点扫描 =====\n${JSON.stringify(scan, null, 2)}`);

const out = { scan, trials: [] };

// ---- ③④ 两次点：描述空 / 描述有内容 -----------------------------------------
const trial = async (label, fillDesc) => {
  if (fillDesc) {
    await page.evaluate(() => {
      const host = document.querySelector('[data-practice-anchor="gen.prompt"]');
      const ta = host?.querySelector('textarea,[contenteditable="true"]');
      if (!ta) return 'no-editor';
      ta.focus();
      if ('value' in ta) { ta.value = '一只猫坐在窗台上'; ta.dispatchEvent(new Event('input', { bubbles: true })); }
      else { ta.textContent = '一只猫坐在窗台上'; ta.dispatchEvent(new InputEvent('input', { bubbles: true })); }
      return 'ok';
    });
    await page.waitForTimeout(700);
  }
  const descVal = await page.evaluate(() => {
    const ta = document.querySelector('[data-practice-anchor="gen.prompt"] textarea,[data-practice-anchor="gen.prompt"] [contenteditable="true"]');
    return ta ? (ta.value ?? ta.textContent ?? '').slice(0, 30) : null;
  });
  const beforeL = await leaves(page);
  const beforeB = await modalBtnSig(page);
  const pt = scan.落点样例[Math.floor(scan.落点样例.length / 2)] ?? [1015, 680];
  await page.mouse.move(pt[0], pt[1]);
  await page.waitForTimeout(300);
  await page.mouse.click(pt[0], pt[1]);
  const series = [];
  for (let i = 0; i < 6; i += 1) {
    await page.waitForTimeout(300);
    const l = await leaves(page); const bs = new Set(beforeL);
    series.push({ 大编辑器: await modalOn(page), 新增: [...new Set(l.filter((x) => !bs.has(x)).map((x) => x.split('@')[0]))] });
  }
  const afterB = await modalBtnSig(page);
  const bDiff = afterB.filter((x) => !beforeB.includes(x));
  const allNew = [...new Set(series.flatMap((s) => s.新增))];
  LOG(`\n--- ${label}（落点 ${JSON.stringify(pt)}，描述=${JSON.stringify(descVal)}）---`);
  LOG(`    大编辑器始终开着: ${series.every((s) => s.大编辑器)}`);
  LOG(`    新增文字 ${allNew.length} 种: ${JSON.stringify(allNew)}`);
  LOG(`    大编辑器内按钮 class/aria 变化 ${bDiff.length} 条: ${JSON.stringify(bDiff.slice(0, 8))}`);
  const rec = { label, pt, descVal, series, btnDiff: bDiff };
  out.trials.push(rec);
  // 复位
  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);
  return rec;
};

await trial('描述为空', false);
await trial('描述有内容', true);

await writeFile(new URL('./batchCT5.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCT5.json');
await browser.close();

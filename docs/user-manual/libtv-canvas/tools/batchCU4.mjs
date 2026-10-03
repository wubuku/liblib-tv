// Batch CU-4：查清资产管理工具行到底几枚、各叫什么。
//
// ⛔ **CU-3 的图和 CU-0 的读数对不上，必须查清再收尾**：
//   - CU-3 实测那行 `总数: 6`，CU-0 只列出 4 枚（另 2 枚有文字，被归到 L1）
//   - ⭐ 更要紧：M-344 图上第 3 枚是**人像图标**（看着像「角色造型室」），
//     而 CU-0 记 `[144,764]` 叫 `切换小地图` —— **图标和名字对不上**。
//
// 本步只读：逐枚报 `aria-label` / 气泡 / svg path / 完整 class，
// 并把「容器内所有 button」一次列全（不按 y 过滤，避免漏）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;

const { browser, page } = await launch();
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
const p = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (p) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1200); }

const info = await page.evaluate(() => {
  const host = document.querySelector('[data-toolbar-collapsed]');
  const hr = host.getBoundingClientRect();
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return {
    容器: { rect: [Math.round(hr.x), Math.round(hr.y), Math.round(hr.width), Math.round(hr.height)], 全文: (host.innerText || '').replace(/\s+/g, ' ').trim(), class: (host.className || '').toString() },
    按钮: [...host.querySelectorAll('button,[role="button"]')].filter(vis).map((b) => {
      const r = b.getBoundingClientRect();
      return {
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
        aria: b.getAttribute('aria-label'),
        title: b.getAttribute('title'),
        tag: b.tagName.toLowerCase(),
        data: Object.fromEntries([...b.attributes].filter((a) => a.name.startsWith('data-')).map((a) => [a.name, a.value])),
        svgPaths: [...b.querySelectorAll('svg path')].map((p2) => (p2.getAttribute('d') || '').slice(0, 52)),
        svgCircles: [...b.querySelectorAll('svg circle,svg rect,svg line')].map((c) => `${c.tagName}:${c.getAttribute('cx') || c.getAttribute('x') || ''},${c.getAttribute('cy') || c.getAttribute('y') || ''},r=${c.getAttribute('r') || ''}`),
        cls: (b.className || '').toString().slice(0, 70),
      };
    }).sort((a, z) => a.rect[0] - z.rect[0]),
  };
});
LOG(`容器: ${JSON.stringify(info.容器, null, 1)}`);
LOG(`\n容器内可见可交互元素 ${info.按钮.length} 枚:`);
for (const b of info.按钮) {
  LOG(`\n  @${JSON.stringify(b.rect)}  <${b.tag}>  text=${JSON.stringify(b.text)}  aria=${JSON.stringify(b.aria)}  title=${JSON.stringify(b.title)}`);
  LOG(`     data=${JSON.stringify(b.data)}`);
  LOG(`     svgPath=${JSON.stringify(b.svgPaths)}`);
  LOG(`     svgOther=${JSON.stringify(b.svgCircles)}`);
  LOG(`     class=${b.cls}`);
}

const readTips = (page) => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...new Set([...document.querySelectorAll('[role="tooltip"]')].filter(vis).map((e) => (e.innerText || '').replace(/\s+/g, ' ⏎ ').trim()))];
});
LOG(`\n===== 逐枚 hover 读气泡 =====`);
const tips = {};
for (const b of info.按钮) {
  await page.mouse.move(400, 300); await page.waitForTimeout(220);
  const base = await readTips(page);
  await page.mouse.move(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
  await page.waitForTimeout(800);
  const novel = (await readTips(page)).filter((t) => !base.includes(t));
  tips[`${b.rect[0]}`] = novel;
  LOG(`  @${JSON.stringify(b.rect).padEnd(20)} aria=${JSON.stringify(b.aria)} 气泡=${novel.length ? `「${novel.join(' | ')}」` : '⛔无'}`);
}

await writeFile(new URL('./batchCU4.json', import.meta.url), JSON.stringify({ info, tips }, null, 2));
LOG('\n已写 tools/batchCU4.json');
await browser.close();

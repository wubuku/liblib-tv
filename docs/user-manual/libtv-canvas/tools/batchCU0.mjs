// Batch CU-0：用「hover 读气泡」这条新路，全画布普查匿名控件。
//
// CT 批次最大的收获不是那三枚按钮，而是**手段**：
//   ⭐⭐ 此前所有批次认控件靠 `aria-label` / 图标 path / 坐标，
//     **几乎没人系统地 hover 过**。CT 一 hover，镜头球直接报出
//     `Panavision DXL2 / 已关闭 / Arri Signature Prime / 35mm / ƒ/4`。
//
// 本步：把全画布**每一个「无文字且无 aria-label」的可交互元素**列出来，
//   逐个 hover 读四种气泡来源（role=tooltip / [title] / aria-describedby /
//   Mantine Tooltip），看有多少个能一次读出真名。
//
// ⛔ **一个都不点。** hover 不写盘、不扣积分。
// ⚠️ 每 hover 一个之间必须把鼠标移到画布角落，否则前一个的气泡会被误读。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;

// 「匿名」分级普查：先列出**全部**可交互元素，再一层层看筛掉了什么。
// ⭐ CU-0 第一版直接一步筛到「无文字+无 aria+无 title」，读出 **0 个** ——
//   说明过滤条件把东西全筛掉了。治法：**分级**，每级都报数，
//   这样才知道是哪一层杀掉的，而不是只看到最终那个 0。
const listAll = (page) => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('button,[role="button"],[role="tab"],[role="menuitem"]')) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (r.x + r.width < 0 || r.x > 1440 || r.y + r.height < 0 || r.y > 810) continue;
    const text = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const aria = e.getAttribute('aria-label');
    const title = e.getAttribute('title');
    let zone = '其他';
    if (e.closest('[data-sidebar-container]')) zone = '画布左下工具条';
    else if (e.closest('nav[data-canvas-navbar]')) zone = '顶栏';
    else if (e.closest('.react-flow__node')) zone = `节点卡片`;
    else if (e.closest('[data-toolbar-collapsed]')) zone = '资产管理入口';
    const dataAttrs = Object.fromEntries([...e.attributes].filter((a) => a.name.startsWith('data-')).map((a) => [a.name, a.value]));
    out.push({
      zone, 节点id: e.closest('.react-flow__node')?.getAttribute('data-id') || null,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text, aria, title, dataAttrs,
      等级: text ? 'L1 有文字' : aria ? 'L2 有 aria' : title ? 'L3 有 title' : 'L4 全匿名',
      tag: e.tagName.toLowerCase(),
      cursor: s.cursor,
      svgClass: e.querySelector('svg')?.getAttribute('class') || null,
      svgPaths: [...e.querySelectorAll('svg path')].map((p) => (p.getAttribute('d') || '').slice(0, 46)),
      子元素: [...e.children].map((c) => `${c.tagName.toLowerCase()}.${(c.className || '').toString().slice(0, 40)}`),
    });
  }
  return out;
});

const readTips = (page) => page.evaluate(() => {
  const vis = (e) => {
    const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0;
  };
  const tips = [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip')].filter(vis)
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean);
  return [...new Set(tips)];
});

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

const all = await listAll(page);
LOG(`全画布视口内可交互元素 ${all.length} 个`);
const tier = {};
for (const it of all) (tier[it.等级] ||= []).push(it);
for (const k of ['L1 有文字', 'L2 有 aria', 'L3 有 title', 'L4 全匿名']) {
  LOG(`  ${k.padEnd(10)} ${(tier[k] || []).length} 个`);
}
const zones = {};
for (const it of all) (zones[it.zone] ||= []).push(it);
LOG(`  按区域: ${Object.entries(zones).map(([z, a]) => `${z}=${a.length}`).join('  ')}`);

LOG(`\n===== L2/L3/L4（无文字的）逐个 hover 读气泡 =====`);
const cand = all.filter((it) => it.等级 !== 'L1 有文字');
LOG(`待测 ${cand.length} 个`);
const results = [];
for (const it of cand) {
  await page.mouse.move(700, 400);
  await page.waitForTimeout(240);
  const base = await readTips(page);
  const [x, y, w, h] = it.rect;
  await page.mouse.move(Math.round(x + w / 2), Math.round(y + h / 2));
  await page.waitForTimeout(800);
  const tips = await readTips(page);
  const novel = tips.filter((t) => !base.includes(t));
  results.push({ ...it, 气泡: novel });
  const 标 = novel.length ? `✅「${novel.join(' / ')}」` : '⛔无';
  LOG(`  ${it.等级} ${it.zone}${it.节点id ? `(${it.节点id})` : ''} @${JSON.stringify(it.rect)} aria=${it.aria} title=${JSON.stringify(it.title)} data=${JSON.stringify(it.dataAttrs)} ${标}`);
}

const 有名 = results.filter((r) => r.气泡.length);
LOG(`\n===== 结果：${有名.length} / ${results.length} 个 hover 读出真名 =====`);
const byName = {};
for (const r of 有名) (byName[r.气泡[0]] ||= []).push(r);
for (const [n, arr] of Object.entries(byName)) LOG(`  「${n}」 × ${arr.length}  —— ${[...new Set(arr.map((a) => `${a.zone}${a.节点id ? `(${a.节点id})` : ''}`))].join('、')}`);

await writeFile(new URL('./batchCU0.json', import.meta.url), JSON.stringify({ all, results }, null, 2));
LOG('\n已写 tools/batchCU0.json');
await browser.close();

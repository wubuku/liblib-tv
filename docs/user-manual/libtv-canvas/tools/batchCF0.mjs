// Batch CF-0：把 Batch CE 那套「按 SVG 路径认按钮」的方法，推广到**视频 / 图片 / 音频**三类节点。
//
// CE 已经坐实：文本节点的「翻译提示词」路径以 `M15.52 7.2c.16 0 .31.1.37.26l3.8 10…` 开头。
// 这一步先问：**另外三类节点的「翻译提示词」是不是同一枚路径？**「提示词优化」又是哪一枚？
// ⭐ 如果路径**逐字相同** ⇒ 同一枚图标，方法可以照搬；不同 ⇒ 每类要单独记。
//
// ⛔ 本步只读图标与状态，**不点**。先把这张「按钮身份证表」建起来。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
// 各节点的 data-id（画布现状：2 文本 / 2 音频 / 2 图片 / 2 视频 / 逐帧拉片 / 导演台 / 智能剪辑）
const NODES = [
  { id: 'v-eMpqKtiLlx', kind: '视频节点 3' },
  { id: 'i-9nlG6HdjK2', kind: '图片节点 2' },
  { id: 'a-CUfJfmKzUJ', kind: '音频节点 6' },
  { id: 't-2AK3Ukyxj3', kind: '文本节点 1' },
];

const { browser, page } = await launch();
const out = { table: [] };

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
await page.waitForTimeout(800);

const readBar = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'not in DOM' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const buttons = [...node.querySelectorAll('button,[role="button"]')].filter(vis).map((b) => {
    const r = b.getBoundingClientRect();
    const svg = b.querySelector('svg');
    const paths = svg ? [...svg.querySelectorAll('path')].map((p) => p.getAttribute('d')).join(' ') : '';
    return {
      aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 16),
      disabled: b.disabled === true, hasSvg: !!svg,
      pathHead: paths.slice(0, 52),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    };
  });
  return { buttons };
}, nid);

for (const n of NODES) {
  // 先 ⌘0 收全画布，再逐个点开
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2000);
  const clicked = await page.evaluate((nid) => {
    const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!el) return false;
    const r = el.getBoundingClientRect();
    // 点节点中心；不在视口内就先把视口挪过去
    return { has: true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }, n.id);
  if (!clicked.has) { out.table.push({ ...n, err: 'not in DOM' }); continue; }
  // 选中
  await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), n.id);
  await page.waitForTimeout(1800);
  const bar = await readBar(n.id);
  out.table.push({ ...n, buttons: bar.buttons?.filter((b) => b.hasSvg || b.t) || [], err: bar.err });
}

await writeFile(resolve(HERE, '.evidence/cf0-bars.json'), JSON.stringify(out, null, 2));
// 打印一张「按钮身份证表」：每类节点、有图标的按钮按路径前缀归类
const byPath = {};
for (const row of out.table) {
  for (const b of (row.buttons || [])) {
    if (!b.hasSvg) continue;
    const k = b.pathHead.slice(0, 40);
    byPath[k] = byPath[k] || { pathHead: k, 出现于: [] };
    byPath[k].出现于.push(`${row.kind}${b.t ? `(${b.t})` : ''}`);
  }
}
console.log('=== 各节点参数条上带图标的按钮 ===');
for (const row of out.table) {
  console.log(`\n[${row.kind}] ${row.err || ''}`);
  for (const b of (row.buttons || [])) {
    console.log(`   aria=${b.aria} 文字="${b.t}" disabled=${b.disabled} 路径=${b.pathHead}`);
  }
}
console.log('\n=== 路径归类（同一路径 = 同一枚图标）===');
for (const k of Object.keys(byPath)) {
  console.log(`  ${k}\n     → ${byPath[k].出现于.join(' / ')}`);
}
await browser.close();

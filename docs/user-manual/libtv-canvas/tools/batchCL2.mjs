// Batch CL-2：收尾 + 把 CL-1 那两处判据缺陷补上。
//
// ⛔ 先认账：CL-1 第一遍被我用 `head -70` 掐掉了输出管道，进程吃到 SIGPIPE 直接死，
//    **它点过 `⤢ 详情`，走之前在画布上留下了一个节点**。第二遍开跑时基线就已经是 12。
//    ⇒ 这不是「读数对不上」，是**上一轮自己捅的娄子**。本步按 id 认人，把它和
//    「使用」造的那个一起删掉。
//
// 本步三件事：
//   ① 列出全部节点 + 名字，**按 id 与 11 个基线比对**找出多出来的，只删 `m-` 且名字
//      以 `素材-` 开头的那几个（= 本轮广场点击造出来的），**绝不碰用户原有的**；
//   ② 补验：详情浮层里那枚 `使用` 按钮，**它的祖先链里到底有没有「风格详情」** ——
//      CL-1 因为容器选错（`querySelectorAll('*')` 命中了 `body`）没验成；
//   ③ 补上「广场面板内部到底有哪些控件」—— 这决定「真正的排序入口有没有」，
//      CL-1 的容器判据（`width<1000`）把面板判没了。
// ⛔ 不发布、不充值、不提交生成。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

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
await page.waitForTimeout(6000);
await closePromos(page);
await page.waitForTimeout(1500);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(700);
}
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);

// ① 全部节点 + 名字 + 多余项
out.节点全表 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), 名字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 34), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
console.log('════ 画布节点全表 ════');
for (const n of out.节点全表) console.log(`  ${n.id.padEnd(18)} ${n.名字}`);
out.多余 = out.节点全表.filter((n) => !BASE.includes(n.id));
console.log('\n与 11 个基线相比多出来的 =', JSON.stringify(out.多余, null, 1));
out.可删 = out.多余.filter((n) => n.id.startsWith('m-') && n.名字.startsWith('素材-'));
out.不敢碰 = out.多余.filter((n) => !out.可删.includes(n));
console.log('判定可删（本轮广场造出来的）=', JSON.stringify(out.可删.map((n) => n.id)));
console.log('判定不敢碰 =', JSON.stringify(out.不敢碰.map((n) => n.id)));

// ② 详情浮层里「使用」的祖先链（只读）
console.log('\n════ 详情浮层里的「使用」：祖先链验证 ════');
await page.locator('button[aria-label="素材库"]').first().click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(2000);
const lb = page.locator('text=风格库').first();
if (await lb.count()) { await lb.click({ timeout: 8000 }).catch(() => {}); await page.waitForTimeout(2200); }
const det = page.locator('button[aria-label="详情"]').first();
await det.hover().catch(() => {});
await page.waitForTimeout(700);
await det.click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(1700);
out.使用按钮 = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '使用');
  if (!b) return { 找到: false };
  const r = b.getBoundingClientRect();
  const chain = [];
  for (let a = b; a && a !== document.body && chain.length < 8; a = a.parentElement) {
    const q = a.getBoundingClientRect();
    chain.push({ tag: a.tagName.toLowerCase(), cls: (a.className || '').toString().slice(0, 60), 尺寸: [Math.round(q.width), Math.round(q.height)], 文字含风格详情: (a.innerText || '').includes('风格详情'), 文字片段: (a.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) });
  }
  return { 找到: true, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 祖先链: chain };
});
if (out.使用按钮.找到) {
  for (const c of out.使用按钮.祖先链) console.log(`  ${c.tag}.${c.cls}  ${JSON.stringify(c.尺寸)} 含「风格详情」=${c.文字含风格详情}  「${c.文字片段}」`);
} else console.log('  ⛔ 页面上没有「使用」按钮（详情浮层没开？）');

// ③ 广场面板内部控件（换判据：从「含风格广场且含十个分类之一」的最深容器里读）
console.log('\n════ 广场面板内部控件 ════');
out.面板 = await page.evaluate(() => {
  // ⭐ 换判据：取**同时**含 `推荐` 与 `摄影写真` 与 `仅看可商用` 的**最小**容器
  let best = null;
  for (const e of document.querySelectorAll('div')) {
    const t = e.innerText || '';
    if (!t.includes('摄影写真') || !t.includes('仅看可商用')) continue;
    if (!best || (e.innerText || '').length < (best.innerText || '').length) best = e;
  }
  if (!best) return null;
  const r = best.getBoundingClientRect();
  const ctrls = [...best.querySelectorAll('button,[role="button"],[role="checkbox"],[role="combobox"],input')].map((b) => {
    const q = b.getBoundingClientRect();
    if (q.width <= 0 || q.height <= 0) return null;
    return { tag: b.tagName.toLowerCase(), 文字: (b.innerText || b.getAttribute('placeholder') || '').replace(/\s+/g, ' ').trim().slice(0, 16), aria: b.getAttribute('aria-label'), role: b.getAttribute('role'), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
  }).filter(Boolean);
  const seen = new Set(); const uniq = [];
  for (const c of ctrls) { const k = `${c.文字}|${c.aria}|${c.role}`; if (!seen.has(k)) { seen.add(k); uniq.push(c); } }
  return { 面板rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 面板内按钮总数: ctrls.length, 去重后: uniq };
});
if (out.面板) {
  console.log('  面板 =', JSON.stringify(out.面板.面板rect), ' 面板内按钮 =', out.面板.面板内按钮总数, ' 去重后 =', out.面板.去重后.length);
  for (const c of out.面板.去重后) console.log(`   ${c.tag} 「${c.文字}」 aria=${c.aria} role=${c.role} @${JSON.stringify(c.rect)}`);
  out.像排序的 = out.面板.去重后.filter((c) => /全部|最新|最热|价格|排序|时间|人气/.test(c.文字 || ''));
  console.log('\n  ⭐ 其中像「排序」的 =', JSON.stringify(out.面板.像排序的));
} else console.log('  ⛔ 仍未定位到面板');

await writeFile(resolve(HERE, '.evidence/cl2-cleanup-and-panels.json'), JSON.stringify(out, null, 2));
console.log('\n本步只读；删除放到下一步做');
await browser.close();

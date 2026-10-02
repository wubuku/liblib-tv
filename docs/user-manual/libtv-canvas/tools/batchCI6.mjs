// Batch CI-6：被动抓画布加载时的 JSON 响应。
//
// 目的有两个，都是只读的：
//   ① **「跟随」到底是什么。** 到目前为止全部证据都来自界面：
//      `正在跟随` / `取消ESC` / `按 ESC 退出` / `aria="退出跟随"`。
//      如果项目数据里带 follow / agent / director 之类的字段，
//      就能**用数据回答**，而不是靠「全站只有 TV Director 叫感知画布」去推。
//   ② **别的 projectId。** CI-5 从画布下拉里一个 id 都没读到
//      （菜单项不带 href / data-project-id，只有 React 内部状态），
//      画布清单几乎肯定来自某个接口，从响应里捞最省事。
//
// ⭐ 只挂 `response` 监听器，**不发任何请求**。⛔ 不点「取消」、不派发任务。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
const caught = [];
page.on('response', async (res) => {
  const ct = (res.headers()['content-type'] || '');
  if (!/json/i.test(ct)) return;
  const u = res.url();
  if (/analytics|sentry|track|log|report|beacon/i.test(u)) return;
  let body = null;
  try { body = await res.json(); } catch { return; }
  caught.push({ url: u.slice(0, 220), status: res.status(), body });
});

await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(4000);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(8000);

console.log(`\n抓到 ${caught.length} 个 JSON 响应\n`);
for (const c of caught) console.log(`  [${c.status}] ${c.url}`);

// ① 全库搜「跟随 / agent / director / follow」类字段
const KEY = /follow|agent|director|watch|observe|trackUser|collab|presence|online|spectat/i;
const hits = [];
const walk = (node, path, depth) => {
  if (depth > 9 || node == null) return;
  if (Array.isArray(node)) { node.slice(0, 3).forEach((v, i) => walk(v, `${path}[${i}]`, depth + 1)); return; }
  if (typeof node !== 'object') return;
  for (const [k, v] of Object.entries(node)) {
    const p = `${path}.${k}`;
    if (KEY.test(k)) {
      hits.push({ 路径: p, 值: typeof v === 'object' ? JSON.stringify(v).slice(0, 220) : String(v).slice(0, 220) });
    }
    walk(v, p, depth + 1);
  }
};
for (const c of caught) walk(c.body, c.url.split('?')[0].split('/').slice(-1)[0], 0);
console.log('\n════ 命中「跟随/agent/director」类字段 ════');
if (!hits.length) console.log('  （0 命中）');
for (const h of hits.slice(0, 60)) console.log(`  ${h.路径}\n      = ${h.值}`);

// ② 从响应里捞别的 projectId
const PIDS = new Set();
const PID = /["']([0-9a-f]{24,32})["']/g;
for (const c of caught) {
  const s = JSON.stringify(c.body);
  if (!/project/i.test(s) && !/canvas/i.test(s)) continue;
  let m; PID.lastIndex = 0;
  while ((m = PID.exec(s))) if (m[1] !== '34226ef170f248248c74f85290228f6b') PIDS.add(m[1]);
}
console.log(`\n════ 响应里出现过的 24~32 位十六进制串（当 projectId 候选）════`);
console.log([...PIDS].slice(0, 30).join('\n') || '  （无）');

await writeFile(resolve(HERE, '.evidence/ci6-network.json'), JSON.stringify({ 响应: caught.map((c) => ({ url: c.url, status: c.status })), 命中字段: hits, 候选id: [...PIDS] }, null, 2));
console.log('\n（本步纯被动监听，未发任何写请求）');
await browser.close();

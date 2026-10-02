// Batch CI-7：CI-6 捞到了 30 个 32 位十六进制串，但**分不清哪个是画布**。
// 本步只做两件事，然后这条线就收工去写正文：
//   ① 从 `detail-by-space` 那个响应里读出**画布名 ↔ projectId** 的对应关系；
//   ② 挑 2 张本轮没开过的画布，用**修正后的判据**（整条祖先链 opacity 连乘）
//      量「正在跟随」横幅有没有出现过可见态 —— CI-2 就是在这读数上栽的。
// ⛔ 纯读：不点「取消」、不派任务。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const MINE = '34226ef170f248248c74f85290228f6b';
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=${MINE}`;
const out = {};

// ① 画布清单
{
  const { browser, page } = await launch();
  let list = null;
  page.on('response', async (res) => {
    if (list) return;
    if (!/json/i.test(res.headers()['content-type'] || '')) return;
    if (!/detail-by-space|space/i.test(res.url())) return;
    try {
      const b = await res.json();
      const d = b?.data;
      if (!d) return;
      // 找带「画布」字样的数组
      const seen = new Set();
      const walk = (n, p, d0) => {
        if (d0 > 6 || n == null) return;
        if (Array.isArray(n)) {
          if (n.length && typeof n[0] === 'object' && /project|canvas|画布/i.test(JSON.stringify(n[0]).slice(0, 300))) {
            for (const it of n.slice(0, 60)) {
              const id = it.id || it.projectId || it.project_id;
              if (id) seen.add(JSON.stringify({ id, 文字: (it.name || it.title || it.projectName || '').slice(0, 24) }));
            }
          }
          n.slice(0, 2).forEach((v, i) => walk(v, `${p}[${i}]`, d0 + 1));
          return;
        }
        if (typeof n === 'object') for (const [k, v] of Object.entries(n)) walk(v, `${p}.${k}`, d0 + 1);
      };
      walk(d, 'data', 0);
      if (seen.size) list = [...seen].map((s) => JSON.parse(s));
    } catch { /* 忽略 */ }
  });
  await open(page, URL_);
  await page.waitForTimeout(7000);
  out.画布清单 = list || [];
  console.log('════ 画布清单 ════');
  for (const c of out.画布清单) console.log(`  ${String(c.id).padEnd(34)} ${c.文字}`);
  await browser.close();
}

const others = out.画布清单.filter((c) => c.id !== MINE);
if (!others.length) { console.log('\n仍没拿到画布清单 ⇒ 关于「别的画布上横幅会不会出现」，输出只能是「没测到」。'); process.exit(0); }

// ② 挑 2 张量横幅
const INSTRUMENT = () => {
  window.__log = [];
  const t0 = performance.now();
  let last = null;
  const sample = () => {
    const el = document.querySelector('[aria-label="退出跟随"]');
    let rec;
    if (el) {
      let acc = 1;
      for (let a = el; a; a = a.parentElement) { acc *= Number(getComputedStyle(a).opacity); if (a.tagName === 'HTML') break; }
      rec = { t: Math.round(performance.now() - t0), 在: true, 累计: Math.round(acc * 1000) / 1000 };
    } else rec = { t: Math.round(performance.now() - t0), 在: false };
    const k = JSON.stringify({ ...rec, t: 0 });
    if (k !== last) { last = k; window.__log.push(rec); }
  };
  sample();
  const id = setInterval(sample, 80);
  setTimeout(() => clearInterval(id), 20000);
};

out.试画布 = [];
for (const c of others.slice(0, 2)) {
  const { browser, ctx, page } = await launch({ reducedMotion: 'no-preference' });
  await ctx.addInitScript(INSTRUMENT);
  await page.goto(`${ORIGIN}/canvas?spaceId=10354929&projectId=${c.id}`, { waitUntil: 'commit', timeout: 60000 });
  await page.waitForTimeout(16000);
  const log = await page.evaluate(() => window.__log);
  const alive = log.filter((r) => r.在);
  const peak = alive.length ? Math.max(...alive.map((r) => r.累计)) : null;
  const 可见样本 = alive.filter((r) => r.累计 > 0.05).length;
  console.log(`\n画布「${c.文字}」(${String(c.id).slice(0, 8)}): 横幅${alive.length ? `出现于 ${alive[0].t}ms` : '**从未出现**'}；峰值累计opacity=${peak}；可见样本 ${可见样本}/${alive.length}`);
  console.log('  样本 =', JSON.stringify(log.slice(0, 10)));
  out.试画布.push({ 名: c.文字, id: c.id, 出现: alive.length > 0, 峰值: peak, 可见样本, 样本数: alive.length, 样本: log.slice(0, 12) });
  await browser.close();
}

await writeFile(resolve(HERE, '.evidence/ci7-canvas-list.json'), JSON.stringify(out, null, 2));
console.log('\n汇总 =', JSON.stringify(out.试画布.map((c) => ({ 名: c.名, 出现: c.出现, 峰值: c.峰值 }))));

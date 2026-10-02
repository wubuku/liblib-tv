// Batch CI-5：换一张**从没开过的画布**去抓「正在跟随」横幅可见的那一瞬。
//
// CI-4 把 CI-2/3 的结论推翻了一半，而且是**推翻我自己**：
//   · 外层完整 class = `pointer-events-none fixed left-1/2 top-0 z-[305]
//     -translate-x-1/2 motion-safe:transition-opacity motion-safe:duration-200`
//   · `motion-safe:` 修饰的是 **transition**（过渡），**不是可见性** —— 我上一轮
//     把 class 尾巴当成「动效才显示」，是过度解读。
//   · 真正的事实是：**外层 inline opacity = 0**，而且在
//     `reducedMotion:'no-preference'` 下**也是 0**。
//
// ⭐ 而 CI-2 之所以误判成「恒为 1、从不淡出」，是因为**量错了节点**：
//    采样器量的是 `border` 那个子容器（自身 opacity 恒 1），
//    真正的动画发生在**它上面一层**。⇒ 累计 opacity 必须逐层连乘，
//    只看目标自己的 opacity **必然**读出一个假的稳定值。
//
// ⭐⭐ 那它为什么现在是 0？两种可能，本步就是去分辨：
//    (a) 它是**加载时浮现、随后自己淡出**的通知（`transition-opacity` 支持这个读法）；
//    (b) 它**只在某个条件下才出现**，现在那个条件不成立。
//    判别办法：换一张**本轮从没打开过**的画布。如果那边能抓到可见态，
//    就说明是「按画布触发」；如果那边也是 0，输出只能是「没测到」。
//
// ⛔ 只读：只开菜单读 projectId、只导航、只量。点完就切回画布 2。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const out = {};

// ⭐ 关键修正：量**整条祖先链的累计 opacity**，不是只量目标自己。
const INSTRUMENT = () => {
  window.__log = [];
  const t0 = performance.now();
  let last = null;
  const sample = () => {
    const el = document.querySelector('[aria-label="退出跟随"]');
    let rec;
    if (el) {
      let acc = 1;
      let owner = null;
      for (let a = el; a; a = a.parentElement) {
        const o = Number(getComputedStyle(a).opacity);
        acc *= o;
        if (owner === null && o < 1) owner = (a.className || '').toString().slice(0, 40);
        if (a.tagName === 'HTML') break;
      }
      const box = el.getBoundingClientRect();
      rec = { t: Math.round(performance.now() - t0), 在: true, 累计: Math.round(acc * 1000) / 1000, 首个不透明层: owner, 文字: (el.innerText || '').trim() };
    } else {
      rec = { t: Math.round(performance.now() - t0), 在: false };
    }
    const k = JSON.stringify({ ...rec, t: 0 });
    if (k !== last) { last = k; window.__log.push(rec); }
  };
  sample();
  const id = setInterval(sample, 80);
  setTimeout(() => clearInterval(id), 25000);
};

// ── 先从画布下拉里取一|本轮没开过的 projectId ───────────────────
{
  const { browser, page } = await launch({ reducedMotion: 'no-preference' });
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(2500);
  // 画布切换器：按钮正文是 `画布 N`
  const sw = page.locator('button').filter({ hasText: /^画布\s*\d+$/ }).first();
  out.切换器找到 = await sw.count();
  if (out.切换器找到) {
    await sw.click({ timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(1500);
    out.画布列表 = await page.evaluate(() => {
      const rows = [];
      for (const el of document.querySelectorAll('a[href*="projectId="], [data-project-id], [role="menuitem"]')) {
        const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
        const href = el.getAttribute('href') || '';
        const m = href.match(/projectId=([0-9a-f]+)/i) || href.match(/projectId=([^&]+)/i);
        const pid = el.getAttribute('data-project-id') || (m ? m[1] : null);
        if (t || pid) rows.push({ 文字: t.slice(0, 24), projectId: pid, href: href.slice(0, 120) });
      }
      return rows;
    });
    console.log('════ 画布列表 ════');
    for (const r of out.画布列表.slice(0, 40)) console.log(`  ${(r.projectId || '?').padEnd(34)} ${r.文字}`);
  }
  await browser.close();
}

const candidates = [...new Set((out.画布列表 || []).map((r) => r.projectId).filter((p) => p && p !== '34226ef170f248248c74f85290228f6b'))];
console.log('\n候选 projectId =', JSON.stringify(candidates));
if (!candidates.length) { console.log('没取到别的画布，本步到此为止（输出只能是「没测到」）'); process.exit(0); }

// ── 逐张试，最多试 3 张，每张都量累计 opacity ────────────────────
out.试过的画布 = [];
for (const pid of candidates.slice(0, 3)) {
  const { browser, ctx, page } = await launch({ reducedMotion: 'no-preference' });
  await ctx.addInitScript(INSTRUMENT);
  await page.goto(`${ORIGIN}/canvas?spaceId=10354929&projectId=${pid}`, { waitUntil: 'commit', timeout: 60000 });
  const shots = [];
  const deadline = Date.now() + 14000;
  let best = 0;
  while (Date.now() < deadline) {
    const st = await page.evaluate(() => {
      const el = document.querySelector('[aria-label="退出跟随"]');
      if (!el) return { 在: false };
      let acc = 1;
      for (let a = el; a; a = a.parentElement) { acc *= Number(getComputedStyle(a).opacity); if (a.tagName === 'HTML') break; }
      const r = el.getBoundingClientRect();
      return { 在: true, 累计: Math.round(acc * 1000) / 1000, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    });
    if (st.在 && st.累计 > best) {
      best = st.累计;
      if (st.累计 >= 0.85) {
        const name = `M-329-${pid.slice(0, 6)}-t${Date.now() % 100000}.png`;
        await shot(page, name, { clip: { x: Math.max(0, st.rect[0] - 300), y: 0, width: 780, height: 84 } });
        shots.push({ name, 累计: st.累计 });
        console.log(`  ⭐ ${pid.slice(0, 8)} 抓到可见态 累计=${st.累计} → ${name}`);
      }
    }
    await page.waitForTimeout(150);
  }
  const log = await page.evaluate(() => window.__log);
  const alive = log.filter((r) => r.在);
  const everVisible = alive.filter((r) => r.累计 > 0.05);
  console.log(`\n画布 ${pid.slice(0, 8)}: 元素出现 ${alive.length ? alive[0].t + 'ms' : '从未出现'}；累计>0.05 的样本 ${everVisible.length}/${alive.length}；峰值 ${Math.max(0, ...alive.map((r) => r.累计))}`);
  out.试过的画布.push({ projectId: pid, 峰值累计: alive.length ? Math.max(...alive.map((r) => r.累计)) : null, 样本数: alive.length, 可见样本: everVisible.length, 截图: shots, 前若干条: log.slice(0, 8) });
  await browser.close();
  if (shots.length) break;
}

await writeFile(resolve(HERE, '.evidence/ci5-other-canvas.json'), JSON.stringify(out, null, 2));
console.log('\n峰值汇总 =', JSON.stringify(out.试过的画布.map((c) => ({ pid: c.projectId.slice(0, 8), 峰值: c.峰值累计, 可见样本: c.可见样本 }))));
console.log('（本步只读：只开菜单读 id、只导航、只量）');

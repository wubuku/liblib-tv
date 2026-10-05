// ⛔⛔ Batch FE 事故抢救：闭环复原第 4 轮之后，11 个节点全部「不在 DOM」。
//
// 机制和 FB 事故一模一样：节点被推得离原点很远 ⇒ 节点群包围盒巨大
// ⇒ `⌘0` fit 出来的 zoom 极小 ⇒ React Flow 只渲染视口内的节点 ⇒ 一个都不渲染。
//
// ⭐⭐⭐⭐⭐ 这次新学到的一条**硬规矩**（FB 事故的加强版）：
//   **关态（吸附态）下绝对不能用「误差换算像素 + 多轮迭代」做精确复原。**
//   吸附把每一个落点量化到 12 的栅格 ⇒ 本轮的「剩余误差」是假的
//   ⇒ 下一轮算出的方向和段长都是错的 ⇒ 越修越偏。
//   FE-2 的 finally 就是这么发散的：
//     轮1 -60264 → -60300｜轮2 → -60216｜轮3 → -60451（⭐ 甚至不是 12 的倍数）｜轮4 → -59724（过冲 727）
//   ⇒ **正确做法：复原前先把「网格吸附」切到开态（不吸附），全程 1:1 复原，最后再切回关态。**
//
// 本脚本分三段，每段都先只读诊断再决定动不动：
//   A 只读：读 zoom / 节点数 / 视口 transform，看清现场
//   B 抢救：⌘0 → 不行就「整理画布」+「保留」
//   C 收尾：切回关态（svg=1）→ 读全部坐标 → 打印需要人工确认的清单
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, BASE } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'restore-fe.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

const 现场 = () => page.evaluate((ids) => {
  const v = document.querySelector('.react-flow__viewport');
  const cs = v ? getComputedStyle(v) : null;
  const 节点 = [...document.querySelectorAll('.react-flow__node')];
  const 在DOM = {}, 坐标表 = {};
  for (const id of ids) {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    在DOM[id] = !!n;
    if (n) {
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      坐标表[id] = t ? [Number(t[1]), Number(t[2])] : null;
    }
  }
  return {
    zoom: cs && /matrix\(([^)]+)\)/.exec(cs.transform || '') ? Number(/matrix\(([^)]+)\)/.exec(cs.transform)[1].split(',')[0]) : null,
    视口transform: cs ? cs.transform : null,
    渲染出的节点数: 节点.length,
    渲染出的id: 节点.map((n) => n.getAttribute('data-id')),
    在DOM, 坐标表,
  };
}, BASE);

const 开关 = () => page.evaluate(() => {
  let b = null;
  for (const x of document.querySelectorAll('button')) {
    const r = x.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if ((x.getAttribute('aria-label') || '').includes('网格吸附')) { b = x; break; }
  }
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { svg数: b.querySelectorAll('svg').length, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
});
const 点开关 = async () => {
  const g = await 开关();
  if (!g) return null;
  await page.mouse.move(g.中心[0], g.中心[1]); await page.waitForTimeout(300);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 170); await page.waitForTimeout(400);
  return 开关();
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 180));

  // ——— A 只读诊断 ———
  let s = await 现场();
  记(`【A1】zoom=${s.zoom}｜渲染节点 ${s.渲染出的节点数} 个｜视口 ${s.视口transform}`);
  R.读数.A1 = s;
  await page.screenshot({ path: EVID + 'fe-restore-A1-现场.png' });

  // ——— B 抢救 ———
  if (s.渲染出的节点数 < BASE.length) {
    记('⛔ 节点没全部渲染，先按 ⌘0');
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(4500);
    s = await 现场();
    记(`【B1】⌘0 之后 zoom=${s.zoom}｜渲染 ${s.渲染出的节点数} 个`);
    R.读数.B1 = s;
  }

  if (s.渲染出的节点数 < BASE.length) {
    记('⛔ 仍然不渲染 ⇒ 用产品自带的「整理画布」+「保留」');
    const btn = await page.evaluate(() => {
      for (const x of document.querySelectorAll('button')) {
        const a = x.getAttribute('aria-label') || '';
        const t = (x.innerText || '').trim();
        if (a.includes('整理画布') || t.includes('整理画布')) {
          const r = x.getBoundingClientRect();
          return { aria: a, 文字: t, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
        }
      }
      return null;
    });
    记('   整理按钮：' + JSON.stringify(btn));
    if (btn) {
      await page.mouse.move(btn.中心[0], btn.中心[1]); await page.waitForTimeout(300);
      await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(2500);
      const 对话框 = await page.evaluate(() => [...document.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter((t) => t && t.length < 8).slice(0, 30));
      记('   弹窗里的按钮：' + JSON.stringify(对话框));
      const 保留 = await page.evaluate(() => {
        for (const x of document.querySelectorAll('button')) {
          if ((x.innerText || '').trim() === '保留') {
            const r = x.getBoundingClientRect();
            if (r.width > 0) return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
          }
        }
        return null;
      });
      记('   「保留」按钮：' + JSON.stringify(保留));
      if (保留) {
        await page.mouse.move(保留[0], 保留[1]); await page.waitForTimeout(300);
        await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(6000);
        await page.keyboard.press('Meta+0');
        await page.waitForTimeout(4000);
        s = await 现场();
        记(`【B2】整理+保留之后 zoom=${s.zoom}｜渲染 ${s.渲染出的节点数} 个`);
        R.读数.B2 = s;
      }
    }
  }

  // ——— C 收尾：开关回关态 + 最终坐标 ———
  const g = await 开关();
  记(`开关当前 svg=${g?.svg数}`);
  if (g && g.svg数 !== 1) {
    const b = await 点开关();
    记(`点回关态 → svg=${b?.svg数}`);
  }
  s = await 现场();
  记(`【C】最终 zoom=${s.zoom}｜渲染 ${s.渲染出的节点数}/${BASE.length} 个`);
  const 表 = {};
  let 偏 = 0, 缺 = 0;
  for (const id of BASE) {
    const 现 = s.坐标表[id] || null;
    表[id] = 现;
    if (!现) { 缺++; 记(`   ⛔ ${id} 读不到坐标`); continue; }
    const d = Math.hypot(现[0] - 坐标[id][0], 现[1] - 坐标[id][1]);
    if (d > 1.5) { 偏++; 记(`   ⚠️ ${id} 偏离 ${d.toFixed(1)}：基线 ${JSON.stringify(坐标[id])} → 现 ${JSON.stringify(现)}`); }
  }
  R.读数.最终 = { zoom: s.zoom, 渲染: s.渲染出的节点数, 表, 偏离个数: 偏, 读不到个数: 缺 };
  记(`偏离基线 ${偏} 个｜读不到 ${缺} 个｜全部是 12 的倍数？ ${Object.values(表).filter(Boolean).every((v) => v[0] % 12 === 0 && v[1] % 12 === 0)}`);
  await page.screenshot({ path: EVID + 'fe-restore-C-收尾.png' });
  记('⛔ 截图 fe-restore-A1-现场.png / fe-restore-C-收尾.png');
} catch (e) {
  记('❌ 出错：' + (e && e.message ? e.message : String(e)));
} finally {
  try { await page.waitForTimeout(12000); } catch (e) { /* 静置 */ }
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}

/**
 * 批次 261：**换入口 —— `Ctrl + 滚轮` 的真实档位是多少？和菜单的 `×1.2` 是不是同一套？**
 *
 * 📌 背景（两处既有记录 + 一处新发现）：
 *   · `20-reference.md:1067` 逐字写着「`Ctrl+滚轮` | 缩放（**约 `18%`/档**）| 实测」——
 *     这是**用户面**的一条断言，批次至今没复验过。
 *   · 批次 257 实测**缩放菜单**的 `放大视图`/`缩小视图` 是 `s(n+1) = round(s(n) × 1.2, 3)`
 *     ⇒ **`+20%`/档**，不是 `18%`。
 *   🔴 于是：**要么两条入口的步长真的不同**（手册要写两个数），
 *   **要么「`18%`」是错的**（要订正 + 台账回填）。**分歧点明确。**
 *
 * 📌 顺带把**滚轮这条路的上下限**也走一遍：
 *   批次 257 测到菜单路径是 `[0.08, 8]`（到达后**菜单项变灰**），
 *   而 `20-reference.md:1271` 的 `[8%, 800%]` 来自**输入框钳位**——
 *   ⇒ 滚轮这条路的限**是第三条独立证据**（立规 104 的正交读量）。
 *
 * 📌 判据（先写死）：**逐级读数、算相邻比值**，不预设是 `1.18` 还是 `1.2`；
 *   找到**平台期**（连读两次逐字相同）再停。
 *
 * 🔴 纪律：滚轮缩放是**纯视图**；不新建、不删除、不上传、不触发生成、
 *   不进扣费页、不点「保存到主体库」、不分享。
 *
 * 用法：node scripts/jimeng-b261.mjs      （读数落盘 /tmp/b261.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B261_OUT || '/tmp/b261.json';
const 宽 = 1280, 高 = 720;

const log = (...a) => console.log(a.join(' '));

const 读缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { scale: m ? Number(m[1]) : null, aria: z ? z.getAttribute('aria-label') : null };
});

const out = { 轮次: 'b261', 视口: [宽, 高], 修饰键试验: {}, 向上: [], 向下: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6500);

  // 🔴 先确定**哪个修饰键**能让滚轮缩放（macOS 上可能是 ⌘）—— 不预设
  const 键候选 = ['Control', 'Meta'];
  let 有效键 = null;
  for (const k of 键候选) {
    const 前 = await 读缩放(p);
    await p.mouse.move(宽 / 2, 高 / 2);
    await p.keyboard.down(k);
    await p.mouse.wheel(0, -240);
    await p.waitForTimeout(700);
    await p.mouse.wheel(0, -240);
    await p.waitForTimeout(700);
    await p.keyboard.up(k);
    const 后 = await 读缩放(p);
    const 变了 = 前.scale !== 后.scale;
    out.修饰键试验[k] = { 前: 前.scale, 后: 后.scale, 变了 };
    log(`  修饰键 ${k}：${前.scale} → ${后.scale} ${变了 ? '✅ 有效' : '❌ 无反应'}`);
    if (变了 && !有效键) 有效键 = k;
    // 🔴 复原到初始缩放，免得两条候选串味
    if (变了) {
      const z = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      await p.mouse.click(z[0], z[1]);
      await p.waitForTimeout(1000);
      const inp = await p.$('[data-testid="canvas-zoom-percent-input"]');
      if (inp) {
        await inp.fill(String(前.scale));
        await p.keyboard.press('Enter');
        await p.waitForTimeout(1200);
      }
      await p.keyboard.press('Escape');
      await p.waitForTimeout(800);
      const 复 = await 读缩放(p);
      log(`     复原到 ${复.scale}`);
    }
  }
  out.有效修饰键 = 有效键;
  if (!有效键) throw new Error('Control 与 Meta 都无法用滚轮缩放');

  const 走 = async (方向, 数组, 标签) => {
    let 前值 = (await 读缩放(p)).scale;
    数组.push({ 次: 0, scale: 前值 });
    for (let i = 1; i <= 40; i++) {
      await p.mouse.move(宽 / 2, 高 / 2);
      await p.keyboard.down(有效键);
      await p.mouse.wheel(0, 方向 * 240);
      await p.keyboard.up(有效键);
      await p.waitForTimeout(420);
      const s = await 读缩放(p);
      const 比 = 前值 ? +(s.scale / 前值).toFixed(6) : null;
      数组.push({ 次: i, scale: s.scale, aria: s.aria, 比 });
      log(`  ${标签} 第 ${i} 次 → ${s.scale}（${s.aria}）比=${比}`);
      if (s.scale === 前值) {
        log(`  ⇒ ${标签} 在第 ${i} 次**读数不再变化**，平台期 = ${s.scale}`);
        数组[数组.length - 1].平台期 = true;
        break;
      }
      前值 = s.scale;
    }
  };

  log(`=== 向上（${有效键}+滚轮放大）===\n`);
  await 走(-1, out.向上, '放大');
  log(`=== 向下（${有效键}+滚轮缩小）===\n`);
  await 走(1, out.向下, '缩小');

  // 📌 汇总：菜单是 ×1.2（批次 257），滚轮是几？
  const 有效的比 = [...new Set(out.向上.filter((x) => x.比).map((x) => x.比))];
  out.向上比值唯一值 = 有效的比;
  log('=== 汇总 ===');
  log(`滚轮放大各档比值的不同取值：${JSON.stringify(有效的比)}`);
  log(`菜单放大是 ×1.2（批次 257）。18% ⇒ ×1.18；20% ⇒ ×1.2。`);
  out.平台 = {
    滚轮上限: (out.向上.filter((x) => x.平台期).map((x) => x.scale).slice(-1)[0]) ?? null,
    滚轮下限: (out.向下.filter((x) => x.平台期).map((x) => x.scale).slice(-1)[0]) ?? null,
  };
  log(`滚轮平台期：上限 ${out.平台.滚轮上限}、下限 ${out.平台.滚轮下限}`);
} catch (e) {
  out.错误 = e.message;
  log('🔴 ' + e.message);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入 ' + OUT);
}
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);
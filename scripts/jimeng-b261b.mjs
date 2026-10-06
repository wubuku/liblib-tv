/**
 * 批次 261 · 重跑「向上」段：b261 的复原逻辑失败，向上那栏是从 `8` 起步的，**无效**。
 *
 * 📌 为什么必须重跑（立规 125：被测量的前提不成立时，结论不成立）：
 *   `b261` 想把缩放复原到初始值，用的是「点缩放钮 → 填输入框 → Enter」，
 *   实际**填进去的是字符串 `0.260267`**，而那个输入框**只接受 `8`–`800` 的整数百分比**
 *   ⇒ 复原失败，缩放被留在 **`8`（封顶）**。
 *   ⇒ 「向上」第 `1` 次就撞平台期，**那一栏不能用来下任何结论**。
 *   ✅ 「向下」那 `26` 档是有效的（它从 `8` 出发一路往下，与初始值无关）。
 *
 * 📌 本步：**重新开一页**，从初始缩放出发，把 `Ctrl + 滚轮` 的**向上整条阶梯**走完，
 *   一直走到读数不再变化为止 —— 让「向上」也有**完整阶梯**，
 *   而不是靠两档外推（立规 133：别拿两档当通性）。
 *
 * 🔴 纪律：滚轮缩放是纯视图；不新建、不删除、不上传、不触发生成、不进扣费页、不分享。
 *
 * 用法：node scripts/jimeng-b261b.mjs      （读数落盘 /tmp/b261b.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B261B_OUT || '/tmp/b261b.json';
const 宽 = 1280, 高 = 720;

const log = (...a) => console.log(a.join(' '));

const 读缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { scale: m ? Number(m[1]) : null, aria: z ? z.getAttribute('aria-label') : null };
});

const out = { 轮次: 'b261b-向上重跑', 视口: [宽, 高], 初始: null, 向上: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6500);

  // 📌 关键：**先断言起点是正常的初始缩放**，不是封顶（b261 踩的就是这个坑）
  const 初 = await 读缩放(p);
  out.初始 = 初;
  log(`初始 scale=${初.scale}（${初.aria}）`);
  if (!(初.scale > 0.05 && 初.scale < 1)) throw new Error(`起点异常（${初.scale}），本轮数据不可用`);

  let 前值 = 初.scale;
  out.向上.push({ 次: 0, scale: 前值 });
  for (let i = 1; i <= 40; i++) {
    await p.mouse.move(宽 / 2, 高 / 2);
    await p.keyboard.down('Control');
    await p.mouse.wheel(0, -240);
    await p.keyboard.up('Control');
    await p.waitForTimeout(420);
    const s = await 读缩放(p);
    const 比 = 前值 ? +(s.scale / 前值).toFixed(6) : null;
    out.向上.push({ 次: i, scale: s.scale, aria: s.aria, 比 });
    log(`  放大 第 ${i} 次 → ${s.scale}（${s.aria}）比=${比}`);
    if (s.scale === 前值) {
      log(`  ⇒ 向上在第 ${i} 次**读数不再变化**，平台期 = ${s.scale}`);
      out.向上[out.向上.length - 1].平台期 = true;
      break;
    }
    前值 = s.scale;
  }

  const 比集 = [...new Set(out.向上.filter((x) => x.比 != null && x.scale !== x.比).map((x) => x.比))];
  out.比值唯一值 = 比集;
  out.平台 = (out.向上.filter((x) => x.平台期).map((x) => x.scale).slice(-1)[0]) ?? null;
  log('=== 汇总 ===');
  log(`有效档数 ${out.向上.length - 1}；相邻比值的不同取值：${JSON.stringify(比集)}`);
  log(`平台期（滚轮放大上限）= ${out.平台}`);
  log(`18% ⇒ ×1.18；20% ⇒ ×1.2。菜单是 ×1.2（批次 257）。`);
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
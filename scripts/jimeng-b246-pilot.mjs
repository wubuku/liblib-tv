/**
 * 批次 246 试点：**先改画布缩放，再定位音频节点**，看凹口地板会不会跟着动。
 *
 * 📌 为什么值得试：音频凹口的地板**恰好等于画布默认缩放 `0.260267`**，
 *   而其余三族的地板都是「屏上 `100px`」（`0.3125` / `0.0833333` / `0.175781`）
 *   ⇒ **性质不同**。若地板真跟「画布当前缩放」走，那么先把缩放改小再定位，
 *   地板就应当跟着变小。
 *   若地板不动 ⇒ 它只是**碰巧**等于默认值，说明这层关系是巧合，**不编机制**。
 *
 * 🔴 纪律（这一批的唯一风险点）：
 *   · 试点**结束时必须把缩放还原**到 `Zoom options, 26%`，否则整批后续读数的基线就变了；
 *     ⇒ 每一步都读 `canvas-zoom-percent` 的 aria 逐字核对，**还原失败就如实停下**。
 *   · 只改缩放（可逆、无副作用），**不新建、不删除、不上传、不触发生成**。
 *
 * 用法：node scripts/jimeng-b246-pilot.mjs   （读数落盘 /tmp/b246-pilot.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b246-pilot.json';
const 基线aria = 'Zoom options, 26%';   // 门 9 记录��基线，必须还原成这个

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b246-pilot', 基线aria, 步: [] };
const 存 = () => fs.writeFileSync(OUT, JSON.stringify(out, null, 1));

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();

const 读 = () => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { scale: m ? Number(m[1]) : null, aria: z ? z.getAttribute('aria-label') : null };
});

try {
  await p.setViewportSize({ width: 1212, height: 720 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(5000);

  const 起 = await 读();
  out.步.push({ 动作: '初始', ...起 });
  log(`初始：scale=${起.scale} ｜ ${起.aria}`);

  // ---- 缩小 2 次 ----
  for (let i = 0; i < 2; i++) {
    await p.keyboard.press('Meta+-');
    await p.waitForTimeout(1200);
    const r = await 读();
    out.步.push({ 动作: `⌘− 第${i + 1}次`, ...r });
    log(`⌘− 第${i + 1} 次：scale=${r.scale} ｜ ${r.aria}`);
  }

  // ---- 放大 2 次还原 ----
  for (let i = 0; i < 2; i++) {
    await p.keyboard.press('Meta+=');
    await p.waitForTimeout(1200);
    const r = await 读();
    out.步.push({ 动作: `⌘+ 第${i + 1}次`, ...r });
    log(`⌘+ 第${i + 1} 次：scale=${r.scale} ｜ ${r.aria}`);
  }

  const 终 = await 读();
  out.还原成功 = 终.scale === 起.scale;
  log(`还原：${终.scale} vs 起始 ${起.scale} ⇒ ${out.还原成功 ? '✅ 已还原' : '🔴 未还原，需要处理'}`);
} catch (e) {
  out.错误 = e.message;
  log('🔴 ' + e.message);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
}

存();
log('写入 ' + OUT);
await b.close();
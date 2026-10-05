/**
 * 批次 205 e 轮：切清楚「批次 199 的 12 档逐字相同」和我这轮的 `w/2 − 542.9`
 * 到底谁对 —— 还是**两者量的是不同的状态**。
 *
 * 批次 199 §4.122.2 的做法：**一个新页签**里连续改 12 次宽度，读 `.react-flow__viewport`
 *   的 `transform` 原文 ⇒ 12 档全是 `translate(97.1509px, -30.4641px) scale(0.260267)`
 *   （其中 1000/1200/1240/1272/1279/1280/1281/1288/1300/1366/1400/1600）。
 * 而 205 的 a/d 轮：**每档新开页 + goto** 重新加载，
 *   读到的初态 tx 是 `57.1509(1200) / 63.1509(1212) / 67.1509(1220) / 73.1509(1232)`，
 *   正好落在 **`tx = w/2 − 542.9`** 这条直线上 ⇒ 只有 w=1280 那一档两者相同。
 *
 * ⚠️ 立规 79：**没对齐状态量之前，不许判谁对**。
 * 差别只有一个：199 是「**加载一次、之后只改视口**」，205 是「**按该宽度重新加载**」。
 * 本轮把两个方向都测出来：
 *   ① 1280 加载 → 改成 1212：tx 跟着走吗？（若是 ⇒ 199 的 1212 行才是真读数）
 *   ② 1280 加载 → 改成 1212 → 再改回 1280：tx 回得去吗？
 *   ③ 1212 加载 → 改成 1280：tx 跟着走吗？
 *
 * 只读：只读 transform，不点任何东西。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;

const log = (...a) => console.log(a.join(' '));
const 读tx = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  return { transform: vp ? vp.style.transform : null, 视口: [innerWidth, innerHeight] };
});

const out = { 轮次: 'b205e', 高度固定: H, 读法: { 批次199: '新页签加载一次，之后只 setViewportSize', 批次205: '每档新开页 + goto 重新加载' }, 步骤: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 记 = async (p, 名) => { const r = await 读tx(p); out.步骤.push({ 步骤: 名, ...r }); log(`  ${名} → ${r.transform}（视口 ${r.视口}）`); return r; };

// —— 方向①：1280 加载 → 1212 → 1280 ——
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);
    await 记(p, '① 1280 加载后');
    await p.setViewportSize({ width: 1212, height: H });
    await p.waitForTimeout(4000);
    await 记(p, '①→ 改成 1212');
    await p.setViewportSize({ width: 1280, height: H });
    await p.waitForTimeout(4000);
    await 记(p, '①→ 再改回 1280');
  } catch (e) { out.步骤.push({ 出错: e.message }); log('🔴 ' + e.message); }
  finally { await p.close(); }
}

// —— 方向②：1212 加载 → 1280 ——
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1212, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);
    await 记(p, '② 1212 加载后');
    await p.setViewportSize({ width: 1280, height: H });
    await p.waitForTimeout(4000);
    await 记(p, '②→ 改成 1280');
  } catch (e) { out.步骤.push({ 出错: e.message }); log('🔴 ' + e.message); }
  finally { await p.close(); }
}

// —— 方向③：1200 加载（批次 199 表里也有这一档）——
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1200, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);
    const r = await 记(p, '③ 1200 加载后');
    const m = r.transform ? /translate\(([-\d.]+)px/.exec(r.transform) : null;
    const tx = m ? Number(m[1]) : null;
    out.校验 = { 宽: 1200, 实测tx: tx, 公式_w2减542_9: 1200 / 2 - 542.9, 批次199表里的值: 97.1509 };
    log(`  校验：1200 档 tx=${tx}；公式 w/2−542.9=${1200 / 2 - 542.9}；批次 199 表里写的是 97.1509`);
  } catch (e) { out.步骤.push({ 出错: e.message }); log('🔴 ' + e.message); }
  finally { await p.close(); }
}

fs.writeFileSync('/tmp/b205e.json', JSON.stringify(out, null, 1));
log('\n写入 /tmp/b205e.json');
process.exit(0);

/**
 * 批次 258 · 第三步：**先把信噪比提上去，再判「它是不是 `16:9`」。**
 *
 * 📌 待判的那一点：`568.8752 / 320 = 1.777735`，而 `16/9 = 1.777778`，
 *   两者在**第 `5` 位小数**上差 `0.000043`。
 *   🔴 而现有读量的散布（时间线两个节点读出 `1200.0005` 与 `1200.0006`）
 *   说明**本测法的散布大约在 `1e-3` 量级** ⇒ `4.3e-5` 的差**落在噪声里，判不了**。
 *   ⇒ 立规 136：**精度不够时不要下结论，先把被测量的信噪比提上去。**
 *
 * 📌 **提信噪比的办法（本步做的事）**：误差来源是 `rect` 的量化 `q`，
 *   而 `布局宽 = rect宽 / scale` ⇒ **误差 `= q / scale`** ⇒ **`scale` 越大越准**。
 *   ⇒ 用缩放菜单的 `缩放至200%`（`scale = 2`，精确值）重测
 *   ⇒ 误差降为原来的 `1/2.6`；再用 `放大视图` 推到封顶 `8.0` 再测一次
 *   ⇒ 误差降为原来的 `1/30`。
 *   📌 **两次读数互为校验**（立规 104）。
 *
 * 📌 纪律：只改视图缩放，**不动任何画布内容**；不建不删不上传不生成不扣费不分享。
 *
 * 用法：node scripts/jimeng-b258c.mjs      （读数落盘 /tmp/b258c.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B258C_OUT || '/tmp/b258c.json';
const 宽 = 1280, 高 = 720;

const log = (...a) => console.log(a.join(' '));

const 读缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { scale: m ? Number(m[1]) : null, aria: z ? z.getAttribute('aria-label') : null };
});

const 打开菜单并点 = async (p, 词) => {
  const 钮 = await p.evaluate(() => {
    const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!z) return null;
    const b = z.getBoundingClientRect();
    return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)];
  });
  if (!钮) throw new Error('找不到缩放读数钮');
  await p.mouse.click(钮[0], 钮[1]);
  await p.waitForTimeout(1100);
  const 位 = await p.evaluate((w) => {
    const 面 = document.querySelector('[data-testid="canvas-zoom-menu"]');
    if (!面) return null;
    const e = Array.from(面.querySelectorAll('div,button')).find((x) => (x.innerText || '').trim().startsWith(w));
    if (!e) return null;
    const b = e.getBoundingClientRect();
    return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)];
  }, 词);
  if (!位) return false;
  await p.mouse.click(位[0], 位[1]);
  await p.waitForTimeout(1400);
  return true;
};

const 量全体 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const s = m ? Number(m[1]) : null;
  const 取 = (nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return null;
    const b = n.getBoundingClientRect();
    return {
      rect宽: b.width, rect高: b.height,
      css宽: Math.round((b.width / s) * 100000) / 100000,
      css高: Math.round((b.height / s) * 100000) / 100000,
    };
  };
  return {
    scale: s,
    图像: 取('node_gref4sw056'),
    视频: 取('node_236ctpehgg'),
    文本: 取('node_3bfb9r79qe'),
    时间线: 取('node_d4tjtpnatq'),
  };
});

const out = { 轮次: 'b258c', 视口: [宽, 高], 档: [], 结论: null };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6500);

  // 📌 档 1：进页时那个 scale（约 0.26）
  out.档.push({ 档: '进页', ...(await 量全体(p)) });

  // 📌 档 2：缩放至200%（scale 恰为 2）
  await 打开菜单并点(p, '缩放至200%');
  out.档.push({ 档: '缩放至200%', ...(await 量全体(p)) });

  // 📌 档 3：一路放大到封顶（批次 257 实测封顶是 8.0）
  for (let i = 0; i < 24; i++) {
    const 前 = await 读缩放(p);
    if (前.scale >= 8) break;
    await 打开菜单并点(p, '放大视图');
  }
  out.档.push({ 档: '放大到封顶', ...(await 量全体(p)) });

  log('=== 三档读数 ===');
  for (const d of out.档) {
    log(`  ${d.档}：scale=${d.scale}`);
    if (d.图像) log(`     图像 ${d.图像.css宽} × ${d.图像.css高}   （长宽比 ${(Math.max(d.图像.css宽, d.图像.css高) / Math.min(d.图像.css宽, d.图像.css高)).toFixed(7)}）`);
    if (d.视频) log(`     视频 ${d.视频.css宽} × ${d.视频.css高}`);
    if (d.文本) log(`     文本 ${d.文本.css宽} × ${d.文本.css高}`);
    if (d.时间线) log(`     时间线 ${d.时间线.css宽} × ${d.时间线.css高}`);
  }

  // 📌 判据：若三档读数在更高档位上**收敛到同一个值**，那个值就是布局常量
  const 高档 = out.档[out.档.length - 1];
  const 图宽 = 高档.图像 ? 高档.图像.css宽 : null;
  const 视频高 = 高档.视频 ? 高档.视频.css高 : null;
  out.算式 = {
    '16比9在320下': +(320 * 16 / 9).toFixed(6),
    测得图像宽: 图宽,
    差_图宽减16比9: 图宽 != null ? +(图宽 - 320 * 16 / 9).toFixed(6) : null,
    测得视频高: 视频高,
    差_视频高减16比9: 视频高 != null ? +(视频高 - 320 * 16 / 9).toFixed(6) : null,
    图像宽与视频高之差: (图宽 != null && 视频高 != null) ? +(图宽 - 视频高).toFixed(6) : null,
  };
  log('=== 判据 ===');
  log(JSON.stringify(out.算式, null, 1));
  const 差 = Math.abs(out.算式.差_图宽减16比9 ?? 0);
  out.结论 = 差 < 0.002
    ? `在 scale=${高档.scale} 下测得 ${图宽}，与 16:9 的 ${(320 * 16 / 9).toFixed(4)} 只差 ${差} ⇒ **可以按 16:9 记**`
    : `在 scale=${高档.scale} 下测得 ${图宽}，与 16:9 的 ${(320 * 16 / 9).toFixed(4)} 差 ${差}，**超出本档可分辨范围** ⇒ **不是 16:9**，按实测值记`;
  log(out.结论);
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
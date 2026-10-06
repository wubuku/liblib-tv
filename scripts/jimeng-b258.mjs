/**
 * 批次 258：**布局盒全普查** —— 把 `76` 个节点的**精确 CSS 宽高**一次性量出来，
 *   看 `568.875` 这个数到底出现在哪些地方。
 *
 * 📌 背景（批次 256）：视频 1 的布局高反推出来是 **`568.875`**，
 *   而批次 252 记过图像族的反推宽落在 **`568.8748 – 568.8765`**（判为该节点的 CSS 宽）。
 *   ⇒ **同一个数，一个当宽、一个当高。** 批次 256 如实记下「为什么，未测」。
 *
 * 📌 本批**不去猜**，只做一件最有信息量的事：**把分布量出来**（立规 135）。
 *   一个数在**一个量里出现一次**是巧合；**在 N 个地方出现**就是规律。
 *   ⇒ 判据（先写死）：
 *     · `568.875` 只出现在那两处 ⇒ **巧合，如实记为巧合**；
 *     · 它还出现在别处 / 出现在别的族 ⇒ **不是巧合**，那是某个共同来源；
 *     · 出现的地方能归出规则（如「每个媒体节点必有一边 = 568.875」）⇒ 写下来。
 *
 * 📌 **量法**：读 `scale`（视口 transform 里那个值），
 *   再用 `getBoundingClientRect().width / scale` 还原布局宽 —— 比 `offsetWidth` 强，
 *   因为 `offsetWidth` 是**取整**的（图像节点 `offsetWidth=569` 而 CSS 宽是 `568.875`
 *   ⇒ 差 `0.125`，只靠 `offsetWidth` **根本看不出**这个数）。
 *   ⚠️ 两个读法都要记，**互相校验**（立规 104 的正交读量）。
 *
 * 🔴 纪律：一个控件都不点；只开新页、只读 DOM；不建不删不上传不生成不扣费不分享。
 *
 * 用法：node scripts/jimeng-b258.mjs      （读数落盘 /tmp/b258.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B258_OUT || '/tmp/b258.json';
const 宽 = 1280, 高 = 720;
const 目标 = 568.875;

const log = (...a) => console.log(a.join(' '));

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
const out = { 轮次: 'b258', 视口: [宽, 高], 目标, 节点: [], 分布: {}, 结论: null };
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6500);

  const 数据 = await p.evaluate(() => {
    const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
    const scale = m ? Number(m[1]) : null;
    const 节点 = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const cls = typeof n.className === 'string' ? n.className : '';
      const kind = (cls.match(/react-flow__node-([a-z]+)/) || [])[1] || '（无 kind 修饰符）';
      const r = n.getBoundingClientRect();
      return {
        id: n.getAttribute('data-id'),
        kind,
        名: (n.innerText || '').trim().split('\n')[0] || null,
        offset宽: n.offsetWidth,
        offset高: n.offsetHeight,
        css宽: scale ? Math.round((r.width / scale) * 10000) / 10000 : null,
        css高: scale ? Math.round((r.height / scale) * 10000) / 10000 : null,
      };
    });
    return { scale, 节点 };
  });

  out.scale = 数据.scale;
  out.节点 = 数据.节点;
  log(`scale = ${数据.scale}，节点 ${数据.节点.length} 个`);

  // 📌 两个读法互相校验：css 宽应当约等于 offsetWidth
  const 差 = out.节点.map((n) => Math.abs(n.css宽 - n.offset宽));
  out.最大偏差 = Math.max(...差);
  log(`两个读法的最大偏差 = ${out.最大偏差}（offsetWidth 取整 ⇒ 预期 < 1）`);

  // 📌 分布：按 (kind, css宽, css高) 归并
  const 键 = (n) => `${n.kind} | ${n.css宽} × ${n.css高}`;
  const 计 = {};
  for (const n of out.节点) {
    const k = 键(n);
    (计[k] = 计[k] || { 个数: 0, 样例: [] });
    计[k].个数++;
    if (计[k].样例.length < 2) 计[k].样例.push(`${n.名}(${n.id})`);
  }
  out.分布 = 计;
  log('=== 布局盒分布（kind | css宽 × css高）===');
  for (const [k, v] of Object.entries(计)) log(`  ${String(v.个数).padStart(3)} 个  ${k}   e.g. ${v.样例.join(' / ')}`);

  // 🔴 目标数出现在哪些地方
  const 近 = (v) => Math.abs(v - 目标) < 0.01;
  out.命中 = [];
  for (const n of out.节点) {
    const 位 = [];
    if (近(n.css宽)) 位.push('宽');
    if (近(n.css高)) 位.push('高');
    if (位.length) out.命中.push({ 名: n.名, id: n.id, kind: n.kind, 作为: 位.join('+'), css宽: n.css宽, css高: n.css高 });
  }
  log(`=== 接近 ${目标} 的位置：${out.命中.length} 处 ===`);
  for (const h of out.命中) log(`  ${h.名} (${h.kind}) 当${h.作为}：${h.css宽} × ${h.css高}`);

  // 📌 判据（先写死的那三条）
  const 族集 = [...new Set(out.命中.map((h) => h.kind))];
  out.结论 = out.命中.length === 0
    ? '目标数一处都没出现（与批次 252/256 的读数矛盾，须复查量法）'
    : (族集.length === 1 && out.命中.length <= 2
      ? `只出现在 ${out.命中.length} 处、且同属 ${族集[0]} 一族 ⇒ 记为巧合，不推广`
      : `出现在 ${out.命中.length} 处、横跨 ${族集.length} 族（${族集.join('、')}）⇒ 不是巧合`);
  log('=== 结论 ===');
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
/**
 * 批次 258 · 第二步：**判定 `568.875` 是不是「由内容算出来的」**。
 *
 * 📌 普查（b258）给出的结构：`image` 盒 = `568.875 × 320`（横）、
 *   `video` 盒 = `320 × 568.875`（竖）—— **互为转置**；
 *   其余各族全是 `320 × 320`（text/audio/external）或 `1200 × 207`（timeline）。
 *
 * 🔴 但「`568.875` 同时当宽和当高」有两种读法，**本步要分开**：
 *   ① **由内容算出来的**：图像的 `568.875` 来自它自己的宽高比，
 *      视频的 `568.875` 来自它自己的宽高比 ⇒ **两个各自独立的数碰巧相等**；
 *   ② **一个共同的默认值**：媒体节点不按内容算，固定用 `568.875 × 320`
 *      （竖着用就是转置）⇒ **同一个数**。
 *   ⇒ **判据很干净：视频节点是空的吗？**
 *      空节点**没有内容** ⇒ 若它仍是 `568.875` ⇒ 只能是 ②（默认值）。
 *
 * 📌 顺带抄下两个节点的 `aria-label` 逐字（里面带资源状态），
 *   以及算一下两个盒子的长宽比到底是不是 `16:9`。
 *
 * 🔴 纪律：只读 DOM；不建不删不上传不生成不扣费不分享。
 *
 * 用法：node scripts/jimeng-b258b.mjs      （读数落盘 /tmp/b258b.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B258B_OUT || '/tmp/b258b.json';
const 宽 = 1280, 高 = 720;
const 目标节点 = [
  { id: 'node_gref4sw056', 名: 'b22-upload（图像）' },
  { id: 'node_236ctpehgg', 名: '视频 1（视频）' },
  { id: 'node_pxvkay973v', 名: '导演台' },
  { id: 'node_3bfb9r79qe', 名: '文本 1' },
];

const log = (...a) => console.log(a.join(' '));

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
const out = { 轮次: 'b258b', 视口: [宽, 高], 节点: [], 算式: {} };
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6500);

  out.scale = await p.evaluate(() => {
    const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
    return m ? Number(m[1]) : null;
  });

  for (const t of 目标节点) {
    const r = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return null;
      const b = n.getBoundingClientRect();
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const s = m ? Number(m[1]) : null;
      const 媒体 = Array.from(n.querySelectorAll('img,video,canvas,svg image')).map((e) => ({
        tag: e.tagName.toLowerCase(),
        源: e.getAttribute('src') ? e.getAttribute('src').slice(0, 90) : null,
        自然宽: e.naturalWidth ?? null,
        自然高: e.naturalHeight ?? null,
        currentSrc: e.currentSrc ? e.currentSrc.slice(0, 90) : null,
      }));
      return {
        aria: n.getAttribute('aria-label'),
        文案: (n.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 160),
        css宽: s ? Math.round((b.width / s) * 10000) / 10000 : null,
        css高: s ? Math.round((b.height / s) * 10000) / 10000 : null,
        媒体元素: 媒体,
        媒体元素数: 媒体.length,
        // 📌 「有没有素材」的第二个独立读量（不看 aria，只看 DOM 里有没有真媒体元素）
        有海报图: !!n.querySelector('img'),
        有video标签: !!n.querySelector('video'),
      };
    }, t.id);
    out.节点.push({ 名: t.名, id: t.id, ...(r || { 缺: true }) });
  }

  log('=== 逐字读数 ===');
  for (const n of out.节点) {
    if (n.缺) { log(`  ${n.名}：节点不存在`); continue; }
    log(`  ${n.名}：${n.css宽} × ${n.css高}｜媒体元素 ${n.媒体元素数} 个`
      + `（img=${n.有海报图} video=${n.有video标签}）`);
    log(`     aria=${JSON.stringify(n.aria)}`);
    if (n.媒体元素.length) log(`     媒体=${JSON.stringify(n.媒体元素)}`);
  }

  const 媒体节点 = out.节点.filter((n) => !n.缺 && n.媒体元素数 > 0);
  out.算式.长宽比 = out.节点.filter((n) => n.css宽).map((n) => ({
    名: n.名, 比: Math.round((Math.max(n.css宽, n.css高) / Math.min(n.css宽, n.css高)) * 100000) / 100000,
  }));
  log('=== 长宽比 ===');
  for (const n of out.算式.长宽比) log(`  ${n.名}：${n.比}`);
  log(`  16/9 = ${(16 / 9).toFixed(6)}`);
  log(`=== 判定 ===`);
  log(`有媒体元素的节点数 = ${媒体节点.length}（${媒体节点.map((n) => n.名).join('、') || '无'}）`);
  if (媒体节点.length === 0) {
    out.结论 = '两个媒体节点**都没有任何媒体元素** ⇒ 568.875 不可能由内容算出 ⇒ 它是默认值（立规 113 不猜「怎么实现」）';
  } else {
    out.结论 = '存在媒体元素 ⇒ 需要用它的自然宽高再判一次，不能只看 DOM 里有没有标签';
  }
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
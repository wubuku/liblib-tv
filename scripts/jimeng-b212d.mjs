/**
 * 批次 212 d 轮：用 **requestAnimationFrame 逐帧**重采一次取景，判「有没有动画」。
 *
 * 🔴 本轮**先纠自己的错**：
 *   b 轮用 700ms 间隔采样，读到「帧1 = 点击前、帧2 = 终态」，
 *   于是我以为「取景是瞬移，没有动画」。
 *   但手册记的取景动画约 **400ms**（批次 191 那串 `0.277/0.475/0.792/…`），
 *   **采样间隔比动画还长 ⇒ 必然看不见中间态**。
 *   ⇒ 「读起来像瞬移」与「真的是瞬移」在这个采样率下**不可区分**。
 *
 * 本轮把采样器搬进页面：点击前装一个 rAF 循环，每帧记一次
 * `.react-flow__viewport` 的 transform 原文，连采 1800ms ⇒ 60fps 下约 108 个样本。
 *
 * 三个格子：
 *   ① `1212` + `音频 68`（受影响档）：起点与终点都是 `0.260267`？还是中间动过？
 *   ② `1232` + `音频 68`（正常档）：`0.260267 → 0.5` 之间有没有中间值？
 *   ③ `1212` + `文本 3`（对照，不受影响）：应该一路 `0.5`… 起点其实是 `0.260267`
 *
 * 只读：不新建/删除/拖动节点。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 格们 = [
  { 宽: 1212, id: 'node_tadm1nyykc', 词: '音频 68', 名: '①1212音频68_受影响档' },
  { 宽: 1232, id: 'node_tadm1nyykc', 词: '音频 68', 名: '②1232音频68_正常档' },
  { 宽: 1212, id: 'node_5gftn3dnt1',  词: '文本 3',  名: '③1212文本3_对照' },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b212d', 格们, 结果: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const g of 格们) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: g.宽, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);

    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (!搜索钮) { out.结果[g.名] = { 无效臂: '找不到搜索钮' }; await p.close(); continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]);
    await p.waitForTimeout(1500);
    const 有输入框 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      if (!e) return false;
      e.focus(); e.select(); return true;
    });
    if (!有输入框) { out.结果[g.名] = { 无效臂: '找不到搜索输入框' }; await p.close(); continue; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(250);
    await p.keyboard.type(g.词, { delay: 90 });
    await p.waitForTimeout(2200);
    const 输入回读 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      return e ? e.value : null;
    });
    const tid = 'canvas-search-result-node_' + g.id.replace(/^node_/, '');
    const 前置 = await p.evaluate((t) => {
      const e = document.querySelector(`[data-testid="${t}"]`);
      if (!e) return { 存在: false };
      const r = e.getBoundingClientRect();
      return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }, tid);
    if (!前置.存在 || 输入回读 !== g.词) {
      out.结果[g.名] = { 无效臂: !前置.存在 ? '目标行不在' : '输入没进去', 输入回读 };
      log(`${g.名} ⛔ 无效臂`); await p.close(); continue;
    }

    // 🔑 先装 rAF 采样器，再点击
    await p.evaluate((id) => {
      window.__轨迹 = [];
      const t0 = performance.now();
      const 采 = () => {
        const vp = document.querySelector('.react-flow__viewport');
        const n2 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        const r = n2 ? n2.getBoundingClientRect() : null;
        window.__轨迹.push({
          ms: Math.round(performance.now() - t0),
          tf: vp ? vp.style.transform : null,
          cy: r ? Math.round((r.y + r.height / 2) * 1000) / 1000 : null,
        });
        if (performance.now() - t0 < 1800) requestAnimationFrame(采);
      };
      requestAnimationFrame(采);
    }, g.id);
    await p.waitForTimeout(120);
    await p.mouse.click(前置.点[0], 前置.点[1]);
    await p.waitForTimeout(2200);

    const 轨迹 = await p.evaluate(() => window.__轨迹 || []);
    const scaleOf = (tf) => { const m = tf ? /scale\(([\d.]+)\)/.exec(tf) : null; return m ? Number(m[1]) : null; };
    const 采样 = 轨迹.map((f) => ({ ms: f.ms, s: scaleOf(f.tf), cy: f.cy }));
    const 唯s = [...new Set(采样.map((x) => x.s))];
    const 唯tf = [...new Set(轨迹.map((x) => x.tf))];
    out.结果[g.名] = { 宽: g.宽, 目标: g.id, 帧数: 采样.length, 唯一scale: 唯s, 唯一transform数: 唯tf.length,
      采样: 采样.map((x) => [x.ms, x.s]), 断言: { 判据: '逐帧采到多个不同 scale 即说明有中间态', 有中间态: 唯s.length > 2 } };
    log(`${g.名}：帧数 ${采样.length}，唯一 scale ${JSON.stringify(唯s)}，唯一 transform ${唯tf.length} 个`);
    log('   前 14 帧 [ms, scale]：' + JSON.stringify(采样.slice(0, 14).map((x) => [x.ms, x.s])));
    log('   后 6 帧 [ms, scale]：' + JSON.stringify(采样.slice(-6).map((x) => [x.ms, x.s])));
  } catch (e) { out.结果[g.名] = { 出错: e.message }; log(`${g.名} 🔴 ${e.message}`); }
  finally { await p.close(); }
}

fs.writeFileSync('/tmp/b212d.json', JSON.stringify(out, null, 1));
log('\n写入 /tmp/b212d.json');
process.exit(0);

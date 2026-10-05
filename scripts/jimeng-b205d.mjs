/**
 * 批次 205 d 轮：最后一个、也是最要紧的一问 ——
 * 「`w=1212` 时取景把缩放停在 `26%`」，到底是**最终目标**还是**只是慢**？
 *
 * a/b/c 三轮合起来的事实：
 *   w ≤ 1211：落点中心 Y = **360**（= 720/2，视口正中），缩放终态 **50%**
 *   w = 1212：落点中心 Y ≈ **259.7**，缩放在 0.7s、2.8s、3.5s 三个时点都是 **26%**
 *   w = 1230：缩放终态 **49%**（差一点点到 50%）
 *   w ≥ 1232：缩放终态 **50%**，中心 Y ≈ 259.8
 *
 * ⚠️ b 轮的收敛判据有个盲区：它看的是**最后 4 帧**，而动画**还没开始**时那 4 帧
 *   本来就相同 ⇒ 会误报「第 2 帧起已收敛」。所以「b 轮说收敛」不足以证明它不会再变。
 *
 * 本轮只做一件事：在 1212 / 1220 / 1232 三档上，**每 1 秒采一次、连采 30 次**（30 秒），
 * 把缩放随时间的整条轨迹记下来。
 *   · 若 1212 的缩放在 30 秒内**始终**停在 26% ⇒ 它是最终目标，断点是真的
 *   · 若它某个时刻**继续往 50% 爬** ⇒ 前面三轮的「断点」结论全部作废
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 目标 = 'canvas-search-result-node_tadm1nyykc';
const H = 720;
const 宽集 = [1212, 1220, 1232];
const 秒 = 30;

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b205d', 宽集, 采样: `每 1s × ${秒}s`, 档: {} };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const w of 宽集) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    out.档[w] = {};

    // 🔴 取景**之前**先记初态（批次 199 说 12 档逐字相同，这里在断点两侧复核）
    out.档[w].初态 = await p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      return vp ? vp.style.transform : null;
    });

    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (!搜索钮) { out.档[w] = { 无效臂: '找不到搜索钮' }; await p.close(); continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]);
    await p.waitForTimeout(1500);
    const 有输入框 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      if (!e) return false;
      e.focus(); e.select(); return true;
    });
    if (!有输入框) { out.档[w] = { 无效臂: '找不到搜索输入框' }; await p.close(); continue; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(250);
    await p.keyboard.type(搜索词, { delay: 90 });
    await p.waitForTimeout(2200);
    const 输入回读 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      return e ? e.value : null;
    });
    const 前置 = await p.evaluate((tid) => {
      const e = document.querySelector(`[data-testid="${tid}"]`);
      if (!e) return { 存在: false };
      const r = e.getBoundingClientRect();
      return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }, 目标);
    if (!前置.存在 || 输入回读 !== 搜索词) {
      out.档[w] = { 无效臂: !前置.存在 ? '目标行不在' : '输入没进去', 输入回读, 初态: out.档[w].初态 };
      log(`${w} ⛔ 无效臂`);
      await p.close(); continue;
    }
    out.档[w].初态_取景前 = await p.evaluate(() => document.querySelector('.react-flow__viewport').style.transform);

    await p.mouse.click(前置.点[0], 前置.点[1]);

    // —— 每 1 秒采一次，连采 30 次 ——
    const 轨迹 = [];
    for (let t = 0; t < 秒; t++) {
      await p.waitForTimeout(1000);
      轨迹.push(await p.evaluate((tid) => {
        const id = tid.replace('canvas-search-result-node_', 'node_');
        const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        const r = n ? n.getBoundingClientRect() : null;
        const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
        return { t: null,
          缩放: m ? Number(m[3]) : null, tx: m ? Number(m[1]) : null, ty: m ? Number(m[2]) : null,
          中心Y: r ? Math.round((r.y + r.height / 2) * 1000) / 1000 : null,
          中心X: r ? Math.round((r.x + r.width / 2) * 1000) / 1000 : null,
          缩放aria: z ? z.getAttribute('aria-label') : null };
      }, 目标));
    }
    轨迹.forEach((f, i) => { f.t = i + 1; });

    const 缩放轨迹 = 轨迹.map((f) => f.缩放);
    const 唯一缩放 = [...new Set(缩放轨迹)];
    out.档[w].轨迹 = 轨迹;
    out.档[w].缩放唯一值 = 唯一缩放;
    out.档[w].最终 = 轨迹[轨迹.length - 1];
    out.档[w]['变过'] = 唯一缩放.length > 1;
    log(`${w} | 初态 ${out.档[w].初态_取景前}`);
    log(`   缩放轨迹（前 6 + 后 4）：${JSON.stringify(缩放轨迹.slice(0, 6))} … ${JSON.stringify(缩放轨迹.slice(-4))}`);
    log(`   缩放唯一值 ${JSON.stringify(唯一缩放)}（${唯一缩放.length} 个）｜ 30 秒内变过=${out.档[w]['变过']}`);
    log(`   最终 中心=(${轨迹[秒 - 1].中心X}, ${轨迹[秒 - 1].中心Y}) 缩放aria=${轨迹[秒 - 1].缩放aria}`);
  } catch (e) {
    out.档[w] = { 出错: e.message };
    log(`${w} 🔴 ${e.message}`);
  } finally { await p.close(); }
}

fs.writeFileSync('/tmp/b205d.json', JSON.stringify(out, null, 1));
log('\n写入 /tmp/b205d.json');
process.exit(0);

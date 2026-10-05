/**
 * 批次 213 b 轮：补齐 `text` 类型的样本（3 个节点里只点过 `文本 3`），
 * 并把每个被点节点的**渲染变体**在点击那一刻读下来，和「中招 / 不中招」摆在一起。
 *
 * 批次 213 a 轮已把**全部 76 个节点**的变体表取齐（不需要点击）：
 *   `26%` 档：timeline 2 `timeline-flow-node`｜text 3 `text-flow-node-compact`｜
 *              audio 68 `audio-node-compact`｜external 1 `director-stage-flow-node-shell`｜
 *              video 1 `video-node-compact`｜image 1 `image-node-compact`
 *   `50%` 档：timeline 2 不变｜text 3 `text-flow-node-full`｜audio 68 **`audio-node-empty`**｜
 *              external 1 不变｜video 1 **`video-node-empty`**｜image 1 `image-node-result`
 *
 * ⇒ 两个候选判据当场分出高下：
 *   ❌「`26%` 档是否 compact」—— **被否**：`文本 3` 与 `图片` 在 `26%` 也是 compact，却**不中招**
 *   ✅「`50%` 档是否渲染 `*-node-empty`」—— 与批次 212 全部 **15 个实测节点逐字重合**
 *      （中招 10 个 = 9 audio + 1 video，全在 `-empty` 族；不中招 5 个全不在）
 *
 * ⚠️ 但这只是**相关**：`audio` 与 `video` 恰好是仅有的两个 `-empty` 族类型
 * ⇒ 「类型」与「`-empty` 族」在本画布上**完全共变**，单靠点节点分不开。
 * 要分开必须**跨族移动一个节点**（即让某个 audio/video 节点有媒体、改渲染 `-result`），
 * 那是下一轮的事。本轮先把 `text` 这一族的 3 个样本补齐。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 宽集 = [1210, 1212];
const 节点们 = [
  { 名: '文本1', id: 'node_3bfb9r79qe', 词: '文本 1', 类型: 'text',     画布: [480.055, 240],      变体50: 'text-flow-node-full' },
  { 名: '文本2', id: 'node_aw29cp094x', 词: '文本 2', 类型: 'text',     画布: [520.055, 278.75],   变体50: 'text-flow-node-full' },
  { 名: '文本3', id: 'node_5gftn3dnt1',  词: '文本 3', 类型: 'text',     画布: [560.055, 319.375],  变体50: 'text-flow-node-full' },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b213b', 高度固定: H, 宽集, 节点们, 档: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const w of 宽集) {
  out.档[w] = {};
  for (const n of 节点们) {
    const p = await ctx.newPage();
    try {
      await p.setViewportSize({ width: w, height: H });
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
      if (!搜索钮) { out.档[w][n.名] = { 无效臂: '找不到搜索钮' }; await p.close(); continue; }
      await p.mouse.click(搜索钮[0], 搜索钮[1]);
      await p.waitForTimeout(1500);
      const 有输入框 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (!e) return false;
        e.focus(); e.select(); return true;
      });
      if (!有输入框) { out.档[w][n.名] = { 无效臂: '找不到搜索输入框' }; await p.close(); continue; }
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(250);
      await p.keyboard.type(n.词, { delay: 90 });
      await p.waitForTimeout(2200);
      const 输入回读 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        return e ? e.value : null;
      });
      const tid = 'canvas-search-result-node_' + n.id.replace(/^node_/, '');
      const 前置 = await p.evaluate((t) => {
        const e = document.querySelector(`[data-testid="${t}"]`);
        if (!e) return { 存在: false };
        const r = e.getBoundingClientRect();
        return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      }, tid);
      if (!前置.存在 || 输入回读 !== n.词) {
        out.档[w][n.名] = { 无效臂: !前置.存在 ? '目标行不在' : '输入没进去', 输入回读 };
        log(`${w} ${n.名} ⛔ 无效臂`); await p.close(); continue;
      }

      // 🔑 点击**之前**先记下该节点此刻的渲染变体（26% 初始档）
      const 点前变体 = await p.evaluate((id) => {
        const n2 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        if (!n2) return null;
        const cands = ['text-flow-node-compact', 'text-flow-node-full', 'audio-node-compact',
          'video-node-compact', 'image-node-compact', 'timeline-flow-node', 'director-stage-flow-node-shell'];
        return cands.filter((c) => n2.querySelector(`[data-testid="${c}"]`));
      }, n.id);

      await p.mouse.click(前置.点[0], 前置.点[1]);
      await p.waitForTimeout(4000);
      const 采样 = [];
      for (let k = 0; k < 3; k++) {
        采样.push(await p.evaluate((id) => {
          const n2 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
          const vp = document.querySelector('.react-flow__viewport');
          const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
          const r = n2 ? n2.getBoundingClientRect() : null;
          return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
            屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
            vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
        }, n.id));
        await p.waitForTimeout(500);
      }
      const ss = [...new Set(采样.map((x) => x.vp && x.vp[2]))];
      out.档[w][n.名] = { 类型: n.类型, 画布: n.画布, 变体50: n['变体50'], 点前变体,
        采样, 末: 采样[2], 断言: { 判据: '3 次采样 scale 相同', 通过: ss.length === 1 } };
      log(`${w} ${n.名} (${n.类型}) 点前变体=${JSON.stringify(点前变体)} → s=${JSON.stringify(ss)} 中心=${JSON.stringify(采样[2].中心)} 屏上=${JSON.stringify(采样[2].屏上)}`);
    } catch (e) { out.档[w][n.名] = { 出错: e.message }; log(`${w} ${n.名} 🔴 ${e.message}`); }
    finally { await p.close(); }
  }
}

out.汇总 = 节点们.map((n) => {
  const g = out.档[1212] && out.档[1212][n.名];
  const s = g && g.末 && g.末.vp ? g.末.vp[2] : null;
  return { 名: n.名, 类型: n.类型, 点前变体: g && g.点前变体, 终态scale: s, 中招: s !== null && s < 0.499 };
});
log('\n汇总（w=1212）：');
for (const r of out.汇总) log(`  ${r.名} 点前变体=${JSON.stringify(r.点前变体)} s=${r.终态scale} ${r.中招 ? '🔴 中招' : '✅ 不中招'}`);

fs.writeFileSync('/tmp/b213b.json', JSON.stringify(out, null, 1));
log('\n写入 /tmp/b213b.json');
process.exit(0);

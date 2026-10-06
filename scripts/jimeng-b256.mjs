/**
 * 批次 256：把取景律补到**第 5、6 族** —— `external`（导演台）与 `video`（视频 1）。
 *
 * 📌 背景：侦察（b256-recon）把 `76` 个节点按 `react-flow__node-<kind>` 分族：
 *   `text` `3` 个（`W=320`）、`timeline` `2` 个（`W=1200`）、`audio` `68` 个（`W=320`）、
 *   `image` `1` 个（`W=569`）、**`external` `1` 个（导演台，`W=320`）**、
 *   **`video` `1` 个（视频 1，`W=320`）**；画布上**没有** `主体` 节点（工具栏有入口，画布无实例）。
 *   🔴 批次 248/251/252 只把 `412` 律验到 `4` 族 ⇒ **「通性」这句话目前只覆盖那 `4` 族，
 *   不能顺延到第 `5`、`6` 族。**
 *
 * 📌 **预测先算好**（立规 129：现象宽度要先算出来，而且它不是常数）：
 *   `W = 320` ⇒ 四段折线的三个接缝分别在
 *     `w = 437.6`（应用下限 `0.08` 交点）、`w = 512`（窄侧斜坡交族内地板 `100/W`）、
 *     `w = 632`（族内地板交宽侧斜坡）、`w = 692`（宽侧斜坡触封顶 `0.5`）。
 *   ⇒ 选 `w = 460 / 500 / 512 / 632 / 692 / 300`：
 *     **三个接缝全部选上**（`512`、`632`、`692`），让预测在**最容易被推翻**的位置挨打。
 *
 * 📌 判据：**落点逐字相等**，容差 `5e-6`（立规 128 —— 容差要大于量化噪声而小于目标差异）。
 *
 * 🔴 纪律：
 *   · 正交读量：读完缩放再点搜索结果行，**不点结果行之外的任何东西**；
 *   · **不新建、不删除、不上传、不触发生成、不进扣费页、不点「保存到主体库」、不分享**；
 *   · 缩放不跨页持久化 ⇒ 每臂开新页；**一格键都不用按**。
 *
 * 用法：node scripts/jimeng-b256.mjs      （读数落盘 /tmp/b256.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B256_OUT || '/tmp/b256.json';
const 高 = 720;

// 🔴 两个新族；`W` 来自 b256-recon 实测的 offsetWidth，不是猜的
const 节点表 = [
  { id: 'node_pxvkay973v', 名: '导演台', kind: 'external', W: 320, 词: ['导演台', '导演'] },
  { id: 'node_236ctpehgg', 名: '视频 1', kind: 'video', W: 320, 词: ['视频 1', '视频'] },
];

// 📌 四段折线，**预测**与**实测**分开记（不允许看到实测再改预测）
const 预测 = (w, W) => {
  const 应用地板 = 0.08;
  const 族内地板 = 100 / W;
  const 封顶 = 0.5;
  const 窄 = w - 412;
  const 宽 = w - 532;
  let 落点;
  if (窄 <= 应用地板 * W) 落点 = 应用地板;
  else if (窄 <= 100) 落点 = 窄 / W;
  else if (宽 <= 100) 落点 = 族内地板;
  else 落点 = Math.min(宽 / W, 封顶);
  return { 落点: +落点.toFixed(9), 屏上: +Math.min(Math.max(窄, 应用地板 * W), Math.max(宽, 族内地板 * W)).toFixed(4), 区: (窄 <= 应用地板 * W) ? '应用下限' : (窄 <= 100 ? '窄侧斜坡' : (宽 <= 100 ? '族内地板' : '宽侧斜坡')) };
};

const 宽表 = [460, 500, 512, 632, 692, 300];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b256', 高, 臂: [] };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const nd of 节点表) {
  for (const 宽 of 宽表) {
    const p = await ctx.newPage();
    const 记 = { 节点: nd.名, kind: nd.kind, W: nd.W, 宽, 高 };
    Object.assign(记, 预测(宽, nd.W));
    记.预测_落点 = 记.落点;
    try {
      await p.setViewportSize({ width: 宽, height: 高 });
      await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p.waitForTimeout(5000);

      const 钮 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('button, [role="button"]'))
          .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      if (!钮) throw new Error('找不到搜索钮');
      await p.mouse.click(钮[0], 钮[1]);
      await p.waitForTimeout(1500);

      const 短名 = nd.id.replace(/^node_/, '');
      let 点 = null;
      for (const 词 of nd.词) {
        await p.evaluate(() => {
          const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
          if (inp) { inp.focus(); inp.select(); }
        });
        await p.keyboard.type(词, { delay: 85 });
        await p.waitForTimeout(2200);
        const 读行 = await p.evaluate((nid) => {
          const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
          const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
          return { 回读: inp ? inp.value : null, 有行: !!e };
        }, 短名);
        if (读行.有行 && 读行.回读 === 词) {
          点 = await p.evaluate((nid) => {
            const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
            if (!e) return null;
            const r = e.getBoundingClientRect();
            return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
          }, 短名);
          if (点) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(5000); 记.用的词 = 词; break; }
        }
      }
      if (!点) throw new Error('候选词都没命中那一行');
      await p.keyboard.press('Escape');
      await p.waitForTimeout(600);
      await p.keyboard.press('Escape');
      await p.waitForTimeout(900);

      记.定位后 = await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
        const nr = n ? n.getBoundingClientRect() : null;
        return {
          落点: m ? Number(m[1]) : null,
          aria: z ? z.getAttribute('aria-label') : null,
          布局宽: n ? n.offsetWidth : null,
          屏上原始: nr ? [nr.width, nr.height] : null,
          中心Y: nr ? Math.round(nr.y + nr.height / 2) : null,
          状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
        };
      }, nd.id);

      if (记.定位后.屏上原始 && 记.定位后.落点) {
        记.反推W = +(记.定位后.屏上原始[0] / 记.定位后.落点).toFixed(4);
      }
      记.命中预测 = 记.定位后.落点 != null && Math.abs(记.定位后.落点 - 记.预测_落点) < 5e-6;
      log(`【${nd.名}@${宽}】${记.区} 预测 ${记.预测_落点} → 实测 ${记.定位后.落点}`
        + `（${记.定位后.aria}）｜ 屏上原始 ${JSON.stringify(记.定位后.屏上原始)}`
        + `｜ 反推W ${记.反推W}｜ 中心Y ${记.定位后.中心Y}｜ ${记.命中预测 ? '✅' : '❌ 不符'}`);
    } catch (e) {
      记.错误 = e.message;
      log(`🔴 ${nd.名}@${宽} ${e.message}`);
    } finally {
      try { await p.close(); } catch (e) { /* 忽略 */ }
    }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((a) => !a.错误 && a.命中预测 != null);
out.命中数 = 好.filter((a) => a.命中预测).length;
out.总臂数 = out.臂.length;
out.按族 = {};
for (const a of out.臂) {
  out.按族[a.节点] = out.按族[a.节点] || { 命中: 0, 总: 0 };
  out.按族[a.节点].总++;
  if (a.命中预测) out.按族[a.节点].命中++;
}
log('=== 汇总 ===');
log(JSON.stringify(out.按族));
log(`${out.命中数} / ${out.总臂数} 命中`);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);
/**
 * 批次 253：**开一个新轴 —— 视口高度**。此前所有探针都只变「宽」，高度恒为 `720`。
 *
 * 📌 **为什么要开这个轴**：批次 244–252 把取景律测到
 *   「窄侧 `screen = w − 412`、宽侧 `screen = w − 532`、两个地板、封顶 `0.5`」，
 *   而这整条律里**每一个常数都是在「高度 = 720」这一个值上定出来的**。
 *   ⇒ **`412` 与 `532` 究竟是「视口宽减去某个横向余量」，
 *   还是「某个与高宽都有关的量在 `H=720` 这一个切片上的值」，从未被区分过。**
 *   🔴 若两者有关，把高度换掉就会**平移拐点**（`412` / `512` / `532` / `692` 全部动）；
 *   若无关，读数应当**逐字不变**。⇒ 两种可能，**分歧点明确**。
 *
 * 📌 顺带用**中心 `Y`** 做第二条正交读量（立规 104）：
 *   此前所有读数的 `中心 Y` 恒为 `360`，而 `360 = 720 / 2`
 *   ⇒ **「居中」到底是「画布区域正中」还是「`H=720` 的正中」，也只有这一个切片测过。**
 *   预期：高度换成 `1080` 后中心 `Y` 若是 `540` ⇒ 跟 `H/2` 走；若是 `360` ⇒ 跟某条固定的横向规则走。
 *
 * 📌 预测**先算好**、与实测分开记（批次 252 的做法）：
 *   若高度无关 ⇒ 落点与批次 252 同 `w` 的读数**逐字相同**。
 *
 * 🔴 纪律：
 *   · **正交读量**：读完缩放再点搜索结果行；**不点结果行之外的任何东西**；
 *   · **不新建、不删除、不上传、不触发生成、不进扣费页、不点「保存到主体库」、不分享**；
 *   · 缩放不跨页持久化 ⇒ 每臂开新页即可；**一格键都不用按**；
 *   · 节点固定为 **`文本 1`**（`node_3bfb9r79qe`，`W = 320`），
 *     因为它有批次 251/252 的**同 `w` 基线读数**可供逐字比对。
 *
 * 用法：node scripts/jimeng-b253.mjs            （读数落盘 /tmp/b253.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B253_OUT || '/tmp/b253.json';

const nd = { id: 'node_3bfb9r79qe', 名: '文本 1', W: 320, 词: ['文本 1', '文本'] };

// 🔴 每臂自带**高**（此前全部是 720）—— 本批唯一的变量就是高度
const 臂表 = [
  { 宽: 500, 高: 360,  说明: '斜坡段（`w=500`），高度缩到 `360`（原先恒 `720` 的一半）。预测：若高度无关 ⇒ 落点仍 `0.275`、屏上仍 `88`' },
  { 宽: 500, 高: 720,  说明: '基线切片：与批次 251 的 `w=500` 逐字对照' },
  { 宽: 500, 高: 1080, 说明: '高度放大 `1.5` 倍。预测：落点仍 `0.275`；**中心 `Y` 若是 `540` ⇒ 跟 `H/2` 走**' },
  { 宽: 460, 高: 360,  说明: '斜坡段另一档，窄视口。预测落点仍 `0.15`、屏上仍 `48`' },
  { 宽: 460, 高: 1080, 说明: '同上。预测落点仍 `0.15`、中心 `Y` 若是 `540`' },
  { 宽: 632, 高: 360,  说明: '**族内地板区**（`100px`）：预测落点仍 `0.3125`、屏上仍 `100` —— 这一档验的是**地板也与高度无关**' },
  { 宽: 632, 高: 1080, 说明: '同上' },
  { 宽: 300, 高: 1080, 说明: '**应用缩放下限区**（`0.08`）：预测落点仍 `0.08`、屏上仍 `25.6` —— 三个地板一起验高度无关' },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b253', 节点: nd.名, 臂: [] };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { scale: m ? Number(m[1]) : null, aria: z ? z.getAttribute('aria-label') : null };
});

let 臂序 = 0;
for (const 臂 of 臂表) {
  const p = await ctx.newPage();
  const 记 = { 臂序: ++臂序, 节点: nd.名, W: nd.W, 宽: 臂.宽, 高: 臂.高, 说明: 臂.说明 };
  // 🔴 预测先算好并**与实测分开记** —— 不允许「看到实测之后再改预测」
  记.预测_屏上 = +(臂.宽 - 412).toFixed(4);
  记.预测_中心Y = Math.round(臂.高 / 2);
  记.预测_落点 = Math.max(0.08, Math.min((臂.宽 - 412) / nd.W, 100 / nd.W));
  try {
    await p.setViewportSize({ width: 臂.宽, height: 臂.高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);

    记.定位时缩放 = await 读缩放(p);

    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    });
    if (!钮) throw new Error('找不到搜索钮');
    await p.mouse.click(钮[0] + Math.round(钮[2] / 2), 钮[1] + Math.round(钮[3] / 2));
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
    // 📌 判定用**落点逐字相等**；落点只写到 3–6 位小数 ⇒ 容差取 5e-6（立规 128）
    记.命中预测 = 记.定位后.落点 != null && Math.abs(记.定位后.落点 - 记.预测_落点) < 5e-6;
    记.中心Y符合H2 = 记.定位后.中心Y === 记.预测_中心Y;
    log(`【${nd.名} @${臂.宽}x${臂.高}】预测 ${记.预测_落点} → 实测 ${记.定位后.落点}`
      + `（${记.定位后.aria}）｜ 屏上原始 ${JSON.stringify(记.定位后.屏上原始)}`
      + `｜ 反推W ${记.反推W}｜ 中心Y ${记.定位后.中心Y}｜ ${记.命中预测 ? '✅ 命中' : '❌ 不符'}`);
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 ${nd.名} @${臂.宽}x${臂.高} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  out.臂.push(记);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);
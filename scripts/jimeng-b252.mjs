/**
 * 批次 252：把「`screen = w − 412` 是取景通性」这条**推到底** —— 时间线与图像的窄侧。
 *
 * 📌 批次 251 已在**文本与音频**两个族上验到 `8/8` 逐字相同，
 *   两族的算法宽 `W` 都是 `320` ⇒ 得出「屏上律与 `W` 无关，只有 `落点 = 屏上 / W` 随族变」。
 *   ⚠️ **但这只验了两个「`W` 相同的族」** —— 它们一致，**并不能证明这条律与 `W` 无关**：
 *   若真律是「`落点 = 某个只对 `W=320` 成立的函数`」，两族当然会一致（立规 123 第 1 问）。
 *   ⇒ **必须换一个 `W` 明显不同的族去撞**。
 *
 * 🔴🔴 **本批的关键：两个族的「可分辨窗口」宽度完全不同，而且都很窄**
 *   （窄侧律 `scale = (w − 412)/W`，被两个地板夹住：
 *    · 应用缩放下限 `0.08` ⇒ 屏上 `0.08 × W`
 *    · 族内 `100px` 地板 ⇒ 屏上 `100`
 *   ⇒ **斜坡段存在的条件是 `0.08 × W < 100`**，即 `W < 1250`；
 *     而**斜坡段在屏上只有 `100 − 0.08W` 像素宽**）：
 *
 *     | 族 | `W` | 可分辨窗口（屏上宽） | 对应 `w` 区间 | 需要多细的步长 |
 *     |---|---|---|---|---|
 *     | 文本 / 音频 | `320` | `100 − 25.6 = 74.4px` | `437.6` – `512` | `20` 就够（批次 249 已测） |
 *     | **时间线** | **`1200`** | **`100 − 96 = 4px`** | **`508` – `512`** | 🔴 **`1px`**（立规 121） |
 *     | 图像 | `5120/9 ≈ 568.9` | `100 − 45.5 = 54.5px` | `457.5` – `512` | `20` 够 |
 *
 *   ⇒ 📌 **时间线只有 `4` 个像素宽的窗口能分辨两条律** ⇒ 必须 **`1px` 一档**
 *     （立规 121：「扫了很多档」≠「扫到过那个宽度」—— `20` 步长会**整段跳过**它）。
 *
 * 📌 预测（**是预测，不是发现**；本批不成立就不写进正文）：
 *   时间线 `W=1200`：`460→0.08`、`500→0.08`、`508→0.08`、`509→(97)/1200=0.0808333`、
 *                    `511→(99)/1200=0.0825`、`512→100/1200=0.0833333`
 *   图像 `W=5120/9`：`460→48/(5120/9)=0.084375`、`480→0.119531`、`500→0.154688`、
 *                   `560→100/(5120/9)=0.175781`、`632→0.175781`
 *
 * 🔴 纪律：
 *   · **正交读量**：读完缩放再点搜索结果行；**不点结果行之外的任何东西**；
 *   · **不新建、不删除、不上传、不触发生成、不进扣费页、不点「保存到主体库」、不分享**；
 *   · 缩放不跨页持久化 ⇒ 每臂开新页即可；**一格键都不用按**；
 *   · 搜索命中判定用**节点名**（时间线 1/2 有文字内容，图片节点按节点名）。
 *
 * 用法：node scripts/jimeng-b252.mjs            （读数落盘 /tmp/b252.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B252_OUT || '/tmp/b252.json';

// 🔴 每臂自带节点与搜索词 —— 本批要撞**两个 `W` 完全不同**的族
const 节点表 = {
  时间线2: { id: 'node_d4tjtpnatq', 名: '时间线 2', W: 1200, 词: ['时间线 2', '时间线'] },
  图片: { id: 'node_gref4sw056', 名: '图片 b22-upload', W: 5120 / 9, 词: ['图片 b22-upload', 'b22-upload', '图片 b22'] },
};

const 臂表 = [
  // —— 时间线：4px 窗口，必须 1px ——
  { 节点: '时间线2', 宽: 500, 说明: '斜坡段之外：预测仍在应用下限 0.08（(500−412)/1200 = 0.0733 < 0.08）' },
  { 节点: '时间线2', 宽: 508, 说明: '**可分辨窗口左边界**：`(508−412)/1200 = 0.08`，与下限相等 ⇒ 预期仍是 0.08' },
  { 节点: '时间线2', 宽: 509, 说明: '**窗口内**：预测 `(509−412)/1200 = 0.0808333`（第一次离开下限）' },
  { 节点: '时间线2', 宽: 510, 说明: '预测 `(510−412)/1200 = 0.0816667`' },
  { 节点: '时间线2', 宽: 511, 说明: '预测 `(511−412)/1200 = 0.0825`' },
  { 节点: '时间线2', 宽: 512, 说明: '**窗口右边界**：预测 `100/1200 = 0.0833333`（族内地板）' },
  { 节点: '时间线2', 宽: 560, 说明: '地板区：预测 `0.0833333`' },
  // —— 图像：54.5px 窗口，20px 步长够 ——
  { 节点: '图片', 宽: 460, 说明: '斜坡段：预测 `48/(5120/9) = 0.084375`（高于下限 0.08 ⇒ 不被压）' },
  { 节点: '图片', 宽: 480, 说明: '预测 `68/(5120/9) = 0.119531`' },
  { 节点: '图片', 宽: 500, 说明: '预测 `88/(5120/9) = 0.154688`' },
  { 节点: '图片', 宽: 560, 说明: '地板区：预测 `100/(5120/9) = 0.175781`' },
  { 节点: '图片', 宽: 632, 说明: '地板区右端：预测 `0.175781`' },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b252', 臂: [] };

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
  const nd = 节点表[臂.节点];
  const p = await ctx.newPage();
  const 记 = { 臂序: ++臂序, 节点: nd.名, W: nd.W, 宽: 臂.宽, 说明: 臂.说明 };
  // 🔴 预测先算好并**与实测分开记** —— 不允许「看到实测之后再改预测」
  记.预测_屏上 = +(臂.宽 - 412).toFixed(4);
  记.预测_落点 = Math.max(0.08, Math.min((臂.宽 - 412) / nd.W, 100 / nd.W));
  try {
    await p.setViewportSize({ width: 臂.宽, height: 720 });
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
    log(`【${nd.名} @w=${臂.宽}】预测 ${记.预测_落点} → 实测 ${记.定位后.落点}`
      + `（${记.定位后.aria}）｜ 屏上原始 ${JSON.stringify(记.定位后.屏上原始)}`
      + `｜ 反推W ${记.反推W}｜ 中心Y ${记.定位后.中心Y}｜ ${记.命中预测 ? '✅ 命中' : '❌ 不符'}`);
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 ${nd.名} @w=${臂.宽} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  out.臂.push(记);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);
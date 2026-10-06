/**
 * 批次 247：音频凹口地板的**方向性** —— 它是「纯跟当前缩放」还是「有个硬上限」？
 *
 * 📌 批次 246 只朝**一侧**推过（⌘−），所以两种机制在已有两格上**同形不可分辨**：
 *     (a) 地板 = **当前画布缩放**（无上限）
 *     (b) 地板 = `min(0.260267, 当前画布缩放)`     —— `0.260267` 是默认缩放
 *   ⇒ 本批按立规 123 **朝两侧都推**，且**不用默认值那一格定机制**。
 *
 * 🔴🔴 **第一次跑（已归档 `/tmp/b247-run1.json`）有两个自身缺陷，必须写下来**：
 *   ① **「不按任何键」的对照臂被自己的键位探测污染了** ——
 *      探测循环在每臂开头**无条件**跑，于是对照臂实际按了一次 `⌘=`。
 *      （它意外产出了决定性读数，但**不能**当对照用。）
 *   ② 第 2 臂作废：取键时写了 `.raw`，而候选项的字段名是 `键` ⇒ 取到 `undefined` ⇒ 自查抛错弃臂。
 *      本版已改用 `候.键`，并把探测挪到**只有需要它的臂**才跑。
 *
 * 📌 **键位**（已由批次 246 试点 + 本批第一次跑**双向验证**）：
 *   `Meta+Minus` 缩小、`Meta+Equal` 放大，**都按 `×1.2` 递进**。
 *   ⚠️ 阶梯是**离散的**：每步 `×1.2` 后取整到 `3` 位小数，
 *      所以 `0.217 → 0.26 → 0.312 → 0.375`，**来回不可逆**（回不到 `0.260267`）。
 *
 * 📌 顺带钉死一个悬着的量：音频节点的**布局宽**（`offsetWidth`，未缩放）与
 *   **屏上原始浮点**（`getBoundingClientRect()`，不做取整）。
 *   批次 246 只有「屏上取整后 `69` ÷ `0.217`」一格，除法只能定到 `±1/zoom`，
 *   分不清 `320` 与 `318`；原始浮点能定到小数点后多位。
 *
 * 🔴 纪律：
 *   · **正交读量**：改完缩放必须先读 `canvas-zoom-percent` 确认生效，**再**点搜索结果行；
 *   · **不点结果行之外的任何东西**，不新建、不删除、不上传、不触发生成；
 *   · 缩放不跨页持久化 ⇒ 每臂开新页即可；
 *   · **四臂全是同一个节点 `音频 68` @ `w=1212`**，唯一变量是「按了几次键」。
 *
 * 用法：node scripts/jimeng-b247.mjs   （读数落盘 /tmp/b247.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b247.json';
const 宽 = 1212;                  // 音频凹口的起点；四臂**全部**停在这里，唯一变量是「按了几次键」
const 音频ID = 'node_tadm1nyykc';
const 音频词 = ['音频 68', '音频'];

// 🔴 **放大键不再现场探测**，直接硬编码 —— 理由与代价都写在这里：
//   `Meta+Equal` 已被**两处独立证据**验证确实被页面接管
//   （批次 246 试点：`0.181 → 0.217 → 0.26`；本批第一次跑：`0.260267 → 0.312`）。
//   现场探测要求「按一次键看读数」，而那一次按鍵**本身就是对当前臂的污染** ——
//   于是「需要探测的那一臂」永远会比别的臂多按一次 ⌘+（第一批的对照臂就是这么被毁掉的）。
//   ⇒ **改成：按了之后逐臂断言「缩放确实变了」，没变就如实作废该臂**（见循环末尾的检查），
//   **绝不用一次「为了发现键位」而多出来的按键去污染任何一格的读数**。
const 放大键 = 'Meta+Equal';

const 臂表 = [
  { 名: '第0臂·真·不按任何键（对照）', 按键: [],
    说明: '对照组：什么都不按，落点应逐字是 0.260267。立规 123 的第 3 问——默认值本身定不了机制，但必须先把它钉住' },
  { 名: '第1臂·⌘+ 一次', 按键: ['ZOOMIN'],
    说明: '画布升到默认值**之上**。若地板纯跟缩放 ⇒ 落点约 0.312；若硬上限 min(0.260267,·) ⇒ 仍 0.260267。**这就是分开两种机制的那一格**' },
  { 名: '第2臂·⌘+ 两次', 按键: ['ZOOMIN', 'ZOOMIN'],
    说明: '画布约 0.375，**再往上一格**。确认「跟着升」不是一次性的巧合' },
  { 名: '第3臂·⌘− 两次', 按键: ['Meta+Minus', 'Meta+Minus'],
    说明: '画布约 0.181（批次 246 只到 0.217）。往下再补一格，看是否同样逐字跟随' },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b247', 宽, 节点: '音频 68', 臂: [] };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

let 放大键_已校验 = true;         // 硬编码键已被两处证据验证（批次 246 试点 + 本批第一次跑），此常量仅作文档锚点

const 读缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { scale: m ? Number(m[1]) : null, 原始: vp ? (vp.style.transform || '') : null, aria: z ? z.getAttribute('aria-label') : null };
});

for (const 臂 of 臂表) {
  const p = await ctx.newPage();
  const 记 = { 臂: 臂.名, 说明: 臂.说明 };
  try {
    await p.setViewportSize({ width: 宽, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);

    记.定位前缩放 = await 读缩放(p);

    // ---- 按本臂指定的键序列（`ZOOMIN` = 已硬编码并被证据验证的放大键）----
    for (const k of 臂.按键) {
      await p.keyboard.press(k === 'ZOOMIN' ? 放大键 : k);
      await p.waitForTimeout(1500);
      // 🔴 每按一次就断言「缩放真的动了」，没动**立刻弃臂** —— 而不是等到臂末才发现整臂作废
      const 现 = await 读缩放(p);
      const 前 = 记.定位前缩放.scale;
      if (现.scale === 前) {
        throw new Error(`按 ${k === 'ZOOMIN' ? 放大键 : k} 没改到缩放（仍是 ${前}），本臂作废（不改机制、不猜）`);
      }
      记.定位前缩放 = 现;      // 逐次推进，供臂末的「按键没改到缩放」检查复用
    }
    记.定位时缩放 = await 读缩放(p);
    log(`【${臂.名}】定位时缩放 ${记.定位时缩放.scale}（${记.定位时缩放.aria}）｜ ${记.定位时缩放.原始}`);

    // ---- 搜索 → 点结果行定位 ----
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
    await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (inp) { inp.focus(); inp.select(); }
    });

    const 短名 = 音频ID.replace(/^node_/, '');
    let 点 = null;
    for (const 词 of 音频词) {
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
        布局高: n ? n.offsetHeight : null,
        屏上: nr ? [Math.round(nr.width), Math.round(nr.height)] : null,
        屏上原始: nr ? [nr.width, nr.height] : null,
        中心Y: nr ? Math.round(nr.y + nr.height / 2) : null,
        状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
      };
    }, 音频ID);

    // 反推：屏上原始浮点 ÷ 落点 ⇒ 算法宽 W（比「屏上取整 ÷ 落点」精确得多）
    if (记.定位后.屏上原始 && 记.定位后.落点) {
      记.反推W = +(记.定位后.屏上原始[0] / 记.定位后.落点).toFixed(4);
      记.屏上应等于布局乘落点 = [记.定位后.布局宽 * 记.定位后.落点, 记.定位后.布局高 * 记.定位后.落点];
    }
    log(`【${臂.名}】落点 ${记.定位后.落点}（${记.定位后.aria}）｜ 布局 ${记.定位后.布局宽}×${记.定位后.布局高} ｜ 屏上原始 ${JSON.stringify(记.定位后.屏上原始)} ｜ 中心Y ${记.定位后.中心Y} ｜ 反推W ${记.反推W}`);
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 ${臂.名} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  out.臂.push(记);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

log('写入 ' + OUT);
await b.close();
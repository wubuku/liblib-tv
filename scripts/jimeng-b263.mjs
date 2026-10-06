/**
 * 批次 263：**补上取景律的第 7 族 —— `subject`（`W = 352`）**。
 *
 * 📌 背景（批次 262 挖出来的缺口）：
 *   画布上 `76` 个节点里**一个主体节点都没有** ⇒ 批次 256 的「`6` 族普查」里
 *   `subject` **根本没出现** ⇒ 🔴 **「`412` 律是通性」这句话至今只覆盖 `6` 族**
 *   （text / timeline / audio / image / external / video），**第 `7` 族一次都没测过**。
 *   而 `20-reference.md` 明写主体节点是 **`352×352`** ⇒ `W = 352`，
 *   这个 `W` 也**不在已验过的 `{320, 569, 1200}` 里面** ⇒ **换了个宽度再验一族**。
 *
 * 📌 **预测先算好**（立规 129：现象宽度要先算出来，而且它不是常数）：
 *   `W = 352` ⇒ 四段折线的接缝：
 *     `w = 440.16`（应用下限 `0.08` 交点）、`w = 512`（窄侧斜坡交族内地板 `100/352`）、
 *     `w = 632`（族内地板交宽侧斜坡）、`w = 708`（宽侧斜坡触封顶 `0.5`）。
 *   ⇒ 选 `w = 460 / 500 / 512 / 632 / 708 / 300`：
 *     **三个接缝全部选上**（`512`、`632`、`708`），让预测在最容易被推翻的位置挨打。
 *
 * 📌 **可逆性是硬要求**（立规 140）：
 *   本批**必须新建一个主体节点**（画布上默认没有），量完**删掉**，
 *   并**在实验流程之外**再开一页核对末态 ⇒ 必须回到 **`76` 个节点 / `0` 边 / `0` 选中**。
 *   ⚠️ 每臂**开新页**（批次 260 已证 `resize` 不重算，只有「定位」会重算）。
 *
 * 🔴 纪律：
 *   · **绝不点任何生成按钮**（生成 = 扣费）；主体节点不弹生成面板，但仍不看即点；
 *   · 删除只用 **⌫ / Backspace**（手册记载的删除键），失败再退到 `⌘Z`，**并如实记录用了哪个**；
 *   · 不点「保存到主体库」、不分享、不上传、不触发任何生成、不进扣费页。
 *
 * 用法：node scripts/jimeng-b263.mjs      （读数落盘 /tmp/b263.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B263_OUT || '/tmp/b263.json';
const 高 = 720;
const W = 352;                       // 📌 来自批次 262 实测的 offsetWidth
const 宽表 = [460, 500, 512, 632, 708, 300];

const log = (...a) => console.log(a.join(' '));

// 📌 预测与实测分开记，不允许看到实测再改预测
const 预测 = (w, Wd) => {
  const 应用地板 = 0.08, 族内地板 = 100 / Wd, 封顶 = 0.5;
  const 窄 = w - 412, 宽 = w - 532;
  let 落点;
  if (窄 <= 应用地板 * Wd) 落点 = 应用地板;
  else if (窄 <= 100) 落点 = 窄 / Wd;
  else if (宽 <= 100) 落点 = 族内地板;
  else 落点 = Math.min(宽 / Wd, 封顶);
  const 区 = (窄 <= 应用地板 * Wd) ? '应用下限' : (窄 <= 100 ? '窄侧斜坡' : (宽 <= 100 ? '族内地板' : '宽侧斜坡'));
  return { 落点: +落点.toFixed(9), 区 };
};

const 数节点 = (p) => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);

const 找工具条项 = (p, 名) => p.evaluate((nm) => {
  const b = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === nm);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  if (r.width < 4 || r.height < 4) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, 名);

const out = { 轮次: 'b263', 高, W, 宽表, 建节点: {}, 臂: [], 收尾: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

// ============ 第 1 步：建一个主体节点 ============
let 主体id = null, 主体名 = null;
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(7000);
    const 基线 = await 数节点(p);
    out.建节点.基线 = 基线;
    log(`建节点前：${基线} 个节点`);
    if (基线 !== 76) throw new Error(`基线不是 76（是 ${基线}），中止本批`);

    const 位 = await 找工具条项(p, '主体');
    if (!位) throw new Error('工具条里找不到「主体」');
    await p.mouse.click(位[0], 位[1]);
    await p.waitForTimeout(3500);
    const 建后 = await 数节点(p);
    out.建节点.建后 = 建后;
    const 新 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node'))
      .map((n) => ({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'), t: n.style.transform, off: [n.offsetWidth, n.offsetHeight] }))
      .filter((x) => (x.aria || '').startsWith('主体')));
    out.建节点.候选 = 新;
    log(`建后：${建后} 个节点；主体节点：${JSON.stringify(新)}`);
    if (建后 !== 基线 + 1) throw new Error(`建节点没成功（${基线} → ${建后}）`);
    if (!新.length) throw new Error('没找到新建的主体节点');
    主体id = 新[0].id; 主体名 = 新[0].aria;
    out.建节点.id = 主体id; out.建节点.aria = 主体名;
    log(`✅ 主体节点：${主体名}（${主体id}）offsetWidth=${新[0].off[0]}`);
  } catch (e) {
    out.建节点.错误 = e.message;
    log('🔴 建节点失败：' + e.message);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

if (主体id) {
  // ============ 第 2 步：每臂开新页，搜索定位，量 ============
  for (const 宽 of 宽表) {
    const p = await ctx.newPage();
    const 记 = { 宽, 高, W };
    Object.assign(记, 预测(宽, W));
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

      const 短名 = 主体id.replace(/^node_/, '');
      let 点 = null;
      for (const 词 of [主体名.replace('主体 node: ', ''), '主体']) {
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
      }, 主体id);

      if (记.定位后.屏上原始 && 记.定位后.落点) {
        记.反推W = +(记.定位后.屏上原始[0] / 记.定位后.落点).toFixed(4);
      }
      记.命中预测 = 记.定位后.落点 != null && Math.abs(记.定位后.落点 - 记.预测_落点) < 5e-6;
      log(`【主体@${宽}】${记.区} 预测 ${记.预测_落点} → 实测 ${记.定位后.落点}（${记.定位后.aria}）`
        + `｜屏上 ${JSON.stringify(记.定位后.屏上原始)}｜反推W ${记.反推W}｜中心Y ${记.定位后.中心Y}`
        + `｜${记.命中预测 ? '✅' : '❌ 不符'}`);
    } catch (e) {
      记.错误 = e.message;
      log(`🔴 主体@${宽} ${e.message}`);
    } finally {
      try { await p.close(); } catch (e) { /* 忽略 */ }
    }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));   // 📌 每臂独立落盘（立规 140）
  }
}

// ============ 第 3 步：删掉主体节点，回到 76 ============
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(7000);
    const 前 = await 数节点(p);
    out.收尾.删前 = 前;
    log(`\n收尾：删前 ${前} 个节点`);
    if (主体id && 前 === 77) {
      // 📌 先用搜索定位选中它（与各臂同一条路，顺带再验一次定位）
      const 钮 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('button, [role="button"]'))
          .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      await p.mouse.click(钮[0], 钮[1]);
      await p.waitForTimeout(1500);
      const 短名 = 主体id.replace(/^node_/, '');
      await p.evaluate(() => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        if (inp) { inp.focus(); inp.select(); }
      });
      await p.keyboard.type('主体', { delay: 85 });
      await p.waitForTimeout(2200);
      const 点 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }, 短名);
      if (点) {
        await p.mouse.click(点[0], 点[1]);
        await p.waitForTimeout(2500);
        await p.keyboard.press('Escape');
        await p.waitForTimeout(800);
        const 选中数 = await p.evaluate(() => {
          const m = document.body.innerText.match(/(\d+) nodes, \d+ edges, (\d+) selected/);
          return m ? Number(m[2]) : null;
        });
        log(`   定位后选中数 = ${选中数}`);
        // 📌 删除只用 ⌫ / Backspace（手册记载的键）
        await p.keyboard.press('Backspace');
        await p.waitForTimeout(2500);
        const 后 = await 数节点(p);
        out.收尾.用Backspace后 = 后;
        log(`   ⌫ 之后：${后} 个节点`);
        if (后 !== 76) {
          log(`   ⚠️ ⌫ 没删掉，退到 ⌘Z`);
          await p.keyboard.press('Meta+z');
          await p.waitForTimeout(2500);
          const 再 = await 数节点(p);
          out.收尾.用MetaZ后 = 再;
          log(`   ⌘Z 之后：${再} 个节点`);
        }
      } else {
        out.收尾.错 = '搜不到主体节点，无法选中';
      }
    }
  } catch (e) {
    out.收尾.错误 = e.message;
    log('🔴 收尾失败：' + e.message);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ============ 第 4 步：**在实验流程之外**再查一次末态（立规 140） ============
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(7000);
    const 独立 = await p.evaluate(() => {
      const ns = [...document.querySelectorAll('.react-flow__node')];
      return {
        个数: ns.length,
        主体: ns.filter((n) => (n.getAttribute('aria-label') || '').startsWith('主体')).map((n) => n.getAttribute('aria-label')),
        状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
      };
    });
    out.独立复查 = 独立;
    log(`\n=== 独立复查（新开页）===\n${JSON.stringify(独立, null, 1)}`);
    out.回到基线 = 独立.个数 === 76;
    log(out.回到基线 ? '✅ 已回到基线 76' : `🔴 未回到基线（${独立.个数}）`);
  } catch (e) {
    out.独立复查错 = e.message;
    log('🔴 独立复查失败：' + e.message);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
}

const 好 = out.臂.filter((a) => !a.错误 && a.命中预测 != null);
out.命中数 = 好.filter((a) => a.命中预测).length;
out.总臂数 = out.臂.length;
log(`\n=== 汇总：${out.命中数} / ${out.总臂数} 命中 ===`);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);
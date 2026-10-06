/**
 * 批次 232：在**凹口**这个订正后的模型下，重判「`w*` 到底由什么决定」。
 *
 * 🔴 批次 231 已经确定了两件事：
 *   ① **`w*` 是「按族」的规则** —— 同为 `320×320` 的两个音频节点（坐标、`z-index`、
 *      创建时间全不同）在 `1212/1215/1218` 的落点**逐字相同**。
 *   ② 那个窗口是**凹口**（两侧都是 `0.5`），不是斜坡 ⇒ 批次 223/226 的
 *      「CSS 尺寸不决定带子」**是在斜坡模型下得出的，需要重判**。
 *
 * 🔴 还悬着的那一个反例：`视频 1`（`320×569`，`react-flow__node-video`）`w* = 1212`，
 * 而批次 223 记的**上传结果媒体视频**（`569×320`，**同为 `react-flow__node-video`**）
 * 是 `≈1202`。若那半句成立，则**族之内还要再按 CSS 宽度分** ——
 * 「`w*` 只由族决定」就不成立。
 *
 * 📌 本批的正取手：那个 `569×320` 的视频节点**已经被删掉了**（本批开页清点：
 *    画布 `76` 个节点里 `video` kind **只剩 `视频 1` 一个**）。
 *    但批次 225 实测过：**新建的空视频节点就是 `569×320`**（与上传结果同尺寸同 class，
 *    只差有没有 `<img>`）⇒ **新建一个视频节点，就等于把那个对照组请回来。**
 *
 * 📌 判读（写死，避免事后找说法）：
 *   · 新视频节点在 `1212` 落点 `= 0.260267`（= `z₀`、斜坡）⇒ **与 `视频 1` 同族同起点**
 *     ⇒ **`w*` 只由 kind 决定，CSS 宽度不分族** ⇒ 批次 226 的结论在凹口模型下**得到确认**
 *   · 新视频节点在 `1212` 落点 `= 0.5`（封顶）⇒ 它的凹口不在 `1212`
 *     ⇒ **族之内确实还要再按别的分** ⇒ 批次 223/226 的结论要再收窄
 *
 * 📌 方法纪律（本批的立意就是它）：
 *   **不扫、不二分**，只**直接测模型最关键的预言**（立规 113）。
 *   凹口是局部窗口，往两侧扫只会读到平的 `0.5`（批次 229/230 那 `56` 臂就是这么白扫的）。
 *
 * ⛔ 只新建 / 删除**本会话自己创建**的那一个节点；不碰别人的节点；
 *   不触发生成、不进入扣费页、不点「保存到主体库」、不分享、不下载。
 *
 * 用法：node scripts/jimeng-b232.mjs  （原始读数 /tmp/b232.json，日志 /tmp/b232.log）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b232.json';
// 只测这几个宽度：1212 是「视频 1 的 w*」＝模型的关键预言；1195 / 1235 是两侧的平段作对照；
// 1202 是批次 223 记的「媒体视频 ≈1202」那半句，测一下新视频节点在那一档是什么样。
const 宽度档 = [1195, 1202, 1212, 1235];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b232', 宽度档, 新节点: null, 臂: [], 删除: null };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  const z = /z-index:\s*(-?\d+)/.exec(n.style.cssText || '');
  const k = /react-flow__node-(\w+)/.exec(n.className || '');
  return {
    id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    kind: k ? k[1] : null, css: [n.offsetWidth, n.offsetHeight],
    z: z ? Number(z[1]) : null, 有img: !!n.querySelector('img'),
    画布: m ? [Math.round(Number(m[1]) * 100) / 100, Math.round(Number(m[2]) * 100) / 100] : null,
  };
}));

async function 臂(w, 靶) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const z0 = await p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    if (!(await 清单(p)).some((n) => n.id === 靶.id)) return { w, 无效臂: '节点不在' };

    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    });
    if (!钮) return { w, 无效臂: '找不到搜索钮' };
    await p.mouse.click(钮[0] + Math.round(钮[2] / 2), 钮[1] + Math.round(钮[3] / 2));
    await p.waitForTimeout(1500);
    const 有框 = await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (!inp) return false;
      inp.focus(); inp.select();
      return true;
    });
    if (!有框) return { w, 无效臂: '找不到搜索输入框' };

    let 用的词 = null;
    for (const 词 of 靶.词) {
      await p.evaluate(() => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        if (inp) { inp.focus(); inp.select(); }
      });
      await p.keyboard.type(词, { delay: 85 });
      await p.waitForTimeout(2200);
      const 读 = await p.evaluate((nid) => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        const 行 = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        return { 回读: inp ? inp.value : null, 有行: !!行 };
      }, 靶.id.replace(/^node_/, ''));
      if (读.有行 && 读.回读 === 词) {
        const 点 = await p.evaluate((nid) => {
          const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
          if (!e) return null;
          const r = e.getBoundingClientRect();
          return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
        }, 靶.id.replace(/^node_/, ''));
        if (点) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(4600); 用的词 = 词; break; }
      }
    }
    if (!用的词) return { w, 无效臂: '候选词都没命中那一行' };

    const 采 = async () => p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const r = n ? n.getBoundingClientRect() : null;
      return {
        中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
        屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
        vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null,
      };
    }, 靶.id);
    const 三采 = [];
    for (let i = 0; i < 3; i++) { 三采.push(await 采()); await p.waitForTimeout(450); }
    const 末 = 三采[2];
    return {
      w, z0, 用的词,
      scale: 末.vp ? 末.vp[2] : null,
      屏上: 末.屏上, 中心: 末.中心,
      页内一致: [...new Set(三采.map((x) => x.vp && x.vp[2]))].length === 1,
      分支: 末.中心 && 末.中心[1] === 360 ? '居中50' : '斜坡',
      封顶: 末.vp ? Math.abs(末.vp[2] - 0.5) < 1e-9 : null,
    };
  } catch (e) {
    return { w, 无效臂: '异常 ' + e.message };
  } finally {
    try { await p.close(); } catch (e) { /* 页签可能被别的会话关掉 */ }
  }
}

const 打印 = (r) => (r.无效臂
  ? `  w=${r.w} ⛔ ${r.无效臂}`
  : `  w=${r.w} z0=${r.z0} → s=${r.scale} 屏上=${JSON.stringify(r.屏上)} 中心Y=${r.中心 ? r.中心[1] : null} 分支=${r.分支} ${r.封顶 ? '封顶' : '凹口内'}`);

let 自建 = null;
try {
  // ---- 步骤 1：新建一个视频节点（批次 225 实测它是 569×320，与上传结果同尺寸） ----
  {
    const p = await ctx.newPage();
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const 建前 = (await 清单(p)).map((n) => n.id);
    const 入口 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '视频');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    });
    if (!入口) throw new Error('找不到「视频」入口');
    await p.mouse.click(入口[0] + Math.round(入口[2] / 2), 入口[1] + Math.round(入口[3] / 2));
    await p.waitForTimeout(4000);
    const 新增 = (await 清单(p)).filter((n) => !建前.includes(n.id));
    if (新增.length !== 1) throw new Error('新建节点数不是 1：' + 新增.length);
    const n = 新增[0];
    自建 = { id: n.id, 名: '新视频', 词: [String(n.aria).replace(/^.*?node:\s*/, ''), '视频', (String(n.aria).match(/\d+/) || [''])[0]].filter(Boolean), css: n.css, kind: n.kind, z: n.z, 画布: n.画布, 有img: n.有img };
    out.新节点 = 自建;
    log('【新建】' + JSON.stringify(自建));
    log('【对照】视频 1 = 320×569 / video / 已知 w* = 1212（批次 221 实测）');
    log('  📌 批次 223 记的「上传结果媒体视频 569×320 / video / ≈1202」那个节点**已被删除**，');
    log('     而批次 225 实测「新建的空视频节点就是 569×320」⇒ 本次新建的节点正好顶替那个对照组。');
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }

  // ---- 步骤 2：只测模型最关键的预言 + 两侧对照 ----
  log('════ 逐档 ════');
  for (const w of 宽度档) {
    const r = await 臂(w, 自建);
    out.臂.push(r);
    log(打印(r));
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));   // 每臂都落盘（立规 111）
  }

  // ---- 步骤 3：判读 ----
  const 在1212 = out.臂.find((r) => r.w === 1212 && !r.无效臂);
  const 在1202 = out.臂.find((r) => r.w === 1202 && !r.无效臂);
  const 有效 = out.臂.filter((r) => !r.无效臂);
  out.结论 = {
    有效臂: 有效.length,
    一致性: 有效.every((r) => r.页内一致),
    凹口内档: 有效.filter((r) => r.封顶 === false).map((r) => r.w),
    在1212落点: 在1212 ? 在1212.scale : null,
    在1202落点: 在1202 ? 在1202.scale : null,
    参照视频1在1212: 0.260267,
    判读: !在1212 ? '1212 那一臂无效，不能下结论'
      : (在1212.封顶 === false
        ? '新视频在 1212 落在凹口内且落点 = z₀ ⇒ 与 视频 1 同起点 ⇒ w* 只由 kind 决定，CSS 宽度不分族'
        : '新视频在 1212 已封顶（落点 0.5）⇒ 它的凹口不在 1212 ⇒ 族之内还要再按别的分'),
  };
  log('【结论】' + JSON.stringify(out.结论));
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
} catch (e) {
  out.出错 = e.message;
  log('🔴 ' + e.message);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

// ---- 收尾：删掉自建节点（Backspace；批次 228 实测 Delete 对已选中节点无效） ----
if (自建) {
  try {
    const p = await ctx.newPage();
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);
    const 点 = await p.evaluate((nid) => {
      const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      for (let dy = -r.height / 4; dy <= r.height / 4; dy += 6) {
        for (let dx = -r.width / 4; dx <= r.width / 4; dx += 6) {
          const x = Math.round(r.x + r.width / 2 + dx);
          const y = Math.round(r.y + r.height / 2 + dy);
          const h = document.elementFromPoint(x, y);
          if (h && h.closest(`.react-flow__node[data-id="${nid}"]`) && !h.closest('[role="dialog"], button, a, input, textarea')) return [x, y];
        }
      }
      return null;
    }, 自建.id);
    if (点) {
      await p.mouse.click(点[0], 点[1]);
      await p.waitForTimeout(1200);
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(2600);
    }
    out.删除 = { id: 自建.id, 还在: (await 清单(p)).some((n) => n.id === 自建.id) };
    log('【删除】' + JSON.stringify(out.删除));
    out.收尾状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    log('【收尾】' + out.收尾状态行);
    try { await p.close(); } catch (e) { /* 忽略 */ }
  } catch (e) { log('🔴 收尾 ' + e.message); }
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
await b.close();